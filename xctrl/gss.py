#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import logging

from flowmodmsg import FlowModMsgBuilder
from vmac_lib import VMACBuilder

# Priorities
BGP_PRIORITY = 6
ARP_PRIORITY = 6
VNH_ARP_PRIORITY = 5
ARP_BROADCAST_PRIORITY = 5
OUTBOUND_PRIORITY = 4
FORWARDING_PRIORITY = 4

INBOUND_PRIORITY = 3

INBOUND_BIT_PRIORITY = 2

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
OFPP_ANY = 0xffffffff               # Not associated with a physical port.

class GSS(object):
    def __init__(self, sender, config):
        self.sender = sender
        self.config = config
        self.vmac_builder = VMACBuilder(self.config.vmac_options)
        self.fm_builder = None

    def handle_BGP(self, rule_type):
        ### BGP traffic to route server
        port = self.config.route_server.ports[0]
        action = {"fwd": [port.id]}
        match = {"eth_dst": port.mac, "tcp_src": BGP}
        self.fm_builder.add_flow_mod("insert", rule_type, BGP_PRIORITY, match, action)

        match = {"eth_dst": port.mac, "tcp_dst": BGP}
        self.fm_builder.add_flow_mod("insert", rule_type, BGP_PRIORITY, match, action)

        ### BGP traffic to participants
        for participant in self.config.peers.values():
            for port in participant.ports:
                match = {"eth_dst": port.mac, "tcp_src": BGP}
                action = {"fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, BGP_PRIORITY, match, action)
                match = {"eth_dst": port.mac, "tcp_dst": BGP}
                self.fm_builder.add_flow_mod("insert", rule_type, BGP_PRIORITY, match, action)

    def handle_ARP(self, rule_type):
        ### direct ARP requests for VNHs to ARP proxy
        port = self.config.arp_proxy.ports[0]
        match = {"eth_type": ETH_TYPE_ARP, "arp_tpa": (str(self.config.vnhs.network), str(self.config.vnhs.netmask))}
        action = {"fwd": [port.id]}
        self.fm_builder.add_flow_mod("insert", rule_type, VNH_ARP_PRIORITY, match, action)

        ### direct all ARP requests for the route server to it
        port = self.config.route_server.ports[0]
        match = {"eth_type": ETH_TYPE_ARP, "eth_dst": port.mac}
        action = {"fwd": [port.id]}
        self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, action)

        for participant in self.config.peers.values():
            ### make sure ARP replies reach the participants
            for port in participant.ports:
                match = {"eth_type": ETH_TYPE_ARP, "eth_dst": port.mac}
                action = {"fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, action)

            ### direct gratuituous ARPs only to the respective participant
            vmac = self.vmac_builder.next_hop_match(participant.name, False)
            vmac_mask = self.vmac_builder.next_hop_mask(False)
            match = {"in_port": self.config.arp_proxy.ports[0].id, "eth_type": ETH_TYPE_ARP, "eth_dst": (vmac, vmac_mask)}
            action = {"set_eth_dst": MAC_BROADCAST}
            fwd = []
            for port in participant.ports:
                fwd.append(port.id)
            action["fwd"] = fwd
            self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, action)

        ### flood ARP requests - but only on non switch-switch ports
        match = {"eth_type": ETH_TYPE_ARP, "eth_dst": MAC_BROADCAST}
        ports = []
        for participant in self.config.peers.values():
            for port in participant.ports:
                ports.append(port.id)
        ports.append(self.config.arp_proxy.ports[0].id)
        ports.append(self.config.route_server.ports[0].id)

        action = {"fwd": ports}
        self.fm_builder.add_flow_mod("insert", rule_type, ARP_BROADCAST_PRIORITY, match, action)

    def handle_participant_with_outbound(self, rule_type):
        for participant in self.config.peers.values():
            ### outbound policies specified
            if participant.outbound_rules:
                mac = None
                for port in participant.ports:
                    if mac is None:
                        mac = port.mac
                    match = {"in_port": port.id}
                    action = {"set_eth_src": mac, "fwd": ["outbound"]}
                    self.fm_builder.add_flow_mod("insert", rule_type, OUTBOUND_PRIORITY, match, action) 

    def handle_participant_with_inbound(self, rule_type, mask_inbound_bit):
        for participant in self.config.peers.values():
            ### inbound policies specified
            if participant.inbound_rules:
                i = 0
                for port in participant.ports:
                    vmac = self.vmac_builder.part_port_match(participant.name, i, False)
                    i += 1
                    vmac_mask = self.vmac_builder.part_port_mask(mask_inbound_bit)
                    match = {"eth_dst": (vmac, vmac_mask)}
                    action = {"set_eth_dst": port.mac, "fwd": [port.id]}
                    self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, action)

    def default_forwarding(self, rule_type):
        for participant in self.config.peers.values():
            ### default forwarding
            if not participant.inbound_rules:
                vmac = self.vmac_builder.next_hop_match(participant.name, False)
                vmac_mask = self.vmac_builder.next_hop_mask(False)
                port = participant.ports[0]
                match = {"eth_dst": (vmac, vmac_mask)}
                action = {"set_eth_dst": port.mac, "fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, action)

    def default_forwarding_inbound(self, rule_type, fwd):
        ## set the inbound bit to zero
        for participant in self.config.peers.values():
            if participant.inbound_rules:
                port = participant.ports[0]
                vmac_match = self.vmac_builder.next_hop_match(participant.name, False)
                vmac_match_mask = self.vmac_builder.next_hop_mask(False)
                vmac_action = self.vmac_builder.part_port_match(participant.name, 0, False) 
                match = {"eth_dst": (vmac_match, vmac_match_mask)}
                action = {"set_eth_dst": vmac_action, "fwd": [fwd]}
                self.fm_builder.add_flow_mod("insert", "inbound", INBOUND_PRIORITY, match, action)

    def handle_inbound(self, rule_type):
        vmac = self.vmac_builder.only_first_bit()
        match = {"eth_dst": (vmac, vmac)}
        action = {"fwd": ["outbound"]}
        self.fm_builder.add_flow_mod("insert", rule_type, INBOUND_BIT_PRIORITY, match, action)

    def match_any_fwd(self, rule_type, dst):
        match = {}
        action = {"fwd": [dst]}
        self.fm_builder.add_flow_mod("insert", rule_type, DEFAULT_PRIORITY, match, action)

    def delete_flow_rule(self, rule_type, cookie, cookie_mask):
        self.fm_builder.delete_flow_mod("remove", rule_type, cookie, cookie_mask)

class GSSmS(GSS):
    def __init__(self, sender, config):
        super(GSSmS, self).__init__(sender, config)
        self.logger = logging.getLogger('GSSmS')
        self.fm_builder = FlowModMsgBuilder(0, self.config.flanc_auth["key"])
 
    def start(self):
        self.logger.info('start')
        self.init_fabric()

    def init_fabric(self):
        self.logger.info('init fabric')
        
        # MAIN SWITCH
        ## handle BGP traffic
        self.logger.info('create flow mods to handle BGP traffic')
        self.handle_BGP("main-in")

        ## handle ARP traffic
        self.logger.info('create flow mods to handle ARP traffic')
        self.handle_ARP("main-in")

        ## handle all participant traffic depending on whether they specified inbound/outbound policies
        self.logger.info('create flow mods to handle participant traffic')
        ### outbound policies specified
        self.handle_participant_with_outbound("main-in")
        ### inbound policies specified
        self.handle_participant_with_inbound("main-in", True)
        ### default forwarding
        self.default_forwarding("main-in")

        ## direct packets with inbound bit set to the inbound switch
        self.handle_inbound("main-in")

        # OUTBOUND SWITCH
        ## whatever doesn't match on any other rule, send to inbound switch
        self.match_any_fwd("outbound", "inbound")

        # INBOUND SWITCH
        ## set the inbound bit to zero
        self.default_forwarding_inbound("inbound", "main-in")

        ## send all other packets to main
        self.match_any_fwd("inbound", "main-in")

        self.sender.send(self.fm_builder.get_msg())

        self.logger.info('sent flow mods to reference monitor')

class GSSmT(GSS):
    def __init__(self, sender, config):
        super(GSSmT, self).__init__(sender, config)
        self.logger = logging.getLogger('GSSmT')
        self.fm_builder = FlowModMsgBuilder(0, self.config.flanc_auth["key"])

    def start(self):
        self.logger.info('start')
        self.init_fabric()

    def init_fabric(self):
        self.logger.info('init fabric')
        
        # MAIN-IN TABLE
        ## handle BGP traffic
        self.logger.info('create flow mods to handle BGP traffic')
        self.handle_BGP("main-in")

        ## handle ARP traffic
        self.logger.info('create flow mods to handle ARP traffic')
        self.handle_ARP("main-in")

        ## handle all participant traffic depending on whether they specified inbound/outbound policies
        self.logger.info('create flow mods to handle participant traffic')
        ### outbound policies specified
        self.handle_participant_with_outbound("main-in")
        ## direct packets with inbound bit set to the inbound switch
        self.handle_inbound("main-in")
        ## whatever doesn't match on any other rule, send to inbound switch
        self.match_any_fwd("main-in", "main-out")

        # OUTBOUND SWITCH
        ## whatever doesn't match on any other rule, send to inbound switch
        self.match_any_fwd("outbound", "inbound")

        # INBOUND SWITCH
        ## set the inbound bit to zero
        self.default_forwarding_inbound("inbound", "main-out")
        ## send all other packets to main
        self.match_any_fwd("inbound", "main-out")

        # MAIN-OUT TABLE
        ### inbound policies specified
        self.handle_participant_with_inbound("main-out", False)
        ### default forwarding
        self.default_forwarding("main-out")

        self.sender.send(self.fm_builder.get_msg())

        self.logger.info('sent flow mods to reference monitor')
