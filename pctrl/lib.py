#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import errno
import json
from multiprocessing.connection import Client
from netaddr import IPNetwork
from socket import error as SocketError

from xctrl.flowmodmsg import FlowModMsgBuilder
from peer import BGPPeer


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



    def get_arp_client(self, logger):
        config = self.config

        conn_info = config["ARP Proxy"]

        return GenericClient(conn_info["GARP_SOCKET"][0], conn_info["GARP_SOCKET"][1], '', logger, 'arp')


    def get_eh_info(self):
        config = self.config

        conn_info = config["Participants"][self.id]["EH_SOCKET"]

        return tuple(conn_info)


    def get_refmon_client(self, logger):
        config = self.config

        conn_info = config["RefMon Server"]

        port    = conn_info["Port"]
        address = conn_info["IP"]

        key = config["Participants"][self.id]["Flanc Key"]

        return GenericClient(address, port, key, logger, 'refmon')


    def get_xrs_client(self, logger):
        config = self.config

        conn_info = config["Route Server"]

        return GenericClient(conn_info["AH_SOCKET"][0], conn_info["AH_SOCKET"][1], '', logger, 'xrs')


class GenericClient(object):
    def __init__(self, address, port, key, logger, sname):
        self.address = address
        self.port = int(port)
        self.key = key
        self.logger = logger
        self.serverName = sname


    def send(self, msg):
        # TODO: Busy wait will do for initial startup but for dealing with server down in the middle of things
        # TODO: then busy wait is probably inappropriate.
        while True: # keep going until we break out inside the loop
            try:
                self.logger.debug('Attempting to connect to '+self.serverName+' server at '+str(self.address)+' port '+str(self.port))
                conn = Client((self.address, self.port))
                self.logger.debug('Connect to '+self.serverName+' successful.')
                break
            except SocketError as serr:
                if serr.errno == errno.ECONNREFUSED:
                    self.logger.debug('Connect to '+self.serverName+' failed because connection was refused (the server is down). Trying again.')
                else:
                    # Not a recognized error. Treat as fatal.
                    self.logger.debug('Connect to '+self.serverName+' gave socket error '+str(serr.errno))
                    raise serr
            except:
                self.logger.exception('Connect to '+self.serverName+' threw unknown exception')
                raise

        conn.send(msg)

        conn.close()
