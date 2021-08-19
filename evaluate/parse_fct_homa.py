#!/usr/bin/env python3

import sys
import argparse
import numpy as np

from generate_traffic import *
from HomaPkt import *


def parse_fct(eval_file, fct_file, traffic_matrix, numOfSubtrees,
              numOfToRsPerSubtree, numOfServersPerRack, evaluatedPrefix):
    echo_tm = dict()

    for src_num in traffic_matrix:
        for dst_num in traffic_matrix[src_num]:
            key1 = (src_num, dst_num)
            key2 = (dst_num, src_num)

            if key1 not in echo_tm:
                echo_tm[key1] = []
            echo_tm[key1].extend(traffic_matrix[src_num][dst_num])

            if key2 not in echo_tm:
                echo_tm[key2] = []
            echo_tm[key2].extend(traffic_matrix[src_num][dst_num])

    # re-sort by time
    for key in echo_tm:
        echo_tm[key] = sorted(echo_tm[key], key=lambda elem: elem[0])


    flows = dict() # msg_id -> (src_num, dst_num, last_time, last_seq)
    count = 0;
    for line in eval_file:
        count+=1
        if "Homa" not in line:
            continue

        toks = line.split()
        pkt = HomaPkt(toks)

        # NOTE: FCT is measured by the time the last packet leaves.
        # TODO: capture pcaps everywhere and measure vs arrival time.
        src = pkt.get("src")
        dst = pkt.get("dst")
        msg_id = pkt.get("msg_id")
        stoks = src.split(".")
        dtoks = dst.split(".")

        src_num = (int(stoks[3]) // 4) + \
                  numOfServersPerRack * int(stoks[2]) + \
                  numOfToRsPerSubtree * numOfServersPerRack * int(stoks[1])
        dst_num = (int(dtoks[3]) // 4) + \
                  numOfServersPerRack * int(dtoks[2]) + \
                  numOfToRsPerSubtree * numOfServersPerRack * int(dtoks[1])

        if src.startswith(evaluatedPrefix) and dst.startswith(evaluatedPrefix):
            if pkt.get("tor") != stoks[2] \
                    or int(pkt.get("svr")) != int(stoks[3])/4:
                # don't double count local receives
                continue

        # Instantiate the flow record if it's the Request
        if pkt.get("type") == "REQUEST":
            assert int(pkt.get("seq_begin")) == 0
            flows[msg_id] = {'src_num': src_num, 'dst_num': dst_num,
                             'last_time': float(pkt.get("time")),
                             'last_seq': int(pkt.get("seq_end"))}

        # check if this is the end of a flow
        if (pkt.get('type') == "REQUEST" or pkt.get('type') == "SCHED" \
                or pkt.get("type") == "UNSCHED"):
            if msg_id in flows:
                flows[msg_id]['last_time'] = float(pkt.get("time"))
                flows[msg_id]['last_seq'] = int(pkt.get("seq_end"))
            else:
                print("Detected dropped REQUEST for msg_id", msg_id)
                # assert msg_id in flows

    found_count = 0
    for flow_record in flows.values():
        tm_key = (flow_record['src_num'], flow_record['dst_num'])
        found = False

        for i in range(len(echo_tm[tm_key])):
            start_time, flow_size = echo_tm[tm_key][i]
            if flow_size == flow_record['last_seq'] + 1:
                fct_file.write("%d %d %f %f %f\n" %
                        (flow_record['src_num'], flow_record['dst_num'],
                         start_time, flow_record['last_time'],
                         flow_record['last_time'] - start_time))
                del echo_tm[tm_key][i]
                found = True
                found_count += 1
                break

        #if not found:
        #    print("Could not find matching flow record (probably incomplete flow):", flow_record)

    print("Found a total of", found_count, "complete flows")


if __name__=="__main__":

    load = 0.70
    numOfSpines = 4
    numOfSubtrees = 2
    numOfToRsPerSubtree = 2
    numOfServersPerRack = 4
    evaluatedPrefix = "1.0."
    linkSpeed = 100e6
    
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=int, help="RNG seed required.")
    parser.add_argument("directory", type=str,
                        help="Directory prefix of pcaps and dumps")
    parser.add_argument("--evaluated_prefix", type=str,
                        help="IP prefix of evaluated region, e.g., 1.0.")
    parser.add_argument("--load", type=float,
                        help="Portion of bisection bandwidth utilized.")
    parser.add_argument("--numClusters", type=int,
                        help="Number clusters to generate traffic for.")
    parser.add_argument("--numToRs", type=int,
                        help="Number of ToR switches/racks per cluster.")
    parser.add_argument("--numServers", type=int,
                        help="Number of servers per rack.")
    parser.add_argument("--linkSpeed", type=float,
                        help="Link speed")
    args = parser.parse_args()

    seed = args.seed
    data_dir = args.directory
    if args.evaluated_prefix:
        evaluatedPrefix = args.evaluated_prefix
    if args.load:
        load = args.load
    if args.numClusters:
        numOfSubtrees = args.numClusters
    if args.numToRs:
        numOfToRsPerSubtree = args.numToRs
    if args.numServers:
        numOfServersPerRack = args.numServers
    if args.linkSpeed:
        linkSpeed = args.linkSpeed
    
    numOfSpines = numOfToRsPerSubtree * numOfToRsPerSubtree

    rng = np.random.RandomState(seed=seed)
    
    emulatedRacks = range(numOfToRsPerSubtree, numOfSubtrees*numOfToRsPerSubtree)

    traffic_matrix = generate_traffic_matrix(rng, load, linkSpeed,
                                             numOfServersPerRack,
                                             numOfToRsPerSubtree, numOfSubtrees,
                                             numOfSpines, emulatedRacks)

    filename = data_dir + '/eval' + str(numOfSubtrees) + '/eval.raw'
    out_fct = data_dir + '/fct_c' + str(numOfSubtrees) + '.dat'
    with open(filename, 'r') as eval_file, \
         open(out_fct, 'w') as fct_file:
            parse_fct(eval_file, fct_file, traffic_matrix, numOfSubtrees,
                      numOfToRsPerSubtree, numOfServersPerRack, evaluatedPrefix)
