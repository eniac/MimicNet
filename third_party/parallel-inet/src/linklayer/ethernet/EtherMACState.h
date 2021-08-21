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

#ifndef ETHERMACSTATE_H_
#define ETHERMACSTATE_H_

#include <omnetpp.h>


class ConnectionState : public cObject
{
public:
    ConnectionState();
    ConnectionState(int moduleId,int gateId);
    virtual ~ConnectionState();

    virtual void parsimPack(cCommBuffer *buffer);
    virtual void parsimUnpack(cCommBuffer *buffer);

    bool isConnected() const
	{
        return connected;
    }

    void setConnected(bool connected)
	{
        this->connected = connected;
    }

    int getGateId() const
	{
        return gateId;
    }

    int getModuleId() const
	{
        return moduleId;
    }

private:
    int moduleId;
    int gateId;
    bool connected;

};


class EtherMACState : public cObject
{
public:
    EtherMACState();
    virtual ~EtherMACState();


    unsigned int& getLastAddress();


    virtual void parsimPack(cCommBuffer *buffer);
    virtual void parsimUnpack(cCommBuffer *buffer);

    void addConnectionState(ConnectionState *state);
    cArray* getConnectionStates();


private:
    unsigned int lastAddress;

    cArray *connectionStates;

};





#endif /* ETHERMACSTATE_H_ */
