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

#ifndef __INET_REDDROPPER_H_
#define __INET_REDDROPPER_H_

#include "INETDefs.h"
#include "AlgorithmicMarkerBase.h"
#include "EcnTag.h"

static double const NaN = 0.0 / 0.0;

/**
 * Implementation of Random Early Detection (RED).
 */
class REDMarker : public AlgorithmicMarkerBase
{
  protected:
    enum RedResult { QUEUE_FULL, RANDOMLY_ABOVE_LIMIT, RANDOMLY_BELOW_LIMIT, ABOVE_MAX_LIMIT, BELOW_MIN_LIMIT };

  protected:
    double wq = 0.0;
    double minth = NaN;
    double maxth = NaN;
    double maxp = NaN;
    double pkrate = NaN;
    double count = NaN;

    double avg = 0.0;
    simtime_t q_time;

    int packetCapacity = -1;
    bool useEcn = false;
    bool markNext = false;

  public:
    REDMarker() {}
  protected:
    virtual ~REDMarker();
    virtual void initialize();
    virtual RedResult doRandomEarlyDetection(const cPacket *packet);
    virtual IPEcnCode getEcn(const cPacket *packet);
    virtual void setEcn(cPacket *packet, IPEcnCode);
    virtual bool shouldDrop(cPacket *packet);
    virtual void markPacket(cPacket *packet);
    virtual void sendOut(cPacket *packet);
};

#endif

