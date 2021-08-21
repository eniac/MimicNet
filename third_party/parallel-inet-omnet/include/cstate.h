//==========================================================================
//   CSTATE.H  -  header for
//                     OMNeT++/OMNEST
//            Discrete System Simulation in C++
//
//==========================================================================

/*--------------------------------------------------------------*
  Copyright (C) 2014 RWTH Aachen University, Chair of Communication and Distributed Systems

  This file is distributed WITHOUT ANY WARRANTY. See the file
  `license' for details on this and other legal matters.
*--------------------------------------------------------------*/

#ifndef CSTATE_H_
#define CSTATE_H_

#include "cownedobject.h"

NAMESPACE_BEGIN

/**
 *  The cState object is responsible to hold the state of a simple module. 
 *  It is serialized and exchanged between LPs. 
 */
class cState : public cObject
{
public:
	/**
	 *  Constructor
	 */
	cState();
    cState(const char* moduleName, int moduleId);

	/**
	 *  Destructor
	 */
    virtual ~cState();

	/**
	 *  The module id of the module which created the cstate object 
	 */
    int getModuleId();

	/**
	 *  The (class) name of the module the cState object belongs to  
	 */
    const char *getModuleName();

	/**
	 *  Getter/setter for the state object 
	 */
    cObject *getState();
    void setState(cObject *state);

	/**
	 *  Since the state is exchanged betweenn different LPs, we need to serialize it  
	 */
    virtual void parsimPack(cCommBuffer *buffer);
    virtual void parsimUnpack(cCommBuffer *buffer);


private:
    const char *moduleName; //the name of the module the state belongs to
    int moduleId;     //the id of the module
    cObject *state;
};

NAMESPACE_END

#endif /* CSTATE_H_ */


