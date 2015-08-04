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
        self.asn_2_participant = {}
        self.participant_2_asn = {}
        self.participants = {}

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

    peers_out = {}
    for participant_name in config:
        participant = config[participant_name]

        for peer in participant["Peers"]:
            if (peer not in peers_out):
                peers_out[peer] = []
            peers_out[peer].append(int(participant_name))

    # TODO: Make sure this is not an insane assumption
    peers_in = peers_out

    for participant_name in config:
        participant = config[participant_name]

        # adding asn and mappings
        asn = participant["ASN"]
        xrs.asn_2_participant[participant["ASN"]] = int(participant_name)
        xrs.participant_2_asn[int(participant_name)] = participant["ASN"]

        # adding ports and mappings
        ports = [{"ID": participant["Ports"][i]['Id'],
                     "MAC": participant["Ports"][i]['MAC'],
                     "IP": participant["Ports"][i]['IP']}
                     for i in range(0, len(participant["Ports"]))]

        # TODO: Add info about participants' event handler socket in the config file
        eh_socket = ('localhost', 5555)

        # create peer and add it to the route server environment
        xrs.participants[int(participant_name)] = XRSPeer(asn, ports, peers_in, peers_out, eh_socket)

    return xrs
