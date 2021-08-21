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

#ifndef IPV4NETWORKCONFIGURATORSTATE_H_
#define IPV4NETWORKCONFIGURATORSTATE_H_

#include <omnetpp.h>


class InterfaceEntryState : public cObject
{
public:
    InterfaceEntryState();
    virtual ~InterfaceEntryState();


    const char* getInterfaceData() const {
        return interfaceData;
    }

    void setInterfaceData(const char* interfaceData) {
        this->interfaceData = interfaceData;
    }

    bool isLoopback() const {
        return loopback;
    }

    void setLoopback(bool loopback) {
        this->loopback = loopback;
    }

    virtual void parsimPack(cCommBuffer *buffer);
    virtual void parsimUnpack(cCommBuffer *buffer);

    const char* getEntryName() const {
        return entryName;
    }

    void setEntryName(const char* entryName) {
        this->entryName = entryName;
    }

    int getNodeInputGateId() const {
        return nodeInputGateId;
    }

    void setNodeInputGateId(int nodeInputGateId) {
        this->nodeInputGateId = nodeInputGateId;
    }

    int getNodeOutputGateId() const {
        return nodeOutputGateId;
    }

    void setNodeOutputGateId(int nodeOutputGateId) {
        this->nodeOutputGateId = nodeOutputGateId;
    }

private:
    bool loopback;
    const char *interfaceData; //the name of the interface Data's class: e.g. IPv4InterfaceData.
    const char *entryName;

    int nodeInputGateId;
    int nodeOutputGateId;


};

class InterfaceTableState : public cObject
{
public:
    InterfaceTableState();
    virtual ~InterfaceTableState();

    virtual void parsimPack(cCommBuffer *buffer);
    virtual void parsimUnpack(cCommBuffer *buffer);

    int getInterfaceTableModuleId() const {
        return interfaceTableModuleId;
    }

    void setInterfaceTableModuleId(int interfaceTableModuleId) {
        this->interfaceTableModuleId = interfaceTableModuleId;
    }

    std::vector<InterfaceEntryState>& getInterfaceEntries();

    const char* getHostModuleFullPath() const {
        return hostModuleFullPath;
    }

    void setHostModuleFullPath(const char* hostModuleFullPath) {
        this->hostModuleFullPath = strdup(hostModuleFullPath);
    }

    int getHostModuleId() const {
        return hostModuleId;
    }

    void setHostModuleId(int hostModuleId) {
        this->hostModuleId = hostModuleId;
    }

private:
    int interfaceTableModuleId;
    const char* hostModuleFullPath;
    int hostModuleId;
    std::vector<InterfaceEntryState> entries;
};


class IPv4NetworkConfiguratorState : public cObject {
public:
    IPv4NetworkConfiguratorState();
    virtual ~IPv4NetworkConfiguratorState();

    std::vector<uint32>& getAssignedInterfaceAddresses();
    std::vector<uint32>& getAssignedNetworkAddresses();
    std::vector<uint32>& getAssignedNetworkNetmasks();

    std::vector<InterfaceTableState>& getInterfaceTableStates();

    virtual void parsimPack(cCommBuffer *buffer);
    virtual void parsimUnpack(cCommBuffer *buffer);

private:
    std::vector<InterfaceTableState> interfaceTableStates;
};

#endif /* IPV4NETWORKCONFIGURATORSTATE_H_ */
