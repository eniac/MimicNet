#include <vector>
#include <unordered_map>
#include "common/Minimal.h"
#include <omnetpp.h>
#include "IPvXAddress.h"
#include "transport/HomaPkt.h"

class MockUdpSocket {
  PUBLIC:
    std::vector<cPacket*> sxPkts;

  PUBLIC:
    MockUdpSocket();
    ~MockUdpSocket();
    void setOutputGate(cGate* gate);
    void bind(uint32_t portNum);
    void sendTo(cPacket* pkt, IPvXAddress dest, uint32_t destPort);
    HomaPkt* getGrantPkt(IPvXAddress dest, uint64_t mesgId);
};
