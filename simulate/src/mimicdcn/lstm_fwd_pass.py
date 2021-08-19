"""
100k w/ GPU
real    1m9.765s
user    1m6.536s
sys     0m3.132s

100k w/ CPU
real    1m36.717s
user    30m12.380s
sys     0m25.692s

10k w/ CPU
real    0m10.081s
user    3m4.440s
sys     0m2.572s
"""

DEBUG = False

import h5py
import sys
import torch
import torch.autograd as autograd
import torch.nn as nn

import numpy as np

#DEVSTR = 'cuda'
DEVSTR = 'cpu'
device = torch.device(DEVSTR)

######################################################################
# Create the model:

class MimicNetLSTM(nn.Module):
    def __init__(self, input_size = 18, num_layers = 2, window_size = 10,
                 variant = "TCP",
                 dis_meta_last_min = 0.0, dis_meta_last_step = 0.0,
                 dis_meta_ewma_min = 0.0, dis_meta_ewma_step = 0.0,
                 dis_meta_latency_min = 0.0, dis_meta_latency_step = 0.0):
        super(MimicNetLSTM, self).__init__()

        self.input_size = input_size
        self.hidden_size = input_size * window_size
        self.num_layers = num_layers
        self.window_size = window_size
        self.output_size = 1
        self.variant = variant

        self.dis_meta_last_min = dis_meta_last_min
        self.dis_meta_last_step = dis_meta_last_step
        self.dis_meta_ewma_min = dis_meta_ewma_min
        self.dis_meta_ewma_step = dis_meta_ewma_step
        self.dis_meta_latency_min = dis_meta_latency_min
        self.dis_meta_latency_step = dis_meta_latency_step

        # batch_first – If True, then the input and output tensors are provided
        # as (batch, seq, feature) or (batch, num_layers, hidden_size).
        self.lstm = nn.LSTM(self.input_size, self.hidden_size, self.num_layers,
                            batch_first = True)

        self.linearL = nn.Linear(self.hidden_size, 1)
        self.linearD = nn.Linear(self.hidden_size, 1)
        self.sigmoid = nn.Sigmoid()
        if self.variant == "DCTCP":
            self.linearE = nn.Linear(self.hidden_size, 1)

        self.prev_drop = 0
        self.prev_latency = 0
        self.prev_ecn = 0

    def init_hidden(self, batch_size = 1):
        h_t = torch.zeros(batch_size, self.num_layers, self.hidden_size,
                          dtype = torch.double).to(device)
        c_t = torch.zeros(batch_size, self.num_layers, self.hidden_size,
                          dtype = torch.double).to(device)
        self.hidden_state = (h_t, c_t)

    def forward(self, data):
        data = data.view(1, 1, self.input_size)
        lstm_out, self.hidden_state = self.lstm(data, (self.hidden_state[0].view(self.num_layers, 1, -1), self.hidden_state[1].view(self.num_layers, 1, -1))) ## Qizhen: to tune hidden state

        X = lstm_out[:,-1,:].view(1, -1)
        l_output = self.linearL(X)
        d_output = self.sigmoid(self.linearD(X))

        if self.variant == "DCTCP":
            e_output = self.sigmoid(self.linearE(X))
            return d_output, l_output, e_output
        else:
            return d_output, l_output

######################################################################
def loadModel(model_name, standalone = False):
    print(model_name, file=sys.stderr)
    # if not standalone:
        # Necessary when embedded in C++ code
        # model_name = str(model_name, encoding='utf-8')
    state = torch.load(model_name, map_location=lambda storage, loc: storage)
    model = MimicNetLSTM(variant = state['variant'],
                         input_size = state['input_size'],
                         num_layers = state['num_layers'],
                         window_size = state['window_size'],
                         dis_meta_last_min = state['dis_meta_last_min'],
                         dis_meta_last_step = state['dis_meta_last_step'],
                         dis_meta_ewma_min = state['dis_meta_ewma_min'],
                         dis_meta_ewma_step = state['dis_meta_ewma_step'],
                         dis_meta_latency_min = state['dis_meta_latency_min'],
                         dis_meta_latency_step = state['dis_meta_latency_step']
                        ).to(device)
    model.double()
    model.load_state_dict(state['model_state_dict'])
    model.init_hidden()
    return model

