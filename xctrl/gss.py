#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import os
import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from flowmodmsg import FlowModMsgBuilder
from vmac_lib import VMACBuilder


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
    def __init__(self, logger, sender, config):
        self.logger = logger
        self.sender = sender
        self.config = config
        self.fm_builder = FlowModMsgBuilder(0, self.config.flanc_auth["key"])
        self.vmac_builder = VMACBuilder(self.config.vmac_options)

    def handle_BGP(self, rule_type):
        ### BGP traffic to route server
        port = self.config.route_server.ports[0]
        action = {"fwd": [port.id]}
        match = {"eth_dst": port.mac, "tcp_src": BGP}
        self.fm_builder.add_flow_mod("insert", rule_type, "bgp", match, action)

        match = {"eth_dst": port.mac, "tcp_dst": BGP}
        self.fm_builder.add_flow_mod("insert", rule_type, "bgp", match, action)

        ### BGP traffic to participants
        for participant in self.config.peers.values():
            for port in participant.ports:
                match = {"eth_dst": port.mac, "tcp_src": BGP}
                action = {"fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, "bgp", match, action)
                match = {"eth_dst": port.mac, "tcp_dst": BGP}
                self.fm_builder.add_flow_mod("insert", rule_type, "bgp", match, action)

    def handle_ARP_in_main(self, rule_type):
        ### direct all ARP responses for the route server to it
        port = self.config.route_server.ports[0]
        match = {"eth_type": ETH_TYPE_ARP, "eth_dst": port.mac}
        action = {"fwd": [port.id]}
        self.fm_builder.add_flow_mod("insert", rule_type, "arp", match, action)

        for participant in self.config.peers.values():
            ### make sure ARP replies reach the participants
            for port in participant.ports:
                match = {"eth_type": ETH_TYPE_ARP, "eth_dst": port.mac}
                action = {"fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, "arp", match, action)

            ### direct gratuituous ARPs only to the respective participant
            i = 0
            for port in participant.ports:
                vmac = self.vmac_builder.part_port_match(participant.name, i, inbound_bit = False)
                vmac_mask = self.vmac_builder.part_port_mask(False)
                match = {"in_port": "arp",
                         "eth_type": ETH_TYPE_ARP,
                         "eth_dst": (vmac, vmac_mask)}
                action = {"set_eth_dst": MAC_BROADCAST, "fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, "arp", match, action)
                i += 1

        ### flood ARP requests that have gone through the arp switch, but only on non switch-switch ports
        match = {"in_port": "arp",
                 "eth_type": ETH_TYPE_ARP,
                 "eth_dst": MAC_BROADCAST}
        ports = []
        for participant in self.config.peers.values():
            for port in participant.ports:
                ports.append(port.id)
        ports.append(self.config.route_server.ports[0].id)

        action = {"fwd": ports}
        self.fm_builder.add_flow_mod("insert", rule_type, "arp_broadcast", match, action)

        ### forward all ARP requests to the arp switch
        match = {"eth_type": ETH_TYPE_ARP}
        action = {"fwd": ["arp"]}
        self.fm_builder.add_flow_mod("insert", rule_type, "arp_filter", match, action)

    def handle_ARP_in_arp(self, rule_type):
        ### direct ARP requests for VNHs to ARP proxy
        port = self.config.arp_proxy.ports[0]
        match = {"in_port": "main",
                 "eth_type": ETH_TYPE_ARP,
                 "arp_tpa": (str(self.config.vnhs.network), str(self.config.vnhs.netmask))}
        action = {"fwd": [port.id]}
        self.fm_builder.add_flow_mod("insert", rule_type, "vnh_arp", match, action)

        ### send all other ARP requests back
        match = {"eth_type": ETH_TYPE_ARP, "in_port": "main"}
        action = {"fwd": [OFPP_IN_PORT]}
        self.fm_builder.add_flow_mod("insert", rule_type, "default", match, action)

        ### send all ARP replies from the ARP proxy to the main switch
        match = {"eth_type": ETH_TYPE_ARP, "in_port": "arp proxy"}
        action = {"fwd": ["main"]}
        self.fm_builder.add_flow_mod("insert", rule_type, "default", match, action)

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
                    self.fm_builder.add_flow_mod("insert", rule_type, "outbound", match, action)

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
                    action = {"set_eth_dst": port.mac,
                              "fwd": [port.id]}
                    self.fm_builder.add_flow_mod("insert", rule_type, "output", match, action)

    def default_forwarding(self, rule_type):
        for participant in self.config.peers.values():
            ### default forwarding
            if not participant.inbound_rules:
                vmac = self.vmac_builder.next_hop_match(participant.name, False)
                vmac_mask = self.vmac_builder.next_hop_mask(False)
                port = participant.ports[0]
                match = {"eth_dst": (vmac, vmac_mask)}
                action = {"set_eth_dst": port.mac,
                          "fwd": [port.id]}
                self.fm_builder.add_flow_mod("insert", rule_type, "output", match, action)

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
                self.fm_builder.add_flow_mod("insert", "inbound", "inbound", match, action)

    def handle_inbound(self, rule_type):
        vmac = self.vmac_builder.only_first_bit()
        match = {"eth_dst": (vmac, vmac)}
        action = {"fwd": ["outbound"]}
        self.fm_builder.add_flow_mod("insert", rule_type, "inbound", match, action)

    def match_any_fwd(self, rule_type, dst):
        match = {}
        action = {"fwd": [dst]}
        self.fm_builder.add_flow_mod("insert", rule_type, "default", match, action)

    def delete_flow_rule(self, rule_type, cookie, cookie_mask):
        self.fm_builder.delete_flow_mod("remove", rule_type, cookie, cookie_mask)

    def start(self):
        self.logger.info('start')
        self.init_fabric()
        self.sender.send(self.fm_builder.get_msg())
        self.logger.info('sent flow mods to reference monitor')


class GSSmS(GSS):
    def __init__(self, sender, config):
        super(GSSmS, self).__init__(util.log.getLogger('GSSmS'), sender, config)

    def init_fabric(self):
        self.logger.info('init fabric')

        # MAIN SWITCH
        ## handle BGP traffic
        self.logger.info('create flow mods to handle BGP traffic')
        self.handle_BGP("main-in")

        ## handle ARP traffic
        self.logger.info('create flow mods to handle ARP traffic')
        self.handle_ARP_in_main("main-in")

        self.handle_ARP_in_arp("arp")

        ## handle all participant traffic depending on whether they specified inbound/outbound policies
        self.logger.info('create flow mods to handle participant traffic')
        ### outbound policies specified
        self.handle_participant_with_outbound("main-in")
        ### inbound policies specified
        self.handle_participant_with_inbound("main-in", True)
        ### default forwarding
        self.default_forwarding("main-in")

        ## break loop for packets with false VMACs
        self.break_loop()

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

    def break_loop(self):
        match = {"in_port": "inbound"}
        action = {}
        self.fm_builder.add_flow_mod("insert", "main-in", "loop", match, action)


class GSSmT(GSS):
    def __init__(self, sender, config):
        super(GSSmT, self).__init__(util.log.getLogger('GSSmT'), sender, config)

    def init_fabric(self):
        self.logger.info('init fabric')

        # MAIN-IN TABLE
        ## handle BGP traffic
        self.logger.info('create flow mods to handle BGP traffic')
        self.handle_BGP("main-in")

        ## handle ARP traffic
        self.logger.info('create flow mods to handle ARP traffic')
        self.handle_ARP_in_main("main-in")

        self.handle_ARP_in_arp("arp")

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


class GSSoS(GSS):
    def __init__(self, sender, config):
        super(GSSoS, self).__init__(util.log.getLogger('GSSoS'), sender, config)

    def init_fabric(self):
        self.logger.info('init fabric')

        # MAIN-IN TABLE
        # handle BGP traffic
        self.logger.info('create flow mods to handle BGP traffic')
        self.handle_BGP('main-in')

        # handle ARP traffic
        self.logger.info('create flow mods to handle ARP traffic')
        self.handle_ARP_in_main('main-in')

        self.handle_ARP_in_arp('arp')

        # handle all participant traffic depending on whether they specified inbound/outbound policies
        self.logger.info('create flow mods to handle participant traffic')
        # outbound policies specified
        self.handle_participant_with_outbound("main-in")
        # direct packets with inbound bit set to the inbound switch
        self.handle_inbound('main-in')
        # whatever doesn't match on any other rule, send to inbound switch
        self.match_any_fwd('main-in', 'main-out')

        # OUTBOUND SWITCH
        # whatever doesn't match on any other rule, send to inbound switch
        self.match_any_fwd('outbound', 'inbound')

        # INBOUND SWITCH
        # set the inbound bit to zero
        self.default_forwarding_inbound('inbound', 'main-out')
        # send all other packets to main
        self.match_any_fwd('inbound', 'main-out')

        # MAIN-OUT TABLE
        # inbound policies specified
        self.handle_participant_with_inbound('main-out', False)
        # default forwarding
        self.default_forwarding('main-out')
