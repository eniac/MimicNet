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

#include <unordered_set>
#include<iterator>
#include<iostream>
#include "MimicEchoSynthesizer.h"
#include "transport/HomaPkt.h"
#include "networklayer/contract/IPvXAddressResolver.h"
#include "networklayer/common/InterfaceEntry.h"
#include "networklayer/common/InterfaceTable.h"
#include "networklayer/ipv4/IPv4InterfaceData.h"
Define_Module(MimicEchoSynthesizer);


MimicEchoSynthesizer::MimicEchoSynthesizer()
{
    selfMsg = NULL;
}

MimicEchoSynthesizer::~MimicEchoSynthesizer()
{
}
void
MimicEchoSynthesizer::initialize()
{
    selfMsg = new cMessage("sendTimer");
    simtime_t start = simTime();
    selfMsg->setKind(START);
    scheduleAt(start, selfMsg);

}

void
MimicEchoSynthesizer::handleMessage(cMessage *msg)
{
    if (msg->isSelfMessage()) {
        ASSERT(msg == selfMsg);
        switch(msg->getKind()) {
            case START:
                processStart();
                break;
            case SEND:
                processSend();
                break;
            case STOP:
                processStop();
                break;
            default:
                throw cRuntimeError("Invalid kind %d in self message",
                        (int)selfMsg->getKind());
        }
    } else {
        processRcvdMsg(check_and_cast<AppMessage*>(msg));
    }
}

void
MimicEchoSynthesizer::processStart()
{
    // set srcAddress. The assumption here is that each host has only one
    // non-loopback interface and the IP of that interface is srcAddress.
    //InterfaceTable* ifaceTable = dynamic_cast<InterfaceTable*>(getSubmodule("interfaceTable"));
    InterfaceTable* ifaceTable =
            check_and_cast<InterfaceTable*>(
            getModuleByPath("^.interfaceTable"));
    InterfaceEntry* srcIface = NULL;
    IPv4InterfaceData* srcIPv4Data = NULL;
    for (int i=0; i < ifaceTable->getNumInterfaces(); i++) {
        if ((srcIface = ifaceTable->getInterface(i)) &&
                !srcIface->isLoopback() &&
                (srcIPv4Data = srcIface->ipv4Data())) {
            break;
        }
    }
    if (!srcIface) {
        throw cRuntimeError("Can't find a valid interface on the host");
    } else if (!srcIPv4Data) {
        throw cRuntimeError("Can't find an interface with IPv4 address");
    }
    srcAddress = IPvXAddress(srcIPv4Data->getIPAddress());

}

void
MimicEchoSynthesizer::processStop() {
}

void
MimicEchoSynthesizer::processSend()
{
}

void
MimicEchoSynthesizer::processRcvdMsg(cPacket* msg)
{
    AppMessage* rcvdMsg = check_and_cast<AppMessage*>(msg);
    uint64_t msgByteLen = (uint64_t)(rcvdMsg->getByteLength());
    EV_INFO << "Received a message of length " << msgByteLen
            << "Bytes" << endl;
    //printf("%s Received %d Bytes from %s!\n", rcvdMsg->getDestAddr().get4().str().c_str(), msgByteLen, rcvdMsg->getSrcAddr().get4().str().c_str());
    if (rcvdMsg->getIsEcho() == 1)
    {
        delete rcvdMsg;
        return ;
    }
    AppMessage *appMessage = new AppMessage("EchoMsg");
    appMessage->setByteLength(msgByteLen);
    appMessage->setDestAddr(rcvdMsg->getSrcAddr());
    appMessage->setSrcAddr(rcvdMsg->getDestAddr());
    appMessage->setMsgCreationTime(appMessage->getCreationTime());
    appMessage->setTransportSchedDelay(appMessage->getCreationTime());
    appMessage->setIsEcho(1);
    send(appMessage, "transportOut");
    delete rcvdMsg;
}

void
MimicEchoSynthesizer::finish()
{
    cancelAndDelete(selfMsg);
}
