#ifndef __INET_MIMICDCN_H
#define __INET_MIMICDCN_H

//#define ENABLE_CUDA_LSTM
//#define ENABLE_PYTHON_LSTM

//#define DEBUG

#include "csimplemodule.h"
#include "simtime.h"
#include "transport/tcp_common/TCPSegment.h"
#include "transport/udp/UDPPacket.h"
#include "transport/HomaPkt.h"
#include "networklayer/ipv4/IPv4Datagram.h"
#include "networklayer/arp/ARPPacket_m.h"
#include "linklayer/ethernet/EtherFrame.h"
#include "PrescheduledMsg_m.h"

#include <iostream>
#include <fstream>
#include <functional>
#include <deque>
#include <memory>
#include <string>
#include <climits>

#ifdef ENABLE_CUDA_LSTM
    #include <cuda_runtime_api.h>
    #include "lstm_fwd_tcp.h"
    #include "lstm_fwd_dctcp.h"
    #include "lstm_fwd_homa.h"
#elif defined(ENABLE_PYTHON_LSTM)
    #include <Python.h>
#else
    #error You should specify at least one LSTM type
#endif

#define NO_CONGES 0
#define INCR_CONGES 1
#define MAX_CONGES 2
#define DECR_CONGES 3
#define CONGES_LEVELS 4

class PacketWrapper {
public:
    virtual bool getEcn() const = 0;
    virtual void setEcn() = 0;
    virtual int getPrio() const = 0;
    virtual int getLength() const = 0;
};

class IPv4DatagramWrapper : public PacketWrapper {
public:
    IPv4DatagramWrapper(IPv4Datagram *dgram) { dgram_ = dgram; }
    bool getEcn() const { return dgram_->getExplicitCongestionNotification() == 3; }
    void setEcn() {
        if (dgram_->getExplicitCongestionNotification() != 0) {
            // 3 is IP_ECN_CE in EcnTag.h
            dgram_->setExplicitCongestionNotification(3);
        }
    }
    int getPrio() const {
        cPacket* pkt = HomaPkt::searchEncapHomaPkt(dgram_);
        if (pkt) {
            return check_and_cast<HomaPkt*>(pkt)->getPriority();
        }
        throw std::runtime_error("Could not find encapsulated Homa packet!");
    }
    int getLength() const {
        dgram_->getByteLength();
    }
private:
    IPv4Datagram* dgram_;
};

class PreschedWrapper : public PacketWrapper {
public:
    PreschedWrapper(PrescheduledMsg *pm) { pm_ = pm; }
    bool getEcn() const { return pm_->getEcn(); }
    void setEcn() { /* do nothing */ }
    int getPrio() const { return pm_->getPriority(); }
    int getLength() const { return pm_->getLength(); }
private:
    PrescheduledMsg* pm_;
};

struct MLMetadata {
    MLMetadata(const char* library, const char* name, int servers_per_tor,
               int num_aggs, int num_agg_intfs, int num_tors, int num_features);
    ~MLMetadata();

    void updateCongesState(double latency);
    virtual void setLastFeatures(double current_time, PacketWrapper* pw) = 0;
    
    double lastpacket_;
    double ewma_;

    // Should match bin_data_by_time.py
    // TODO: hyperparameterize these
    const SimTime BIN_WINDOW = 0.0006;
    const double LATENCY_MEDIAN = 0.00103;
    const double LATENCY_VARIANCE = 0.000200;
    const double LATENCY_DROP_THRESHOLD = 0.0005;

    int conges_state_;
    SimTime cur_bin_start_time_;
    double bin_latency_sum_;
    int bin_num_packets_;
    int bin_num_drops_;

    const int num_features_;

#ifdef ENABLE_CUDA_LSTM
    int FT_INDEX_CONGES;
    int FT_INDEX_SERVER;
    int FT_INDEX_AGG;
    int FT_INDEX_AGGINTF;
    int FT_INDEX_TORS;
    int FT_INDEX_LAST;
    int FT_INDEX_END;

    double prev_drop_;      // last prediction, drop
    double prev_latency_;   // last prediction, latency

    double* input_;
#endif

#ifdef ENABLE_PYTHON_LSTM
    PyObject *p_module_;
    PyObject *p_model_;
    PyObject *p_func_;

    double* input_;
#endif
};

struct MLMetadataTCP : MLMetadata {
    MLMetadataTCP(const char* library, const char* name, int servers_per_tor,
                  int num_aggs, int num_agg_intfs, int num_tors);

    void setLastFeatures(double current_time, PacketWrapper* pw);

#ifdef ENABLE_CUDA_LSTM
    std::unique_ptr<MimicNetLstmTcp> model_;
#endif
};

struct MLMetadataDCTCP : MLMetadata {
    MLMetadataDCTCP(const char* library, const char* name, int servers_per_tor,
                    int num_aggs, int num_agg_intfs, int num_tors);

    void setLastFeatures(double current_time, PacketWrapper* pw);

#ifdef ENABLE_CUDA_LSTM
    std::unique_ptr<MimicNetLstmDctcp> model_;
    double prev_ECN_;       // last prediction, ECN
#endif
};

struct MLMetadataHoma : MLMetadata {
    MLMetadataHoma(const char* library, const char* name, int servers_per_tor,
                   int num_aggs, int num_agg_intfs, int num_tors);

    void setLastFeatures(double current_time, PacketWrapper* pw);

#ifdef ENABLE_CUDA_LSTM
    std::unique_ptr<MimicNetLstmHoma> model_;
#endif
};

class MimicDCN : public cSimpleModule {
  public:
    MimicDCN() {}

  protected:
    virtual void initialize();
    virtual void handleMessage(cMessage *msg);
    virtual void finish();

  private:
    double predict_packet_helper(IPv4Datagram* dgram, int aggregation,
                                 int interface, MLMetadata* meta,
                                 bool isIncoming);
#if defined(ENABLE_CUDA_LSTM) || defined(ENABLE_PYTHON_LSTM)
    double predict(PacketWrapper* pkt, int destServ, int destToR, int srcServ,
                   int srcToR, int aggregation, int interface, MLMetadata* meta,
                   bool isIncoming);
#endif
    void parse_ecmp_seeds();

    void handleARPReq(cMessage *msg, ARPPacket* arp_packet, EtherFrame* frame);
    void handleEgress(cMessage *msg, IPv4Datagram* dgram, EtherFrame* frame);
    void handleIngress(cMessage *msg, IPv4Datagram* dgram, const int agg_gate);

    void routeMsg(cMessage *msg);

    int ecmp(const std::string& flowBin, int size, int seed);

    void loadAndScheduleInterMimicTraffic(std::string file_name, double shape,
                                          double loc, double scale,
                                          bool isIncoming); 

    template <typename... FlowT>
    int ecmp_helper(int size, int seed, FlowT... flow);

    std::string convertToFlowBin(const IPv4Address& srcIP, unsigned short srcPort, const IPv4Address& destIP, unsigned short destPort);
    std::string convertToFlowBin(const IPv4Address& srcIP, const IPv4Address& destIP);

    std::unique_ptr<MLMetadata> ing_;
    std::unique_ptr<MLMetadata> egr_;

    // Values taken from ini parameters
    enum Variant { TCP, DCTCP, Homa };
    Variant variant_;
    std::deque<int> tor_seeds_;
    std::deque<int> agg_seeds_;
    int servers_per_tor_;
    int num_aggs_;
    int num_agg_intfs_;
    int num_tors_;
    int numUplinks;
   
    // Value calculated from ini parameters
    double max_latency_;
    double min_latency_;
    short num_intgates_;
};

#endif

