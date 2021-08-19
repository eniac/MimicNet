#!/usr/bin/env python3

import sys
import argparse
import numpy as np

from generate_traffic import *
from Packet import *


def parse_fct(eval_file, fct_file, traffic_matrix, numOfSubtrees,
              numOfToRsPerSubtree, numOfServersPerRack, evaluatedPrefix, includeLocalFlows):
    flows = dict() # [src_num, dst_num, base_seq]

    for line in eval_file:
        if ">" not in line:
            continue
        toks = line.split()
        pkt = Packet(toks)

        src = pkt.get("src")
        dst = pkt.get("dst")
        stoks = src.split(".")
        dtoks = dst.split(".")

        if src.startswith(evaluatedPrefix) and dst.startswith(evaluatedPrefix):
            if includeLocalFlows:
                if pkt.get("tor") != stoks[2] \
                        or int(pkt.get("svr")) != int(stoks[3])/4:
                    # don't double count local receives
                    continue
            else:
                continue

        # Set the base sequence # if it's the SYN
        # Unless it's an echo. Then ignore it.
        if ("S" in pkt.get("flags")) and (not pkt.get('ack_num')):
            src_num = (int(stoks[3]) // 4) + \
                      numOfServersPerRack * int(stoks[2]) + \
                      numOfToRsPerSubtree * numOfServersPerRack * int(stoks[1])
            dst_num = (int(dtoks[3]) // 4) + \
                      numOfServersPerRack * int(dtoks[2]) + \
                      numOfToRsPerSubtree * numOfServersPerRack * int(dtoks[1])

            if src not in flows:
                flows[src] = dict()
            if dst in flows[src]:
                # SYN retransmit
                assert flows[src][dst][2] == int(pkt.get("seq_begin"))
            flows[src][dst] = [src_num, dst_num, int(pkt.get("seq_begin"))]

        # check if this is the end of a flow
        if pkt.get('ack_num') and (dst in flows) and (src in flows[dst]):
            dst_num, src_num, seq_base = flows[dst][src]
            ack_num = int(pkt.get("ack_num"))

            # If we're not expecting anything else, the other side is probably
            # still sending
            if len(traffic_matrix[dst_num][src_num]) <= 0:
                # Not sure why this is 2 instead of 1...
                if seq_base + 2 < ack_num:
                    print("Extra packet!", seq_base, pkt)
                continue

            start_time, flow_size = traffic_matrix[dst_num][src_num][0]
            end_seq = seq_base + flow_size

            while ack_num >= end_seq:
                if ack_num - end_seq > 500:
                    # Missed a few packets.  A few of these are expected
                    print("Skipping ahead!", ack_num - end_seq, \
                          "seq_base", seq_base, "flow_size", flow_size, pkt)

                # write 
                fct_file.write("%d %d %f %f %f\n" % (dst_num, src_num,
                                                  start_time, pkt.get('time'),
                                                  pkt.get('time') - start_time))
                traffic_matrix[dst_num][src_num].pop(0)

                seq_base = seq_base + flow_size
                flows[dst][src] = [dst_num, src_num, seq_base]

                # If this was the last one we were expecting, we're done
                if len(traffic_matrix[dst_num][src_num]) <= 0:
                    break

                start_time, flow_size = traffic_matrix[dst_num][src_num][0]
                end_seq = seq_base + flow_size

    # print("Unfinished Flows:")
    # for i in traffic_matrix:
    #     if i >= numOfToRsPerSubtree * numOfServersPerRack:
    #         continue
    #     for j in traffic_matrix[i]:
    #         if traffic_matrix[i][j]:
    #             print(i, j, ":", traffic_matrix[i][j])


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
                      numOfToRsPerSubtree, numOfServersPerRack, evaluatedPrefix, True)
