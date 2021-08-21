//
// Copyright (C) 2020 OpenSim Ltd., 2021 Qizhen Zhang
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
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//

#ifndef __INET_ECNTAG_H
#define __INET_ECNTAG_H

enum IPEcnCode {
  IP_ECN_NOT_ECT = 0,
  IP_ECN_ECT_1 = 1,
  IP_ECN_ECT_0 = 2,
  IP_ECN_CE = 3
};

#endif

