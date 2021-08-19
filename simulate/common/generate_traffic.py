import argparse
import numpy as np
import sys


class custom_distribution:
    def __init__(self, rng, xp, fp):
        """takes x, y points of cdf"""
        np.all(np.diff(xp) > 0)
        self.rng = rng
        self.xp = xp
        self.fp = fp
    def sample(self, size=1):
        sampled_prob = self.rng.uniform(0, 1, size)
        # use interp func to find x given y
        sampled_x = [np.interp(prob, self.fp, self.xp) for prob in sampled_prob]
        return sampled_x

def generate_traffic_matrix(rng, load, linkSpeed, numOfServersPerRack,
                            numOfToRsPerSubtree, numOfSubtrees, numOfSpines,
                            emulatedRacks, includeIntraMimicTraffic = True,
                            includeInterMimicTraffic = True, end_time = 20.0):
    # bisection bandwidth = numSpine * linkRate
    # float from 0-1 specifying percentage of bisection bandwidth to use

    #NOTE: This could be substituted with a different distribution
    xp = [0, 10000, 20000, 30000, 50000, 80000,
          200000, 1e+06, 2e+06, 5e+06, 1e+07, 3e+07]
    fp = [0, 0.15, 0.2, 0.3, 0.4, 0.53, 0.6, 0.7, 0.8, 0.9, 0.97, 1]
    mean_flow_size = 1709062 * 8 # 1709062B from 1M samples of DCTCP
    dctcp_dist = custom_distribution(rng, xp, fp)

    numOfServers = numOfServersPerRack * numOfToRsPerSubtree * numOfSubtrees
    start_time = 0.0

    # 100Mbps * number of spine links
    bisection_bandwidth = linkSpeed * numOfSpines * numOfSubtrees;

    lambda_rate = bisection_bandwidth * load / mean_flow_size
    mean_interarrival_time = 1.0 / lambda_rate

    print("mean_interarrival_time =", mean_interarrival_time)
    print("estimated num of flows =", (end_time - start_time) / mean_interarrival_time)

    curr_time = start_time
    traffic_matrix = dict()
    while curr_time < end_time:
        interval = rng.exponential(mean_interarrival_time)
        curr_time += interval

        flow_size_in_bytes = int(dctcp_dist.sample(size=1)[0])

        # pick a random set of racks
        srcRack = -1
        dstRack = -1
        while srcRack == dstRack:
            srcRack = rng.choice(np.arange(0, numOfSubtrees*numOfToRsPerSubtree))
            dstRack = rng.choice(np.arange(0, numOfSubtrees*numOfToRsPerSubtree))

        src = rng.choice(np.arange(0, numOfServersPerRack)) + srcRack*numOfServersPerRack
        dst = rng.choice(np.arange(0, numOfServersPerRack)) + dstRack*numOfServersPerRack

        src_cluster = int(srcRack / numOfToRsPerSubtree)
        dst_cluster = int(dstRack / numOfToRsPerSubtree)

        intra_mimic = (srcRack in emulatedRacks) and (src_cluster == dst_cluster)
        inter_mimic = (srcRack in emulatedRacks) and (dstRack in emulatedRacks) and (src_cluster != dst_cluster)
        if intra_mimic and (not includeIntraMimicTraffic):
            continue
        if inter_mimic and (not includeInterMimicTraffic):
            continue

        if src not in traffic_matrix:
            traffic_matrix[src] = dict()
        if dst not in traffic_matrix[src]:
            traffic_matrix[src][dst] = []
        traffic_matrix[src][dst].append([curr_time, flow_size_in_bytes])

    return traffic_matrix

