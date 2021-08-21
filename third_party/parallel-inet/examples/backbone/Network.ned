//
// Copyright (C) 2014 RWTH Aachen University, Chair of Communication and Distributed Systems
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//
//
// Authors: Ralf Bettermann, Mirko Stoffers, James Gross, Klaus Wehrle 
//

package inet.examples.backbone;

import ned.DelayChannel;
import ned.DatarateChannel;
import inet.nodes.inet.Router;
import inet.nodes.inet.StandardHost;
import inet.networklayer.autorouting.ipv4.IPv4NetworkConfigurator;
import inet.nodes.ethernet.EtherSwitch;

network Net60
{
    parameters:
        int numConfigurators = default(1);
        int numTreeLans = default(57);
        
        double internetChannelDelay @unit(ms) = default(5ms);

    types:

    submodules:
        backbonerouter[57]: Router {
            parameters:
                //address = index;
        }

        treeLan[numTreeLans]: TreeNetwork {
            parameters:
        }
        configurator[numConfigurators]: IPv4NetworkConfigurator {
            parameters:
        }


    connections allowunconnected:


        backbonerouter[0].ethg++ <--> BackboneChannel <--> backbonerouter[1].ethg++;
        backbonerouter[1].ethg++ <--> BackboneChannel <--> backbonerouter[2].ethg++;
        backbonerouter[1].ethg++ <--> BackboneChannel <--> backbonerouter[4].ethg++;
        backbonerouter[3].ethg++ <--> BackboneChannel <--> backbonerouter[4].ethg++;
        backbonerouter[4].ethg++ <--> BackboneChannel <--> backbonerouter[5].ethg++;
        backbonerouter[4].ethg++ <--> BackboneChannel <--> backbonerouter[7].ethg++;
        backbonerouter[5].ethg++ <--> BackboneChannel <--> backbonerouter[6].ethg++;
        backbonerouter[5].ethg++ <--> BackboneChannel <--> backbonerouter[10].ethg++;
        backbonerouter[6].ethg++ <--> BackboneChannel <--> backbonerouter[7].ethg++;
        backbonerouter[6].ethg++ <--> BackboneChannel <--> backbonerouter[9].ethg++;
        backbonerouter[7].ethg++ <--> BackboneChannel <--> backbonerouter[8].ethg++;
        backbonerouter[7].ethg++ <--> BackboneChannel <--> backbonerouter[12].ethg++;
        backbonerouter[9].ethg++ <--> BackboneChannel <--> backbonerouter[11].ethg++;
        backbonerouter[10].ethg++ <--> BackboneChannel <--> backbonerouter[11].ethg++;
        backbonerouter[10].ethg++ <--> BackboneChannel <--> backbonerouter[13].ethg++;
        backbonerouter[11].ethg++ <--> BackboneChannel <--> backbonerouter[12].ethg++;
        backbonerouter[11].ethg++ <--> BackboneChannel <--> backbonerouter[14].ethg++;
        backbonerouter[12].ethg++ <--> BackboneChannel <--> backbonerouter[15].ethg++;
        backbonerouter[13].ethg++ <--> BackboneChannel <--> backbonerouter[18].ethg++;
        backbonerouter[14].ethg++ <--> BackboneChannel <--> backbonerouter[15].ethg++;
        backbonerouter[14].ethg++ <--> BackboneChannel <--> backbonerouter[22].ethg++;
        backbonerouter[15].ethg++ <--> BackboneChannel <--> backbonerouter[16].ethg++;
        backbonerouter[16].ethg++ <--> BackboneChannel <--> backbonerouter[17].ethg++;
        backbonerouter[16].ethg++ <--> BackboneChannel <--> backbonerouter[23].ethg++;
        backbonerouter[18].ethg++ <--> BackboneChannel <--> backbonerouter[19].ethg++;
        backbonerouter[18].ethg++ <--> BackboneChannel <--> backbonerouter[21].ethg++;
        backbonerouter[19].ethg++ <--> BackboneChannel <--> backbonerouter[20].ethg++;
        backbonerouter[19].ethg++ <--> BackboneChannel <--> backbonerouter[26].ethg++;
        backbonerouter[20].ethg++ <--> BackboneChannel <--> backbonerouter[21].ethg++;
        backbonerouter[20].ethg++ <--> BackboneChannel <--> backbonerouter[24].ethg++;
        backbonerouter[20].ethg++ <--> BackboneChannel <--> backbonerouter[25].ethg++;
        backbonerouter[21].ethg++ <--> BackboneChannel <--> backbonerouter[22].ethg++;
        backbonerouter[21].ethg++ <--> BackboneChannel <--> backbonerouter[23].ethg++;
        backbonerouter[21].ethg++ <--> BackboneChannel <--> backbonerouter[24].ethg++;
        backbonerouter[23].ethg++ <--> BackboneChannel <--> backbonerouter[24].ethg++;
        backbonerouter[24].ethg++ <--> BackboneChannel <--> backbonerouter[28].ethg++;
        backbonerouter[25].ethg++ <--> BackboneChannel <--> backbonerouter[27].ethg++;
        backbonerouter[26].ethg++ <--> BackboneChannel <--> backbonerouter[32].ethg++;
        backbonerouter[27].ethg++ <--> BackboneChannel <--> backbonerouter[29].ethg++;
        backbonerouter[27].ethg++ <--> BackboneChannel <--> backbonerouter[30].ethg++;
        backbonerouter[27].ethg++ <--> BackboneChannel <--> backbonerouter[32].ethg++;
        backbonerouter[28].ethg++ <--> BackboneChannel <--> backbonerouter[29].ethg++;
        backbonerouter[28].ethg++ <--> BackboneChannel <--> backbonerouter[31].ethg++;
        backbonerouter[29].ethg++ <--> BackboneChannel <--> backbonerouter[31].ethg++;
        backbonerouter[30].ethg++ <--> BackboneChannel <--> backbonerouter[36].ethg++;
        backbonerouter[31].ethg++ <--> BackboneChannel <--> backbonerouter[33].ethg++;
        backbonerouter[32].ethg++ <--> BackboneChannel <--> backbonerouter[34].ethg++;
        backbonerouter[33].ethg++ <--> BackboneChannel <--> backbonerouter[37].ethg++;
        backbonerouter[34].ethg++ <--> BackboneChannel <--> backbonerouter[35].ethg++;
        backbonerouter[34].ethg++ <--> BackboneChannel <--> backbonerouter[40].ethg++;
        backbonerouter[35].ethg++ <--> BackboneChannel <--> backbonerouter[36].ethg++;
        backbonerouter[35].ethg++ <--> BackboneChannel <--> backbonerouter[39].ethg++;
        backbonerouter[36].ethg++ <--> BackboneChannel <--> backbonerouter[37].ethg++;
        backbonerouter[37].ethg++ <--> BackboneChannel <--> backbonerouter[38].ethg++;
        backbonerouter[38].ethg++ <--> BackboneChannel <--> backbonerouter[39].ethg++;
        backbonerouter[38].ethg++ <--> BackboneChannel <--> backbonerouter[42].ethg++;
        backbonerouter[39].ethg++ <--> BackboneChannel <--> backbonerouter[40].ethg++;
        backbonerouter[39].ethg++ <--> BackboneChannel <--> backbonerouter[41].ethg++;
        backbonerouter[40].ethg++ <--> BackboneChannel <--> backbonerouter[43].ethg++;
        backbonerouter[40].ethg++ <--> BackboneChannel <--> backbonerouter[44].ethg++;
        backbonerouter[40].ethg++ <--> BackboneChannel <--> backbonerouter[52].ethg++;
        backbonerouter[41].ethg++ <--> BackboneChannel <--> backbonerouter[42].ethg++;
        backbonerouter[41].ethg++ <--> BackboneChannel <--> backbonerouter[43].ethg++;
        backbonerouter[42].ethg++ <--> BackboneChannel <--> backbonerouter[43].ethg++;
        backbonerouter[43].ethg++ <--> BackboneChannel <--> backbonerouter[46].ethg++;
        backbonerouter[44].ethg++ <--> BackboneChannel <--> backbonerouter[45].ethg++;
        backbonerouter[44].ethg++ <--> BackboneChannel <--> backbonerouter[47].ethg++;
        backbonerouter[45].ethg++ <--> BackboneChannel <--> backbonerouter[46].ethg++;
        backbonerouter[46].ethg++ <--> BackboneChannel <--> backbonerouter[49].ethg++;
        backbonerouter[47].ethg++ <--> BackboneChannel <--> backbonerouter[48].ethg++;
        backbonerouter[48].ethg++ <--> BackboneChannel <--> backbonerouter[50].ethg++;
        backbonerouter[48].ethg++ <--> BackboneChannel <--> backbonerouter[51].ethg++;
        backbonerouter[49].ethg++ <--> BackboneChannel <--> backbonerouter[50].ethg++;
        backbonerouter[50].ethg++ <--> BackboneChannel <--> backbonerouter[53].ethg++;
        backbonerouter[51].ethg++ <--> BackboneChannel <--> backbonerouter[52].ethg++;
        backbonerouter[51].ethg++ <--> BackboneChannel <--> backbonerouter[53].ethg++;
        backbonerouter[52].ethg++ <--> BackboneChannel <--> backbonerouter[53].ethg++;
        backbonerouter[52].ethg++ <--> BackboneChannel <--> backbonerouter[54].ethg++;
        backbonerouter[53].ethg++ <--> BackboneChannel <--> backbonerouter[56].ethg++;
        backbonerouter[54].ethg++ <--> BackboneChannel <--> backbonerouter[55].ethg++;
        backbonerouter[55].ethg++ <--> BackboneChannel <--> backbonerouter[56].ethg++;

        for i=0..numTreeLans-1 {
            backbonerouter[i].ethg++ <--> InternetChannel{delay=internetChannelDelay;} <--> treeLan[i].ethg;
        }

}

