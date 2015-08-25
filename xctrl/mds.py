#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import logging

from flowmodmsg import FlowModMsgBuilder

# Priorities
BGP_PRIORITY = 4
ARP_PRIORITY = 4

OUTBOUND_PRIORITY = 3

FORWARDING_PRIORITY = 2

INBOUND_PRIORITY = 1

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

class MDS(object):
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
        self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, action)

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

        ### flood ARP requests
        match = {"eth_type": ETH_TYPE_ARP, "eth_dst": MAC_BROADCAST}
        action = {"fwd": [OFPP_FLOOD]}
        self.fm_builder.add_flow_mod("insert", rule_type, ARP_PRIORITY, match, action)

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

    def handle_participant_with_inbound(self, rule_type):
        for participant in self.config.peers.values():
            ### inbound policies specified
            if participant.inbound_rules:
                for port in participant.ports:
                    match = {"eth_dst": port.mac}
                    action = {"fwd": ["inbound"]}
                    self.fm_builder.add_flow_mod("insert", rule_type, INBOUND_PRIORITY, match, action)

    def default_forwarding(self, rule_type):
        for participant in self.config.peers.values():
            ### default forwarding
            if not participant.inbound_rules:
                port = participant.ports[0]
                match = {"eth_dst": port.mac}
                action = {"fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, FORWARDING_PRIORITY, match, action)

    def default_forwarding_inbound(self, rule_type, fwd):
        ## set the inbound bit to zero
        for participant in self.config.peers.values():
            if participant.inbound_rules:
                port = participant.ports[0]
                match = {"eth_dst": port.mac, "in_port": "inbound"}
                action = {"fwd": [fwd]}
                self.fm_builder.add_flow_mod("insert", "inbound", FORWARDING_PRIORITY, match, action)

    def match_any_fwd(self, rule_type, dst):
        match = {}
        action = {"fwd": [dst]}
        self.fm_builder.add_flow_mod("insert", rule_type, DEFAULT_PRIORITY, match, action)

class MDSmS(GSS):
    def __init__(self, sender, config):
        super(MDSmS, self).__init__(sender, config)
        self.logger = logging.getLogger('MDSmS')
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
        self.handle_participant_with_inbound("main-in")
        ### default forwarding
        self.default_forwarding("main-in")

        # OUTBOUND SWITCH

        # INBOUND SWITCH
        ## send all other packets to main
        self.match_any_fwd("inbound", "main-in")

        self.sender.send(self.fm_builder.get_msg())

        self.logger.info('sent flow mods to reference monitor')

class MDSmT(GSS):
    def __init__(self, sender, config):
        super(MDSmT, self).__init__(sender, config)
        self.logger = logging.getLogger('MDSmT')
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
        ## whatever doesn't match on any other rule, send to inbound switch
        self.match_any_fwd("main-in", "main-out")

        # OUTBOUND SWITCH

        # INBOUND SWITCH
        ## set the inbound bit to zero
        self.default_forwarding_inbound("inbound", "main-out")
        ## send all other packets to main
        self.match_any_fwd("inbound", "main-out")

        # MAIN-OUT TABLE
        ### default forwarding
        self.default_forwarding("main-out")

        self.sender.send(self.fm_builder.get_msg())

        self.logger.info('sent flow mods to reference monitor')
