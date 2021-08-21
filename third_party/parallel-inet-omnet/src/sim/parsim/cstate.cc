//=========================================================================
//  CSTATE.CC - part of
//
//                    OMNeT++/OMNEST
//             Discrete System Simulation in C++
//
//=========================================================================

/*--------------------------------------------------------------*
  Copyright (C) 2014 RWTH Aachen University, Chair of Communication and Distributed Systems

  This file is distributed WITHOUT ANY WARRANTY. See the file
  `license' for details on this and other legal matters.
*--------------------------------------------------------------*/

#include "cstate.h"
#include "globals.h"
#include "cexception.h"

#ifdef WITH_PARSIM
#include "ccommbuffer.h"
#endif

USING_NAMESPACE

Register_Class(cState);

cState::cState(){}

cState::cState(const char * moduleName, int moduleId) {
    this->moduleName = opp_strdup(moduleName);
    this->moduleId = moduleId;
    this->state = NULL;
}

cState::~cState(){

}

int cState::getModuleId()
{
    return moduleId;
}

const char *cState::getModuleName()
{
    return moduleName;
}

cObject *cState::getState()
{
    return state;
}
void cState::setState(cObject *state)
{
    this->state = state;
}

void cState::parsimPack(cCommBuffer *buffer)
{
    buffer->pack(this->moduleName);
    buffer->pack(this->moduleId);

    if(this->state == NULL)
        throw cRuntimeError("Error while parallel initializing: No state assigned. You have to assign a state with cState::setState() to your state object.");

    buffer->packObject(this->state);
}

void cState::parsimUnpack(cCommBuffer *buffer)
{

    buffer->unpack(this->moduleName);
    buffer->unpack(this->moduleId);
    this->state = buffer->unpackObject();
}

