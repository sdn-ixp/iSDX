#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json

from netaddr import IPNetwork

''' Config Parser '''
class Config(object):
    def __init__(self, config_file):    
        self.mode = None

        self.vmac_mode = None
        self.vmac_options = None

        self.vnhs = None

        self.refmon = None

        self.flanc_auth = None

        self.route_server = None

        self.arp_proxy = None

        self.peers = {}

        # loading config file
        config = json.load(open(config_file, 'r'))
        
        # parse config
        self.parse_config(config)

    def parse_config(self, config):
        if "Mode" in config:
            self.mode = 0 if config["Mode"] == "Multi-Switch" else 1
        if "VMAC" in config:
            if "Mode" in config["VMAC"]:
                self.vmac_mode = 0 if config["VMAC"]["Mode"] == "MDS" else 1
            if "Options" in config["VMAC"]:
                self.vmac_options = config["VMAC"]["Options"]
        if "RefMon Server" in config:
            self.refmon = config["RefMon Server"]

        if "Flanc Auth Info" in config:
            self.flanc_auth = config["Flanc Auth Info"]

        if "VNHs" in config:
            self.vnhs = IPNetwork(config["VNHs"])

        if "Route Server" in config:
            self.route_server = Peer("RS", [Port(config["Route Server"]["Port"], config["Route Server"]["MAC"], config["Route Server"]["IP"])])

        if "ARP Proxy" in config:
            self.arp_proxy = Peer("ARP", [Port(config["ARP Proxy"]["Port"], config["ARP Proxy"]["MAC"], config["ARP Proxy"]["IP"])])

        if "Participants" in config:
            for participant_name, participant in config["Participants"].iteritems():
                participant_name = int(participant_name)
                if ("Inbound Rules" in participant):
                    inbound_rules = participant["Inbound Rules"]
                if ("Outbound Rules" in participant):
                    outbound_rules = participant["Outbound Rules"]
            
                if ("Ports" in participant):
                    ports = [Port(participant["Ports"][i]['Id'],
                              participant["Ports"][i]['MAC'],
                              participant["Ports"][i]['IP'])
                              for i in range(0, len(participant["Ports"]))]
                      
                self.peers[participant_name] = Participant(participant_name, ports, inbound_rules, outbound_rules)


class Peer(object):
     def __init__(self, name, ports):
         self.name = name
         self.ports = ports 

class Port(object):
     def __init__(self, id, mac, ip):
         self.id = id
         self.mac = mac
         self.ip = ip

class Participant(Peer):
     def __init__(self, name, ports, inbound_rules, outbound_rules):
         super(Participant, self).__init__(name, ports)
         self.inbound_rules = inbound_rules
         self.outbound_rules = outbound_rules
