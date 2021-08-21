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

#ifndef __INET_THRESHOLDMARKER_H_
#define __INET_THRESHOLDMARKER_H_

#include "INETDefs.h"
#include "AlgorithmicMarkerBase.h"
#include "EcnTag.h"


/**
 * Implementation of Random Early Detection (RED).
 */
class ThresholdMarker : public AlgorithmicMarkerBase
{
  protected:
    int K = -1;
    int packetCapacity = -1;
    bool useEcn = false;

  public:
    ThresholdMarker() {}
  protected:
    virtual ~ThresholdMarker();
    virtual void initialize();
    virtual IPEcnCode getEcn(const cPacket *packet);
    virtual void setEcn(cPacket *packet, IPEcnCode);
    virtual bool shouldDrop(cPacket *packet);
    virtual void markPacket(cPacket *packet);
};

#endif
