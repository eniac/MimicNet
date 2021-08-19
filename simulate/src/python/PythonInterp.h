//
// Copyright (C) 2000 Institut fuer Telematik, Universitaet Karlsruhe
// Copyright (C) 2004-2011 Andras Varga
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


#ifndef __PYTHONINTERP_H
#define __PYTHONINTERP_H

#include "csimplemodule.h"

/**
 * Implements the UDP protocol: encapsulates/decapsulates user data into/from UDP.
 *
 * More info in the NED file.
 */
class PythonInterp : public cSimpleModule
{
  public:
    PythonInterp() {}
    virtual ~PythonInterp() {}

  protected:
    virtual void initialize();
    virtual void finish();
};

#endif

