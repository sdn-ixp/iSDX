import struct
import binascii
import socket

ETH_BROADCAST = 'ff:ff:ff:ff:ff:ff'
ETH_TYPE_ARP = 0x0806

eth_length = 14
arp_length = 28

def parse_packet(raw_packet):
    packet = raw_packet[0]
    eth_frame = parse_eth_frame(packet[0:eth_length])
    arp_packet = parse_arp_packet(packet[eth_length:(eth_length+arp_length)])

    return packet, eth_frame, arp_packet

def parse_eth_frame(frame):
    eth_detailed = struct.unpack("!6s6s2s", frame)

    eth_frame = {"dst_mac": ':'.join('%02x' % ord(b) for b in eth_detailed[0]),
                 "src_mac": ':'.join('%02x' % ord(b) for b in eth_detailed[1]),
                 "type": eth_detailed[2]}
    return eth_frame

def parse_arp_packet(packet):
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

def craft_arp_packet(packet, dst_mac):
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

def craft_eth_frame(frame, dst_mac, data):
    eth_frame = [
        binascii.unhexlify(frame["src_mac"].replace(':', '')),
        binascii.unhexlify(dst_mac.replace(':', '')),
        frame["type"],
        ''.join(data)]

    return eth_frame



def craft_garp_response(SPA, TPA, SHA, THA, eth_src, eth_dst):
    "Craft Gratuitous ARP Response Message"
    """
    Format ARP reply:
    eth_src = VMAC, eth_dst = requester_mac, SHA = VMAC, SPA = vnhip, THA = requester_mac, TPA = requester_ip

    Format gratuitous ARP:
    eth_src = VMAC, eth_dst = 00..00<part_id>, SHA = VMAC, SPA = vnhip, THA = VMAC, TPA = vnhip
    """
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
        binascii.unhexlify(SHA.replace(':', '')),
        # SPA
        socket.inet_aton(str(SPA)),
        # THA
        binascii.unhexlify(THA.replace(':', '')),
        # TPA
        socket.inet_aton(str(TPA))
    ]
    eth_frame = [
        # Destination address:
        binascii.unhexlify(eth_dst.replace(':', '')),
        # Source address:
        binascii.unhexlify(eth_src.replace(':', '')),
        # Protocol
        struct.pack("!h", ETH_TYPE_ARP),
        # Data
        ''.join(arp_packet)
    ]
    return ''.join(eth_frame)
