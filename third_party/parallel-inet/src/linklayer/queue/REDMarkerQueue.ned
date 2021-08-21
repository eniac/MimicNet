//
// Copyright (C) 2021 Qizhen Zhang
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


package inet.linklayer.queue;

import inet.linklayer.queue.FIFOQueue;
import inet.linklayer.queue.REDMarker;
import inet.linklayer.IOutputQueue;

module REDMarkerQueue like IOutputQueue
{
    gates:
        input in;
        output out;

    submodules:
        red: REDMarker;
        fifo: FIFOQueue;
    connections:
        in --> red.in[0];
        red.out[0] --> fifo.in++;
        fifo.out --> out;
}

