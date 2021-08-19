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
package homatransport.application;

//
// This module generates messages with sizes taken from distributions like DCTCP
// or Facebook key-value workload and passes the generated messages to the
// transport layer to the transport protocol.
//
simple MimicEchoSynthesizer
{
    parameters:

    gates:
        input transportIn @label(AppMessage/up);
        output transportOut @labels(AppMessage/down);
}
