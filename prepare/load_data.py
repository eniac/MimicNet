#!/usr/bin/env python3

import numpy as np

def load_data(latency_fn, features_fn, drop_fn):
    latency_file = open(latency_fn)
    features_file = open(features_fn)
    drop_file = open(drop_fn)

    x = []
    y_l = []
    y_d = []
    y_e = []

    for latency_line in latency_file.readlines(): #timestamp, latency, network_state
        features_line = features_file.readline()
        drop_line = drop_file.readline() #drop

        # TCP:
        # approx. server, approx. aggregation switch, approx. aggregation interface, 
        # approx. ToR, change in timestamp since last message,
        # ewma of packet interarrival time
        # Homa:
        # approx. server, approx. aggregation switch, approx. aggregation interface, 
        # approx. ToR, priority, length, change in timestamp since last message,
        # ewma of packet interarrival time
        split_line = features_line.strip().split()
        timestamp, latency, network_state = latency_line.strip().split()
        drop_toks = drop_line.strip().split()
        drop = drop_toks[0]
        if len(drop_toks) > 1:
            ecn = drop_toks[1]

        x_new = [float(network_state)]
        for val in split_line:
            x_new.append(float(val))

        #x_new = netstate, emulated_server, agg, agg_intf, emulated_tor,
        #        time_diff, ewma, [start_ecn]
        x.append(x_new)
        y_d.append(int(drop))
        y_l.append(float(latency))
        if len(drop_toks) > 1:
            y_e.append(int(ecn))

    x = np.array(x)
    y_d = np.array(y_d)
    y_l = np.array(y_l)
    y_e = np.array(y_e)

    return (x, y_d, y_l, y_e)

if __name__=="__main__":
    import sys
    import argparse
    import pickle

    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=str, help="Feature file path")
    parser.add_argument("latencies", type=str, help="Latency data file path")
    parser.add_argument("drops", type=str, help="Drop data file path")
    parser.add_argument("output_file", type=str, help="Output file path")
    args = parser.parse_args()

    x, y_d, y_l, y_e = load_data(args.latencies, args.features, args.drops)
    if y_e.size != 0:
        data = {'X':x, 'y_d':y_d, 'y_l': y_l, 'y_e': y_e}
    else:
        data = {'X':x, 'y_d':y_d, 'y_l': y_l}
    pickle.dump(data, open(args.output_file,'wb'))
