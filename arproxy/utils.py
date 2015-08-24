

def send_data(sock, data):
    "Send the data over socket `sock`"
    conn = Client(sock, authkey = None)
    conn.send(json.dumps(data))
    reply = json.load(conn.recv())
    conn.close()
    return reply

def craft_garp_reponse(vmac_addr, dst_mac):
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
    return ''.join(eth_frame)
