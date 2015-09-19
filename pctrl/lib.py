#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import requests
import json
from netaddr import *
from multiprocessing.connection import Client
from peer import BGPPeer as BGPPeer

import sys
sys.path.insert(0,'../xctrl')
from flowmodmsg import FlowModMsgBuilder


# from bgp_interface import get_all_participants_advertising

LOG = False



MULTISWITCH = 0
MULTITABLE  = 1

SUPERSETS = 0
MDS       = 1



class PConfig(object):
    def __init__(self, config_file, id):
        self.id = str(id)

        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.parse_modes()

        self.parse_various()



    def parse_modes(self):
        config = self.config

        if config["Mode"] == "Multi-Switch":
            self.dp_mode = MULTISWITCH
        else:
            self.dp_mode = MULTITABLE

        vmac_cfg = config["VMAC"]

        if vmac_cfg["Mode"] == "Superset":
            self.vmac_mode = SUPERSETS
        else:
            self.vmac_mode = MDS

        self.vmac_options = vmac_cfg["Options"]


    def get_nexthop_2_part(self):
        config = self.config

        nexthop_2_part = {}

        for part in config["Participants"]:
            for port in config["Participants"][part]["Ports"]:
                nexthop = str(port["IP"])
                nexthop_2_part[nexthop] = int(part)

        return nexthop_2_part


    def parse_various(self):
        config = self.config

        participant = config["Participants"][self.id]

        self.ports = participant["Ports"]
        self.port0_mac = self.ports[0]["MAC"]

        self.peers_in = participant["Peers"]
        self.peers_out = self.peers_in

        self.asn = participant["ASN"]


        self.VNHs = IPNetwork(config["VNHs"])




    def get_bgp_instance(self):
        return BGPPeer(self.id, self.asn, self.ports, self.peers_in, self.peers_out)



    def get_arp_client(self):
        config = self.config

        conn_info = config["ARP Proxy"]

        return GenericClient(conn_info["GARP_SOCKET"][0], conn_info["GARP_SOCKET"][1])


    def get_eh_info(self):
        config = self.config

        conn_info = config["Participants"][self.id]["EH_SOCKET"]

        return tuple(conn_info)


    def get_refmon_client(self):
        config = self.config

        conn_info = config["RefMon Server"]

        port    = conn_info["Port"]
        address = conn_info["IP"]

        key = config["Participants"][self.id]["Flanc Key"]
	key = conn_info["key"]
        return GenericClient(address, port, key)


    def get_xrs_client(self):
        config = self.config

        conn_info = config["Route Server"]

        return GenericClient(conn_info["AH_SOCKET"][0], conn_info["AH_SOCKET"][1])


class GenericClient():
    def __init__(self, address, port, key = ""):
        self.address = address
        self.port = int(port)
        self.key = key

    def send(self, msg):
        #conn = Client((self.address, self.port), authkey=str(self.key))
        conn = Client((self.address, self.port))

        conn.send(msg)

        conn.close()