if __name__=="__main__":

    load = 0.70
    includeIntraMimicTraffic = False
    includeInterMimicTraffic = False
    numOfSpines = 4
    numOfSubtrees = 2
    numOfToRsPerSubtree = 2
    numOfServersPerRack = 4
    variant = "TCP"
    linkSpeed = 100e6
    
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=int, help="RNG seed required.")
    parser.add_argument("outfile", type=str, help="File to write traffic to.")
    parser.add_argument("--load", type=float,
                        help="Portion of bisection bandwidth utilized.")
    parser.add_argument("--includeIntraMimicTraffic", action="store_true",
                        help="Whether traffic local to the approximated " \
                             "cluster should be included.")
    parser.add_argument("--includeInterMimicTraffic", action="store_true",
                        help="Whether traffic between approximated cluster " \
                             "should be included.")
    parser.add_argument("--numCores", type=int,
                        help="Number of core switches (determines bisection " \
                             "bandwidth).")
    parser.add_argument("--numClusters", type=int,
                        help="Number clusters to generate traffic for.")
    parser.add_argument("--numToRs", type=int,
                        help="Number of ToR switches/racks per cluster.")
    parser.add_argument("--numServers", type=int,
                        help="Number of servers per rack.")
    parser.add_argument("--variant", type=str,
                        help="{TCP, Homa} Default is TCP.")
    parser.add_argument("--length", type=float,
                        help="The length of the trace in seconds.")
    parser.add_argument("--linkSpeed", type=float,
                        help="Link speed")
    args = parser.parse_args()

    seed = args.seed
    outfile = args.outfile
    length = 20.0
    if args.load:
        load = args.load
    if args.includeIntraMimicTraffic:
        includeIntraMimicTraffic = True
    if args.includeInterMimicTraffic:
        includeInterMimicTraffic = True
    if args.numCores:
        numOfSpines = args.numCores
    if args.numClusters:
        numOfSubtrees = args.numClusters
    if args.numToRs:
        numOfToRsPerSubtree = args.numToRs
    if args.numServers:
        numOfServersPerRack = args.numServers
    if args.variant:
        variant = args.variant
    if args.length:
        length = args.length
    if args.linkSpeed:
        linkSpeed = args.linkSpeed

    if variant == "TCP":
        variant_lower = "tcp"
        variant_camel = "Tcp"
        setupListeners = True
    elif variant == "Homa":
        setupListeners = False
    else:
        assert(False)

    rng = np.random.RandomState(seed=seed)
    numOfServers = numOfServersPerRack * numOfToRsPerSubtree * numOfSubtrees
    numOfServersPerSubtree = numOfServersPerRack * numOfToRsPerSubtree
    emulatedRacks = range(numOfToRsPerSubtree, numOfSubtrees*numOfToRsPerSubtree)
    emulatedClusters = range(1, numOfSubtrees)

    traffic_matrix = generate_traffic_matrix(rng, load, linkSpeed,
                                             numOfServersPerRack,
                                             numOfToRsPerSubtree, numOfSubtrees,
                                             numOfSpines, emulatedRacks,
                                             includeIntraMimicTraffic,
                                             includeInterMimicTraffic,
                                             length)

    num_flows = 0
    print(outfile)
    with open(outfile, "w") as outf:
        # set number of TCP apps
        # Each one gets a sender and listener to each other server. (n-1)*2 apps per server
        numRealSenders = numOfServers - numOfServersPerRack
        numApproxSenders = numRealSenders
        if not includeIntraMimicTraffic:
            numApproxSenders -= (numOfToRsPerSubtree - 1) * numOfServersPerRack
        if not includeInterMimicTraffic:
            numApproxSenders -= (numOfSubtrees - 2) * numOfServersPerSubtree

        for local_cluster in range(numOfSubtrees):
            if local_cluster in emulatedClusters:
                numApps = 2 * numApproxSenders
            else:
                numApps = 2 * numRealSenders

            for local_rack in range(numOfToRsPerSubtree):
                for local_server in range(numOfServersPerRack):
                    host_index = (local_rack * numOfServersPerRack) + local_server
                    if variant == "TCP":
                        outf.write("**.cluster[%d].host[%d].numTcpApps = %d\n" \
                                    % (local_cluster, host_index, numApps))
                    elif variant == "Homa":
                        outf.write("**.cluster[%d].host[%d].numTrafficGeneratorApp = %d\n" \
                                    % (local_cluster, host_index, numApps/2))

        if setupListeners:
            # set up listeners
            # there should be servers-1 listeners per server
            for local_cluster in range(numOfSubtrees):
                for local_rack in range(numOfToRsPerSubtree):
                    for local_server in range(numOfServersPerRack):
                        local_app = 0

                        for remote_cluster in range(numOfSubtrees):
                            if local_cluster in emulatedClusters:
                                if (not includeIntraMimicTraffic) \
                                        and (local_cluster == remote_cluster):
                                    continue
                                if (not includeInterMimicTraffic) \
                                        and (remote_cluster in emulatedClusters):
                                    continue
                            for remote_rack in range(numOfToRsPerSubtree):
                                if (local_cluster == remote_cluster) \
                                        and (local_rack == remote_rack):
                                    continue

                                for remote_server in range(numOfServersPerRack):
                                    remote_server_index = (remote_cluster * numOfServersPerSubtree) \
                                        + (remote_rack * numOfServersPerRack) \
                                        + remote_server

                                    host_index = (local_rack * numOfServersPerRack) + local_server
                                    app_name = "**.cluster[%d].host[%d].tcpApp[%d]" \
                                                % (local_cluster, host_index, local_app)

                                    outf.write("%s.typename = \"TCPEchoApp\"\n" % (app_name))
                                    outf.write("%s.localAddress = \"1.%d.%d.%d\"\n" \
                                                % (app_name, local_cluster, local_rack, local_server*4))
                                    outf.write("%s.localPort = %d\n" % (app_name, 1000 + remote_server_index))
                                    outf.write("%s.echoFactor = 1.0\n" % (app_name))

                                    local_app += 1

        # set up senders
        for local_cluster in range(numOfSubtrees):
            for local_rack in range(numOfToRsPerSubtree):
                for local_server in range(numOfServersPerRack):
                    local_server_index = (local_cluster * numOfServersPerSubtree) \
                                    + (local_rack * numOfServersPerRack) \
                                    + local_server
                    if not setupListeners:
                        local_app = 0
                    elif local_cluster in emulatedClusters:
                        local_app = numApproxSenders
                    else:
                        local_app = numRealSenders

                    for remote_cluster in range(numOfSubtrees):
                        if remote_cluster in emulatedClusters:
                            if (not includeIntraMimicTraffic) \
                                    and (local_cluster == remote_cluster):
                                continue
                            if (not includeInterMimicTraffic) \
                                    and (local_cluster in emulatedClusters):
                                continue
                        for remote_rack in range(numOfToRsPerSubtree):
                            if (local_cluster == remote_cluster) \
                                    and (local_rack == remote_rack):
                                continue

                            for remote_server in range(numOfServersPerRack):
                                remote_server_index = (remote_cluster * numOfServersPerSubtree) \
                                    + (remote_rack * numOfServersPerRack) \
                                    + remote_server

                                outf.write("\n")
                                host_index = (local_rack * numOfServersPerRack) + local_server

                                if variant == "TCP":
                                    app_name = "**.cluster[%d].host[%d].tcpApp[%d]" \
                                                % (local_cluster, host_index, local_app)
                                elif variant == "Homa":
                                    app_name = "**.cluster[%d].host[%d].trafficGeneratorApp[%d]" \
                                                % (local_cluster, host_index, local_app)
                                local_app += 1

                                if (local_server_index in traffic_matrix.keys()) \
                                        and (remote_server_index in traffic_matrix[local_server_index].keys()):
                                    flow_array = traffic_matrix[local_server_index][remote_server_index]

                                    if variant == "TCP":
                                        outf.write("%s.typename = \"TCPSessionApp\"\n" % (app_name))
                                        outf.write("%s.localPort = %d\n" % (app_name, 65535 - remote_server_index))
                                        outf.write("%s.connectPort = %d\n" % (app_name, 1000 + local_server_index))
                                        outf.write("%s.tOpen = %.9fs\n" % (app_name, flow_array[0][0]))
                                        outf.write("%s.tClose = %.9fs\n" % (app_name, flow_array[-1][0]+1))
                                        outf.write("%s.active = true\n" % (app_name))

                                        outf.write("%s.localAddress = \"1.%d.%d.%d\"\n" \
                                                    % (app_name, local_cluster, local_rack, local_server*4))
                                        outf.write("%s.connectAddress = \"1.%d.%d.%d\"\n" \
                                                    % (app_name, remote_cluster, remote_rack, remote_server*4))
                                    elif variant == "Homa":
                                        outf.write("%s.startTime = %.9fs\n" % (app_name, flow_array[0][0]))
                                        outf.write("%s.stopTime = %.9fs\n" % (app_name, flow_array[-1][0]+1))
                                        outf.write("%s.destAddress = \"1.%d.%d.%d\"\n" \
                                                    % (app_name, remote_cluster, remote_rack, remote_server*4))

                                    script = ""
                                    for d in flow_array:
                                        if script != "":
                                            script = script + "; "
                                        script = script + "%.9f %d" % (d[0], d[1])

                                        num_flows += 1
                                        if num_flows % 10000 == 0:
                                            outf.flush()
                                    outf.write("%s.sendScript = \"%s\"\n" % (app_name, script))

                                else:
                                    # print ("local_server_index %d not in traffic_matrix" % (local_server_index))
                                    outf.write("%s.typename = \"TCPSinkApp\"\n" % (app_name))
                                    outf.write("%s.localPort = %d\n" % (app_name, 65535 - remote_server_index))
                                    outf.write("%s.localAddress = \"1.%d.%d.%d\"\n" \
                                                % (app_name, local_cluster, local_rack, local_server*4))


    print("number of flows =", num_flows)
