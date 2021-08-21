//
// Copyright (C) 2012 Opensim Ltd.
// Author: Tamas Borbely
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

#include "REDMarker.h"
#include "EtherFrame.h"
#include "IPv4Datagram.h"
#include "opp_utils.h"

Define_Module(REDMarker);

REDMarker::~REDMarker()
{
}

void REDMarker::initialize()
{
    AlgorithmicMarkerBase::initialize();

    wq = par("wq");
    if (wq < 0.0 || wq > 1.0)
        throw cRuntimeError("Invalid value for wq parameter: %g", wq);
    minth = par("minth");
    maxth = par("maxth");
    maxp = par("maxp");
    pkrate = par("pkrate");
    count = -1;
    if (minth < 0.0)
        throw cRuntimeError("minth parameter must not be negative");
    if (maxth < 0.0)
        throw cRuntimeError("maxth parameter must not be negative");
    if (minth >= maxth)
        throw cRuntimeError("minth must be smaller than maxth");
    if (maxp < 0.0 || maxp > 1.0)
        throw cRuntimeError("Invalid value for maxp parameter: %g", maxp);
    if (pkrate < 0.0)
        throw cRuntimeError("Invalid value for pkrate parameter: %g", pkrate);
    useEcn = par("useEcn");
    packetCapacity = par("packetCapacity");
    if (maxth > packetCapacity) {
        throw cRuntimeError("Warning: packetCapacity < maxth. Setting capacity to maxth");
        packetCapacity = maxth;
    }
}

REDMarker::RedResult REDMarker::doRandomEarlyDetection(const cPacket *packet)
{
    int queueLength = getLength();

    if (queueLength > 0) {
        // TD: This following calculation is only useful when the queue is not empty!
        avg = (1 - wq) * avg + wq * queueLength;
    }
    else {
        // TD: Added behaviour for empty queue.
        const double m = SIMTIME_DBL(simTime() - q_time) * pkrate;
        avg = pow(1 - wq, m) * avg;
    }

    if (queueLength >= packetCapacity) { // maxth is also the "hard" limit
        EV_DEBUG << "Queue length (" << queueLength << ") >= capacity (" << packetCapacity << ")\n";
        count = 0;
        return QUEUE_FULL;
    }
    else if (minth <= avg && avg < maxth) {
        count++;
        const double pb = maxp * (avg - minth) / (maxth - minth);
        const double pa = pb / (1 - count * pb); // TD: Adapted to work as in [Floyd93].
        if (dblrand() < pa) {
            EV_DEBUG << "Random early packet detected (avg queue len = " << avg << ", pb = " << pb << ")\n";
            count = 0;
            return RANDOMLY_ABOVE_LIMIT;
        }
        else
            return RANDOMLY_BELOW_LIMIT;
    }
    else if (avg >= maxth) {
        EV_DEBUG << "Average queue length (" << avg << ") >= maxth (" << maxth << ")\n";
        count = 0;
        return ABOVE_MAX_LIMIT;
    }
    else {
        count = -1;
    }

    return BELOW_MIN_LIMIT;
}

IPEcnCode REDMarker::getEcn(const cPacket *packet)
{
    IPEcnCode ecn = IP_ECN_NOT_ECT;
    if (dynamic_cast<const EtherFrame *>(packet) != NULL) {
        const IPv4Datagram *ipv4pkt = dynamic_cast<IPv4Datagram *>(packet->getEncapsulatedPacket());
        if (ipv4pkt != NULL) {
            ecn = static_cast<IPEcnCode>(ipv4pkt->getExplicitCongestionNotification());
        }
    }
    return ecn;
}

void REDMarker::setEcn(cPacket *packet, IPEcnCode ecn)
{
    cPacket *higherlayerpkt = packet->decapsulate();
    IPv4Datagram *ipv4pkt = check_and_cast<IPv4Datagram *>(higherlayerpkt); // guaranteed to be IPv4 packet
    ipv4pkt->setExplicitCongestionNotification(ecn);
    packet->encapsulate(ipv4pkt);
}

bool REDMarker::shouldDrop(cPacket *packet)
{
    if (getLength() >= packetCapacity) {
        return true;
    }
    return false;
}

void REDMarker::markPacket(cPacket *packet)
{
    RedResult lastResult = doRandomEarlyDetection(packet);
    switch (lastResult) {
        case RANDOMLY_ABOVE_LIMIT:
        case ABOVE_MAX_LIMIT: {
            if (useEcn) {
                IPEcnCode ecn = getEcn(packet);
                if (ecn != IP_ECN_NOT_ECT) {
                    // if next packet should be marked and it is not
                    if (markNext && ecn != IP_ECN_CE) {
                        setEcn(packet, IP_ECN_CE);
                        markNext = false;
                    }
                    else {
                        if (ecn == IP_ECN_CE)
                            markNext = true;
                        else
                            setEcn(packet, IP_ECN_CE);
                    }
                }
            }
        }
        case RANDOMLY_BELOW_LIMIT:
        case BELOW_MIN_LIMIT:
        case QUEUE_FULL:
            return;
        default:
            throw cRuntimeError("Unknown RED result");
    }
}

void REDMarker::sendOut(cPacket *packet)
{
    int index = packet->getArrivalGate()->getIndex();
    send(packet, "out", index);
    int queueLength = getLength();
    if (queueLength == 0)
        q_time = simTime();
}
