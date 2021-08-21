//
// Copyright (C) 2000 Institut fuer Telematik, Universitaet Karlsruhe
// Copyright (C) 2004,2011 Andras Varga
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


#include "UDPBackboneApp.h"
#include "UDPControlInfo_m.h"
#include "IPvXAddressResolver.h"
#include "InterfaceTableAccess.h"
#include "IPv4InterfaceData.h"

Define_Module(UDPBackboneApp);


simsignal_t UDPBackboneApp::sentPkSignal = SIMSIGNAL_NULL;
simsignal_t UDPBackboneApp::rcvdPkSignal = SIMSIGNAL_NULL;

void UDPBackboneApp::initialize(int stage)
{
    // because of IPvXAddressResolver, we need to wait until interfaces are registered,
    // address auto-assignment takes place etc.
    if (stage != 5)
        return;


    numSent = 0;
    numReceived = 0;
    counter = 0;

    WATCH(numSent);
    WATCH(numReceived);

    sentPkSignal = registerSignal("sentPk");
    rcvdPkSignal = registerSignal("rcvdPk");

    localPort = par("localPort");
    destPort = par("destPort");

    probabilitySendLocal = par("probabilitySendLocal");
    if(probabilitySendLocal < 0 || probabilitySendLocal > 1)
        error("invalid probabilitySendLocal Parameter (not in range 0,1)");

    socket.setOutputGate(gate("udpOut"));
    socket.bind(localPort);
    setSocketOptions();

    cModule *interfaceTableMod = this->getParentModule()->getSubmodule("interfaceTable");
    ASSERT(interfaceTableMod);
    InterfaceTable *interfaceTable = check_and_cast<InterfaceTable *>(interfaceTableMod);
    int numInterfaces = interfaceTable->getNumInterfaces();

    int myAddress = 0;
    for(int i = 0; i < numInterfaces; ++i)
    {
        InterfaceEntry *ie = interfaceTable->getInterface(i);
        if(!ie->isLoopback() && ie->ipv4Data())
        {
            myAddress = ie->ipv4Data()->getIPAddress().getInt();
            break;
        }
    }

    //get local and global addresses from ipv4NetworkConfigurator
    cModule *mod = simulation.getSystemModule()->getSubmodule("configurator",0);
    int numConfigurators = mod->getVectorSize();
    for(int i = 0; i < numConfigurators; ++i)
    {
        mod = simulation.getSystemModule()->getSubmodule("configurator",i);
        if(!mod->isPlaceholder())
            break;
    }

    IPv4NetworkConfigurator *conf = check_and_cast<IPv4NetworkConfigurator *>(mod);

    int myNetworkAddress = conf->getNetworkAddress(myAddress);

    destLocalAddresses = conf->getLocalAddresses(myNetworkAddress);
    destRemoteAddresses = conf->getNotLocalAddresses(myNetworkAddress);

    ASSERT(destLocalAddresses.size() > 0);
    ASSERT(destRemoteAddresses.size() > 0);

    stopTime = par("stopTime").doubleValue();
    simtime_t startTime = par("startTime").doubleValue();
    if (stopTime != 0 && stopTime <= startTime)
        error("Invalid startTime/stopTime parameters");


    simtime_t firstMessageTime = startTime + par("sendInterval").doubleValue();

    cMessage *timerMsg = new cMessage("sendTimer");
    scheduleAt(firstMessageTime, timerMsg);
}

void UDPBackboneApp::finish()
{
    std::cout << getFullPath() << " received=" << numReceived << endl;
}

void UDPBackboneApp::setSocketOptions()
{
    int timeToLive = par("timeToLive");
    if (timeToLive != -1)
        socket.setTimeToLive(timeToLive);

    int typeOfService = par("typeOfService");
    if (typeOfService != -1)
        socket.setTypeOfService(typeOfService);

    const char *multicastInterface = par("multicastInterface");
    if (multicastInterface[0])
    {
        IInterfaceTable *ift = InterfaceTableAccess().get(this);
        InterfaceEntry *ie = ift->getInterfaceByName(multicastInterface);
        if (!ie)
            throw cRuntimeError("Wrong multicastInterface setting: no interface named \"%s\"", multicastInterface);
        socket.setMulticastOutputInterface(ie->getInterfaceId());
    }

    bool receiveBroadcast = par("receiveBroadcast");
    if (receiveBroadcast)
        socket.setBroadcast(true);

    bool joinLocalMulticastGroups = par("joinLocalMulticastGroups");
    if (joinLocalMulticastGroups)
        socket.joinLocalMulticastGroups();
}

IPvXAddress UDPBackboneApp::chooseDestAddr()
{

    double randValue = par("sendLocal");

    if(randValue <= probabilitySendLocal) //send to local host
    {
        EV << "send To Local Host rand=" << randValue << endl;

        int k = intrand(destLocalAddresses.size());
        return destLocalAddresses[k];
    }
    else //send to not local host
    {
        EV << "send To Remote Host rand=" << randValue << endl;

        int k = intrand(destRemoteAddresses.size());
        return destRemoteAddresses[k];
    }


}

cPacket *UDPBackboneApp::createPacket()
{
    char msgName[32];
    sprintf(msgName, "UDPBackboneAppData-%d", counter++);

    cPacket *payload = new cPacket(msgName);
    payload->setByteLength(par("messageLength").longValue());
    return payload;
}

void UDPBackboneApp::sendPacket()
{
    cPacket *payload = createPacket();
    IPvXAddress destAddr = chooseDestAddr();

    emit(sentPkSignal, payload);
    socket.sendTo(payload, destAddr, destPort);
    numSent++;
}

void UDPBackboneApp::handleMessage(cMessage *msg)
{
    if (msg->isSelfMessage())
    {

        if(msg->getKind()==1000)
        {
            delete msg;
        }
        else
        {
            // send, then reschedule next sending
            sendPacket();
            simtime_t d = simTime() + par("sendInterval").doubleValue();
            if (stopTime == 0 || d < stopTime)
                scheduleAt(d, msg);
            else
                delete msg;
            }
    }
    else if (msg->getKind() == UDP_I_DATA)
    {
        // process incoming packet
        processPacket(PK(msg));
        numReceived++;
    }
    else if (msg->getKind() == UDP_I_ERROR)
    {
        EV << "Ignoring UDP error report\n";
        delete msg;
    }
    else
    {
        error("Unrecognized message (%s)%s", msg->getClassName(), msg->getName());
    }

    if (ev.isGUI())
    {
        char buf[40];
        sprintf(buf, "rcvd: %d pks\nsent: %d pks", numReceived, numSent);
        getDisplayString().setTagArg("t", 0, buf);
    }
}

void UDPBackboneApp::processPacket(cPacket *pk)
{
    emit(rcvdPkSignal, pk);
    EV << "Received packet: " << UDPSocket::getReceivedPacketInfo(pk) << endl;
    delete pk;

}

