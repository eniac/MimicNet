#!/usr/bin/env python3

import argparse
import math
import numpy as np
import os
import pickle
import statistics
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable, Function

from common.discretization import *
from common.loss import *
from common.utils import *

use_cuda = torch.cuda.is_available()
device = torch.device("cuda" if use_cuda else "cpu")

print("USING CUDA:", use_cuda)

is_log = False

##  Feature vector for 2-rack DCTCP (20 features)
##      0 1 2 3 - Congestion state
##      4 5 6 7 - Server
##      8 9 - Agg
##      10 11 - Agg interface
##      12 13 - ToR
##      14 - Time since last packet
##      15 - EWMA
##      16 - ECN
##      17 - Last drop prediction
##      18 - Last latency prediction
##      19 - Last ECN prediction

class NetworkApproxLSTM(nn.Module):
    def __init__(self, input_size=20, num_layers=2, window_size=10):
        super(NetworkApproxLSTM, self).__init__()

        self.input_size = input_size
        # remember window_size packets
        self.hidden_size = input_size * window_size
        self.num_layers = num_layers
        self.window_size = window_size
        self.output_size = 1
        self.variant = "DCTCP"

        # batch_first – If True, then the input and output tensors are provided
        # as (batch, seq, feature) or (batch, num_layers, hidden_size).
        self.lstm = nn.LSTM(self.input_size, self.hidden_size, self.num_layers,
                            batch_first = True) 

        self.linearL = nn.Linear(self.hidden_size, 1)
        self.linearD = nn.Linear(self.hidden_size, 1)
        self.linearE = nn.Linear(self.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def init_hidden(self, batch_size = 1):
        h_t = torch.zeros(batch_size, self.num_layers, self.hidden_size,
                          dtype=torch.double).to(device)
        c_t = torch.zeros(batch_size, self.num_layers, self.hidden_size,
                          dtype=torch.double).to(device)
        self.hidden_state = (h_t, c_t)

    def forward(self, data):
        X = data.view(-1, self.window_size, self.input_size)
        batch_size = X.shape[0]
        lstm_out, self.hidden_state = self.lstm(X, (self.hidden_state[0].view(self.num_layers, batch_size, -1), self.hidden_state[1].view(self.num_layers, batch_size, -1))) ## Qizhen: to tune hidden state

        l_output = self.linearL(lstm_out[:,-1,:].view(batch_size, -1))
        d_output = self.sigmoid(self.linearD(lstm_out[:,-1,:].view(batch_size, -1)))
        e_output = self.sigmoid(self.linearE(lstm_out[:,-1,:].view(batch_size, -1)))
        return d_output, l_output, e_output


def discretize_features(X, y_l, granu = 1000):
    Last, meta_last = discretize((X.T[-3]).astype(float), granu)
    EWMA, meta_ewma = discretize((X.T[-2]).astype(float), granu)
    Latency, meta_latency = discretize(y_l.astype(float), granu)

    Last = np.array([[l] for l in Last]).astype(int)
    EWMA = np.array([[e] for e in EWMA]).astype(int)
    Latency = np.array(Latency).astype(int)

    data = np.concatenate((X.T[:-3].T, Last, EWMA, X.T[-1:].T), axis = 1)

    return data, Latency, meta_last, meta_ewma, meta_latency

def format_data(X, y_d, y_l, y_e, num_servers = 4, degree = 2,
                network_states = 4, include_label = False):
    Congestion = convertToOneHot((X.T[0]).astype(int), network_states)
    Server = convertToOneHot((X.T[1]).astype(int), num_servers)
    Agg = convertToOneHot(X.T[2].astype(int), degree)
    Agg_intf = convertToOneHot(X.T[3].astype(int), degree)
    ToR = convertToOneHot(X.T[4].astype(int), degree)

    data = np.concatenate((Congestion, Server, Agg, Agg_intf, ToR, X.T[5:].T), \
                          axis = 1)

    if not include_label:
        return data, y_d, y_l, y_e

    data = np.concatenate((data[1:], np.stack((y_d[:-1], y_l[:-1], y_e[:-1]), axis=1)), axis=1)
    return data, y_d[1:], y_l[1:], y_e[1:]

def pad_zeros(X, y_d, y_l, y_e, window_size):
    pad_size = window_size - 1
    print ("X shape", X.shape)
    empty_X = np.zeros((pad_size, len(X[0]))).astype(int)
    print ("empty X shape", empty_X.shape)
    empty_y = np.zeros((pad_size)).astype(int)
    return np.concatenate((empty_X, X)), np.concatenate((empty_y, y_d)), \
           np.concatenate((empty_y, y_l)), np.concatenate((empty_y, y_e))

def train_both_data_generator(large_train_samples, large_train_d_targets,
                              large_train_l_targets, large_train_e_targets,
                              window_size, index, batch_size):
    if index + window_size + (batch_size - 1) > len(large_train_samples):
        return None
    train_batch = [large_train_samples[index+i : index+i+window_size] for i in range(batch_size)]
    train_batch = np.array(train_batch).reshape(len(train_batch), len(train_batch[0]), len(train_batch[0][0]))
    d_label_batch = [large_train_d_targets[index+i+window_size - 1] for i in range(batch_size)]
    l_label_batch = [large_train_l_targets[index+i+window_size - 1] for i in range(batch_size)]
    d_label_batch = np.array(d_label_batch).reshape(len(d_label_batch), 1)
    l_label_batch = np.array(l_label_batch).reshape(len(l_label_batch), 1)
    e_label_batch = [large_train_e_targets[index+i+window_size - 1] for i in range(batch_size)]
    e_label_batch = np.array(e_label_batch).reshape(len(e_label_batch), 1)
    return train_batch, d_label_batch, l_label_batch, e_label_batch

def train(model, data, target_drop, target_latency, target_ecn, optimizer,
          alpha=0.33, beta=0.33, drop_weight=0.5, ecn_weight=0.5,
          latency_loss='huber', discretized_max=1000):
    model.init_hidden(data.shape[0])
    data = data.to(device, dtype=torch.double)
    target_drop = target_drop.to(device, dtype=torch.double)
    target_latency = target_latency.to(device, dtype=torch.double)
    target_ecn = target_ecn.to(device, dtype=torch.double)

    pred_drop, pred_latency, pred_ecn = model(data)

    pred_drop = pred_drop.view(-1, 1)
    pred_latency = pred_latency.view(-1, 1)
    target_drop = target_drop.view(-1, 1)
    target_latency = target_latency.view(-1, 1)
    loss_drop = weighted_binary_cross_entropy(pred_drop, target_drop, weight0=(1-drop_weight))

    if latency_loss == 'huber':
        loss_latency = rescaled_huber_loss(pred_latency, target_latency, discretized_max = discretized_max)
    elif latency_loss == 'mse':
        loss_latency = rescaled_mean_squared_error(pred_latency, target_latency, discretized_max = discretized_max)
    elif latency_loss == 'male':
        loss_latency = rescaled_mean_absolute_log_error(pred_latency, target_latency, discretized_max = discretized_max)
    elif latency_loss == 'mae':
        loss_latency = rescaled_mean_absolute_error(pred_latency, target_latency, discretized_max = discretized_max)
    else:
        loss_latency = mean_absolute_error(pred_latency, target_latency)

    loss = alpha*loss_latency + beta*loss_drop

    pred_ecn = pred_ecn.view(-1, 1)
    target_ecn = target_ecn.view(-1, 1)
    loss_ecn = weighted_binary_cross_entropy(pred_ecn, target_ecn, weight0=(1-ecn_weight))
    loss += (1 - alpha - beta)*loss_ecn

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()

def test(model, data, target_drop, target_latency, target_ecn,
         alpha=0.33, beta=0.33, drop_weight=0.5, ecn_weight=0.5,
         latency_loss='huber', discretized_max=1000):
    model.init_hidden(data.shape[0])
    data = data.to(device, dtype=torch.double)
    target_drop = target_drop.to(device, dtype=torch.double)
    target_latency = target_latency.to(device, dtype=torch.double)
    target_ecn = target_ecn.to(device, dtype=torch.double)

    pred_drop, pred_latency, pred_ecn = model(data)

    pred_drop = pred_drop.view(-1, 1)
    pred_latency = pred_latency.view(-1, 1)
    target_drop = target_drop.view(-1, 1)
    target_latency = target_latency.view(-1, 1)
    lossDrop = weighted_binary_cross_entropy(pred_drop, target_drop, weight0=(1-drop_weight))

    if latency_loss == 'huber':
        lossLatency = rescaled_huber_loss(pred_latency, target_latency, discretized_max = discretized_max)
    elif latency_loss == 'mse':
        lossLatency = rescaled_mean_squared_error(pred_latency, target_latency, discretized_max = discretized_max)
    elif latency_loss == 'male':
        lossLatency = rescaled_mean_absolute_log_error(pred_latency, target_latency, discretized_max = discretized_max)
    elif latency_loss == 'mae':
        lossLatency = rescaled_mean_absolute_error(pred_latency, target_latency, discretized_max = discretized_max)
    else:
        lossLatency = mean_absolute_error(pred_latency, target_latency)

    loss = alpha*lossLatency + beta*lossDrop

    pred_ecn = pred_ecn.view(-1, 1)
    target_ecn = target_ecn.view(-1, 1)
    lossEcn = weighted_binary_cross_entropy(pred_ecn, target_ecn, weight0=(1-ecn_weight))
    loss += (1 - alpha - beta)*lossEcn

    return loss.item()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("data_dict", type=str,
                        help="Data dictionary pickle file")
    parser.add_argument("degree", type=int,
                        help="Number of ToRs/Aggs/AggUplinks per cluster")

    parser_saveload = parser.add_argument_group('model saving/loading')
    parser_saveload.add_argument("--model_name", type=str,
                                 help="Output model filename")
    parser_saveload.add_argument("--direction", type=str,
                                 choices=['INGRESS', 'EGRESS'],
                                 help="direction hint to prepend to model name")
    parser_saveload.add_argument("--load_model", type=str,
                                 help="path to a pretrained model")

    parser_model = parser.add_argument_group('model and feature options')
    parser_model.add_argument("--num_layers", type=int,
                              help="number of layers in lstm")
    parser_model.add_argument("--double_type", dest="double_type",
                              action="store_true",
                              help="make the model double type")
    parser_model.add_argument("--window_size", type=int,
                              help="number of packets in the window")
    parser_model.add_argument("--include_label", dest="include_label",
                              action="store_true",
                              help="Include previous predictions of drop and " \
                                   "latency in feature set")
    parser_model.add_argument("--exclude_label", dest="include_label",
                              action="store_false",
                              help="Exclude previous predictions of drop and " \
                                   "latency in feature set")
    parser_model.add_argument("--disc_factor", type=float,
                              help="Discretization factor")

    parser_loss = parser.add_argument_group('loss options')
    parser_loss.add_argument("--latency_loss", type=str,
                             choices=['huber', 'mse', 'male', 'mae',
                                      'mae_norescale'],
                             help="Loss function for latency")
    parser_loss.add_argument("--drop_weight", type=float,
                             help="weight on drops [0-1]")
    parser_loss.add_argument("--ecn_weight", type=float,
                             help="weight on drops [0-1]")
    parser_loss.add_argument("--alpha", type=float,
                             help="Weight parameter for latency influence")
    parser_loss.add_argument("--beta", type=float,
                             help="Weight parameter for drop influence")

    parser_train = parser.add_argument_group('training options')
    parser_train.add_argument("--num_epochs", type=int,
                              help="number of epoch to run for")
    parser_train.add_argument("--batch_size", type=int,
                              help="How many examples per batch")
    parser_train.add_argument("--learning_rate", type=float,
                              help="Learning rate constant")
    parser_train.add_argument("--train_size", type=int,
                              help="number of packets for training " \
                                   "(-1 means all data)")
    parser_train.add_argument("--train_size_prop", type=float,
                              help="Proportion of packets for training (do " \
                                   "not set this for all data)")
    parser_train.add_argument("--enable_validation", dest="enable_validation",
                              action="store_true",
                              help="split 10%% of data to be validation data")

    parser.set_defaults(direction="INGRESS")

    parser.set_defaults(num_layers=2)
    parser.set_defaults(double_type=True)
    parser.set_defaults(window_size=12)
    parser.set_defaults(include_label=True)
    parser.set_defaults(disc_factor=1000)

    parser.set_defaults(latency_loss='huber')
    parser.set_defaults(drop_weight=0.9)
    parser.set_defaults(ecn_weight=0.9)
    parser.set_defaults(alpha=0.5)
    parser.set_defaults(beta=0.25)

    parser.set_defaults(num_epochs=10)
    parser.set_defaults(batch_size=128)
    parser.set_defaults(learning_rate=1e-4)
    parser.set_defaults(train_size=-1)
    parser.set_defaults(enable_validation=False)

    args = parser.parse_args()

    data_dict = args.data_dict
    degree = args.degree

    direction = args.direction

    num_layers = args.num_layers
    double_type = args.double_type
    window_size = args.window_size
    include_label = args.include_label
    disc_factor = args.disc_factor

    latency_loss = args.latency_loss
    drop_weight = args.drop_weight
    ecn_weight = args.ecn_weight
    alpha = args.alpha
    beta = args.beta

    num_epochs = args.num_epochs
    batch_size = args.batch_size
    learning_rate = args.learning_rate
    train_size = args.train_size
    enable_validation = args.enable_validation

    torch.cuda.manual_seed_all(22)
    torch.manual_seed(22)

    pdata = pickle.load(open(data_dict, 'rb'))
    X, y_d, y_l, y_e = pdata['X'], pdata['y_d'], pdata['y_l'], pdata['y_e']

    print("Discretizing with factor %s..." % disc_factor)
    X, y_l, dis_meta_last, dis_meta_ewma, dis_meta_latency = \
            discretize_features(X, y_l, disc_factor)
    print("meta_last =", dis_meta_last, "meta_ewma =", dis_meta_ewma,
          "meta_latency =", dis_meta_latency)

    # Trim for training
    if train_size != -1:
        X = X[:train_size]
        y_d = y_d[:train_size]
        y_l = y_l[:train_size]
        y_e = y_e[:train_size]
    if args.train_size_prop is not None:
        X = X[:round(len(X) * args.train_size_prop)]
        y_d = y_d[:round(len(y_d) * args.train_size_prop)]
        y_l = y_l[:round(len(y_l) * args.train_size_prop)]
        y_e = y_e[:round(len(y_e) * args.train_size_prop)]

    print("Formatting...")
    X, y_d, y_l, y_e = format_data(X, y_d, y_l, y_e, degree = degree,
                                   include_label = include_label)

    print("Priming...")
    X, y_d, y_l, y_e = pad_zeros(X, y_d, y_l, y_e, window_size)
    print("Feature vector size: ", X.shape)


    if args.model_name is None:
        if args.train_size_prop is None:
            model_name = "%s_LSTM_Pytorch_Double%s_SW%s_LAYER%s_FEAT%s_BATCH%s_WIN%s_Alpha%s_Beta%s_DWeight%s_EWeight%s_LatLoss%s_EPOCH%s" \
                       % (str(direction), str(double_type), str(degree),
                          str(num_layers), str(X.shape[1]), str(batch_size),
                          str(window_size), str(alpha), str(beta),
                          str(drop_weight), str(ecn_weight), str(latency_loss),
                          str(num_epochs))
        else:
            model_name = "%s_LSTM_Pytorch_Double%s_SW%s_FEAT%s_BATCH%s_WIN%s_Alpha%s_Beta%_DWeight%s_EWeight%s_EPOCH%s_PROP%s" \
                       % (str(direction), str(double_type), str(degree),
                          str(X.shape[1]), str(batch_size), str(window_size),
                          str(alpha), str(beta), str(drop_weight),
                          str(ecn_weight), str(num_epochs),
                          str(args.train_size_prop))
    else:
        model_name = args.model_name

    print("Model name =", model_name)

    start_epoch = 0

    if args.load_model:
        checkpoint = torch.load(args.load_model,
                                map_location=lambda storage, loc:storage)
        assert checkpoint["variant"] == "DCTCP"

        input_size = checkpoint["input_size"]
        window_size = checkpoint["window_size"]
        start_epoch = checkpoint["start_epoch"]
        print("Loading model from checkpoint:", args.load_model,
              "with", (start_epoch + 1), "epochs")
        model = NetworkApproxLSTM(input_size=input_size, window_size=window_size).to(device)
        if double_type:
            model.double()
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model = NetworkApproxLSTM(input_size=X.shape[1], num_layers=num_layers,
                                  window_size=window_size).to(device)
        if double_type:
            model.double()

    print(model)

    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    print ("batch size = %s" % batch_size)

    rs = [_ for _ in range(math.floor(X.shape[0]/batch_size) - 1)]

    # batches_in_epoch = math.floor(X.shape[0]/batch_size) - 1 - window_size
    for i in range(num_epochs):
        print('EPOCH: ', (i + start_epoch))
        if is_log:
            train_log.write("\nEPOCH: %s\n\n" % (i + start_epoch))

        index = 0
        steps = (X.shape[0] - window_size) / batch_size

        loss_list = []
        loss_count = []
        if enable_validation:
            val_loss_list = []
            val_loss_count = []

        while window_size + index + (batch_size - 1) <= X.shape[0]:
            cur_step = (int)(index/batch_size)

            X_train, Y_d_train, Y_l_train, Y_e_train = \
                    train_both_data_generator(X, y_d, y_l, y_e, window_size, \
                                              index, batch_size)
            X_train, Y_d_train, Y_l_train, Y_e_train = \
                    torch.from_numpy(X_train), \
                    torch.from_numpy(Y_d_train), \
                    torch.from_numpy(Y_l_train), \
                    torch.from_numpy(Y_e_train)

            if enable_validation:
                val_size = (int)(X_train.shape[0] * 0.1)
                X_test = X_train[-val_size:, :, :]
                Y_d_test = Y_d_train[-val_size:, :]
                Y_l_test = Y_l_train[-val_size:, :]

                X_train = X_train[:-val_size, :, :]
                Y_d_train = Y_d_train[:-val_size, :]
                Y_l_train = Y_l_train[:-val_size, :]

                Y_e_test = Y_e_train[-val_size:, :]
                Y_e_train = Y_e_train[:-val_size, :]

            loss_value = train(model, X_train, Y_d_train, Y_l_train, Y_e_train,
                               optimizer, alpha, beta, drop_weight, ecn_weight,
                               latency_loss, disc_factor)
            loss_list.append(loss_value)
            loss_count.append(len(X_train))
            if cur_step % 1000 == 0 or steps - cur_step <= 1:
                print('STEP: ', cur_step, '/', steps,
                         ' last loss: ', loss_value,
                         ' min loss: ', min(loss_list),
                         ' max loss: ', max(loss_list),
                         ' avg loss:', sum(loss_list)/ len(loss_list),
                         ' med loss:', statistics.median(loss_list))
            if enable_validation:
                val_loss_value = test(model, X_test, Y_d_test, Y_l_test, 
                                      Y_e_test, alpha, beta, drop_weight,
                                      ecn_weight, latency_loss,
                                      discretized_max = disc_factor)
                val_loss_list.append(val_loss_value)
                val_loss_count.append(len(X_test))
            index += batch_size

        print("Saving model...")
        save_ckpt(model_name + "_epoch" + str(start_epoch+i+1) + ".ckpt",
                  model, start_epoch + i,
                  dis_meta_last, dis_meta_ewma, dis_meta_latency)
        save_hdf5(model_name + "_epoch" + str(start_epoch+i+1) + ".hdf5",
                  model, device, start_epoch + i,
                  dis_meta_last, dis_meta_ewma, dis_meta_latency)

        print("Current train loss:", sum(loss_list)/sum(loss_count))
        if enable_validation:
            print("Current valid loss:", sum(val_loss_list)/sum(val_loss_count))

    print("Saving final model...")
    save_ckpt(model_name + ".ckpt", model, start_epoch + num_epochs,
              dis_meta_last, dis_meta_ewma, dis_meta_latency)
    save_hdf5(model_name + ".hdf5", model, device, start_epoch + num_epochs,
              dis_meta_last, dis_meta_ewma, dis_meta_latency)

    if is_log:
        train_log.close()
