import argparse
import sys
import random


parser = argparse.ArgumentParser()
parser.add_argument("seed", type=int, help="RNG seed required.")
parser.add_argument("outfile", type=str, help="outfile required.")
parser.add_argument("route_prefix", type=str, \
                    help="Prefix for route config files.")
parser.add_argument("datadir", type=str, help="result dir required.")
parser.add_argument("--mimic", action="store_true", \
                    help="For when we are generating a mimic config.")
parser.add_argument("--mimic_homa", action="store_true", \
                    help="For when we are generating a mimic config for Homa.")
parser.add_argument("--numClusters", type=int, \
                    help="Number clusters to generate traffic for.")
parser.add_argument("--numToRsAndUplinks", type=int, \
                    help="Number of ToRs/Aggs/AggUplinks per cluster.")
parser.add_argument("--numServers", type=int, \
                    help="Number of servers per rack.")
parser.add_argument("--parallel", action="store_true", \
                    help="For when we are generating a parallel config.")
args = parser.parse_args()

seed = args.seed
outfile = args.outfile
route_prefix = args.route_prefix
datadir = args.datadir

mimic = False
mimic_homa = False
numClusters = 2
degree = 2
numOfServersPerRack = 4
parallel = False

if args.mimic_homa:
    mimic_homa = True
if args.mimic:
    mimic = True
if args.numClusters:
    numClusters = args.numClusters
if args.numToRsAndUplinks:
    degree = args.numToRsAndUplinks
if args.numServers:
    numOfServersPerRack = args.numServers
if args.parallel:
    parallel = True


random.seed(seed)
emulatedClusters = range(1, numClusters)
numCores = degree * degree
numAggsPerSubtree = degree
numToRsPerSubtree = degree

if mimic or mimic_homa:
    netname = "ApproxFatTree"
else:
    netname = "FatTree"


