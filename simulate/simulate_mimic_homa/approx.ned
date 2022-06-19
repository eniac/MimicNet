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

import inet.networklayer.autorouting.ipv4.IPv4NetworkConfigurator;

import approx.python.PythonInterp;


network ApproxFatTree
{
    parameters: 
        int numHelpers = default(1);
        int numClusters = default(2);
        int numCores = default(4);
        int degree = default(2);
        int serversPerRack = default(4);

    @display("bgb=817,468");
    submodules:
        python[numHelpers]: PythonInterp { }
        configurator[numHelpers]: IPv4NetworkConfigurator { }
        cluster[numClusters]: <> like ICluster {
            degree = degree;
            serversPerRack = serversPerRack;
        }
        core[numCores]: MyRouter { }

    connections:
        for i=0..(sizeof(cluster)-1), for j=0..(sizeof(core)-1) {
            core[j].ethg++ <--> NormalChannel <--> cluster[i].port[j];
        }
}
