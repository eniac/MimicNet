#!/usr/bin/env python3

import sys

if len(sys.argv) != 2:
    print("Usage: ./query_p90.py [input_path]")

input_path = sys.argv[1]

val_num = dict()
total_sum = 0

with open(input_path, "r") as input_file:
    for val_str in input_file:
        vals = val_str.strip().split()
        val = float(vals[-1])
        if val not in val_num:
            val_num[val] = 1
        else:
            val_num[val] += 1
        total_sum += 1

val_num_sorted = list(val_num.items())
val_num_sorted.sort()

cur_sum = 0
for val, num in val_num_sorted:
    cur_sum += num
    if (float(cur_sum)/float(total_sum)) >= 0.9:
        print("90-percentile in", input_path, "=",val)
        break