with open(outfile, "w") as outf:
    outf.write('%s.numClusters = %d\n' % (netname, numClusters))
    outf.write('%s.numCores = %d\n' % (netname, numCores))
    outf.write('%s.degree = %d\n' % (netname, degree))
    outf.write('%s.serversPerRack = %d\n' % (netname, numOfServersPerRack))

    # Assign partitions
    if parallel:
        outf.write('%s.numHelpers = %d\n' % (netname, numClusters + 1))

        for i in range(numClusters):
            outf.write('**.python[%d]**.partition-id = %d\n' % (i, i))
            outf.write('**.configurator[%d]**.partition-id = %d\n' % (i, i))
            outf.write('**.cluster[%d]**.partition-id = %d\n' % (i, i))
            outf.write('**.configurator[%d].config=xmldoc("%s")\n' \
                       % (i, route_prefix + str(i)))
            outf.write('**.cluster[%d]**.networkLayer.configurator.' \
                       'networkConfiguratorModule = "%s.configurator[%d]"\n' \
                       % (i, netname, i))

        outf.write('**.python[%d]**.partition-id = %d\n' \
                   % (numClusters, numClusters))
        outf.write('**.configurator[%d]**.partition-id = %d\n' \
                   % (numClusters, numClusters))
        outf.write('**.configurator[%d].config=xmldoc("%s")\n' \
                   % (numClusters, route_prefix + str(numClusters)))
        outf.write('**.core[*]**.partition-id = %d\n' % (numClusters))
        outf.write('**.core[*]**.networkLayer.configurator.' \
                   'networkConfiguratorModule = "%s.configurator[%d]"\n' \
                   % (netname, numClusters))

    else:
        outf.write('**.networkLayer.configurator.networkConfiguratorModule ' \
                   '= "%s.configurator[0]"\n' % (netname))
        outf.write('**.configurator[*].config=xmldoc("%s")\n' % (route_prefix))


    # Set cluster types
    if mimic:
        outf.write('**.cluster[0].typename = "RealCluster"\n')
        for i in range(1, numClusters):
            outf.write('**.cluster[%d].typename = "MimicCluster"\n' % (i))
            outf.write('**.cluster[%d].mimicDCN.core_intf = %d\n' % (i, i))
    elif mimic_homa:
        outf.write('**.cluster[0].typename = "HomaCluster"\n')
        for i in range(1, numClusters):
            outf.write('**.cluster[%d].typename = "MimicHomaCluster"\n' % (i))
            outf.write('**.cluster[%d].mimicDCN.core_intf = %d\n' % (i, i))


    # Set seeds
    for i in range(0, numClusters):
        if (mimic_homa or mimic) and (i in emulatedClusters):
            torseeds = ""
            for j in range(0, numToRsPerSubtree):
                torseeds += " " + str(random.randint(0, 32767))
            outf.write('**.cluster[%d].mimicDCN.torEcmpSeeds = "%s"\n' \
                       % (i, torseeds[1:]))
        else:
            for j in range(0, numToRsPerSubtree):
                outf.write('**.cluster[%d].tor[%d].SEED = %d\n' \
                           % (i, j, random.randint(0, 32767)))
    for i in range(0, numClusters):
        if (mimic_homa or mimic) and (i in emulatedClusters):
            aggseeds = ""
            for j in range(0, numAggsPerSubtree):
                aggseeds += " " + str(random.randint(0, 32767))
            outf.write('**.cluster[%d].mimicDCN.aggEcmpSeeds = "%s"\n' \
                       % (i, aggseeds[1:]))
        else:
            for j in range(0, numAggsPerSubtree):
                outf.write('**.cluster[%d].agg[%d].SEED = %d\n' \
                           % (i, j, random.randint(0, 32767)))

    # TrainPCAPs config
    if (not mimic_homa) and (not mimic):
        # instrument cluster 1
        numAggUplinks = int(numCores / numAggsPerSubtree)

        outf.write('\n\n[Config TrainPCAPs]\n')
        outf.write('\n**.cluster[1].agg[**].numFeatureRecorders = %d\n\n' \
                   % (numAggUplinks))

        for i in range(0, numAggsPerSubtree):
            for j in range(0, numAggUplinks):
                pdmp = '**.cluster[1].agg[%d].featureRecorder[%d]' % (i, j)
                intf = numToRsPerSubtree + j
                outf.write('%s.moduleNamePatterns = "eth[%d]"\n' % (pdmp, intf))
                outf.write('%s.pdmpFile = "%s/edges%d/aggregation_%d_inf%d.pdmp"\n' \
                           % (pdmp, datadir, numClusters, i, j))

        outf.write('\n**.cluster[1].tor[**].numFeatureRecorders = 4\n\n')

        for i in range(0, numToRsPerSubtree):
            for j in range(0, numOfServersPerRack):
                pdmp = '**.cluster[1].tor[%d].featureRecorder[%d]' \
                       % (i, j)
                intf = j
                outf.write('%s.moduleNamePatterns = "eth[%d]"\n' % (pdmp, intf))
                rack_index = numToRsPerSubtree + i
                outf.write('%s.pdmpFile = "%s/hosts%d/host_%d_%d.pdmp"\n' \
                           % (pdmp, datadir, numClusters, rack_index, j))


    # EvalPCAPs config
    outf.write('\n\n[Config EvalPCAPs]\n')
    outf.write('\n**.cluster[0].host[**].numFeatureRecorders = 1\n\n')

    for i in range(0, numToRsPerSubtree):
        for j in range(0, numOfServersPerRack):
            pdmp = '**.cluster[0].host[%d].featureRecorder[0]' \
                   % (i * numOfServersPerRack + j)
            outf.write('%s.pdmpFile = "%s/eval%d/eval_%d_%d.pdmp"\n' \
                       % (pdmp, datadir, numClusters, i, j))


    # DebugPCAPs config
    if mimic_homa or mimic:
        outf.write('\n\n[Config DebugPCAPs]\n')
        outf.write('\n**.core[*].numFeatureRecorders = 1\n\n')

        for i in range(0, numCores):
            pdmp = '**.core[%d].featureRecorder[0]' % (i)
            outf.write('%s.pdmpFile = "%s/debug%d/core_%d.pdmp"\n' \
                       % (pdmp, datadir, numClusters, i))

        outf.write('\n**.cluster[1].host[*].numFeatureRecorders = 1\n\n')

        for i in range(0, numToRsPerSubtree):
            for j in range(0, numOfServersPerRack):
                pdmp = '**.cluster[1].host[%d].featureRecorder[0]' \
                       % (i * numOfServersPerRack + j)
                rack_index = i + numToRsPerSubtree
                outf.write('%s.pdmpFile = "%s/debug%d/host_%d_%d.pdmp"\n' \
                           % (pdmp, datadir, numClusters, rack_index, j))
