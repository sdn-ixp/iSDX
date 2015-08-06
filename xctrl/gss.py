#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from flowmodmsg import FlowModMsg
from ss_lib import VMACBuilder

class GSS(object):
    def __init__(self, sender, config):
        self.sender = sender
        self.config = config
        self.vmac_builder = VMACBuilder(self.config.vmac_options)

class GSSmS(GSS):
    # Priorities
    BGP_PRIORITY = 5
    ARP_PRIORITY = 5
    ARP_BROADCAST_PRIORITY = 4
    OUTBOUND_PRIORITY = 3
    FORWARDING_PRIORITY = 2

    INBOUND_PRIORITY = 2

    DEFAULT_PRIORITY = 1

    # Ports
    BGP = 179

    # ETH Types
    ETH_TYPE_ARP = 0x0806

    # MAC Addresses
    MAC_BROADCAST = "ff:ff:ff:ff:ff:ff"

    # OF Special Ports
    OFPP_MAX = 0xffffff00
    OFPP_IN_PORT = 0xfffffff8       # Send the packet out the input port. This
                                    # virtual port must be explicitly used
                                    # in order to send back out of the input
                                    # port.
    OFPP_TABLE = 0xfffffff9         # Perform actions in flow table.
                                    # NB: This can only be the destination
                                    # port for packet-out messages.
    OFPP_NORMAL = 0xfffffffa        # Process with normal L2/L3 switching.
    OFPP_FLOOD = 0xfffffffb         # All physical ports except input port and
                                    # those disabled by STP.
    OFPP_ALL = 0xfffffffc           # All physical ports except input port.
    OFPP_CONTROLLER = 0xfffffffd    # Send to controller.
    OFPP_LOCAL = 0xfffffffe         # Local openflow "port".
    OFPP_ANY = 0xffffffff 	        # Not associated with a physical port.

    def __init__(self, sender, config):
        super(GSSmS, self).__init__(sender, config)

    def init_fabric(self):
        msg = FlowModMsg(flanc_auth["participant"], flanc_auth["key"])

        # MAIN SWITCH
        ## handle BGP traffic
        port = self.config.route_server.ports[0]
        action = {"fwd": [port.id]}
        match = {"eth_dst": port.mac, "tcp_src": BGP}
        msg.add_flow_mod("insert", "main", BGP_PRIORITY, match, action)
        match = {"eth_dst": port.mac, "tcp_dst": BGP}
        msg.add_flow_mod("insert", "main", BGP_PRIORITY, match, action)

        for participant in self.config.peers:
            for port in participant.ports
                match = {"eth_dst": port.mac, "tcp_src": BGP}
                action = {"fwd": [port.id]}
                msg.add_flow_mod("insert", "main", BGP_PRIORITY, match, action)
                match = {"eth_dst": mac, "tcp_dst": BGP}
                msg.add_flow_mod("insert", "main", BGP_PRIORITY, match, action)

        ## handle ARP traffic
        ### direct ARP requests for VNHs to ARP proxy
        port = self.config.route_server.ports[0]
        match = {"eth_type": ETH_TYPE_ARP, "arp_tpa": (str(self.vnhs.network), str(self.vnhs.netmask))}
        action = {"fwd": [port.id]}
        msg.add_flow_mod("insert", "main", ARP_PRIORITY, match, action)

        ### direct all ARP requests for the route server to it
        port = self.config.route_server.ports[0]
        match = {"eth_type": ETH_TYPE_ARP, "eth_dst": port.mac}
        action = {"fwd": [port.id]}
        msg.add_flow_mod("insert", "main", ARP_PRIORITY, match, action)

        for participant in self.config.peers:
            ### make sure ARP replies reach the participants
            for port in participant.ports:
                match = {"eth_type": ETH_TYPE_ARP, "eth_dst": port.mac}
                action = {"fwd": [port.id]}
                msg.add_flow_mod("insert", "main", ARP_PRIORITY, match, action)

            ### direct gratuituous ARPs only to the respective participant
            vmac = self.vmac_builder.next_hop_match(participant.name, False)
            vmac_mask = self.vmac_builder.next_hop_mask(False)
            match = {"in_port": self.arp_proxy.ports[0].id, "eth_type": ETH_TYPE_ARP, "eth_dst": (vmac, vmac_mask)}
            action = {"set_eth_dst": MAC_BROADCAST}
            fwd = []
            for port in participants.ports:
                fwd.append(port.id)
            action["fwd"] = fwd
            msg.add_flow_mod("insert", "main", ARP_PRIORITY, match, action)


        match = {"eth_type": ETH_TYPE_ARP, "eth_dst": MAC_BROADCAST}
        action = {"fwd": [OFPP_FLOOD]}
        msg.add_flow_mod("insert", "main", ARP_BROADCAST_PRIORITY, match, action)

        ## handle all participant traffic depending on whether they specified inbound/outbound policies
        for participant in self.config.peers:
            ### outbound policies specified
            if participant.outbound_rules:
                mac = None
                for port in participant.ports:
                    if mac is None:
                        mac = port.mac
                    match = {"in_port": port.id}
                    action = {"set_eth_src": mac, "fwd": ["outbound"]}
                    msg.add_flow_mod("insert", "main", OUTBOUND_PRIORITY, match, action)                

            ### inbound policies specified
            if participant.inbound_rules:
                i = 0
                for port in participant.ports:
                    vmac = self.vmac_builder.part_port_match(participant.name, i, False)
                    vmac_mask = self.vmac_builder.part_port_mask(False)
                    match = {"eth_dst": (vmac, vmac_mask)}
                    action = {"set_eth_dst": port.mac, "fwd": [port.id]}
                    msg.add_flow_mod("insert", "main", FORWARDING_PRIORITY, match, action)               

            ### default forwarding
            else:
                vmac = self.vmac_builder.next_hop_match(participant.name, False)
                vmac_mask = self.vmac_builder.next_hop_mask(False)
                port = participant.ports[0]
                match = {"eth_dst": (vmac, vmac_mask)}
                action = {"set_eth_dst": port.mac, "fwd": [port.id]}
                msg.add_flow_mod("insert", "main", FORWARDING_PRIORITY, match, action)

        ## direct packets with inbound bit set to the inbound switch
        vmac = self.vmac_builder.only_first_bit()

        match = {"eth_dst": (vmac, vmac)}
        action = {"fwd": ["inbound"]}
        msg.add_flow_mod("insert", "main", DEFAULT_PRIORITY, match, action)

        # OUTBOUND SWITCH
        ## whatever doesn't match on any other rule, send to inbound switch
        match = {}
        action = {"fwd": ["inbound"]}
        msg.add_flow_mod("insert", "outbound", DEFAULT_PRIORITY, match, action)

        # INBOUND SWITCH
        ## set the inbound bit to zero
        for participant in self.config.peers:
            if participant.inbound_rules:
                port = participant.ports[0]
                vmac_match = self.vmac_builder.next_hop_match(participant.name, False)
                vmac_match_mask = self.vmac_builder.next_hop_mask(False)
                vmac_action = self.vmac_builder.part_port_match(participant.name, 0, False) 
                match = {"eth_dst": (vmac_match, vmac_match_mask)}
                action = {"set_eth_dst": vmac_action, "fwd": ["main"]}
                msg.add_flow_mod("insert", "inbound", INBOUND_PRIORITY, match, action)

        ## send all other packets to main
        match = {}
        action = {"fwd": ["main"]}
        msg.add_flow_mod("insert", "inbound", DEFAULT_PRIORITY, match, action)

        self.sender.send(msg)

class GSSmT(GSS):
    def __init__(self, sender, config):
        super(GSSmT, self).__init__(sender, config)

    def init_fabric(self):
        pass
