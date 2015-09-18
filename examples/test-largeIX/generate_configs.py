#!/usr/bin/env python
#  Author:
#  Arpit Gupta (arpitg@cs.princeton.edu)

import json
import os
from random import shuffle, randint
import sys
import argparse
import glob

fname = "rib1.txt"
path = "ribs/*"
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

def getMatchHash(part, peer, count):
    if "AS" in part: part = int(part.split("AS")[1])
    if "AS" in peer: peer = int(peer.split("AS")[1])

    return int(1*part+1*peer+count)


def getParticipants():
    asn_2_ip = {}
    files=glob.glob(path)
    for file in files:
        print "File::", file
        with open(file, 'r') as f:
            print "Loaded the RIB file"
            for line in f.readlines():
                if "FROM" in line:
                    line
                    tmp = line.split("FROM: ")[1].split("\n")[0].split(" ")
                    #print tmp
                    if tmp[1] not in asn_2_ip:
                        asn_2_ip[tmp[1]] = {}
                    asn_2_ip[tmp[1]][tmp[0]] = 0

    #print asn_2_ip
    print "Assigning Ports"
    port_id = 10
    for part in asn_2_ip:
        for ip in asn_2_ip[part]:
            asn_2_ip[part][ip] = port_id
            port_id += 1

    out_fname = "asn_2_ip.json"
    with open(out_fname,'w') as f:
        json.dump(asn_2_ip, f)

    return asn_2_ip


def generatePoliciesParticipant(part, asn_2_ip, asn_2_id, count, limit_out):
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
            tmp_policy["match"]["in_port"] = asn_2_ip[part].values()[0]

            # Action: fwd to peer's first port (visible to part)
            tmp_policy["action"] = {"fwd":asn_2_id[peer]}

            # Add this to participants' outbound policies
            policy["outbound"].append(tmp_policy)


    policy["inbound"] = []
    inbound_count = randint(1, limit_out)
    for ind in range(1, peer_count+1):
        tmp_policy = {}
        # Assign Cookie ID
        tmp_policy["cookie"] = cookie_id
        cookie_id += 1

        # Match
        match_hash = getMatchHash(part, 'AS0', ind)
        tmp_policy["match"] = {}
        tmp_policy["match"]["tcp_dst"] = match_hash


        # Action: fwd to peer's first port (visible to part)
        tmp_policy["action"] = {"fwd":asn_2_ip[part].values()[0]}

        # Add this to participants' outbound policies
        policy["inbound"].append(tmp_policy)


    # Dump the policies to appropriate directory
    policy_filename = "participant_"+part+".py"
    policy_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "policies"))
    policy_file = os.path.join(policy_path, policy_filename)
    with open(policy_file,'w') as f:
        json.dump(policy, f)


def generate_global_config(asn_2_ip):
    # load the base config
    config_filename = "sdx_global.cfg"
    config_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config"))
    config_file = os.path.join(config_path, config_filename)
    #print "config file: ", config_file
    asn_2_id = {}
    unique_id = 1

    server_filename = "server_settings.cfg"
    server_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
    server_file = os.path.join(server_path, server_filename)
    server_settings = ""

    with open(server_file, 'r') as f:
        server_settings = json.load(f)
	print server_settings

    for part in asn_2_ip:
        if part not in asn_2_id:
            asn_2_id[part] = unique_id
            unique_id += 1

    with open(config_file, 'r') as f:
        config = json.load(f)
        config["Participants"] = {}
        eh_port = 7777

	config["RefMon Server"]["IP"] = server_settings["server1"]["IP"]
	config["Route Server"]["AH_SOCKET"] = [server_settings["server2"]["IP"], 6666]

        for part in asn_2_ip:
            part_id = asn_2_id[part]

            config["Participants"][part_id] = {}
            config["Participants"][part_id]["Ports"] = []
            for nhip in asn_2_ip[part]:
                tmp = {}
                tmp["Id"] = asn_2_ip[part][nhip]
                tmp["MAC"] = ""
                tmp["IP"] = str(nhip)
                config["Participants"][part_id]["Ports"].append(tmp)
            config["Participants"][part_id]["ASN"] = part
            config["Participants"][part_id]["Peers"] = [asn_2_id[x] for x in filter(lambda x: x!=part, asn_2_ip.keys())]
            config["Participants"][part_id]["Inbound Rules"] = "true"
            config["Participants"][part_id]["Outbound Rules"] = "true"
	    host = ""
	    if int(server_settings["server1"]["FROM"]) <= part_id and part_id <= int(server_settings["server1"]["TO"]): config["Participants"][part_id]["EH_SOCKET"] = [server_settings["server1"]["IP"], eh_port]
	    elif int(server_settings["server2"]["FROM"]) <= part_id and part_id <= int(server_settings["server2"]["TO"]): config["Participants"][part_id]["EH_SOCKET"] = [server_settings["server2"]["IP"], eh_port]
	    elif int(server_settings["server3"]["FROM"]) <= part_id and part_id <= int(server_settings["server3"]["TO"]): config["Participants"][part_id]["EH_SOCKET"] = [server_settings["server3"]["IP"], eh_port]
            #config["Participants"][part_id]["EH_SOCKET"] = ["localhost", eh_port]
            config["Participants"][part_id]["Flanc Key"] = "Part"+str(part_id)+"Key"
            eh_port += 1

        config["RefMon Settings"]["fabric connections"]["main"] = {}
        config["RefMon Settings"]["fabric connections"]["main"]["inbound"] = 1
        config["RefMon Settings"]["fabric connections"]["main"]["outbound"] = 2
        config["RefMon Settings"]["fabric connections"]["main"]["route server"] = 3
        config["RefMon Settings"]["fabric connections"]["main"]["arp proxy"] = 4
        config["RefMon Settings"]["fabric connections"]["main"]["refmon"] = 5


        for part in asn_2_ip:
            part_id = asn_2_id[part]
            config["RefMon Settings"]["fabric connections"]["main"][part_id] = asn_2_ip[part].values()

        with open(config_file, "w") as f:
            json.dump(config, f)

        with open("asn_2_id.json", "w") as f:
            json.dump(asn_2_id, f)

    return asn_2_id


''' main '''
if __name__ == '__main__':
    #parser = argparse.ArgumentParser()
    #parser.add_argument('frac', help='fraction of SDN fowarding peers')
    #args = parser.parse_args()
    #frac = float(args.frac)
    # Parse ribs to extract asn_2_ip
    asn_2_ip = getParticipants()

    #asn_2_ip = {"AS1":"1","AS2":"2","AS3":"3"}
    #asn_2_ports = {"AS1":[1], "AS2":[2,3], "AS3":[4,5]}
    asn_2_ip = json.load(open("asn_2_ip.json", 'r'))
    asn_2_id = generate_global_config(asn_2_ip)

    # Params
    #count = 10
    #count = int(frac*len(asn_2_ip.keys()))
    #limit_out = 4


    #for part in asn_2_ip:
    #    generatePoliciesParticipant(part, asn_2_ip, asn_2_id, count, limit_out)