######################################################################
# from https://stackoverflow.com/questions/29831489/numpy-1-hot-array
def convertToOneHot(vector, num_classes=None):
    """
    Converts an input 1-D vector of integers into an output
    2-D array of one-hot vectors, where an i'th input value
    of j will set a '1' in the i'th row, j'th column of the
    output array.

    Example:
        v = np.array((1, 0, 4))
        one_hot_v = convertToOneHot(v)
        print one_hot_v

        [[0 1 0 0 0]
         [1 0 0 0 0]
         [0 0 0 0 1]]
    """

    assert isinstance(vector, np.ndarray)
    assert len(vector) > 0

    if num_classes is None:
        num_classes = np.max(vector)+1
    else:
        assert num_classes > 0
        assert num_classes >= np.max(vector)

    result = np.zeros(shape=(len(vector), num_classes))
    result[np.arange(len(vector)), vector] = 1
    return result.astype(int)

def format_record(model, x, num_servers = 4, degree = 2, network_states = 4,
                  include_label = True):
    #([delta_timestamp, network_state, server, agg, agg_intf, ToR, ewma, ecn]
    cong_state = convertToOneHot(np.array([x[0]]).astype(int), network_states)
    server = convertToOneHot(np.array([x[1]]).astype(int), num_servers)
    agg =  convertToOneHot(np.array([x[2]]).astype(int), degree)
    agg_intf = convertToOneHot(np.array([x[3]]).astype(int), degree)
    tor = convertToOneHot(np.array([x[4]]).astype(int), degree)

    # Discretization
    x[5] = int((x[5] - model.dis_meta_last_min) / model.dis_meta_last_step)
    x[6] = int((x[6] - model.dis_meta_ewma_min) / model.dis_meta_ewma_step)

    if include_label:
        # Discretization
        dis_latency = int((model.prev_latency - model.dis_meta_latency_min) \
                          / model.dis_meta_latency_step)
        if model.variant == "DCTCP":
            prev = np.array([[model.prev_drop, dis_latency, model.prev_ecn]])
        else:
            prev = np.array([[model.prev_drop, dis_latency]])
        data = np.concatenate(([cong_state, server, agg, agg_intf, tor,
                                np.array([x[5:]]), prev]), axis=1)
    else:
        data = np.concatenate(([cong_state, server, agg, agg_intf, tor,
                                np.array([x[5:]])]), axis=1)

    return data

######################################################################

def getValue(model, cong_state, server, agg, agg_intf, tor, delta_t, ewma,
             ecn = None):
    if model.variant == "DCTCP":
        feats = [cong_state, server, agg, agg_intf, tor, delta_t, ewma, ecn]
    else:
        feats = [cong_state, server, agg, agg_intf, tor, delta_t, ewma]
    data = format_record(model, feats)  # TODO: parameterize num_servers, etc

    if DEVSTR == 'cuda':
        data = tensor(data, dtype=torch.double, device=device)
    else:
        data = torch.from_numpy(data)

    pred = model(data)
    if DEBUG:
        print("Predicted:", pred)

    model.prev_drop = pred[0].item()
    model.prev_latency = model.dis_meta_latency_min \
                         + int(pred[1].item()) * model.dis_meta_latency_step

    if model.variant == "DCTCP":
        model.prev_ecn = pred[2].item()
        return (round(model.prev_drop), model.prev_latency, model.prev_ecn)
    else:
        return (round(model.prev_drop), model.prev_latency)


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("model_file", type=str,
                        help=".ckpt containing the model")
    parser.add_argument("-n", "--num_iterations", type=str,
                        help="number of iterations")
    parser.add_argument("--print", dest="print", action="store_true",
                        help="Print the predictions")
    parser.set_defaults(print=False)
    args = parser.parse_args()

    model_file = args.model_file
    iterations = 100

    if args.num_iterations:
        iterations = int(args.num_iterations)
    if args.print:
        DEBUG = True


    model = loadModel(args.model_file, standalone = True)
    for i in range(iterations):
        getValue(model, 0, 3, 0, 1, 0, 0.018506378999999996, 0.0185)
        """
        First 10:
        0.015631179452361265 -35.911424034147544
        0.0050697807630961855 -39.415307408982464
        0.00436126113412601 -22.19772254268874
        0.003435803833287677 -13.375730615006965
        0.0027080350036782293 -4.595605910091438
        0.0018272853255990864 17.667903831481905
        0.0015002579354626941 44.547339099546306
        0.0011238919515134094 52.43503653387368
        0.0007467786299259581 56.25187112789537
        0.0005471540539698069 57.34559824184005
        """
