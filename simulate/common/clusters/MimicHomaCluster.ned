//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

import homatransport.common.HomaHost;

import approx.mimicdcn.MimicDCN;

module MimicHomaCluster like ICluster
{
    parameters:
        int degree;

    gates:
        inout port[degree*degree];

    submodules:
        host[degree*4]: HomaHost {
            hostConfig = xmldoc("config.xml", "/hostConfig");
        }
        mimicDCN: MimicDCN {
            num_tors = degree;
            num_aggs = degree;
            num_agg_intfs = degree;
        }

    connections:
        for i=0..(sizeof(port)-1) {
            port[i] <--> mimicDCN.extport++;
        }

        for i=0..(sizeof(host)-1) {
            host[i].ethg++ <--> NormalChannel <--> mimicDCN.intport++;
        }
}
