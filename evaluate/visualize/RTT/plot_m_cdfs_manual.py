#!/usr/bin/env python3

import sys
import os
from scipy.stats import wasserstein_distance

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

# prints the last column of the FCT datafile to its own file
for f in file_list:
    with open(f, "r") as fctf, open(f+".tmp", "w+") as tmpf:
        for l in fctf:
            tmpf.write(l.strip().split(" ")[-1]+"\n")

values = []
for i in range(len(file_list)):
    f = file_list[i]+".tmp"
    with open(f) as ftmp:
        value = [float(x.strip()) for x in ftmp.readlines()]
        values.append(value)

w1_distance_list = []
for i in range(1, len(file_list)):
    print("Comparing file%s to file0" % i)
    w1_distance = wasserstein_distance(values[0], values[i])
    w1_distance_list.append(w1_distance)
    print("Wasserstein Distance:", w1_distance)


tmp_gnuplot_str = ""
for i in range(len(file_list)):
    f = file_list[i]
    os.system("./value_list_to_cdf.py %s %s" % (f+".tmp", f+".cdf"))
    if i == 0:
        tmp_gnuplot_str += ("\"%s\" using 1:2 title \"%s\" w lines lw 5 lc rgb \"%s\",\\\n" % (f+".cdf", title_list[i], color_list[i]))
    else:
        tmp_gnuplot_str += ("\"%s\" using 1:2 title \"%s (%.5f)\" w lines lw 5 lc rgb \"%s\",\\\n" % (f+".cdf", title_list[i], w1_distance_list[i - 1], color_list[i]))

gnuplot_str = '''
reset
# set term pdf size 7, 3.85 enhanced dashed color font 'Helvetica,30'
set term pdf size 7, 3.25 enhanced dashed color font 'Helvetica,30'
set output "%s.pdf"
set logscale x
set nologscale y
set yrange [0.0:1.0]
set xrange [0.001:100]
set key autotitle columnheader right bottom samplen 1 font ',27'
set xlabel "Latency (s)"
set ylabel "Fraction of Packets"
set border 10
plot ''' % (output_name)

gnuplot_str += tmp_gnuplot_str

gnuplot_str = gnuplot_str[:-3]

gnuplot_file = open(output_name+".gs", "w")
gnuplot_file.write(gnuplot_str)
gnuplot_file.close()

os.system("gnuplot %s.gs" % output_name)

for f in file_list:
    os.system("rm %s" % f+".tmp")
