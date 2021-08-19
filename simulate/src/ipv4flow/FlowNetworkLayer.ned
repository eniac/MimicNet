package approx.ipv4flow;

import inet.networklayer.arp.ARP;
import inet.networklayer.autorouting.ipv4.IPv4NodeConfigurator;
import inet.networklayer.ipv4.ErrorHandling;
import inet.networklayer.ipv4.ICMP;
import inet.networklayer.ipv4.IIGMP;


//
// Network layer of an IPv4 node.
//
// Interfaces to transport layer: TCP, UDP, echo/ping, RSVP
//
module FlowNetworkLayer
{
    parameters:
        bool proxyARP = default(true);
        string igmpType = default("IGMPv2");
        *.routingTableModule = default("^.^.routingTable");
        @display("i=block/fork");
    gates:
        input ifIn[] @labels(IPv4Datagram);
        output ifOut[] @labels(IPv4Datagram);
        input transportIn[] @labels(IPv4ControlInfo/down);
        output transportOut[] @labels(IPv4ControlInfo/up);
        input pingIn[] @labels(PingPayload/down);
        output pingOut[] @labels(PingPayload/up);
        input igmpIn;
        output igmpOut;

    submodules:
        configurator: IPv4NodeConfigurator {
            @display("p=39,158");
        }
        ip: IPv4Flow {
            parameters:
                useProxyARP = true; // as routes with unspecified next-hop addr are quite common
                @display("p=85,95;q=queue");
            gates:
                queueIn[sizeof(ifIn)];
                queueOut[sizeof(ifOut)];
        }
        arp: ARP {
            parameters:
                respondToProxyARP = proxyARP;
                @display("p=202,142;q=pendingQueue");
        }
        icmp: ICMP {
            parameters:
                @display("p=160,63");
        }
        igmp: <igmpType> like IIGMP {
            parameters:
                @display("p=39,33");
        }
        errorHandling: ErrorHandling {
            parameters:
                @display("p=239,63");
        }

    connections allowunconnected:
        for i=0..sizeof(transportIn)-1 {
            transportIn[i] --> { @display("m=n"); } --> ip.transportIn++;
        }
        for i=0..sizeof(transportOut)-1 {
            ip.transportOut++ --> { @display("m=n"); } --> transportOut[i];
        }

        ip.transportOut++ --> icmp.localIn;
        ip.transportIn++ <-- icmp.sendOut;

        ip.transportOut++ --> igmp.ipIn;
        ip.transportIn++ <-- igmp.ipOut;

        for i=0..sizeof(pingOut)-1 {
            icmp.pingOut++ --> { @display("m=n"); } --> pingOut[i];
        }
        for i=0..sizeof(pingIn)-1 {
            icmp.pingIn++ <-- { @display("m=n"); } <-- pingIn[i];
        }

        icmp.errorOut --> errorHandling.in;

        ip.arpOut --> arp.netwIn;
        ip.arpIn <-- arp.netwOut;

        igmp.routerOut --> igmpOut;
        igmp.routerIn <-- igmpIn;

        for i=0..sizeof(ifIn)-1 {
            ip.queueIn[i] <-- { @display("m=s"); } <-- ifIn[i];
        }
        for i=0..sizeof(ifOut)-1 {
            ip.queueOut[i] --> { @display("m=s"); } --> ifOut[i];
        }
}

