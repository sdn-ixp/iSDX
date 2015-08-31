#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json

class FlowModMsgBuilder(object):
    def __init__(self, participant, key):
        self.participant = participant
        self.key = key
        self.flow_mods = []

    def add_flow_mod(self, mod_type, rule_type, priority, match, action, cookie = None):        
        if cookie is None:
            cookie = (len(self.flow_mods)+1, 65535)

        fm = { 
               "cookie": cookie,
               "mod_type": mod_type,
               "rule_type": rule_type,
               "priority": priority,
               "match": match,
               "action": action
             }

        self.flow_mods.append(fm)

        return cookie

    def delete_flow_mod(self, mod_type, rule_type, cookie, cookie_mask):
        fm = {
            "cookie": (cookie, cookie_mask),
            "mod_type": mod_type,
            "rule_type": rule_type,
        }

        self.flow_mods.append(fm)

    def get_msg(self):
        msg = {
                "auth_info": {
                               "participant" : self.participant,
                               "key" : self.key
                             },
                "flow_mods": self.flow_mods
              }

        return msg

#  request body format:
#    {"auth_info": {
#            "participant": 1,
#            "key": "xyz"
#            }
#     "flow_mods": [
#            { "cookie": (1, 2**16-1),
#              "mod_type": "insert/remove",
#              "rule_type": "inbound/outbound/main",
#              "priority": 1,
#              "match" : {
#                         "eth_type" : 0x0806,
#                         "arp_tpa" : ("172.1.0.0", "255.255.255.0"),
#                         "in_port" : 5,
#                         "eth_dst" : "ff:ff:ff:ff:ff:ff",
#                         "eth_src" : "80:23:ff:98:10:01",
#                         "ipv4_src" : "192.168.1.1",
#                         "ipv4_dst" : "192.168.1.2", 
#                         "tcp_src" : 80, 
#                         "tcp_dst" : 179,
#                         "udp_src" : 23,
#                         "udp_dst" : 22, 
#                        },
#              "action" : {
#                         "fwd": ["inbound"/"outbound"/"main-in"/main-out"],
#                         "set_eth_src": "80:23:ff:98:10:01",
#                         "set_eth_dst": ("00:00:00:00:00:01","00:00:00:00:03:ff")
#                         }
#            },
#            { "cookie": (2, 2**16-1),
#              "mod_type": "insert/remove",
#              "rule_type": "inbound/outbound/main",
#              "match" : {"tcp_dst" : 80},
#              "action" : {"fwd": [3]}
#            }
#            ...]
#    }

