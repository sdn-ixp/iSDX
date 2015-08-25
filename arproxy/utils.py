import struct
import binascii


eth_length = 14
arp_length = 28

def parse_packet(raw_packet):
    packet = packet[0]
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


def craft_garp_reponse(vnhip, dstip, vmac_addr, dst_mac):
    "Craft Gratuitous ARP Response Message"
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
        socket.inet_aton(str(vnhip)),
        # THA
        binascii.unhexlify(vmac_addr.replace(':', '')),
        # TPA
        socket.inet_aton(str(vnhip))
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
    return ''.join(eth_frame)
