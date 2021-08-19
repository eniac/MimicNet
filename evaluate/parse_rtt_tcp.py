#!/usr/bin/env python3

import sys

from Packet import *


STATUS_INTERVAL = 50000
MAX_RTT = 0.1

if len(sys.argv) < 4:
    print("Usage: python parse_rtt_tcp.py directory num_clusters evaluatedprefix")
    exit(1)


data_dir = sys.argv[1]
num_clusters = sys.argv[2]
prefix = sys.argv[3]

lines_read = 0
unmatched_sent = dict()
expected_acks = dict()
last_seen_ack = dict()


filename = data_dir + '/eval' + num_clusters + '/eval.raw'
out_thr = data_dir + '/rtt_c' + num_clusters + '.dat'
with open(filename, 'r') as eval_file, \
     open(out_thr, 'w') as out_latency_file:
    total_pkts = 0
    local_pkts = 0
    for line in eval_file:
        lines_read += 1
        if ((STATUS_INTERVAL != 0) and (lines_read % STATUS_INTERVAL == 0)):
            count = 0
            for key1,val1 in unmatched_sent.items():
                count += len(val1)

            print("lines read: " + str(lines_read) + \
                  ", unmatched: " + str(count))

        if ">" not in line:
            continue
        toks = line.split()
        packet = Packet(toks)

        total_pkts += 1

        src = packet.get("src")
        dst = packet.get("dst")

        if src.startswith(prefix):
            # Sent packet.  We are expecting an ACK later.
            if (not packet.get("seq_begin")) or (not packet.get("seq_end")):
                # No seq number, must be an ACK generated in the target cluster
                continue

            if packet.get("seq_begin") == packet.get("seq_end"):
                packet.set("expected_ack", int(packet.get("seq_end")) + 1)
            else:
                packet.set("expected_ack", int(packet.get("seq_end")))

            key = (src, dst)
            if key not in expected_acks:
                expected_acks[key] = set()
            if packet.get("expected_ack") in expected_acks[key]:
                # print("Retransmission!", line)
                continue
            expected_acks[key].add(packet.get("expected_ack"))

            if key not in unmatched_sent:
                unmatched_sent[key] = []
            unmatched_sent[key].append(packet)

            if dst.startswith(prefix):
                local_pkts += 1
        
        elif dst.startswith(prefix):
            # received packet
            if packet.get("ack_num") == None:
                continue

            if src not in last_seen_ack:
                last_seen_ack[src] = dict()
            if dst in last_seen_ack[src] \
                    and packet.get("ack_num") == last_seen_ack[src][dst]:
                # print("Duplicate ACK!")
                continue
            last_seen_ack[src][dst] = packet.get("ack_num")

            key = (dst, src)

            found = False
            for suitor in unmatched_sent[key][:]:
                if suitor.get("expected_ack") == int(packet.get("ack_num")):
                    # found a match!
                    found = True
                    time_diff = packet.get("time") - suitor.get("time")
                    out_latency_file.write(str(time_diff) + '\n')
                    unmatched_sent[key].remove(suitor)
                    break
                elif suitor.get("time") + MAX_RTT < packet.get("time"):
                    unmatched_sent[key].remove(suitor)

            # if not found:
            #     print("Didn't find a match!", lines_read, ":", line)

        else:
            assert("Packet not to or from evaluated cluster. Likely a bug." \
                   and False)
    print("local/total: %s/%s=%s" % (local_pkts, total_pkts, (local_pkts-0.0)/total_pkts))