channel BackboneChannel extends DatarateChannel
{
    parameters:
        delay = default(100us);
        datarate = default(100Gbps);
}
channel InternetChannel extends DatarateChannel
{
    parameters:
        datarate = default(10Gbps);
}

channel TreeChannel extends DatarateChannel
{
    parameters:
        delay = default(100us);
        datarate = default(10Gbps);
}
channel SwitchChannel extends DatarateChannel
{
    parameters:
        delay = default(5us);
        datarate = default(10Gbps);
}
channel HostChannel extends DatarateChannel
{
    parameters:
        delay = default(100us);
        datarate = default(1Gbps);
}


module TreeNetwork
{
    parameters:
        int h; 				//number of levels of the tree (routers)
        int k; 				//branching factor (routers)
        int numLeafHosts;	//number of hosts which will be connected to each leaf router
        int numInnerHosts;	//number of hosts which will be connected to each inner router

        //variables, which cannot be overwritten in .ini file
        int numRouter = (1-(k)^(h))/(1-k);		//Geometric series
        int numLeafRouter = k^(h-1);
        int numInnerRouter = (1-k^(h-1))/(1-k);

        @display("i=cloud_s");

    gates:
        inout ethg;		//connects this model to the outside

    submodules:
        router[numRouter]: Router {
            parameters:
                //address = index;
        }

