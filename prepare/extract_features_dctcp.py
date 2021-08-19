#!/usr/bin/env python3

import argparse
from Packet import *
import murmur
import random
import sys
import os

"""
Ingress:
  Features: dest server, [dest rack], ingress, time delta, #msg in last t
  Targets: time delta, drop

Egress:
  Features: src server, [src rack], egress, time delta, #msg in last t
  Targets: time delta, drop
"""

STATUS_INTERVAL = 100000

# See Lucas and Saccuci 1990
EWMA_WEIGHT = 0.3
MAX_RTT = 0.1
DEBUG = False


def find_match(pkt, unmatched_packets, forward_tester, reverse_tester,
               second_file, reverse_first_file):
    global fail

    # search unmatched packets first
    counter = 0
    for suitor in unmatched_packets[:]:
        counter += 1
        if suitor.matches(pkt):
            unmatched_packets.remove(suitor)
            if suitor.get("time") - pkt.get("time") > MAX_RTT * 0.9:
                print("WARNING: observed RTT within 10% of MAX_RTT (" + \
                      str(suitor.get("time") - pkt.get("time")) + \
                      ").  Consider bumping it up if this happens repeatedly.")
            return suitor.get("time"), suitor
        elif suitor.get("time") + MAX_RTT < pkt.get("time"):
            print("WE GOT A PACKET WE DIDNT SEND:", suitor)
            fail += 1
            unmatched_packets.remove(suitor)

    # otherwise, start reading new packets
    line = second_file.readline()
    while line:
        if ">" not in line:
            line = second_file.readline()
            continue
        toks = line.split()
        suitor = Packet(toks)

        counter += 1

        if reverse_tester(suitor):
            reverse_first_file.write(line)
            line = second_file.readline()
            continue

        emulated_ip, _ = forward_tester(suitor)
        if not emulated_ip:
            line = second_file.readline()
            continue

        if pkt.matches(suitor):
            if suitor.get("time") - pkt.get("time") > MAX_RTT * 0.9:
                print("WARNING: observed RTT within 10% of MAX_RTT (" + \
                      str(suitor.get("time") - pkt.get("time")) + \
                      ").  Consider bumping it up if this happens repeatedly.")
            return suitor.get("time"), suitor

        unmatched_packets.append(suitor)
        if suitor.get("time") > pkt.get("time") + MAX_RTT:
            # print ("Did not find match in", MAX_RTT, "seconds. Packet drop?")
            # print ("Searched %d suitors to determine ingress packet dropped" % (counter))
            return None, None

        line = second_file.readline()

    # print("Did not find match. Packet drop?")
    return None, None

def extract_mimic_features(pkt, second_pkt, emulated_ip, other_ip,
                           time_diff, ewma, tor_seeds, agg_seeds, degree):
    #### Ingress features:
    ####     Destination Server, ingress agg, ingress agg interface,
    ####     Destination ToR, time since last packet, EWMA, ECN
    #### Egress features:
    ####     Origin server, egress agg, egress agg interface, origin ToR,
    ####     time since last packet, EWMA, ECN

    # emulated server and tor
    emulated_ip_bytes = emulated_ip.split('.')
    emulated_server = int((int(emulated_ip_bytes[3]) / 4))
    emulated_tor = int(emulated_ip_bytes[2])

    # agg and agg_intf
    if "agg" in pkt.data:
        agg = pkt.get("agg")
        agg_intf = pkt.get("interface")
    elif (not DEBUG) and second_pkt:
        agg = second_pkt.get("agg")
        agg_intf = second_pkt.get("interface")
    else:
        # must be an egress packet (emulated->other) that got lost. recompute.
        # technically, we don't need to do this is second_pkt exists, but its a
        #   sanity check
        cluster = int(emulated_ip_bytes[1])
        emulated_port = int(pkt.get("src")[pkt.get("src").rindex('.')+1:])
        other_port = int(pkt.get("dst")[pkt.get("dst").rindex('.')+1:])

        assert(tor_seeds and agg_seeds and degree != None)

        tor_seed = tor_seeds[cluster][emulated_tor]
        num_aggs = degree
        agg = murmur.ecmp_helper(num_aggs, tor_seed, emulated_ip, emulated_port,
                                 other_ip, other_port)
        agg_seed = agg_seeds[cluster][agg]
        num_agg_intfs = degree
        agg_intf = murmur.ecmp_helper(num_agg_intfs, agg_seed, emulated_ip,
                                      emulated_port, other_ip, other_port)

        if DEBUG and second_pkt:
            assert(agg == int(second_pkt.get("agg")))
            assert(agg_intf == int(second_pkt.get("interface")))

    ecn = pkt.get("ecn")

    features_str = ' '.join((str(emulated_server), str(agg), str(agg_intf),
                            str(emulated_tor), str(time_diff), str(ewma),
                            str(ecn))) + '\n'

    return features_str


