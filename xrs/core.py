#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)

## RouteServer-specific imports
import json
from netaddr import *

###
### I(X)P (R)oute (S)erver (XRS) Class
###

class XRS():
    def __init__(self):
        self.server = None
        self.ah_socket = None
        self.participants = {}

        # Several useful mappings
        self.port_2_participant = {}
        self.participant_2_port = {}
        self.portip_2_participant = {}
        self.participant_2_portip = {}
        self.portmac_2_participant = {}
        self.participant_2_portmac = {}
        self.asn_2_participant = {}
        self.participant_2_asn = {}

###
### I(X)P (R)oute (S)erver (XRS) Peer Class
###

class XRSPeer():
    def __init__(self, asn, ports, peers_in, peers_out, eh_socket):
        self.asn = asn
        self.ports = ports
        self.peers_in = peers_in
        self.peers_out = peers_out
        self.eh_socket = eh_socket
