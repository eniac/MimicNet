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

module HomaCluster like ICluster
{
    parameters:
        int degree;
        int serversPerRack;

    gates:
        inout port[degree*degree];

    submodules:
        host[degree*serversPerRack]: HomaHost {
            hostConfig = xmldoc("config.xml", "/hostConfig");
        }
        tor[degree]: MyRouter {}
        agg[degree]: MyRouter {}

    connections:     
        for i=0..(degree-1), for j=0..(serversPerRack-1) {
            host[i*serversPerRack+j].ethg++ <--> NormalChannel <--> tor[i].ethg++;
        }

        for i=0..(degree-1), for j=0..(degree-1) {
            tor[i].ethg++ <--> NormalChannel <--> agg[j].ethg++;
        }

        for i=0..(degree-1), for j=0..(degree-1) {
            agg[j].ethg++ <--> port[i*degree+j];
        }
}
