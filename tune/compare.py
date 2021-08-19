#!/usr/bin/env python3

import sys
import os
from scipy.stats import wasserstein_distance
from scipy.stats import ks_2samp

def compare_fct_mse(input1, input2):
    fct_dict = dict()

    with open(input1, "r") as f1:
        for line in f1:
            toks = line.split()
            dst = int(toks[0])
            src = int(toks[1])
            start = float(toks[2])
            fct = float(toks[4])

            fct_dict[(dst, src, start)] = fct

    mse = 0.0
    num_flows = 0

    with open(input2, "r") as f2:
        for line in f2:
            toks = line.split()
            dst = int(toks[0])
            src = int(toks[1])
            start = float(toks[2])

            fct = float(toks[4])
            if (dst, src, start) not in fct_dict:
                continue
            se = (fct - fct_dict[(dst, src, start)]) ** 2
            mse = mse + se
            num_flows = num_flows + 1

    if num_flows < 1:
        return 1000000000, num_flows
    else:
        return mse / num_flows, num_flows

def compare_ks_cdf(input1, input2):
    with open(input1) as f1, open(input2) as f2:
        cdf1 = [float(x.strip().split()[0]) for x in f1.readlines()[1:]]
        cdf2 = [float(x.strip().split()[0]) for x in f2.readlines()[1:]]
        ks_stat, _ = ks_2samp(cdf1, cdf2)
        return ks_stat

def compare_w1_cdf(input1, input2):
    with open(input1) as f1, open(input2) as f2:
        cdf1 = [float(x.strip().split()[0]) for x in f1.readlines()[1:]]
        cdf2 = [float(x.strip().split()[0]) for x in f2.readlines()[1:]]
        w1_dist = wasserstein_distance(cdf1, cdf2)
        return w1_dist

def compare_ks(input1, input2):
    with open(input1) as f1, open(input2) as f2:
        val1 = [float(x.strip().split()[-1]) for x in f1.readlines()[1:]]
        val2 = [float(x.strip().split()[-1]) for x in f2.readlines()[1:]]
        ks_stat, _ = ks_2samp(val1, val2)
        return ks_stat

def compare_w1(input1, input2):
    with open(input1) as f1, open(input2) as f2:
        val1 = [float(x.strip().split()[-1]) for x in f1.readlines()[1:]]
        val2 = [float(x.strip().split()[-1]) for x in f2.readlines()[1:]]
        w1_dist = wasserstein_distance(val1, val2)
        return w1_dist

def compare_pct(input1, input2, pct):
    val1_num = dict()
    val2_num = dict()
    total_sum1 = 0
    total_sum2 = 0
    with open(input1) as f1, open(input2) as f2:
        for val_str in f1:
            vals = val_str.strip().split()
            val = float(vals[-1])
            if val not in val1_num:
                val1_num[val] = 1
            else:
                val1_num[val] += 1
            total_sum1 += 1
        for val_str in f2:
            vals = val_str.strip().split()
            val = float(vals[-1])
            if val not in val2_num:
                val2_num[val] = 1
            else:
                val2_num[val] += 1
            total_sum2 += 1
        val1_num_sorted = list(val1_num.items())
        val2_num_sorted = list(val2_num.items())
        val1_num_sorted.sort()
        val2_num_sorted.sort()

        cur_sum = 0
        pct1 = 0
        pct2 = 0
        for val, num in val1_num_sorted:
            cur_sum += num
            if (float(cur_sum) / float(total_sum1)) * 100 >= pct:
                pct1 = val
                print("pct1 is updated: " + str(pct1))
                break
        cur_sum = 0
        for val, num in val2_num_sorted:
            cur_sum += num
            if (float(cur_sum) / float(total_sum2)) * 100 >= pct:
                pct2 = val
                print("pct2 is updated: " + str(pct2))
                break
        return abs(pct1 - pct2)

def compare_ks_no0s(input1, input2):
    with open(input1) as f1, open(input2) as f2:
        val1 = [float(x.strip().split()[-1]) for x in f1.readlines()[1:]]
        val2 = [float(x.strip().split()[-1]) for x in f2.readlines()[1:]]
        val1_no0s = [x for x in val1 if x > 0]
        val2_no0s = [x for x in val2 if x > 0]
        ks_stat, _ = ks_2samp(val1_no0s, val2_no0s)
        return ks_stat

def compare_w1_no0s(input1, input2):
    with open(input1) as f1, open(input2) as f2:
        val1 = [float(x.strip().split()[-1]) for x in f1.readlines()[1:]]
        val2 = [float(x.strip().split()[-1]) for x in f2.readlines()[1:]]
        val1_no0s = [x for x in val1 if x > 0]
        val2_no0s = [x for x in val2 if x > 0]
        w1_dist = wasserstein_distance(val1_no0s, val2_no0s)
        return w1_dist

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./compare_fct.py [real_fct] [approx_fct]")

    real_fct = sys.argv[1]
    approx_fct = sys.argv[2]

    with open(real_fct, "r") as fh:
        total_real_samples = 0
        for line in fh:
            total_real_samples += 1

    print ("Total real samples:", total_real_samples)

    min_mse = 1000000000
    min_version = ""
    if os.path.isdir(approx_fct):
        for fct in os.listdir(approx_fct):
            mse, samples = compare_fct(real_fct, approx_fct+"/"+fct)
            print("Version:", fct, "samples:", samples, "MSE:", mse)
            if mse < min_mse and samples > 0.5*total_real_samples:
                min_mse = mse
                min_version = fct
        print ("Overall min mse: " + min_version)
    else:
        mse, samples = compare_fct(real_fct, approx_fct)
        if samples > 0.5*total_real_samples:
            print ("mse: " + str(mse))
        else:
            print ("Insufficient samples.")
