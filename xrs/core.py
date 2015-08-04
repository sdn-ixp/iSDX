#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)

## RouteServer-specific imports
import json
from netaddr import *
from peer import peer as Peer

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

###
### Config Parser
###

def parse_config(config_file):

    # loading config file
    config = json.load(open(config_file, 'r'))

    '''
        Create RouteServer environment ...
    '''

    # create XRS object
    xrs = XRS()
    # TODO Make sure that we read this from the config file itself
    self.ah_socket = ('localhost', 6666)

    for participant_name in config:
        participant = config[participant_name]

        # adding asn and mappings
        asn = participant["ASN"]
        xrs.asn_2_participant[participant["ASN"]] = int(participant_name)
        xrs.participant_2_asn[int(participant_name)] = participant["ASN"]

        xrs.participant_2_port[int(participant_name)] = []
        xrs.participant_2_portip[int(participant_name)] = []
        xrs.participant_2_portmac[int(participant_name)] = []

        for i in range(0, len(participant["Ports"])):
            xrs.port_2_participant[participant["Ports"][i]['Id']] = int(participant_name)
            xrs.portip_2_participant[participant["Ports"][i]['IP']] = int(participant_name)
            xrs.portmac_2_participant[participant["Ports"][i]['MAC']] = int(participant_name)
            xrs.participant_2_port[int(participant_name)].append(participant["Ports"][i]['Id'])
            xrs.participant_2_portip[int(participant_name)].append(participant["Ports"][i]['IP'])
            xrs.participant_2_portmac[int(participant_name)].append(participant["Ports"][i]['MAC'])

        # adding ports and mappings
        ports = [{"ID": participant["Ports"][i]['Id'],
                     "MAC": participant["Ports"][i]['MAC'],
                     "IP": participant["Ports"][i]['IP']}
                     for i in range(0, len(participant["Ports"]))]

        peers_out = [peer for peer in participant["Peers"]]
        # TODO: Make sure this is not an insane assumption
        peers_in = peers_out

        # TODO: Add info about participants' event handler socket in the config file
        eh_socket = ('localhost', 5555)

        # create peer and add it to the route server environment
        xrs.participants[int(participant_name)] = XRSPeer(asn, ports, peers_in, peers_out, eh_socket)

    return xrs
