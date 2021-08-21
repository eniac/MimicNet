//
// Copyright (C) 2014 RWTH Aachen University, Chair of Communication and Distributed Systems
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
// Authors: Ralf Bettermann, Mirko Stoffers, James Gross, Klaus Wehrle
//

#include "IPv4NetworkConfiguratorState.h"

Register_Class(IPv4NetworkConfiguratorState);

IPv4NetworkConfiguratorState::IPv4NetworkConfiguratorState() {

}

IPv4NetworkConfiguratorState::~IPv4NetworkConfiguratorState() {

}

std::vector<InterfaceTableState>& IPv4NetworkConfiguratorState::getInterfaceTableStates()
{
    return interfaceTableStates;
}

void IPv4NetworkConfiguratorState::parsimPack(cCommBuffer *buffer)
{

    buffer->pack(interfaceTableStates.size());

    for(unsigned int i = 0; i < interfaceTableStates.size();i++)
    {
        interfaceTableStates[i].parsimPack(buffer);
    }

}
void IPv4NetworkConfiguratorState::parsimUnpack(cCommBuffer *buffer)
{



    size_t numInterfaceTableStates;
    buffer->unpack(numInterfaceTableStates);
    for(unsigned int i = 0; i < numInterfaceTableStates; i++)
    {
        InterfaceTableState *its = new InterfaceTableState();
        its->parsimUnpack(buffer);
        interfaceTableStates.push_back(*its);
        delete its;
    }


}


/* InterfaceEntryState */
InterfaceEntryState::InterfaceEntryState()
{

}
InterfaceEntryState::~InterfaceEntryState()
{

}

void InterfaceEntryState::parsimPack(cCommBuffer *buffer)
{
    buffer->pack(loopback);
    buffer->pack(interfaceData);
    buffer->pack(entryName);
    buffer->pack(nodeInputGateId);
    buffer->pack(nodeOutputGateId);


}
void InterfaceEntryState::parsimUnpack(cCommBuffer *buffer)
{
    buffer->unpack(loopback);
    buffer->unpack(interfaceData);
    buffer->unpack(entryName);
    buffer->unpack(nodeInputGateId);
    buffer->unpack(nodeOutputGateId);

}

/*InterfaceTableState*/
InterfaceTableState::InterfaceTableState()
{
    interfaceTableModuleId = -1;
}
InterfaceTableState::~InterfaceTableState()
{

}


void InterfaceTableState::parsimPack(cCommBuffer *buffer)
{
    buffer->pack(interfaceTableModuleId);
    buffer->pack(entries.size());
    for(unsigned int i = 0; i < entries.size();i++)
    {
        entries[i].parsimPack(buffer);
    }

    buffer->pack(hostModuleFullPath);
    buffer->pack(hostModuleId);

}
void InterfaceTableState::parsimUnpack(cCommBuffer *buffer)
{
    buffer->unpack(interfaceTableModuleId);
    size_t numEntries;
    buffer->unpack(numEntries);
    for(unsigned int i = 0; i < numEntries; i++)
    {
        InterfaceEntryState *ies = new InterfaceEntryState();
        ies->parsimUnpack(buffer);
        entries.push_back(*ies);
        delete ies;
    }

    buffer->unpack(hostModuleFullPath);
    buffer->unpack(hostModuleId);

}

std::vector<InterfaceEntryState>& InterfaceTableState::getInterfaceEntries()
{
    return entries;
}

