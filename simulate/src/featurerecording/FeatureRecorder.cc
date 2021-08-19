//
// Copyright (C) 2005 Michael Tuexen
// Copyright (C) 2008 Irene Ruengeler
// Copyright (C) 2009 Thomas Dreibholz
// Copyright (C) 2009 Thomas Reschka
// Copyright (C) 2011 Zoltan Bojthe
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>.
//


#include "FeatureRecorder.h"

#ifdef WITH_IPv4
#include "IPv4Datagram.h"
#endif

#ifdef WITH_IPv6
#include "IPv6Datagram.h"
#endif


//----

Define_Module(FeatureRecorder);

FeatureRecorder::~FeatureRecorder()
{
}

FeatureRecorder::FeatureRecorder() : cSimpleModule()
{
}

void FeatureRecorder::initialize()
{
    const char* file = par("pdmpFile");

    packetDumpStream = new std::ofstream(file);
    packetDumper.setVerbose(par("verbose").boolValue());
    packetDumper.setOutStream(*packetDumpStream);
    signalList.clear();

    {
        cStringTokenizer signalTokenizer(par("sendingSignalNames"));

        while (signalTokenizer.hasMoreTokens())
            signalList[registerSignal(signalTokenizer.nextToken())] = true;
    }

    {
        cStringTokenizer signalTokenizer(par("receivingSignalNames"));

        while (signalTokenizer.hasMoreTokens())
            signalList[registerSignal(signalTokenizer.nextToken())] = false;
    }

    const char* moduleNames = par("moduleNamePatterns");
    cStringTokenizer moduleTokenizer(moduleNames);

    while (moduleTokenizer.hasMoreTokens())
    {
        bool found = false;
        std::string mname(moduleTokenizer.nextToken());
        bool isAllIndex = (mname.length() > 3) && mname.rfind("[*]") == mname.length() - 3;

        if (isAllIndex)
            mname.replace(mname.length() - 3, 3, "");

        for (cModule::SubmoduleIterator i(getParentModule()); !i.end(); i++)
        {
            cModule *submod = i();
            if (0 == strcmp(isAllIndex ? submod->getName() : submod->getFullName(), mname.c_str()))
            {
                found = true;

                for (SignalList::iterator s = signalList.begin(); s != signalList.end(); s++)
                {
                    if (!submod->isSubscribed(s->first, this))
                    {
                        submod->subscribe(s->first, this);
                        EV << "FeatureRecorder " << getFullPath() << " subscribed to "
                           << submod->getFullPath() << ":" << getSignalName(s->first) << endl;
                    }
                }
            }
        }

        if (!found)
        {
            EV << "The module " << mname << (isAllIndex ? "[*]" : "")
                    << " not found for FeatureRecorder " << getFullPath() << endl;
        }
    }
}

void FeatureRecorder::handleMessage(cMessage *msg)
{
    throw cRuntimeError("This module does not handle messages");
}

void FeatureRecorder::receiveSignal(cComponent *source, simsignal_t signalID, cObject *obj)
{
    Enter_Method_Silent();
    cPacket *packet = dynamic_cast<cPacket *>(obj);

    if (packet)
    {
        SignalList::const_iterator i = signalList.find(signalID);
        bool l2r = (i != signalList.end()) ? i->second : true;
        recordPacket(packet, l2r);
    }
}

void FeatureRecorder::recordPacket(cPacket *msg, bool l2r)
{
    packetDumper.dumpPacket(l2r, msg);
}

void FeatureRecorder::finish()
{
     packetDumper.dump("", "pcapRecorder finished");
     packetDumpStream->close();
     delete packetDumpStream;
}

