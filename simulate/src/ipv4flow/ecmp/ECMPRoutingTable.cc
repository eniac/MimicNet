#include "ECMPRoutingTable.h"

#include "murmur.h"

#include <algorithm>

Define_Module(ECMPRoutingTable);

class BestRoutesSortFunctor {
  public:
    bool operator()(const IPv4Route* a, const IPv4Route* b) {
        return a->getGateway() < b->getGateway();
    }
};

class BestRoutesUniqueFunctor {
  public:
    bool operator()(const IPv4Route* a, const IPv4Route* b) {
        return a->getGateway() == b->getGateway();
    }
};

void ECMPRoutingTable::initialize(int stage) {
    IFlowRoutingTable::initialize(stage);
    seed = par("seed");
}

void ECMPRoutingTable::invalidateRoutingCache() {
    routingCache.clear();
}

IPv4Route* ECMPRoutingTable::findBestMatchingRoute(const IPv4Address& dest, const std::string& flowBin) const {
    RoutingCache::iterator it = routingCache.find(flowBin);
    if (it != routingCache.end())
    {
        if (it->second==NULL || it->second->isValid())
            return it->second;
    }

    // find best match (one with longest prefix)
    // default route has zero prefix length, so (if exists) it'll be selected as last resort
    std::vector<IPv4Route*> bestRoutes;
    for (RouteVector::const_iterator i=routes.begin(); i!=routes.end(); ++i)
    {
        IPv4Route *e = *i;
        if (e->isValid()) {
            if (bestRoutes.size() != 0 && e->getDestination() != bestRoutes.back()->getDestination()) {
                break;
            }
            if (IPv4Address::maskedAddrAreEqual(dest, e->getDestination(), e->getNetmask())) {    // match
                bestRoutes.push_back(const_cast<IPv4Route *>(e));
            }
        }
    }

    if (bestRoutes.size() == 0) {
        return NULL;
    } else {
        std::sort(bestRoutes.begin(), bestRoutes.end(), BestRoutesSortFunctor());
        std::vector<IPv4Route*>::iterator newBestRoutesEnd = std::unique(bestRoutes.begin(), bestRoutes.end(), BestRoutesUniqueFunctor());
        bestRoutes.erase(newBestRoutesEnd, bestRoutes.end());
        IPv4Route* bestRoute = bestRoutes[positiveMod(murmur3_32((const unsigned char*)flowBin.data(), flowBin.size(), this->seed), bestRoutes.size())];
        routingCache[flowBin] = bestRoute;
        return bestRoute;
    }
}

IPv4Route* ECMPRoutingTable::findBestMatchingRoute(
            const IPv4Address& dest) const {
    // note: str().c_str() too slow here
    Enter_Method("findBestMatchingRoute(%u.%u.%u.%u)", dest.getDByte(0),
                 dest.getDByte(1), dest.getDByte(2), dest.getDByte(3));

    std::string destBin(4, 0);
    *((int*)destBin.data()) = dest.getInt();

    return findBestMatchingRoute(dest, destBin);
}

IPv4Route* ECMPRoutingTable::findBestMatchingRoute(
            const IPv4Address& src, const IPv4Address& dest) const {
    // note: str().c_str() too slow here
    Enter_Method("findBestMatchingRoute(%u.%u.%u.%u, %u.%u.%u.%u)",
                 src.getDByte(0), src.getDByte(1), src.getDByte(2),
                 src.getDByte(3), dest.getDByte(0), dest.getDByte(1),
                 dest.getDByte(2), dest.getDByte(3));

    std::string srcDestBin(8, 0);
    *(int*)srcDestBin.data() = src.getInt();
    *(int*)(srcDestBin.data() + 4) = dest.getInt();

    return findBestMatchingRoute(dest, srcDestBin);
}

IPv4Route* ECMPRoutingTable::findBestMatchingRoute(
            const IPv4Address& src, const IPv4Address& dest,
            const uint64_t msgId) const {
    // note: str().c_str() too slow here
    Enter_Method("findBestMatchingRoute(%u.%u.%u.%u, %u.%u.%u.%u, %llu)",
                 src.getDByte(0), src.getDByte(1), src.getDByte(2),
                 src.getDByte(3), dest.getDByte(0), dest.getDByte(1),
                 dest.getDByte(2), dest.getDByte(3), msgId);

    std::string srcDestBin(16, 0);
    *(int*)srcDestBin.data() = src.getInt();
    *(int*)(srcDestBin.data() + 4) = dest.getInt();
    *(uint64_t*)(srcDestBin.data() + 8) = msgId;

    return findBestMatchingRoute(dest, srcDestBin);
}

IPv4Route* ECMPRoutingTable::findBestMatchingRoute(
            const IPv4Address& src, unsigned short srcPort,
            const IPv4Address& dest, unsigned short destPort) const {
    // note: str().c_str() too slow here
    Enter_Method("findBestMatchingRoute(%u.%u.%u.%u:%hu, %u.%u.%u.%u:%hu)",
                 src.getDByte(0), src.getDByte(1), src.getDByte(2),
                 src.getDByte(3), srcPort, dest.getDByte(0), dest.getDByte(1),
                 dest.getDByte(2), dest.getDByte(3), destPort);

    std::string srcDestBin(12, 0);
    *(int*)srcDestBin.data() = src.getInt();
    *(unsigned short*)(srcDestBin.data() + 4) = srcPort;
    *(int*)(srcDestBin.data() + 6) = dest.getInt();
    *(unsigned short*)(srcDestBin.data() + 10) = destPort;

    return findBestMatchingRoute(dest, srcDestBin);
}

