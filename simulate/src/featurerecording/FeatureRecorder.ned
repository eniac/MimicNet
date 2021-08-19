//
// Copyright (C) 2005 Michael Tuexen
// Copyright (C) 2008 Irene Ruengeler
// Copyright (C) 2009 Thomas Dreibholz
// Copyright (C) 2011 Zoltan Bojthe
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//
package approx.featurerecording;

//
// Records custom feature lists of frames sent/received by other modules within
// the same host. By default, it records frames sent/received by L2 modules
// of ~StandardHost and ~Router. The output filename is expected in the
// pdmpFile parameter.
//
// <b>Which modules to record:</b> The list of modules can to be specified in
// the moduleNamePatterns parameter. It is a space-separated list of module
// names, which will be interpreted as children of the FeatureRecorder's parent
// module. To record elements of a module vector, add "[*]" to the name
// (example: "eth[*]").
//
// <b>Operation:</b> FeatureRecorder adds signal listeners to the recorded
// modules. The signals subscribed to are "packetSentToLower" and
// "packetReceivedFromLower", but these names can be overridden with the
// sendingSignalNames and receivingSignalNames parameters. The packets
// themselves are expected as cPacket* signal values.

simple FeatureRecorder
{
    parameters:
        bool verbose = default(false);  // whether to log packets on the module output
        string pdmpFile = default(""); // the PCAP file to be written
        string moduleNamePatterns = default("wlan[*] eth[*] ppp[*] ext[*]"); // space-separated list of sibling module names to listen on
        string sendingSignalNames = default("packetSentToLower"); // space-separated list of outbound packet signals to subscribe to
        string receivingSignalNames = default("packetReceivedFromLower"); // space-separated list of inbound packet signals to subscribe to
        @display("i=block/process;is=s");
}

