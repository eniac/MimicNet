package approx.mimicdcn;

simple MimicDCN
{
    parameters:
        @node();

        string variant;
        
        // interface that this cluster connects to on each core switch
        int core_intf;

        int servers_per_tor = default(4);
        int num_aggs = default(2);
        int num_agg_intfs = default(2);
        int num_tors = default(2);

        double min_link_latency = default(0.0005);
        int max_queue_len = default(90);
        double link_speed = default(100000000.0);
        double packet_size = default(1500.0);

        string ing_library;
        string ing_modelprefix;
        string egr_library;
        string egr_modelprefix;

        string ingress_traffic_file = default("");
        string egress_traffic_file = default("");
        string intermimic_model;

        string torEcmpSeeds;
        string aggEcmpSeeds;

    gates:
        inout intport[] @labels(IPv4Datagram-conn);
        inout extport[] @labels(IPv4Datagram-conn);
}
