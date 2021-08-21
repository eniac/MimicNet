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

#include "DCTCPFamily.h"

#include "TCP.h"

DCTCPFamilyStateVariables::DCTCPFamilyStateVariables()
{
    dctcp_ce = false;
    dctcp_alpha = 0;
    dctcp_windEnd = snd_una;
    dctcp_bytesAcked = 0;
    dctcp_bytesMarked = 0;
    dctcp_gamma = 0.0625; // 1/16 (backup 0.16) TODO make it NED parameter;
}

std::string DCTCPFamilyStateVariables::info() const
{
    std::stringstream out;
    out << TCPTahoeRenoFamilyStateVariables::info();
    out << " dctcp_alpha=" << dctcp_alpha;
    out << " dctcp_windEnd=" << dctcp_windEnd;
    out << " dctcp_bytesAcked=" << dctcp_bytesAcked;
    out << " dctcp_bytesMarked=" << dctcp_bytesMarked;
    out << " dctcp_gamma=" << dctcp_gamma;

    return out.str();
}

std::string DCTCPFamilyStateVariables::detailedInfo() const
{
    std::stringstream out;
    out << TCPTahoeRenoFamilyStateVariables::detailedInfo();
    out << " dctcp_alpha=" << dctcp_alpha;
    out << " dctcp_windEnd=" << dctcp_windEnd;
    out << " dctcp_bytesAcked=" << dctcp_bytesAcked;
    out << " dctcp_bytesMarked=" << dctcp_bytesMarked;
    out << " dctcp_gamma=" << dctcp_gamma;
    return out.str();
}

// ---

DCTCPFamily::DCTCPFamily() : TCPTahoeRenoFamily(),
    state((DCTCPFamilyStateVariables *&)TCPTahoeRenoFamily::state)
{
}
