## RouteServer-specific imports
import json
from netaddr import *
from peer import peer as Peer

###
### Extended Route Server Object
###

class XRS():
    def __init__(self):
        self.server = None
        self.participants = {}
        self.port_2_participant = {}
        self.participant_2_port = {}
        self.portip_2_participant = {}
        self.participant_2_portip = {}
        self.portmac_2_participant = {}
        self.participant_2_portmac = {}
        self.asn_2_participant = {}
        self.participant_2_asn = {}
        self.supersets = []

        self.num_VNHs_in_use = 0
        
        self.VNH_2_prefix = {}
        self.prefix_2_VNH = {}
        
        # put it in external config file
        self.superset_threshold = 10
        
        self.max_superset_size = 30
        self.best_path_size = 12
        
        self.VMAC_size = 48
        
        self.rest_api_url = 'http://localhost:8080/asdx/supersets'
        
        self.VNHs = IPNetwork('172.0.1.1/24')
        
###
### Extended Route Server primary functions
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
        
        peers_in = participant["Peers"]
        
        # create peer and add it to the route server environment
        xrs.participants[int(participant_name)] = Peer(asn, ports, peers_in, peers_out[int(participant_name)])
    
    return xrs
