from math import log
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("outfile", type=str, help="outfile required.")
parser.add_argument("--mimic", action="store_true",
                    help="Whether we are generating a mimic config or not.")
parser.add_argument("--mimic_homa", action="store_true",
                    help="Whether we are generating a mimic config or not for Homa.")
parser.add_argument("--numClusters", type=int, help="number of clusters")
parser.add_argument("--serversPerRack", type=int, help="servers per rack")
parser.add_argument("--numToRsAndUplinks", type=int,
                    help="Number of ToRs/Aggs/AggUplinks per cluster (k)")
parser.add_argument("--parallel", action="store_true", \
                    help="For when we are generating a parallel config.")
args = parser.parse_args()

mimic = False
mimic_homa = False
numOfSubtrees = 2
numOfServersPerRack = 4
k = 2
parallel = False

outfile = args.outfile
if args.mimic:
    mimic = True
if args.mimic_homa:
    mimic_homa = True
if args.numClusters:
    numOfSubtrees = args.numClusters
if args.serversPerRack:
    numOfServersPerRack = args.serversPerRack
if args.numToRsAndUplinks:
    degree = args.numToRsAndUplinks
if args.parallel:
    parallel = True

emulated_clusters = range(1, numOfSubtrees)
numCores = degree * degree
numAggUplinks = degree
numAggsPerSubtree = degree
numToRsPerSubtree = degree

assert(sum(map(bool, [mimic_homa, mimic])) <= 1)


def choosePath(path, layer, num_options):
    assert num_options != 0 and ((num_options & (num_options - 1)) == 0), \
            "ERROR: We assume num_options is a power of two"
    num_bits = int(log(num_options, 2))
    return (path >> (layer * num_bits)) % num_options


if parallel:
    outfs = [open("%s%d" % (outfile, x), 'w') for x in range(numOfSubtrees + 1)]
else:
    outfs = [open(outfile, 'w')]
    outf = outfs[0] # default for non-parallel

for f in outfs:
    f.write("<config>\n")

# Server <-> ToR
# Server: 1.<cluster>.<tor>.<server*4>/252
# Inbtwn: 1.<cluster>.<tor>.<server*4+1>/252
for cluster in range(numOfSubtrees):
    if parallel:
        outf = outfs[cluster]
    for tor in range(numToRsPerSubtree):
        for server in range(numOfServersPerRack):
            ip = "1." + str(cluster) + "." + str(tor) + "." + str(server*4)
            host_index = (tor * numOfServersPerRack) + server

            if (mimic or mimic_homa) and (cluster in emulated_clusters): ## QZ
                outf.write('<interface hosts="cluster[%d].host[%d]" names="eth0" address="%s" netmask="255.255.0.0"/>\n' % (cluster, host_index, ip))
            else:
                outf.write('<interface hosts="cluster[%d].host[%d]" names="eth0" address="%s" netmask="255.255.255.252"/>\n' % (cluster, host_index, ip))
                ip = "1." + str(cluster) + "." + str(tor) + "." + str(server*4 + 1)
                outf.write('<interface hosts="cluster[%d].tor[%d]" names="eth%d" address="%s" netmask="255.255.255.252"/>\n' % (cluster, tor, server, ip))

for f in outfs:
    f.write("\n")


# ToR <-> Agg
# ToR: 3.<cluster>.<agg>.<tor*4>/252
# Agg: 3.<cluster>.<agg>.<tor*4+1>/252
for cluster in range(numOfSubtrees):
    if (mimic or mimic_homa) and (cluster in emulated_clusters):
        continue
    if parallel:
        outf = outfs[cluster]
    for agg in range(numAggsPerSubtree):
        for tor in range(numToRsPerSubtree):
            interface_num = numOfServersPerRack + agg
            ip = "3." + str(cluster) + "." + str(agg) + "." + str(tor * 4)
            outf.write('<interface hosts="cluster[%d].tor[%d]" names="eth%d" ' \
                       'address="%s" netmask="255.255.255.252"/>\n' \
                       % (cluster, tor, interface_num, ip))

            ip = "3." + str(cluster) + "." + str(agg) + "." + str(tor * 4 + 1)
            outf.write('<interface hosts="cluster[%d].agg[%d]" names="eth%d" ' \
                       'address="%s" netmask="255.255.255.252"/>\n' \
                       % (cluster, agg, tor, ip))

for f in outfs:
    f.write("\n")


# Agg <-> Core
# Agg:  4.<cluster>.<agg>.<core*4>/252
# Core: 4.<cluster>.<agg>.<core*4+1>/252
for core in range(numCores):
    for cluster in range(numOfSubtrees):
        agg = core % numAggsPerSubtree

        if parallel:
            outf = outfs[numOfSubtrees]
        ip = "4." + str(cluster) + "." + str(agg) + "." + str(core * 4 + 1)
        outf.write('<interface hosts="core[%d]" names="eth%d" address="%s" netmask="255.255.255.252"/>\n' % (core, cluster, ip))

        if (mimic or mimic_homa) and (cluster in emulated_clusters):
            continue
        if parallel:
            outf = outfs[cluster]
        ip = "4." + str(cluster) + "." + str(agg) + "." + str(core * 4)
        interface_num = numToRsPerSubtree + (core / numAggsPerSubtree) # numAggsPerSubtree = uplinks from aggs
        outf.write('<interface hosts="cluster[%d].agg[%d]" names="eth%d" ' \
                   'address="%s" netmask="255.255.255.252"/>\n' \
                   % (cluster, agg, interface_num, ip))

