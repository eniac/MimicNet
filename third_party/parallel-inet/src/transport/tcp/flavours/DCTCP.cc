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

#include "DCTCP.h"

#include <algorithm> // min,max

#include "TCP.h"

Register_Class(DCTCP);

DCTCP::DCTCP() : TCPReno(),
    state((DCTCPStateVariables *&)TCPAlgorithm::state)
{
    loadVector = calcLoadVector = markingProbVector = NULL;
}

DCTCP::~DCTCP()
{
    // delete statistics objects
    delete loadVector;
    delete calcLoadVector;
    delete markingProbVector;
}

void DCTCP::initialize()
{
    TCPReno::initialize();
    state->dctcp_gamma = conn->getTcpMain()->par("dctcpGamma");

    if (conn->getTcpMain()->recordStatistics) {
        loadVector = new cOutVector("load");
        calcLoadVector = new cOutVector("calcLoad");
        markingProbVector = new cOutVector("markingProb");
    }
}

void DCTCP::receivedDataAck(uint32 firstSeqAcked)
{
    TCPTahoeRenoFamily::receivedDataAck(firstSeqAcked);

    if (state->dupacks >= state->dupthresh) {
        //
        // Perform Fast Recovery: set cwnd to ssthresh (deflating the window).
        //
        tcpEV << "Fast Recovery: setting cwnd to ssthresh=" << state->ssthresh << "\n";
        state->snd_cwnd = state->ssthresh;
        
        if (cwndVector)
            cwndVector->record(state->snd_cwnd);
    }
    else {
        bool performSsCa = true; // Stands for: "perform slow start and congestion avoidance"
        if (state && state->ect) {
            // RFC 8257 3.3.1
            uint32 bytes_acked = state->snd_una - firstSeqAcked;

            // bool cut = false; TODO unused?

            // RFC 8257 3.3.2
            state->dctcp_bytesAcked += bytes_acked;

            // RFC 8257 3.3.3
            if (state->gotEce) {
                state->dctcp_bytesMarked += bytes_acked;
                if (markingProbVector) {
                    markingProbVector->record(1);
                }
            }
            else {
                if (markingProbVector) {
                    markingProbVector->record(0);
                }
            }

            // RFC 8257 3.3.4
            if (state->snd_una > state->dctcp_windEnd) {

                if (state->dctcp_bytesMarked) {
                    // cut = true;  TODO unused?
                }

                // RFC 8257 3.3.5
                double ratio;

                ratio = ((double)state->dctcp_bytesMarked / state->dctcp_bytesAcked);
                if (loadVector) {
                    loadVector->record(ratio);
                }

                // RFC 8257 3.3.6
                // DCTCP.Alpha = DCTCP.Alpha * (1 - g) + g * M
                state->dctcp_alpha = state->dctcp_alpha * (1 - state->dctcp_gamma) + state->dctcp_gamma * ratio;
                if (calcLoadVector) {
                    calcLoadVector->record(state->dctcp_alpha);
                }

                // RFC 8257 3.3.7
                state->dctcp_windEnd = state->snd_nxt;

                // RFC 8257 3.3.8
                state->dctcp_bytesAcked = state->dctcp_bytesMarked = 0;
                state->sndCwr = false;
            }

            // Applying DCTCP style cwnd update only if there was congestion and the window has not yet been reduced during current interval
            if ((state->dctcp_bytesMarked && !state->sndCwr)) {

                performSsCa = false;
                state->sndCwr = true;

                // RFC 8257 3.3.9
                state->snd_cwnd = state->snd_cwnd * (1 - state->dctcp_alpha / 2);

                if (cwndVector) {
                    cwndVector->record(state->snd_cwnd);
                }

                uint32_t flight_size = std::min(state->snd_cwnd, state->snd_wnd); // FIXME - Does this formula computes the amount of outstanding data?
                state->ssthresh = std::max(3 * flight_size / 4, 2 * state->snd_mss);

                if (ssthreshVector) {
                    ssthreshVector->record(state->ssthresh);
                }
            }
        }

        if (performSsCa) {
            // If ECN is not enabled or if ECN is enabled and received multiple ECE-Acks in
            // less than RTT, then perform slow start and congestion avoidance.

            if (state->snd_cwnd < state->ssthresh) {
                tcpEV << "cwnd <= ssthresh: Slow Start: increasing cwnd by one SMSS bytes to ";

                // perform Slow Start. RFC 2581: "During slow start, a TCP increments cwnd
                // by at most SMSS bytes for each ACK received that acknowledges new data."
                state->snd_cwnd += state->snd_mss;
                
                if (cwndVector) {
                    cwndVector->record(state->snd_cwnd);
                }
                if (ssthreshVector) {
                    ssthreshVector->record(state->ssthresh);
                }

                tcpEV << "cwnd=" << state->snd_cwnd << "\n";
            }
            else {
                // perform Congestion Avoidance (RFC 2581)
                uint32_t incr = state->snd_mss * state->snd_mss / state->snd_cwnd;

                if (incr == 0)
                    incr = 1;

                state->snd_cwnd += incr;

                if (cwndVector) {
                    cwndVector->record(state->snd_cwnd);
                }
                if (ssthreshVector) {
                    ssthreshVector->record(state->ssthresh);
                }

                //
                // Note: some implementations use extra additive constant mss / 8 here
                // which is known to be incorrect (RFC 2581 p5)
                //
                // Note 2: RFC 3465 (experimental) "Appropriate Byte Counting" (ABC)
                // would require maintaining a bytes_acked variable here which we don't do
                //

                tcpEV << "cwnd > ssthresh: Congestion Avoidance: increasing cwnd linearly, to " << state->snd_cwnd << "\n";
            }
        }
    }

    if (state->sack_enabled && state->lossRecovery) {
        // RFC 3517, page 7: "Once a TCP is in the loss recovery phase the following procedure MUST
        // be used for each arriving ACK:
        //
        // (A) An incoming cumulative ACK for a sequence number greater than
        // RecoveryPoint signals the end of loss recovery and the loss
        // recovery phase MUST be terminated.  Any information contained in
        // the scoreboard for sequence numbers greater than the new value of
        // HighACK SHOULD NOT be cleared when leaving the loss recovery
        // phase."
        if (seqGE(state->snd_una, state->recoveryPoint)) {
            tcpEV << "Loss Recovery terminated.\n";
            state->lossRecovery = false;
        }
        // RFC 3517, page 7: "(B) Upon receipt of an ACK that does not cover RecoveryPoint the
        // following actions MUST be taken:
        //
        // (B.1) Use Update () to record the new SACK information conveyed
        // by the incoming ACK.
        //
        // (B.2) Use SetPipe () to re-calculate the number of octets still
        // in the network."
        else {
            // update of scoreboard (B.1) has already be done in readHeaderOptions()
            conn->setPipe();

            // RFC 3517, page 7: "(C) If cwnd - pipe >= 1 SMSS the sender SHOULD transmit one or more
            // segments as follows:"
            if (((int)state->snd_cwnd - (int)state->pipe) >= (int)state->snd_mss) // Note: Typecast needed to avoid prohibited transmissions
                conn->sendDataDuringLossRecoveryPhase(state->snd_cwnd);
        }
    }

    // RFC 3517, pages 7 and 8: "5.1 Retransmission Timeouts
    // (...)
    // If there are segments missing from the receiver's buffer following
    // processing of the retransmitted segment, the corresponding ACK will
    // contain SACK information.  In this case, a TCP sender SHOULD use this
    // SACK information when determining what data should be sent in each
    // segment of the slow start.  The exact algorithm for this selection is
    // not specified in this document (specifically NextSeg () is
    // inappropriate during slow start after an RTO).  A relatively
    // straightforward approach to "filling in" the sequence space reported
    // as missing should be a reasonable approach."
    sendData(false);
}

bool DCTCP::shouldMarkAck()
{
    // RFC 8257 3.2 page 6
    // When sending an ACK, the ECE flag MUST be set if and only if DCTCP.CE is true.
    return state->dctcp_ce;
}

void DCTCP::processEcnInEstablished()
{
    if (state && state->ect) {
        // RFC 8257 3.2.1
        if (state->gotCeIndication && !state->dctcp_ce) {
            state->dctcp_ce = true;
            state->ack_now = true;
        }

        // RFC 8257 3.2.2
        if (!state->gotCeIndication && state->dctcp_ce) {
            state->dctcp_ce = false;
            state->ack_now = true;
        }
    }
}
