#!/usr/bin/env python3

import sys

from HomaPkt import *


STATUS_INTERVAL = 100000
MAX_RTT = 100

if len(sys.argv) < 4:
    print("Usage: python parse_eval_homa.py directory num_clusters evaluatedprefix")
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
            for key, val in unmatched_sent.items():
                count += len(val)

            print("lines read: " + str(lines_read) + \
                  ", unmatched: " + str(count))

        if "Homa" not in line:
            continue

        toks = line.split()
        packet = HomaPkt(toks)

        src = packet.get("src")
        dst = packet.get("dst")
        msg_id = packet.get("msg_id")
        srctoks = src.split('.')
        dsttoks = dst.split('.')
        
        total_pkts += 1

        # only tracks grant->sched (for rtt)
        if src.startswith(prefix):
            assert(packet.get("tor") == srctoks[2] and int(packet.get("svr")) == int(srctoks[3])/4)
            # Sent grant.  We are expecting an scheduled packet later.
            if packet.get("type") != "GRANT":
                continue

            packet.set("expected_sched", int(packet.get("seq_begin")))

            key = (src, dst, msg_id)
            if key not in expected_acks:
                expected_acks[key] = set()
            if packet.get("expected_sched") in expected_acks[key]:
                print("Retransmission!", line)
                continue
            expected_acks[key].add(packet.get("expected_sched"))

            if key not in unmatched_sent:
                unmatched_sent[key] = []
            unmatched_sent[key].append(packet)

            if dst.startswith(prefix):
                local_pkts += 1

        elif dst.startswith(prefix):
            assert(packet.get("tor") == dsttoks[2] and int(packet.get("svr")) == int(dsttoks[3])/4)
            # got scheduled packet
            if packet.get("type") != "SCHED":
                continue

            key = (dst, src, msg_id)

            found = False
            for suitor in unmatched_sent[key][:]:
                if suitor.get("expected_sched") == int(packet.get("seq_begin")):
                    # found a match!
                    found = True
                    time_diff = packet.get("time") - suitor.get("time")
                    out_latency_file.write(str(time_diff) + '\n')
                    unmatched_sent[key].remove(suitor)
                    break
                elif suitor.get("time") + MAX_RTT < packet.get("time"):
                    unmatched_sent[key].remove(suitor)

            if not found:
                print("Didn't find a match!", lines_read, ":", line)

        else:
            assert("Packet not to or from evaluated cluster. Likely a bug." \
                   and False)
    print("local/total: %s/%s=%s" % (local_pkts, total_pkts, (local_pkts-0.0)/total_pkts))
