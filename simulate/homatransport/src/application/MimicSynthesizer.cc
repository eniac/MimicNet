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
#include "MimicSynthesizer.h"
#include "transport/HomaPkt.h"
#include "networklayer/contract/IPvXAddressResolver.h"
#include "networklayer/common/InterfaceEntry.h"
#include "networklayer/common/InterfaceTable.h"
#include "networklayer/ipv4/IPv4InterfaceData.h"
Define_Module(MimicSynthesizer);

simsignal_t MimicSynthesizer::sentMsgSignal = registerSignal("sentMsg");
simsignal_t MimicSynthesizer::rcvdMsgSignal = registerSignal("rcvdMsg");

MimicSynthesizer::MimicSynthesizer()
{
    selfMsg = NULL;
    commandIndex = 0;
    commands.clear();
}

MimicSynthesizer::~MimicSynthesizer()
{
}
void
MimicSynthesizer::initialize()
{
    startTime = par("startTime").doubleValue();
    stopTime = par("stopTime").doubleValue();
    xmlConfig = par("appConfig").xmlValue();
    const char* DestAddr = par("destAddress");
    destAddress = IPvXAddress(DestAddr);
    const char* sendScripts = par("sendScript");
    parseScript(sendScripts);
    // Setup templated statistics ans signals
    // const char* msgSizeRanges = par("msgSizeRanges").stringValue();
    // registerTemplatedStats(msgSizeRanges);

    // Find host id for parent host module of this app
    cModule* parentHost = this->getParentModule();
    if (strcmp(parentHost->getName(), "host") != 0) {
        throw cRuntimeError("'%s': Not a valid parent module type. Expected"
                " \"HostBase\" for parent module type.",
                parentHost->getName());
    }
    parentHostIdx = parentHost->getIndex();
    // Send timer settings
    if (stopTime >= SIMTIME_ZERO && stopTime < startTime)
        throw cRuntimeError("Invalid startTime/stopTime parameters");

    selfMsg = new cMessage("sendTimer");
    simtime_t start = std::max(startTime, simTime());
    if ((stopTime < SIMTIME_ZERO) || (start < stopTime)) {
        selfMsg->setKind(START);
        scheduleAt(start, selfMsg);
    }

    if (stopTime < SIMTIME_ZERO) {
        stopTime = MAXTIME;
    }

    // Initialize statistic tracker variables
    // numSent = 0;
    // numReceived = 0;
    // WATCH(numSent);
    // WATCH(numReceived);

}

void
MimicSynthesizer::handleMessage(cMessage *msg)
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
MimicSynthesizer::sendMsg(long numBytes)
{
    /*
    IPvXAddress destAddrs;
    if (nextDestHostId == -1) {
        destAddrs = chooseDestAddr();
    } else {
        destAddrs = hostIdAddrMap[nextDestHostId];
    }
    char msgName[100];
    sprintf(msgName, "WorkloadSynthesizerMsg-%d", numSent);
    AppMessage *appMessage = new AppMessage(msgName);
    appMessage->setByteLength(sendMsgSize);
    appMessage->setDestAddr(destAddrs);
    appMessage->setSrcAddr(srcAddress);
    appMessage->setMsgCreationTime(appMessage->getCreationTime());
    appMessage->setTransportSchedDelay(appMessage->getCreationTime());
    emit(sentMsgSignal, appMessage);
    send(appMessage, "transportOut");
    numSent++;
    */
    //printf("%s sends a %lld bytes session message to %s!\n", srcAddress.get4().str().c_str(), numBytes, destAddress.get4().str().c_str());
    AppMessage *appMessage = new AppMessage("Session");
    appMessage->setByteLength(numBytes);
    appMessage->setDestAddr(destAddress);
    appMessage->setSrcAddr(srcAddress);
    appMessage->setIsEcho(0);
    appMessage->setMsgCreationTime(appMessage->getCreationTime());
    appMessage->setTransportSchedDelay(appMessage->getCreationTime());
    emit(sentMsgSignal, appMessage);
    send(appMessage, "transportOut");
}

void
MimicSynthesizer::processStart()
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

    // call parseXml to complete intialization based on the config.xml file
    // Start the Sender application based on the parsed xmlConfig results
    // If this app is not sender or is a sender but no receiver is available for
    // this sender, then just set the sendTimer to the stopTime and only wait
    // for message arrivals.
    if (commands.size() > 0)
    {
        selfMsg->setKind(SEND);
        scheduleAt(std::max(simTime(), commands[0].tSend), selfMsg);
    }
    //selfMsg->setKind(SEND);
    //scheduleAt(simTime(), selfMsg);
}

void
MimicSynthesizer::processStop() {
}

void
MimicSynthesizer::processSend()
{
	long numBytes = commands[commandIndex].numBytes;
    sendMsg(numBytes);

    if (++commandIndex < (int)commands.size()) {
        simtime_t tSend = commands[commandIndex].tSend;
        scheduleAt(std::max(tSend, simTime()), selfMsg);
    }
}


void
MimicSynthesizer::processRcvdMsg(cPacket* msg)
{
    AppMessage* rcvdMsg = check_and_cast<AppMessage*>(msg);
    emit(rcvdMsgSignal, rcvdMsg);
    //simtime_t completionTime = simTime() - rcvdMsg->getMsgCreationTime();
    //emit(msgE2EDelaySignal, completionTime);
    uint64_t msgByteLen = (uint64_t)(rcvdMsg->getByteLength());
    EV_INFO << "Received a message of length " << msgByteLen
            << "Bytes" << endl;

    delete rcvdMsg;
    //numReceived++;
}

void MimicSynthesizer::parseScript(const char *script)
{   
    const char *s = script;
    while (*s)
    {   
        // parse time
        while (isspace(*s))
            s++;
        
        if (!*s || *s == ';')
            break;
        
        const char *s0 = s;
        simtime_t tSend = strtod(s, &const_cast<char *&>(s));
        
        if (s == s0)
            throw cRuntimeError("Syntax error in script: simulation time expected");
        
        // parse number of bytes
        while (isspace(*s))
            s++;
        
        if (!isdigit(*s))
            throw cRuntimeError("Syntax error in script: number of bytes expected");
        
        long numBytes = strtol(s, NULL, 10);
        
        while (isdigit(*s))
            s++;
        
        // add command
        commands.push_back(Command(tSend, numBytes));
        
        // skip delimiter
        while (isspace(*s))
            s++;

        if (!*s)
            break;
        if (*s!=';')
            throw cRuntimeError("Syntax error in script: separator ';' missing");

        s++;

        while (isspace(*s))
            s++;
    }
}

void
MimicSynthesizer::finish()
{
    cancelAndDelete(selfMsg);
}
