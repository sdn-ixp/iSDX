#!/usr/bin/env python
#  Author:
#  Arpit Gupta (arpitg@cs.princeton.edu)

import json
import os
from random import shuffle, randint
import sys

fname = "rrc03.bview.20150820.0000.temp.txt"

"""
TIME: 08/20/15 00:00:00
TYPE: TABLE_DUMP_V2/IPV4_UNICAST
PREFIX: 1.0.0.0/24
SEQUENCE: 0
FROM: 80.249.211.161 AS8283
ORIGINATED: 08/13/15 13:16:25
ORIGIN: IGP
ASPATH: 8283 5580 15169
NEXT_HOP: 80.249.211.161
MULTI_EXIT_DISC: 0
COMMUNITY: 5580:12533 8283:13
"""

def generatePoliciesParticipant(part, asn_2_ip, asn_2_ports, count, limit_out, limit_in):
    # randomly select fwding participants
    peers = filter(lambda x: x!=part, asn_2_ip.keys())
    shuffle(peers)
    fwding_peers = set(peers[:count])

    # Generate Outbound policies
    cookie_id = 1
    policy = {}
    policy["outbound"] = []
    for peer in fwding_peers:

        peer_count = randint(1, limit_out)
        for ind in range(1, peer_count+1):
            tmp_policy = {}

            # Assign Cookie ID
            tmp_policy["cookie"] = cookie_id
            cookie_id += 1

            # Match
            match_hash = getMatchHash(part, peer, ind)
            tmp_policy["match"] = {}
            tmp_policy["match"]["tcp_dst"] = match_hash
            tmp_policy["match"]["in_port"] = asn_2_ports[part][0]

            # Action: fwd to peer's first port (visible to part)
            tmp_policy["action"] = {"fwd":asn_2_ports[peer][0]}

            # Add this to participants' outbound policies
            policy["outbound"].append(tmp_policy)

    # Dump the policies to appropriate directory
    policy_filename = "participant_"+part+".py"
    policy_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "policies"))
    policy_file = os.path.join(policy_path, policy_filename)
    with open(policy_file,'w') as f:
        json.dump(policy, f)


def getParticipants(limit_in):
    asn_2_ip = {}
    asn_2_ports = {}
    with open(fname, 'r') as f:
        print "Loaded the RIB file"
        for line in f.readlines():
            if "FROM" in line:
                tmp = line.split("FROM: ")[1].split(" ")[:-1]
                if tmp[1] not in asn_2_ip:
                    nhip_2_asn[tmp[1]] = tmp[0]
    port_id = 5
    for part in asn_2_ip:
        total_ports = randint(1, limit_in)
        asn_2_ports[part] = []
        for ind in range(1, total_ports+1):
            port_id += ind + port_id
            asn_2_ports[part].append(port_id)

    return asn_2_ip, asn_2_ports
    

''' main '''
if __name__ == '__main__':
    asn_2_ip, asn_2_ports = getParticipants()
    count = int(nparts[0]*0.5)
    limit_out = 4
    limit_in = 2
    for part in asn_2_ip:
        generatePoliciesParticipant(part, asn_2_ip, asn_2_ports, count, limit_out, limit_in)
