#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

class FlowModMsg(object):
    def __init__(self, participant, key):
        self.participant = participant
        self.key = key

        self.flow_mods = []

    def add_flow_mod(self, mod_type, rule_type, priority, match, action):
        id = len(self.flow_mods) + 1
        
        fm = { 
               "id": id,
               "mod_type": mod_type,
               "rule_type": rule_type,
               "priority": priority,
               "match": match,
               "action": action
             }

        self.flow_mods.append(fm)

        return id

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
#            { "id": 1, 
#              "mod_type": "add/remove",
#              "rule_type": "inbound/outbound/main",
#              "priority": 1,
#              "match" : {
#                         "ipv4_src" : "192.168.1.1", 
#                         "ipv4_dst" : "192.168.1.2", 
#                         "tcp_src" : 80, 
#                         "tcp_dst" : 179,
#                         "udp_src" : 23,
#                         "udp_dst" : 22, 
#                        },
#              "action" : {"fwd": 1}
#            },
#            { "id": 2,
#              "mod_type": "add/remove",
#              "rule_type": "inbound/outbound/main",
#              "match" : {"tcp_dst" : 80},
#              "action" : {"fwd": 3}
#            }
#            ...]
#    }