        leafSwitch[numLeafRouter]: EtherSwitch
		{
            parameters:
        }

        leafHost[numLeafRouter*numLeafHosts]: StandardHost
		{
            parameters:
        }

        innerSwitch[numInnerRouter]: EtherSwitch
		{
            parameters:
        }

        innerHost[numInnerRouter*numInnerHosts]: StandardHost
		{
            parameters:
        }

    connections allowunconnected:

        //connect the root router with the outside
        router[0].ethg++ <--> ethg;   //note: the channel is no datarate channel, the module which connects has to be a datarate channel

        //connect the tree network (router[0] is root, router[i]'s k childs are: router[k*i+1],router[k*i+2],...,router[k*i+k])
        for i=0..numInnerRouter - 1, for j=1..k {
            router[i].ethg++ <--> TreeChannel <--> router[k*i+j].ethg++;
        }

        //connect inner routers with inner switches
        for i=0..numInnerRouter -1 {
            router[i].ethg++ <--> SwitchChannel <--> innerSwitch[i].ethg++;
        }

        //connect hosts to each inner Switch
        for i=0..numInnerRouter - 1, for j=0..numInnerHosts - 1 {
            innerSwitch[i].ethg++ <--> HostChannel <--> innerHost[j+(i*numInnerHosts)].ethg++;
        }

        //connect leaf switches to leaf routers
        for i=0..numLeafRouter - 1 {
            router[i+((1-k^(h-1))/(1-k))].ethg++ <--> SwitchChannel <--> leafSwitch[i].ethg++;
        }

        //connect hosts to each leaf switch
        for i=0..numLeafRouter - 1, for j=0..numLeafHosts - 1 {
            leafSwitch[i].ethg++ <--> HostChannel <--> leafHost[j+(i*numLeafHosts)].ethg++;
        }

}





network Net3
{
    parameters:
        int numConfigurators = default(1);
        int numTreeLans = default(3);
        int internetChannelDelay @unit(ms) = default(5ms);
    types:

    submodules:
        backbonerouter[3]: Router {
            parameters:
                //address = index;
        }

        treeLan[numTreeLans]: TreeNetwork {
            parameters:
        }
        configurator[numConfigurators]: IPv4NetworkConfigurator {
            parameters:
                @display("p=232,128");
        }


    connections allowunconnected:


        backbonerouter[0].ethg++ <--> BackboneChannel <--> backbonerouter[1].ethg++;
        backbonerouter[0].ethg++ <--> BackboneChannel <--> backbonerouter[2].ethg++;
        backbonerouter[1].ethg++ <--> BackboneChannel <--> backbonerouter[2].ethg++;

        for i=0..numTreeLans-1 {
            backbonerouter[i].ethg++ <--> InternetChannel{delay=internetChannelDelay;} <--> treeLan[i].ethg;
        }

}
