#!/usr/bin/env python3

import sys

NON_CONGES = '0'
INCR_CONGES = '1'
MAX_CONGES = '2'
DECR_CONGES = '3'

BIN_WINDOW = 0.0006
MEDIAN_VAL = 0.00103
ACCEPTABLE_VARIANCE = 0.000200
MIN_VAL = 0.0005

if __name__ == "__main__":
    fname = sys.argv[1]
    # Assume lines have format: timestamp delay
    with open(fname, 'r') as infile:
        with open(fname+"_binned", 'w') as outfile:
            state = NON_CONGES

            prev_time = 0
            sample_sum = 0
            num_drops = 0
            line_set = []
            for line in infile:
                val = float(line.split()[1])
                time_stamp = float(line.split()[0])
                line_set.append(line.strip())

                sample_sum += val
                if val < MIN_VAL:
                    num_drops += 1

                if time_stamp - prev_time > BIN_WINDOW:
                    temp = sample_sum / len(line_set)
                    if num_drops > len(line_set) / 3:
                        state = MAX_CONGES
                    elif temp > MEDIAN_VAL + ACCEPTABLE_VARIANCE:
                        if (state == NON_CONGES or state == INCR_CONGES):
                            #Last state was uncongested, so congestion is increasing
                            state = INCR_CONGES
                        elif (state == MAX_CONGES or state == DECR_CONGES):
                            #Last state was dropping packets, so conges decreasing
                            state = DECR_CONGES
                    else:
                        state = NON_CONGES
                    for l in line_set:
                        outfile.write(l + " " +  state + '\n')
                    line_set = []
                    prev_time = time_stamp
                    sample_sum = 0
                    num_drops = 0


            for l in line_set:
                outfile.write(l + " " +  state + '\n')