def match_packets(first_file, second_file, forward_tester, reverse_tester,
                  features_file, target_time_file, target_drop_file,
                  reverse_first_file, reverse_second_file,
                  tor_seeds = None, agg_seeds = None, degree = None):
    global fail
    fail = 0

    pkts_handled = 0
    pkts_handled_target = 0

    prev_time = 0.0
    ewma = 0.0

    unmatched_packets = []

    for line in first_file:
        if ">" not in line:
            continue

        toks = line.split()
        pkt = Packet(toks)

        # if it's going in the wrong direction, save it for later
        if reverse_tester(pkt):
            reverse_second_file.write(line)
            continue

        # grab the emulated IP and other IP if it's a packet we care about
        emulated_ip, other_ip = forward_tester(pkt)
        if not emulated_ip:
            continue

        second_time, second_pkt = find_match(pkt, unmatched_packets,
                                             forward_tester, reverse_tester,
                                             second_file, reverse_first_file)

        pkts_handled += 1

        # Time since last pkt
        time_diff = pkt.get("time") - prev_time
        prev_time = pkt.get("time")

        # EWMA
        ewma = (1 - EWMA_WEIGHT) * ewma + EWMA_WEIGHT * time_diff

        # Print ingress and egress features
        features_str = extract_mimic_features(pkt, second_pkt,
                                              emulated_ip, other_ip,
                                              time_diff, ewma,
                                              tor_seeds, agg_seeds, degree)
        features_file.write(features_str)


        #### Targets:
        ####     host delay, drop, ecn
        # NOTE: Include timestamp to make binning data easier
        if second_time:
            delay = abs(second_time - pkt.get("time"))
            target_time_file.write(str(pkt.get("time")) + " "
                                   + str(delay) + '\n')
            target_drop_file.write('0 ' + second_pkt.get("ecn") + '\n')
        else:
            delay = MAX_RTT # set packet drop as MAX_RTT
            target_time_file.write(str(pkt.get("time")) + " "
                                   + str(delay) + '\n')
            target_drop_file.write('1 1' + '\n')

        if (STATUS_INTERVAL != 0) and (pkts_handled >= pkts_handled_target):
            pkts_handled_target += STATUS_INTERVAL
            print("Handled: " + str(pkts_handled) +
                  ", unmatched: " + str(len(unmatched_packets)) +
                  ", failed: " + str(fail))

"""
Forward testers:
    Input: Packet
    Output: (emulated IP, non-emulated IP) if we care about the packet
            (None, None) otherwise

    For *in*, we care about outside->emulated
    For *out*, we care about emulated->outside

Reverse testers:
    Input: Packet
    Output: True if the packet is going reverse of the forward tester,
            False otherwise

    For *in*, we care about emulated->outside
    For *out*, we care about outside->emulated
"""
class Testers():
    def __init__(self, emulated_ips):
        self.emulated_ips = emulated_ips

    def in_forward_tester(self, pkt):
        if (not pkt.get("src").startswith(self.emulated_ips)) \
           and (pkt.get("dst").startswith(self.emulated_ips)):
            return pkt.get("dst")[:pkt.get("dst").rindex('.')], \
                   pkt.get("src")[:pkt.get("src").rindex('.')] 
        return None, None

    def in_reverse_tester(self, pkt):
        return (pkt.get("src").startswith(self.emulated_ips)) \
               and (not pkt.get("dst").startswith(self.emulated_ips))

    def out_forward_tester(self, pkt):
        assert((pkt.get("src").startswith(self.emulated_ips)) \
               and (not pkt.get("dst").startswith(self.emulated_ips)))
        return pkt.get("src")[:pkt.get("src").rindex('.')], \
               pkt.get("dst")[:pkt.get("dst").rindex('.')]

    def out_reverse_tester(self, pkt):
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str,
                        help="Directory prefix of pcaps and dumps")
    parser.add_argument("emulated_prefix", type=str,
                        help='Prefix of cluster that will be approximated. ' \
                             'Expect "1.x.".')
    parser.add_argument("seed", type=int, help="RNG seed for ECMP")
    parser.add_argument("degree", type=int,
                        help="Number of ToRs/Aggs/AggUplinks per cluster")
    parser.add_argument("--num_clusters", type=int, help="Number of clusters")
    args = parser.parse_args()

    data_dir = args.directory
    prefix = args.emulated_prefix
    seed = args.seed
    degree = args.degree
    num_clusters = args.num_clusters if args.num_clusters else 2
    tor_seeds, agg_seeds = murmur.load_seeds(seed, degree, num_clusters)

    edge_filename = data_dir + '/edges' + str(num_clusters) + '/edges.raw'
    host_filename = data_dir + '/hosts' + str(num_clusters) + '/hosts.raw'

    out_edge = data_dir + '/edges' + str(num_clusters) + '/out.tmp'
    out_host = data_dir + '/hosts' + str(num_clusters) + '/out.tmp'

    t = Testers(prefix)

    with open(host_filename, 'r') as host_file, \
        open(edge_filename, 'r') as edge_file, \
        open(data_dir + '/in_features.dat', 'w') as in_features_file, \
        open(data_dir + '/in_target_time.dat', 'w') as in_target_time_file, \
        open(data_dir + '/in_target_drop.dat', 'w') as in_target_drop_file, \
        open(out_edge, 'w') as out_edge_file, \
        open(out_host, 'w') as out_host_file:
        print("Starting to parse incoming...")
        match_packets(edge_file, host_file,
                      t.in_forward_tester, t.in_reverse_tester,
                      in_features_file, in_target_time_file,
                      in_target_drop_file, out_host_file, out_edge_file)

    with open(data_dir + '/out_features.dat', 'w') as out_features_file, \
        open(data_dir + '/out_target_time.dat', 'w') as out_target_time_file, \
        open(data_dir + '/out_target_drop.dat', 'w') as out_target_drop_file, \
        open(out_edge, 'r') as out_edge_file, \
        open(out_host, 'r') as out_host_file:
        print("Starting to parse outgoing...")
        match_packets(out_host_file, out_edge_file,
                      t.out_forward_tester, t.out_reverse_tester,
                      out_features_file, out_target_time_file,
                      out_target_drop_file, None, None,
                      tor_seeds, agg_seeds, degree)

    os.remove(out_edge)
    os.remove(out_host)
