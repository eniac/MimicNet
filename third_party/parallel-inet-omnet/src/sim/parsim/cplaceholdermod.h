//==========================================================================
//  CPLACEHOLDERMOD.H  -  header for
//
//                   OMNeT++/OMNEST
//           Discrete System Simulation in C++
//
//  Author: Andras Varga, 2003
//          Dept. of Electrical and Computer Systems Engineering,
//          Monash University, Melbourne, Australia
//
//==========================================================================

/*--------------------------------------------------------------*
  Copyright (C) 1992-2008 Andras Varga
  Copyright (C) 2006-2008 OpenSim Ltd.
  Copyright (C) 2014 RWTH Aachen University, Chair of Communication and Distributed Systems

  This file is distributed WITHOUT ANY WARRANTY. See the file
  `license' for details on this and other legal matters.
*--------------------------------------------------------------*/

#ifndef __CPLACEHOLDERMOD_H
#define __CPLACEHOLDERMOD_H

#include "cmodule.h"
#include "csimulation.h"

#include "ccomponenttype.h"

NAMESPACE_BEGIN

/**
 * In distributed parallel simulation, modules of the network
 * are distributed across partitions.
 *
 * Represents a module which was instantiated on a remote partition.
 *
 * @ingroup Parsim
 */
class SIM_API cPlaceholderModule : public cModule // so, noncopyable
{
  private:
    char *originClassNamep; //holds the classname of the class the cPlaceholder is representing
    int remoteProcId;

  protected:
    // internal: "virtual ctor" for cGate: creates cProxyGate
    virtual cGate *createGateObject(cGate::Type type);

  public:
    /** @name Constructors, destructor, assignment. */
    //@{
    /**
     * Constructor. Note that module objects should not be created directly,
     * only via their cModuleType objects. See cModule constructor for more info.
     */
    cPlaceholderModule(); //for compatibility, but it should not be used

    cPlaceholderModule(const char *originName);

    /**
     * Destructor.
     */
    virtual ~cPlaceholderModule();
    //@}

    /** @name Redefined cObject member functions. */
    //@{
    /**
     * Produces a one-line description of the object's contents.
     * See cObject for more details.
     */
    virtual std::string info() const;
    //@}

    /** @name Redefined cModule functions */
    //@{
    /**
     * Redefined to return true.
     */
    virtual bool isPlaceholder() const  {return true;}

    /**
     * Not implemented: throws an exception when called.
     */
    virtual void arrived(cMessage *msg, cGate *ongate, simtime_t t);

    //so that serial/parallel case get the same ids and so the same RNG seeds
    virtual void doBuildInside();

    /**
     * Does nothing.
     */
    virtual void scheduleStart(simtime_t t);
    //@}

    /**
     * Returns the classname, of the class, which this cPlaceholder should represent
     */

    virtual const char* getOriginClassName();

    /**
     * Getter/Setter for the remote proc id this placeholder module belongs to
     */
    void setRemoteProcId(int procid);
    int getRemoteProcId();

};


NAMESPACE_END


#endif

