#!/usr/bin/env python3

import sys
from HomaPkt import *


STATUS_INTERVAL = 100000

class Throughput:
    def __init__(self, size, start_time):
        self.size = size
        self.start_time = start_time

if len(sys.argv) < 4:
    print("Usage: python parse_throughput_homa.py directory num_clusters window")
    exit(1)


data_dir = sys.argv[1]
num_clusters = sys.argv[2]
window = float(sys.argv[3])

lines_read = 0
throughput_per_link = dict()
throughput_num = dict()
throughput_num[0] = 0
total_num = 0


filename = data_dir + '/eval' + num_clusters + '/eval.raw'
out_thr = data_dir + '/thr_c' + num_clusters + '.dat'
with open(filename, 'r') as eval_file, \
     open(out_thr, 'w') as out_throughput_file:
    for line in eval_file:
        lines_read += 1
        if ((STATUS_INTERVAL != 0) and (lines_read % STATUS_INTERVAL == 0)):
            print("lines read: " + str(lines_read) + \
                  ", active flows: " + str(len(throughput_per_link)))

        if "Homa" not in line:
            continue
        toks = line.split()
        packet = HomaPkt(toks)

        if packet.get("type") != "REQUEST" and packet.get("type") != "SCHED" \
                and packet.get("type") != "UNSCHED":
            continue

        flow = (packet.get("src"), packet.get("dst"), packet.get("msg_id"))
        if flow not in throughput_per_link:
            throughput_per_link[flow] = Throughput(0, 0)
        throughput = throughput_per_link[flow]

        if packet.get("time") - throughput.start_time > window:
            out_throughput_file.write("{}\n".format(throughput.size))

            if throughput.size not in throughput_num:
                throughput_num[throughput.size] = 0
            throughput_num[throughput.size] += 1
            throughput_num[0] += int((packet.get("time") - throughput.start_time) / window) - 1
            total_num += int((packet.get("time") - throughput.start_time) / window)
            throughput.start_time = packet.get("time")
            throughput.size = 0

        if packet.get("seq_end") and packet.get("seq_begin"):
            throughput.size += int(packet.get("seq_end")) - int(packet.get("seq_begin"))

# with open(results_dir + '/eval_throughput_cdf.dat', 'w') as out_throughput_cdf_file:
#    cur_sum = 0
#    throughput_num_sorted = list(throughput_num.items())
#    throughput_num_sorted.sort()
#    for throughput, num in throughput_num_sorted:
#        cur_sum += num
#        out_throughput_cdf_file.write("{} {}\n".format(throughput, float(cur_sum) / float(total_num)))
