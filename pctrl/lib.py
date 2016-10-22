#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import errno
import json
from multiprocessing.connection import Client
from netaddr import IPNetwork
from socket import error as SocketError
from ryu.lib import hub

import os
import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
from xctrl.flowmodmsg import FlowModMsgBuilder

from peer import BGPPeer
from participant_server import ParticipantServer


class PConfig(object):

    MULTISWITCH = 0
    MULTITABLE  = 1

    SUPERSETS = 0
    MDS       = 1

    def __init__(self, config_file, id):
        self.id = str(id)

        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.parse_modes()

        self.parse_various()


    def parse_modes(self):
        config = self.config

        if config["Mode"] == "Multi-Switch":
            self.dp_mode = self.MULTISWITCH
        else:
            self.dp_mode = self.MULTITABLE

        vmac_cfg = config["VMAC"]

        if vmac_cfg["Mode"] == "Superset":
            self.vmac_mode = self.SUPERSETS
        else:
            self.vmac_mode = self.MDS

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

    def get_macs(self):
        return [port['MAC'] for port in self.ports]

    def get_ports(self):
        return [port['IP'] for port in self.ports]



    def get_bgp_instance(self):
        return BGPPeer(self.id, self.asn, self.ports, self.peers_in, self.peers_out)


    def get_xrs_client(self, logger):
        config = self.config
        conn_info = config["Route Server"]
        return GenericClient2(conn_info["AH_SOCKET"][0], conn_info["AH_SOCKET"][1], '', logger, 'xrs')

    def get_xrs_info(self, logger=None):
        config = self.config
        conn_info = config["Route Server"]
        string = ("%s %s" % (conn_info["AH_SOCKET"][0], conn_info["AH_SOCKET"][1]))
        return string

    # participant client
    def get_participant_client(self, id, logger):
        config = self.config
        conn_info = config["Participants"]
        conn_info = conn_info[str(id)]
        return GenericClient2(conn_info["PH_SOCKET"][0], conn_info["PH_SOCKET"][1], '', logger, 'participant')

    # participant server
    def get_participant_server(self, id, logger):
        config = self.config
        conn_info = config["Participants"]
        part_info = conn_info[str(id)]
        if "PH_SOCKET" not in part_info:
            logger.warn('No PH_SOCKET for participant: ' + str(id))
            return None
        return ParticipantServer(part_info["PH_SOCKET"][0], part_info["PH_SOCKET"][1], logger)


    def get_arp_client(self, logger):
        config = self.config
        conn_info = config["ARP Proxy"]
        return GenericClient2(conn_info["GARP_SOCKET"][0], conn_info["GARP_SOCKET"][1], '', logger, 'arp')

    def get_refmon_client(self, logger):
        config = self.config

        conn_info = config["RefMon Server"]

        port    = conn_info["Port"]
        address = conn_info["IP"]

        key = config["Participants"][self.id]["Flanc Key"]

        return GenericSockClient(address, port, key, logger, 'refmon')

    def isMultiSwitchMode(self):
        return self.dp_mode == self.MULTISWITCH

    def isMultiTableMode(self):
        return self.dp_mode == self.MULTITABLE

    def isSupersetsMode(self):
        return self.vmac_mode == self.SUPERSETS

    def isMDSMode(self):
        return self.vmac_mode == self.MDS


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

class GenericSockClient(object):
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
                conn = hub.connect((self.address, self.port))
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

        conn.sendall(msg)

        conn.close()


class GenericClient2(object):
    def __init__(self, address, port, key, logger, sname):
        self.address = address
        self.port = int(port)
        self.key = key
        self.logger = logger
        self.serverName = sname

        while True: # keep going until we break out inside the loop
            try:
                self.logger.debug('Attempting to connect to '+self.serverName+' server at '+str(self.address)+' port '+str(self.port))
                self.conn = Client((self.address, self.port))
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

    def send(self, msg):
        self.conn.send(json.dumps(msg))

    def poll(self, t):
        return self.conn.poll(t)

    def recv(self):
        return self.conn.recv()

    def close(self):
        self.conn.close()
