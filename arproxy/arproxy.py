#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)

import sys
import json
import socket
import struct
import binascii
from threading import Thread,Event

from multiprocessing.connection import Listener


ETH_BROADCAST = 'ff:ff:ff:ff:ff:ff'
ETH_TYPE_ARP = 0x0806
LOG = False

class ArpProxy():

    def __init__(self, config_file):
        self.run = True
        self.host = None
        self.raw_socket = None
        self.listener_garp = None
        self.garp_socket = None

        self.participants = {}
        self.portmac_2_participant = {}

        self.parse_arpconfig(config_file)

        # Set various listeners
        self.set_arp_listener()
        self.set_garp_listener()

    def parse_arpconfig(self, config_file):
        "Parse the config file to extract eh_sockets and portmac_2_participant"
        with open(config_file, 'r') as f:
            config = json.load(f)
            tmp = config["ARP Proxy"]["GARP_SOCKET"]
            self.garp_socket = tuple([tmp[0], int(tmp[1])])
            for participant_id in config["Participants"]:
                participant = config["Participants"][participant_id]
                self.participants[participant_id] = {}
                self.participants[participant_id]["eh_socket"] = tuple([participant["EH_SOCKET"][0], int(participant["EH_SOCKET"][1])])
                for i in range(0, len(participant["Ports"])):
                    self.portmac_2_participant[participant["Ports"][i]['MAC']] = int(participant_id)


    def set_arp_listener(self):
        # Set listener for ARP requests from IXP Fabric
        self.host = socket.gethostbyname(socket.gethostname())

        try:
            self.raw_socket = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(ETH_TYPE_ARP))
            self.raw_socket.bind(('eth0', 0))
            self.raw_socket.settimeout(1.0)
        except socket.error as msg:
            print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()

    def start_arp_listener(self):
        eth_length = 14
        arp_length = 28

        while self.run:
            # receive arp requests
            try:
                raw_packet = self.raw_socket.recvfrom(65565)
                packet, eth_frame, arp_packet = parse_packet(raw_packet)

                arp_type = struct.unpack("!h", arp_packet["oper"])[0]
                if LOG:
                    print "ARP-PROXY: received ARP-" + ("REQUEST" if (arp_type == 1) else "REPLY") +" SRC: "+eth_frame["src_mac"]+" / "+arp_packet["src_ip"]+" "+"DST: "+eth_frame["dst_mac"]+" / "+arp_packet["dst_ip"]

                if arp_type == 1:
                    # check if the arp request stems from one of the participants
                    requester_srcmac = eth_frame["src_mac"]
                    requested_ip = arp_packet["dst_ip"]
                    response_vmac = self.get_vmac(requester_srcmac, requested_ip)
                    if response_vmac != "":
                        if LOG:
                            print "ARP-PROXY: reply with VMAC "+response_vmac

                        data = self.craft_arp_packet(arp_packet, response_vmac)
                        eth_packet = self.craft_eth_frame(eth_frame, response_vmac, data)
                        self.raw_socket.send(''.join(eth_packet))

            except socket.timeout:
                if LOG:
                    print 'Socket Timeout Occured'

    def stop(self):
        self.run = False
        self.raw_socket.close()
        self.listener_garp.close()

    def set_garp_listener(self):
        "Set listener for gratuitous ARPs from the participants' controller"
        print "Starting the Gratuitous ARP listener"
        self.listener_garp = Listener(self.garp_socket, authkey=None)
        ps_thread = Thread(target=self.start_garp_handler)
        ps_thread.daemon = True
        ps_thread.start()

    def start_garp_handler(self):
        print "Gratuitous ARP Handler started "
        while True:
            conn_ah = self.listener_garp.accept()
            tmp = conn.recv()
            self.process_garp(json.loads(tmp))
            reply = "Gratuitous ARP response processed"
            conn_ah.send(reply)
            conn_ah.close()

    def process_garp(self, data):
        "Process the incoming Gratuitous ARP response"
        garp_message = craft_garp_reponse(data['vmac'], data['dstmac'])
        self.raw_socket.send(garp_message)

    def get_vmac(self, requester_srcmac, requested_ip):
        "Get the VMAC for the arp request message"
        requester_id = self.portmac_2_participant[requester_srcmac]
        if requester_id in self.participants:
            # ARP request is sent by participant with its own SDN controller
            eh_socket = self.participants[requester_id]["eh_socket"]
            data = {}
            data['arp_request'] = requested_ip
            reply = send_data(eh_socket, data)
            vmac = reply['vmac']
            return vmac
        else:
            # No SDN controller for this participant
            vmac = self.get_vmac_default(requester_id)

    def get_vmac_default(self, requester_id):
        " Keep track of VMACs to be returned for non SDN participants"
        # TODO: Complete the logic for this function
        # TODO: We can create these mappings during init itself
        return ''

    def parse_packet(self, raw_packet):
        packet = packet[0]
        eth_frame = self.parse_eth_frame(packet[0:eth_length])
        arp_packet = self.parse_arp_packet(packet[eth_length:(eth_length+arp_length)])

        return packet, eth_frame, arp_packet

    def parse_eth_frame(self, frame):
        eth_detailed = struct.unpack("!6s6s2s", frame)

        eth_frame = {"dst_mac": ':'.join('%02x' % ord(b) for b in eth_detailed[0]),
                     "src_mac": ':'.join('%02x' % ord(b) for b in eth_detailed[1]),
                     "type": eth_detailed[2]}
        return eth_frame

    def parse_arp_packet(self, packet):
        arp_detailed = struct.unpack("2s2s1s1s2s6s4s6s4s", packet)

        arp_packet = {"htype": arp_detailed[0],
                      "ptype": arp_detailed[1],
                      "hlen": arp_detailed[2],
                      "plen": arp_detailed[3],
                      "oper": arp_detailed[4],
                      "src_mac": ':'.join('%02x' % ord(b) for b in arp_detailed[5]),
                      "src_ip": socket.inet_ntoa(arp_detailed[6]),
                      "dst_mac": ':'.join('%02x' % ord(b) for b in arp_detailed[7]),
                      "dst_ip": socket.inet_ntoa(arp_detailed[8])}

        return arp_packet

    def craft_arp_packet(self, packet, dst_mac):
        arp_packet = [
            packet["htype"],
            packet["ptype"],
            packet["hlen"],
            packet["plen"],
            struct.pack("!h", 2),
            binascii.unhexlify(dst_mac.replace(':', '')),
            socket.inet_aton(packet["dst_ip"]),
            binascii.unhexlify(packet["src_mac"].replace(':', '')),
            socket.inet_aton(packet["src_ip"])]

        return arp_packet

    def craft_eth_frame(self, frame, dst_mac, data):
        eth_frame = [
            binascii.unhexlify(frame["src_mac"].replace(':', '')),
            binascii.unhexlify(dst_mac.replace(':', '')),
            frame["type"],
            ''.join(data)]

        return eth_frame

''' main '''
if __name__ == '__main__':
    # start arp proxy
    sdx_ap = ArpProxy("arproxy.cfg")
    ap_thread = Thread(target=sdx_ap.start_arp_listener)
    ap_thread.start()
    while ap_thread.is_alive():
        try:
            ap_thread.join(1)
        except KeyboardInterrupt:
            sdx_ap.stop()
