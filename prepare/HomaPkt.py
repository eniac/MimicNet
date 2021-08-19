#!/usr/bin/env python3

import socket
import struct


"""
Convert an IP string to long

Taken from https://stackoverflow.com/questions/9590965/convert-an-ip-string-to-
                   a-number-and-vice-versa/22272197
"""
def ip2long(ip):
    packed_ip = socket.inet_aton(ip)
    return struct.unpack("!L", packed_ip)[0]

class HomaPkt():
    def __init__(self, toks):
        self.data = dict()

        self.data["time"] = float(toks[0][:-1])
        self.data["src"] = toks[1]
        self.data["dst"] = toks[3][:-1]
        self.data["msg_id"] = toks[5].split('=')[1]
        self.data["type"] = toks[6].split('=')[1]

        seq_range = toks[7][1:-1]
        if ':' in seq_range:
            self.data["seq_begin"], self.data["seq_end"] = seq_range.split(':')
        else:
            self.data["seq_begin"] = seq_range
            self.data["seq_end"] = None

        self.data["priority"] = toks[8].split('=')[1]
        self.data["length"] = toks[9].split('=')[1]

        if 'agg' in toks:
            agg_index = toks.index('agg')
            self.data["agg"] = toks[agg_index + 1]

        if 'tor' in toks:
            tor_index = toks.index('tor')
            self.data["tor"] = toks[tor_index + 1]
        
        if 'svr' in toks:
            svr_index = toks.index('svr')
            self.data["svr"] = toks[svr_index + 1]

        if 'interface' in toks:
            interface_index = toks.index('interface')
            self.data["interface"] = toks[interface_index + 1]

    def get(self, key):
        return self.data[key]

    def set(self, key, value):
        self.data[key] = value

    def matches(self, other_packet):
        if self.data["src"] != other_packet.data["src"]:
            return False
        if self.data["dst"] != other_packet.data["dst"]:
            return False
        if self.data["type"] != other_packet.data["type"]:
            return False
        if self.data["seq_begin"] != other_packet.data["seq_begin"]:
            return False
        if self.data["seq_end"] != other_packet.data["seq_end"]:
            return False
        if self.data["priority"] != other_packet.data["priority"]:
            return False
        if self.data["length"] != other_packet.data["length"]:
            return False
        return True

    def __str__(self):
        return str(self.data["time"]) + ": " + \
                self.data["src"] + "|" + self.data["dst"] + "|" + \
                self.data["msg_id"] + "|" + self.data["type"] + "|" + \
                str(self.data["seq_begin"]) + "|" + \
                str(self.data["seq_end"])
