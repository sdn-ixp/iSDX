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

        self.peers = {}

        # loading config file
        config = json.load(open(config_file, 'r'))
        
        # parse config
        self.parse_config(config)

    def parse_config(self, config)
        if "Mode" in config:
            self.mode = 0 if config["Mode"] == "Multi-Switch" else 1
        if "VMAC" in config:
            if "Mode" in config["VMAC"]:
                self.vmac_mode = 0 if config["VMAC"]["Mode"] == "MDS" else 1
            if "Options" in config["VMAC"]:
                self.vmac_options = config["VMAC"]["Options"]
        if "RefMon Server" in config:
            self.refmon = config["RefMon Server"]

        if "VNHs" in config:
            self.vnhs = IPNetwork(config["VNHs"])

        if "Route Server" in config:
            if "Ports" in config["Route Server"]:
                port = config["Route Server"]["Ports"][0] 
                self.peers["RS"] = Peer("RS", Port(port["Id"], port["MAC"], port["IP"])

        if "ARP Proxy" in config:
            if "Ports" in config["ARP Proxy"]:
                port = config["ARP Proxy"]["Ports"][0]
                self.peers["ARP"] = Peer("ARP", Port(port["Id"], port["MAC"], port["IP"])

        if "Participants" in config:
            for participant_name in config["Participants"]:        
                participant = config[participant_name]
        
                if ("Inbound Rules" in participant):
                    inbound_rules = participant["Inbound Rules"]
                if ("Outbound Rules" in participant):
                    inbound_rules = participant["Outbound Rules"]
            
                if ("Ports" in participant)
                    ports = [Port(participant["Ports"][i]['Id'],
                              "MAC": participant["Ports"][i]['MAC'],
                              "IP": participant["Ports"][i]['IP'])
                              for i in range(0, len(participant["Ports"]))]
                      
                self.peers[participant_name)] = Participant(participant_name, ports, inbound_rules, outbound_rules)


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
