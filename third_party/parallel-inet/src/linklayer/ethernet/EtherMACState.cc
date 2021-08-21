//
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
//
// Authors: Ralf Bettermann, Mirko Stoffers, James Gross, Klaus Wehrle 
//

#include "EtherMACState.h"

Register_Class(EtherMACState);
Register_Class(ConnectionState);

EtherMACState::EtherMACState() {
    lastAddress = 0;
    connectionStates = new cArray();
}

EtherMACState::~EtherMACState() {
    delete connectionStates;
}

unsigned int& EtherMACState::getLastAddress()
{
    return lastAddress;
}

void EtherMACState::parsimPack(cCommBuffer *buffer)
{
    buffer->pack(lastAddress);
    buffer->packObject(connectionStates);



}
void EtherMACState::parsimUnpack(cCommBuffer *buffer)
{
    buffer->unpack(lastAddress);
    connectionStates = dynamic_cast<cArray *>(buffer->unpackObject());
}


void EtherMACState::addConnectionState(ConnectionState *state)
{
    connectionStates->add(state);
}

cArray* EtherMACState::getConnectionStates()
{
    return connectionStates;
}


////////////////////////////////////////


ConnectionState::ConnectionState(){}

ConnectionState::ConnectionState(int moduleId,int gateId)
{
    this->moduleId = moduleId;
    this->gateId = gateId;
    this->connected = false;
}
ConnectionState::~ConnectionState()
{

}

void ConnectionState::parsimPack(cCommBuffer *buffer)
{
    buffer->pack(moduleId);
    buffer->pack(gateId);
    buffer->pack(connected);

}
void ConnectionState::parsimUnpack(cCommBuffer *buffer)
{
    buffer->unpack(moduleId);
    buffer->unpack(gateId);
    buffer->unpack(connected);
}

