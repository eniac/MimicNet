#!/usr/bin/env python3

import argparse
from Packet import *
import numpy as np
from scipy.stats import pareto
import sys


def get_interarrivals(raw_file, direction_test):
    interarrivals = []

    prev_time = None

    for line in raw_file:
        if ">" not in line:
            continue

        toks = line.split()
        pkt = Packet(toks)

        if not direction_test(pkt):
            continue

        if prev_time == None:
            prev_time = pkt.get("time")
            continue
        else:
            interarrivals.append(pkt.get("time") - prev_time)
            prev_time = pkt.get("time")

    return interarrivals


class Testers():
    def __init__(self, emulated_ips):
        self.emulated_ips = emulated_ips

    def ingress_tester(self, pkt):
        local_src = pkt.get("src").startswith(self.emulated_ips)
        local_dst = pkt.get("dst").startswith(self.emulated_ips)

        if (not local_src) and local_dst:
            return True
        return False

    def egress_tester(self, pkt):
        local_src = pkt.get("src").startswith(self.emulated_ips)
        local_dst = pkt.get("dst").startswith(self.emulated_ips)

        if local_src and (not local_dst):
            return True
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str,
                        help="Directory prefix of pcaps and dumps")
    parser.add_argument("emulated_prefix", type=str,
                        help='Prefix of cluster that will be approximated. ' \
                             'Expect "1.x.".')
    args = parser.parse_args()

    data_dir = args.directory
    emulated_prefix = args.emulated_prefix

    edge_filename = data_dir + '/edges2/edges.raw'
    host_filename = data_dir + '/hosts2/hosts.raw'
    intermimic_filename = data_dir + '/intermimic.dat'

    t = Testers(emulated_prefix)

    with open(host_filename, 'r') as host_file, \
         open(edge_filename, 'r') as edge_file, \
         open(intermimic_filename, 'w') as intermimic_file:
        ing_interarrivals = get_interarrivals(edge_file, t.ingress_tester)
        b, loc, scale = pareto.fit(ing_interarrivals)
        intermimic_file.write(" ".join([str(b), str(loc), str(scale)]) + '\n')

        egr_interarrivals = get_interarrivals(host_file, t.egress_tester)
        b, loc, scale = pareto.fit(egr_interarrivals)
        intermimic_file.write(" ".join([str(b), str(loc), str(scale)]) + '\n')
