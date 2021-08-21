//
// Copyright (C) 2020 Marcel Marek, 2021 Qizhen Zhang
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
// along with this program; if not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
//

#ifndef __INET_DCTCP_H
#define __INET_DCTCP_H

#include "DCTCPFamily.h"
#include "TCPReno.h"

/**
 * State variables for DCTCP.
 */
typedef DCTCPFamilyStateVariables DCTCPStateVariables;

/**
 * Implements DCTCP.
 */
class INET_API DCTCP : public TCPReno
{
  protected:
    DCTCPStateVariables *& state;

    cOutVector *loadVector; // will record load
    cOutVector *calcLoadVector; // will record total number of RTOs
    cOutVector *markingProbVector; // will record marking probability

    /** Create and return a DCTCPStateVariables object. */
    virtual TCPStateVariables *createStateVariables()
    {
        return new DCTCPStateVariables();
    }

    virtual void initialize();

  public:
    /** Constructor */
    DCTCP();

    /**
     * Descructor
     * 
    */
    virtual ~DCTCP();

    /** Redefine what should happen when data got acked, to add congestion window management */
    virtual void receivedDataAck(uint32 firstSeqAcked);

    virtual bool shouldMarkAck();

    virtual void processEcnInEstablished();
};

#endif

