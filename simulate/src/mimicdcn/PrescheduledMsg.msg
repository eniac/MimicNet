packet PrescheduledMsg
{
     int dst_server;
     int dst_rack;
     int src_server;
     int src_rack;
     int agg;
     int agg_intf;

     // for DCTCP
     bool ecn;

     // for Homa
     int priority;
     int length;
};
