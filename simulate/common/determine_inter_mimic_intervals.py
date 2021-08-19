import sys
import argparse
import numpy as np
from heapq import *
import murmur
from generate_traffic import generate_traffic_matrix

def getClusterFromIndex(index):
    return index // (tors_per_subtree * servers_per_rack)

def getRackFromIndex(index):
    return (index // servers_per_rack) % tors_per_subtree

def getServerFromIndex(index):
    return index % servers_per_rack

def getEndTimes(remaining_flows, available_bandwidth):
    remaining_flows = sorted(remaining_flows, key=lambda x: x[0])
    active_flows = [] # (size left, flow_record)
    finished_flows = []
    current_time = 0.0

    while remaining_flows or active_flows:
        # progress to the next out_flow
        if remaining_flows:
            next_flow = remaining_flows.pop(0)
            next_time = next_flow[0]
        else:
            next_flow = None
            next_time = float("inf")

        while active_flows and current_time < next_time:
            bandwidth_per_flow = available_bandwidth / len(active_flows)
            size, smallest_flow = active_flows[0] # peek
            estimated_end = current_time + size / bandwidth_per_flow

            if estimated_end <= next_time:
                smallest_flow.append(smallest_flow[1]) # append the flow size to the end
                smallest_flow[1] = estimated_end
                finished_flows.append(smallest_flow)
                heappop(active_flows)
                delta_time = estimated_end - current_time
                current_time = estimated_end
            else:
                delta_time = next_time - current_time
                current_time = next_time
            
            for i in range(len(active_flows)):
                size, flow = active_flows[i]
                remaining_size = size - bandwidth_per_flow * delta_time
                active_flows[i] = (remaining_size, flow)

        if next_flow:
            if current_time < next_time:
                current_time = next_time
            heappush(active_flows, (next_flow[1], next_flow))

    return finished_flows


if __name__=="__main__":    
    parser = argparse.ArgumentParser()
    parser.add_argument("seed", type=int, help="RNG seed required.")
    parser.add_argument("outfolder", type=str, help="Folder to write flows to.")
    parser.add_argument("--load", type=float,
                        help="Portion of bisection bandwidth utilized.")
    parser.add_argument("--includeIntraMimicTraffic", action="store_true",
                        help="Whether traffic local to the approximated " \
                             "cluster should be included.")
    parser.add_argument("--includeInterMimicTraffic", action="store_true",
                        help="Whether traffic between approximated cluster " \
                             "should be included.")
    parser.add_argument("--num_clusters", type=int,
                        help="Number clusters to generate traffic for.")
    parser.add_argument("--degree", type=int,
                        help="Number of ToRs/Aggs/AggUplinks per cluster")
    parser.add_argument("--num_servers", type=int,
                        help="Number of servers per rack.")
    parser.add_argument("--length", type=float,
                        help="The length of the trace in seconds.")
    parser.add_argument("--linkSpeed", type=float,
                        help="Link speed")
    args = parser.parse_args()

    length = 20.0
    load = 0.70
    includeIntraMimicTraffic = False
    includeInterMimicTraffic = False
    num_clusters = 2
    degree = 2
    num_servers = 4
    link_speed = 100e6

    seed = args.seed
    if args.load:
        load = args.load
    if args.includeIntraMimicTraffic:
        includeIntraMimicTraffic = args.includeIntraMimicTraffic
    if args.includeInterMimicTraffic:
        includeInterMimicTraffic = args.includeInterMimicTraffic
    if args.num_clusters:
        num_clusters = args.num_clusters
    if args.degree:
        degree = args.degree
    if args.num_servers:
        servers_per_rack = args.num_servers
    if args.length:
        length = args.length
    if args.linkSpeed:
        link_speed = args.linkSpeed

    tor_seeds, agg_seeds = murmur.load_seeds(seed, degree, num_clusters)
    tors_per_subtree = degree
    intfs_per_agg = degree
    num_cores = degree * degree
    num_of_servers = num_clusters * tors_per_subtree * servers_per_rack
    # 100Mbps * number of spine links
    bisection_bandwidth = link_speed * num_cores * num_clusters;
    available_bandwidth = float(bisection_bandwidth) / num_clusters


    # Get the full traffic matrix and the one we are using
    emulated_racks = range(tors_per_subtree, num_clusters * tors_per_subtree)
    rng = np.random.RandomState(seed=seed)
    leftover_matrix = generate_traffic_matrix(rng, load, link_speed,
                                              servers_per_rack,
                                              tors_per_subtree, num_clusters,
                                              num_cores, emulated_racks, True,
                                              True, length)
    rng = np.random.RandomState(seed=seed)
    traffic_matrix = generate_traffic_matrix(rng, load, link_speed,
                                             servers_per_rack,
                                             tors_per_subtree, num_clusters,
                                             num_cores, emulated_racks,
                                             includeIntraMimicTraffic,
                                             includeInterMimicTraffic,
                                             length)
    for src in traffic_matrix:
        for dst in traffic_matrix[src]:
            del leftover_matrix[src][dst]


    # Assemble all cross-cluster flows
    out_cluster_flows = []
    in_cluster_flows = []
    for i in range(num_clusters):
        out_cluster_flows.append([])
        in_cluster_flows.append([])

    for src in leftover_matrix:
        src_cluster = getClusterFromIndex(src)
        for dst in leftover_matrix[src]:
            dst_cluster = getClusterFromIndex(dst)
            if src_cluster == dst_cluster:
                # Ignore elided intra-mimic traffic as that should already be
                # accounted for
                continue

            # Determine Route Used
            src_rack = getRackFromIndex(src)
            src_server = getServerFromIndex(src)
            src_ip = "1.%d.%d.%d" % (src_cluster, src_rack, src_server*4)
            dst_rack = getRackFromIndex(dst)
            dst_server = getServerFromIndex(dst)
            dst_ip = "1.%d.%d.%d" % (dst_cluster, dst_rack, dst_server*4)
            src_port = 65535 - dst
            dst_port = 1000 + src

            # murmur.ecmp_helper()

            departure_tor_seed = tor_seeds[src_cluster][src_rack]
            num_aggs = tors_per_subtree
            departure_agg = murmur.ecmp_helper(num_aggs, departure_tor_seed,
                                               src_ip, src_port, dst_ip,
                                               dst_port)
            departure_agg_seed = agg_seeds[src_cluster][departure_agg]
            num_agg_intfs = tors_per_subtree
            departure_agg_intf = murmur.ecmp_helper(num_agg_intfs,
                                                    departure_agg_seed, src_ip,
                                                    src_port, dst_ip, dst_port)

            core = departure_agg + (departure_agg_intf * intfs_per_agg)
            arrival_agg = core // degree
            arrival_agg_intf = core % degree

            # Add the flow to the record
            flow_array = leftover_matrix[src][dst]
            for starttime_flowsize in flow_array:
                flow = [starttime_flowsize[0], starttime_flowsize[1],
                        dst_server, dst_rack, src_server, src_rack,
                        departure_agg, departure_agg_intf]
                out_cluster_flows[src_cluster].append(flow)

                flow = [starttime_flowsize[0], starttime_flowsize[1],
                        dst_server, dst_rack, src_server, src_rack,
                        arrival_agg, arrival_agg_intf]
                in_cluster_flows[dst_cluster].append(flow)

    for cluster, out_flows in enumerate(out_cluster_flows[1:], 1):
        finished_flows = getEndTimes(out_flows, available_bandwidth)
        finished_flows = sorted(finished_flows, key=lambda x: x[0])

        filename = args.outfolder+"cl"+str(cluster)+"_departing_flows.flow"
        with open(filename, 'w') as outf:
            for flow in finished_flows:
                outf.write(' '.join([str(flow_item) for flow_item in flow]) + '\n')

    for cluster, in_flows in enumerate(in_cluster_flows[1:], 1):
        finished_flows = getEndTimes(in_flows, available_bandwidth)
        finished_flows = sorted(finished_flows, key=lambda x: x[0])

        filename = args.outfolder+"cl"+str(cluster)+"_arriving_flows.flow"
        with open(filename, 'w') as outf:
            for flow in finished_flows:
                outf.write(' '.join([str(flow_item) for flow_item in flow]) + '\n')
