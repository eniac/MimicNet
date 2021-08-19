#!/usr/bin/env python3

import sys

if len(sys.argv) < 3:
    print("Usage: ./value_list_to_cdf.py [input_path] [output_path]")

input_path = sys.argv[1]
output_path = sys.argv[2]

val_num = dict()
total_sum = 0

with open(input_path, "r") as input_file:
    for val_str in input_file:
        val = float(val_str)
        if val not in val_num:
            val_num[val] = 1
        else:
            val_num[val] += 1
        total_sum += 1

val_num_sorted = list(val_num.items())
val_num_sorted.sort()

with open(output_path, "w") as output_file:
    cur_sum = 0

    for val, num in val_num_sorted:
        cur_sum += num
        output_file.write("{} {}\n".format(val, float(cur_sum) / float(total_sum)))
