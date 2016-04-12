#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)


import argparse
from collections import namedtuple
import json
from multiprocessing.connection import Listener, Client
from netaddr import IPNetwork, IPAddress
import os
import socket
import struct
import sys
from threading import Thread, Lock

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from utils import parse_packet, craft_arp_packet, craft_eth_frame, craft_garp_response


logger = util.log.getLogger('arp')

ETH_BROADCAST = 'ff:ff:ff:ff:ff:ff'
ETH_TYPE_ARP = 0x0806

Config = namedtuple('Config', 'vnhs garp_socket interface')

arpListener = None
config = None

participantsLock = Lock()
portmac2Participant = {}

clientPoolLock = Lock()
clientActivePool = dict()
clientDeadPool = set()


class PctrlClient(object):
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

    def start(self):
        logger.info("ARP Response Handler started")
        while True:
            rv = None
            try:
                rv = self.conn.recv()
            except EOFError as ee:
                pass

            if not (rv and self.process_message(**json.loads(rv))):
                self.close()
                break


    def process_message(self, msgType=None, **data):
        if msgType == 'hello':
            rv = self.process_hello_message(**data)
        elif msgType == 'garp':
            rv = self.process_garp_message(**data)
        else:
            logger.warn("Unrecognized or absent msgType: %s. Message ignored.", msgType)
            rv = True

        return rv


    def process_hello_message(self, macs=None):
        if isinstance(macs, list):
            with participantsLock:
                for mac in macs:
                    portmac2Participant[mac] = self
        else:
            logger.warn("hello message from %s is missing MAC list. 'macs' has value: %s. Closing connection.", self.addr, macs)
            return False

        return True


    def process_garp_message(self, **data):
        """
        Process the incoming ARP data from the Participant Controller:
        -Format ARP Reply:
            eth_src = VMAC, eth_dst = requester_mac, 
            SHA = VMAC, SPA = vnhip, 
            THA = requester_mac, TPA = requester_ip

        -Format Gratuitous ARP:
            eth_src = VMAC, eth_dst = 00..00<part_id>, 
            SHA = VMAC, SPA = vnhip, 
            THA = VMAC, TPA = vnhip
        """

        if data["THA"] == data["eth_dst"]:
            logger.debug("ARP Reply relayed: "+str(data))
        else:
            logger.debug("Gratuitous ARP relayed: "+str(data))

        garp_message = craft_garp_response(**data)
        arpListener.send(garp_message)

        return True


    def send(self, srcmac, ip):
        # ARP request is sent by participant with its own SDN controller
        logger.debug("relay ARP-REQUEST to participant %s", self.addr)
        data = {}
        data['arp'] = [srcmac, ip]
        self.conn.send(json.dumps(data))


    def close(self):
        with clientPoolLock:
            s, t = clientActivePool[self.conn]
            del clientActivePool[self.conn]
            # we can't join() inside the thread,
            # so move to a list and remove later.
            clientDeadPool.add(t)

        self.conn.close()

        with participantsLock:
            macs = [mac for mac,pctl in portmac2Participant.items() if pctl == self]
            for mac in macs:
                del portmac2Participant[mac]


class PctrlListener(object):
    def __init__(self):
        # "Set listener for ARP replies from the participants' controller"
        logger.info("Starting the PctrlListener")
        self.listener_garp = Listener(config.garp_socket, authkey=None, backlog=100)


    def start(self):
        logger.info("ARP Response Handler started")
        while True:
            conn = self.listener_garp.accept()
            pc = PctrlClient(conn, self.listener_garp.last_accepted)
            t = Thread(target=pc.start)
            with clientPoolLock:
                clientActivePool[conn] = (pc, t)

                # while here, join dead threads.
                while clientDeadPool:
                    clientDeadPool.pop().join()

            t.start()


class ArpListener(object):
    def __init__(self):
        # info about non-sdn participants
        # TODO: Create a mapping between actual interface IP addresses
        # and the corresponding MAC addresses for all the non-SDN participants
        # In case of MDS, it is actual mac adresses of these interfaces, in case
        # of the superset scheme it is : 1XXXX-nexthop_id
        # self.nonSDN_nhip_2_nhmac = {}
        try:
            self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(ETH_TYPE_ARP))
            self.sock.bind((config.interface, 0))
        except socket.error as msg:
            logger.error("Can't open socket %s", str(config.interface))
            logger.exception('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            raise


    def start(self):
        while True:
            # receive arp requests
            packet, addr = self.sock.recvfrom(65565)
            eth_frame, arp_packet = parse_packet(packet)

            arp_type = struct.unpack("!h", arp_packet["oper"])[0]
            logger.debug("Received ARP-" + ("REQUEST" if (arp_type == 1) else "REPLY") +" SRC: "+eth_frame["src_mac"]+" / "+arp_packet["src_ip"]+" "+"DST: "+eth_frame["dst_mac"]+" / "+arp_packet["dst_ip"])

            if arp_type == 1:
                # check if the arp request stems from one of the participants
                requester_srcmac = eth_frame["src_mac"]
                requested_ip = arp_packet["dst_ip"]
                # Send the ARP request message to respective controller and forget about it
                if IPAddress(requested_ip) in config.vnhs:
                    self.send_arp_request(requester_srcmac, requested_ip)
    
                    # TODO: If the requested IP address belongs to a non-SDN participant
                    # then refer the structure `self.nonSDN_nhip_2_nhmac` and
                    # send an immediate ARP response.
                    """
                    response_vmac = self.get_vmac_default(requester_srcmac, requested_ip)
                    if response_vmac != "":
                        logger.debug("ARP-PROXY: reply with VMAC "+response_vmac)

                        data = self.craft_arp_packet(arp_packet, response_vmac)
                        eth_packet = self.craft_eth_frame(eth_frame, response_vmac, data)
                        self.sock.send(''.join(eth_packet))
                    """


    def send_arp_request(self, requester_srcmac, requested_ip):
        "Send the arp request to the corresponding pctrl"
        with participantsLock:
            try:
                pctrlClient = portmac2Participant[requester_srcmac]
            except KeyError:
                pctrlClient = None

        if pctrlClient:
            pctrlClient.send(requester_srcmac, requested_ip)


    def send(self, data):
        self.sock.send(data)


def parse_arpconfig(config_file):
    "Parse the config file"

    with open(config_file, 'r') as f:
        config = json.load(f)

    vnhs = IPNetwork(config["VNHs"])

    host, port = config["ARP Proxy"]["GARP_SOCKET"]
    garp_socket = (host, int(port))

    interface = config["ARP Proxy"]["Interface"]

    return Config(vnhs, garp_socket, interface)


def main():
    global arpListener, config

    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    args = parser.parse_args()

    # locate config file
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","examples",args.dir,"config","sdx_global.cfg")

    logger.info("Reading config file %s", config_file)
    config = parse_arpconfig(config_file)

    logger.info("Starting ARP Listener")
    arpListener = ArpListener()
    ap_thread = Thread(target=arpListener.start)
    ap_thread.start()

    # start pctrl listener in foreground
    logger.info("Starting PCTRL Listener")
    pctrlListener = PctrlListener()
    pctrlListener.start()


if __name__ == '__main__':
    main()
