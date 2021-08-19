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

class Packet():
    def __init__(self, toks):
        self.data = dict()

        self.data["time"] = float(toks[0][:-1])
        self.data["src"] = toks[1]
        self.data["dst"] = toks[3][:-1]
        self.data["flags"] = toks[4]

        seq_range = toks[5]
        if ':' in seq_range:
            self.data["seq_begin"], tmp = seq_range.split(':')
            self.data["seq_end"] = tmp.split('(')[0]
        else:
            self.data["seq_begin"] = None
            self.data["seq_end"] = None

        if 'ack' in toks:
            ack_index = toks.index('ack')
            self.data["ack_num"] = toks[ack_index + 1]
        else:
            self.data["ack_num"] = None

        if 'win' in toks:
            win_index = toks.index('win')
            self.data["win_num"] = toks[win_index + 1]
        else:
            self.data["win_num"] = None

        if 'ecn' in toks:
            ecn_index = toks.index('ecn')
            if toks[ecn_index + 1] == "3":
                self.data["ecn"] = "1"
            else:
                self.data["ecn"] = "0"

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
        if self.data["seq_begin"] != other_packet.data["seq_begin"]:
            return False
        if self.data["flags"] != other_packet.data["flags"]:
            return False
        if self.data["seq_end"] != other_packet.data["seq_end"]:
            return False
        if self.data["ack_num"] != other_packet.data["ack_num"]:
            return False
        if self.data["win_num"] != other_packet.data["win_num"]:
            return False
        return True

    def __str__(self):
        return str(self.data["time"]) + ": " + \
                self.data["src"] + "|" + self.data["dst"] + "|" + \
                str(self.data["seq_begin"]) + "|" + \
                str(self.data["seq_end"]) + "|" + \
                str(self.data["ack_num"])