for f in outfs:
    f.write("\n\n")


# target destinations: 1.<cluster>.<tor>.<server*4>
# Server routing tables
for cluster in range(numOfSubtrees):
    if parallel:
        outf = outfs[cluster]
    for tor in range(numToRsPerSubtree):
        for server in range(numOfServersPerRack):
            # uplinks
            host_index = (tor * numOfServersPerRack) + server
            if (mimic or mimic_homa) and (cluster in emulated_clusters):
                outf.write('<route hosts="cluster[%d].host[%d]" destination="1.0.0.0" netmask="255.0.0.0" interface="eth0" />\n' % (cluster, host_index))
            else:
                gw_ip = "1." + str(cluster) + "." + str(tor) + "." + str(server * 4 + 1)
                outf.write('<route hosts="cluster[%d].host[%d]" destination="1.0.0.0" netmask="255.0.0.0" gateway="%s" interface="eth0" />\n' % (cluster, host_index, gw_ip))

for f in outfs:
    f.write('\n')

# ToR routing tables
for cluster in range(numOfSubtrees):
    if (mimic or mimic_homa) and (cluster in emulated_clusters):
        continue
    if parallel:
        outf = outfs[cluster]
    for tor in range(numToRsPerSubtree):
        for dest_cluster in range(numOfSubtrees):
            for dest_tor in range(numToRsPerSubtree):
                if (cluster == dest_cluster) and (tor == dest_tor):
                    #downlink
                    for server in range(numOfServersPerRack):
                        dest_ip = "1." + str(dest_cluster) + "." + str(dest_tor) + "." + str(server*4)
                        gw_ip = "1." + str(dest_cluster) + "." + str(dest_tor) + "." + str(server*4)
                        outf.write('<route hosts="cluster[%d].tor[%d]" destination="%s" netmask="255.255.255.255" gateway="%s" interface="eth%d" />\n' % (cluster, tor, dest_ip, gw_ip, server))
                else:
                    #uplink
                    for dest_server in range(numOfServersPerRack):
                        dest_ip = "1." + str(dest_cluster) + "." + str(dest_tor) + "." + str(dest_server * 4)
                        for path_choice in range(numAggsPerSubtree):
                            interface_num = numOfServersPerRack + path_choice
                            gw_ip = "3." + str(cluster) + "." + str(path_choice) + "." + str(tor * 4 + 1)
                            outf.write('<route hosts="cluster[%d].tor[%d]" destination="%s" netmask="255.255.255.255" gateway="%s" interface="eth%d" />\n' % (cluster, tor, dest_ip, gw_ip, interface_num))
        outf.write('\n')

# Agg routing tables
for cluster in range(numOfSubtrees):
    if (mimic or mimic_homa) and (cluster in emulated_clusters):
        continue
    if parallel:
        outf = outfs[cluster]
    for agg in range(numAggsPerSubtree):
        for dest_cluster in range(numOfSubtrees):
            for dest_tor in range(numToRsPerSubtree):
                if cluster == dest_cluster:
                    # downlink
                    dest_ip = "1." + str(dest_cluster) + "." + str(dest_tor) + ".0"
                    gw_ip = "3." + str(dest_cluster) + "." + str(agg) + "." + str(dest_tor * 4)
                    outf.write('<route hosts="cluster[%d].agg[%d]" destination="%s" netmask="255.255.255.0" gateway="%s" interface="eth%d" />\n' % (cluster, agg, dest_ip, gw_ip, dest_tor))
                else:
                    #uplink
                    for path in range(numOfServersPerRack):
                        dest_ip = "1." + str(dest_cluster) + "." + str(dest_tor) + "." + str(path * 4)
                        for path_choice in range(numAggUplinks):
                            interface_num = numToRsPerSubtree + path_choice
                            gw_core = agg + path_choice * numAggUplinks
                            # gw_core = (agg%2) + path_choice*2
                            gw_ip = "4." + str(cluster) + "." + str(agg) + "." + str(gw_core * 4 + 1)
                            outf.write('<route hosts="cluster[%d].agg[%d]" destination="%s" netmask="255.255.255.255" gateway="%s" interface="eth%d" />\n' % (cluster, agg, dest_ip, gw_ip, interface_num))
        outf.write('\n')

# Core routing tables
if parallel:
    outf = outfs[numOfSubtrees]
for core in range(numCores):
    for dest_cluster in range(numOfSubtrees):
        if (mimic or mimic_homa) and (dest_cluster in emulated_clusters):
            dest_ip = "1." + str(dest_cluster) + ".0.0"
            outf.write('<route hosts="core[%d]" destination="%s" netmask="255.255.0.0" interface="eth%d" />\n' % (core, dest_ip, dest_cluster))
        else:
            for dest_tor in range(numToRsPerSubtree):
                dest_ip = "1." + str(dest_cluster) + "." + str(dest_tor) + ".0"
                gw_agg = core % numAggUplinks
                gw_ip = "4." + str(dest_cluster) + "." + str(gw_agg) + "." + str(core * 4)
                outf.write('<route hosts="core[%d]" destination="%s" netmask="255.255.255.0" gateway="%s" interface="eth%d" />\n' % (core, dest_ip, gw_ip, dest_cluster))

for f in outfs:
    f.write("</config>\n")
    f.close()
