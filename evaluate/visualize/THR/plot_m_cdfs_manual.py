#!/usr/bin/env python3

import sys
import os

from scipy.stats import wasserstein_distance
from scipy.stats import ks_2samp

if len(sys.argv) != 5:
    print("Usage: %s file1|file2|file3 title1|title2|title3 color1|color2|color3 output_name" % sys.argv[0])
    exit()

file_list = sys.argv[1]
title_list = sys.argv[2]
color_list = sys.argv[3]
output_name = sys.argv[4]

file_list = file_list.split("|")
title_list = title_list.split("|")
color_list = color_list.split("|")

print("Comparing values...")
values = []
for i in range(len(file_list)):
    f = file_list[i]
    with open(f) as ftmp, open(f+".tmp", "w+") as ftmpout:
        value = []
        for l in ftmp:
            l = l.strip()
            if float(l) < 0.1:
                continue
            value.append(float(l))
            ftmpout.write(l+"\n")
        # value = [float(x.strip()) for x in ftmp.readlines() if not float(x.strip()) == 0.0]
        values.append(value)

w1_distance_list = []
for i in range(1, len(file_list)):
    print("Comparing file%s to file0" % i)
    w1_distance = wasserstein_distance(values[0], values[i])
    w1_distance_list.append(w1_distance)
    print("Wasserstein Distance:", w1_distance)
    ks_stat, _ = ks_2samp(values[0], values[i])
    print("K-S stat:", ks_stat)

# title_list = ["Homa", "MimicNet (%.0f)" % w1_distance_list[0]]
# color_list = ["#003681", "#A81622"]

tmp_gnuplot_str = ""

for i in range(len(file_list)):
    f = file_list[i]
    os.system("./value_list_to_cdf.py %s %s" % (f+".tmp", f+".cdf"))
    if i == 0:
        tmp_gnuplot_str += ("\"%s\" using 1:2 title \"%s\" w lines lw 5 lc rgb \"%s\",\\\n" % (f+".cdf", title_list[i], color_list[i]))
    else:
        tmp_gnuplot_str += ("\"%s\" using 1:2 title \"%s (%.0f)\" w lines lw 5 lc rgb \"%s\",\\\n" % (f+".cdf", title_list[i], w1_distance_list[i - 1], color_list[i]))

print("Comparing CDFs...")
values = []
for i in range(len(file_list)):
    f = file_list[i]+".cdf"
    with open(f) as ftmp:
        value = [float(x.strip().split()[0]) for x in ftmp.readlines()[1:]]
        values.append(value)
cdf_w1_distance = wasserstein_distance(values[0], values[1])
print("Wasserstein Distance:", cdf_w1_distance)
cdf_ks_stat, _ = ks_2samp(values[0], values[1])
print("K-S stat:", cdf_ks_stat)

gnuplot_str = '''
reset
# set term pdf size 7, 3.85 enhanced dashed color font 'Helvetica,30'
set term pdf size 7, 3.25 enhanced dashed color font 'Helvetica,30'
set output "%s.pdf"
set logscale x
set format x "10^%%T"
set nologscale y
set yrange [0.0:1.0]
set xrange [1:10000000]
set key autotitle columnheader left top samplen 1 font ',27'
set xlabel "Throughput (Bps)"
set ylabel "Fraction"
set border 10
plot ''' % (output_name)

gnuplot_str += tmp_gnuplot_str

gnuplot_str = gnuplot_str[:-3]

gnuplot_file = open(output_name+".gs", "w")
gnuplot_file.write(gnuplot_str)
gnuplot_file.close()

os.system("gnuplot %s.gs" % output_name)
os.system("rm *.tmp")
