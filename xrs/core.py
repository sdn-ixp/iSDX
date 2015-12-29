#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)


from collections import namedtuple

###
### I(X)P (R)oute (S)erver (XRS) Class
###

class XRS(object):
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

XRSPeer = namedtuple('XRSPeer', 'asn ports peers_in peers_out eh_socket')
