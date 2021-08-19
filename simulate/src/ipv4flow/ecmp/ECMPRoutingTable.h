#pragma once

#include "IFlowRoutingTable.h"
#include <cassert>

class INET_API ECMPRoutingTable : public IFlowRoutingTable {
  protected:
    virtual void initialize(int stage);
    int seed;

  public:
    ECMPRoutingTable() : IFlowRoutingTable(){}

    // routing cache: maps flow features to the route
    typedef std::map<std::string, IPv4Route *> RoutingCache;
    mutable RoutingCache routingCache;

    virtual void invalidateRoutingCache();

    virtual IPv4Route* findBestMatchingRoute(const IPv4Address& dest,
                                             const std::string& flowBin) const;
    virtual IPv4Route* findBestMatchingRoute(const IPv4Address& dest) const;
    virtual IPv4Route* findBestMatchingRoute(const IPv4Address& src,
                                             const IPv4Address& dest) const;
    virtual IPv4Route* findBestMatchingRoute(const IPv4Address& src,
                                             const IPv4Address& dest,
                                             const uint64_t msgId) const;
    virtual IPv4Route* findBestMatchingRoute(const IPv4Address& src,
                                             unsigned short srcPort,
                                             const IPv4Address& dest,
                                             unsigned short destPort) const;
};
