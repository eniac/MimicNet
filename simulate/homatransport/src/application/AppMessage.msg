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

cplusplus {{
#include "networklayer/contract/IPvXAddress.h"
}}
class noncobject IPvXAddress;


//
// TODO generated message class
//
packet AppMessage {
     IPvXAddress destAddr;
     IPvXAddress srcAddr;
     bool isEcho; // 0 is session message, 1 is echo message
     simtime_t msgCreationTime;
     simtime_t transportSchedDelay;
     //simtime_t transportSchedPreemptionLag;
     long msgBytesOnWire;
}
