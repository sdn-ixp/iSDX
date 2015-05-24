#!/usr/bin/env python

import sys
import socket
import struct
import binascii
from threading import Thread,Event

from lib import vmac, vmac_best_path

ETH_BROADCAST = 'ff:ff:ff:ff:ff:ff'
ETH_TYPE_ARP = 0x0806
LOG = False

class arp_proxy():
    
    def __init__(self, xrs):
        self.xrs = xrs
        
        self.run = True
        
        # open socket
        self.host = socket.gethostbyname(socket.gethostname())
        
        try:
            self.raw_socket = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(ETH_TYPE_ARP))
            self.raw_socket.bind(('exabgp-eth0', 0))
            self.raw_socket.settimeout(1.0)
        except socket.error as msg:
            print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
        
    def start(self):
        eth_length = 14
        arp_length = 28
    
        while self.run:
            # receive arp requests
            try:
                packet = self.raw_socket.recvfrom(65565)

                packet = packet[0]
                
                eth_frame = self.parse_eth_frame(packet[0:eth_length])
                arp_packet = self.parse_arp_packet(packet[eth_length:(eth_length+arp_length)])

                arp_type = struct.unpack("!h", arp_packet["oper"])[0]
                if LOG:
                    print "ARP-PROXY: received ARP-" + ("REQUEST" if (arp_type == 1) else "REPLY") +" SRC: "+eth_frame["src_mac"]+" / "+arp_packet["src_ip"]+" "+"DST: "+eth_frame["dst_mac"]+" / "+arp_packet["dst_ip"]

                if arp_type == 1:
                    # check if the arp request stems from one of the participants
                    if eth_frame["src_mac"] in self.xrs.portmac_2_participant:
                        # then craft reply using VNH to VMAC mapping
                        print "Crafting REPLY for received Request"
                        vmac_addr = vmac(arp_packet["dst_ip"], self.xrs.portmac_2_participant[eth_frame["src_mac"]], self.xrs)

                        # only send arp request if a vmac exists
                        if vmac_addr <> "":
                            if LOG:
                                print "ARP-PROXY: reply with VMAC "+vmac_addr

                            data = self.craft_arp_packet(arp_packet, vmac_addr)
                            eth_packet = self.craft_eth_frame(eth_frame, vmac_addr, data)

                            self.raw_socket.send(''.join(eth_packet))
                            
            except socket.timeout:
                if LOG:
                    print 'Socket Timeout Occured'

    def stop(self):
        self.run = False
        self.raw_socket.close()
            
    
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
            
    def send_gratuitous_arp(self, changes):
        # then craft reply using VNH to VMAC mapping
        vmac_addr = vmac(changes["VNH"], changes["participant"], self.xrs)
        
        dst_mac = vmac_best_path(changes["participant"], self.xrs)

        arp_packet = [
            # HTYPE
            struct.pack("!h", 1),
            # PTYPE (IPv4)
            struct.pack("!h", 0x0800),
            # HLEN
            struct.pack("!B", 6),
            # PLEN
            struct.pack("!B", 4),
            # OPER (reply)
            struct.pack("!h", 2),
            # SHA
            binascii.unhexlify(vmac_addr.replace(':', '')),
            # SPA
            socket.inet_aton(str(changes["VNH"])),
            # THA
            binascii.unhexlify(vmac_addr.replace(':', '')),
            # TPA
            socket.inet_aton(str(changes["VNH"]))
        ]
        eth_frame = [
            # Destination address:
            binascii.unhexlify(dst_mac.replace(':', '')),
            # Source address:
            binascii.unhexlify(vmac_addr.replace(':', '')),
            # Protocol
            struct.pack("!h", ETH_TYPE_ARP),
            # Data
            ''.join(arp_packet)
        ]
                
        self.raw_socket.send(''.join(eth_frame))   
        
''' main '''    
if __name__ == '__main__':
    # start arp proxy    
    sdx_ap = arp_proxy()
    ap_thread = Thread(target=sdx_ap.start)
    ap_thread.start()
    
    ap_thread.join()