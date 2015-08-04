#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from Queue import Queue

from ryu.ofproto import ether
from ryu.ofproto import inet

LOG = False

class MultiTableController():
    def __init__(self):
        self.datapath = None
        self.ofproto = None
        self.parser = None

        self.fm_queue = Queue()

        # TABLES
        self.MAIN_TABLE = 0
        self.OUTBOUND_TABLE = 1
        self.INBOUND_TABLE = 2
        self.ARP_BGP_TABLE = 3

        # PRIORITIES
        self.FLOW_MISS_PRIORITY = 0

        # COOKIES
        self.NO_COOKIE = 0

    def init_fabrc():    
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        # install table-miss flow entry
        if LOG:
            self.logger.info("INIT: installing flow miss rules")
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, self.NO_COOKIE, self.MAIN_TABLE, self.FLOW_MISS_PRIORITY, match, actions)
        self.add_flow(datapath, self.NO_COOKIE, self.OUTBOUND_TABLE, self.FLOW_MISS_PRIORITY, match, actions)
        self.add_flow(datapath, self.NO_COOKIE, self.INBOUND_TABLE, self.FLOW_MISS_PRIORITY, match, actions)
        self.add_flow(datapath, self.NO_COOKIE, self.ARP_BGP_TABLE, self.FLOW_MISS_PRIORITY, match, actions)

    def switch_connect(dp):
        self.datapath = dp

        self.init_fabric()

        if is_ready():
            while not self.fm_queue.empty():
                self.process_flow_mod(self.fm_queue.get())

    def switch_disconnect(dp):

    def process_flow_mod(fm):
        if not is_ready():
            self.fm_queue.put(fm)
        else:
           
    def packet_in():

    def is_ready():
        if self.datapath:
            return True
        return False

    def add_flow(self, datapath, cookie, table, priority, match, actions, instructions=[], buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        if actions:
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        else:
            inst = []

        if instructions is not None:
            inst.extend(instructions)
        
        cookie_mask = 0
        if (cookie <> 0):
            cookie_mask = self.cookie_mask
  
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, cookie=cookie, cookie_mask=cookie_mask, table_id=table, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, cookie=cookie, cookie_mask=cookie_mask, table_id=table, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

class MultiSwitchController():
    def __init__(self):
        self.datapaths = {}

    def switch_connect():

        if is_ready():
            while not self.fm_queue.empty():
                self.process_flow_mod(self.fm_queue.get())

    def switch_disconnect():

    def process_flow_mod():
        if not is_ready():
            self.fm_queue.put(fm)
        else:

    def packet_in():

    def is_ready():
        if "main" in self.datapaths and "inbound" in self.datapaths and "outbound" in self.datapaths:
            return True
        return False

class FlowMod():
    def __init__(self, origin, flow_mod):
        self.mod_types = ["insert", "remove"]
        self.rule_types = ["inbound", "outbound", "main"]
        self.flow_mod = {}

        if (!validate_flow_mod(origin, flow_mod)):
            raise FlowModValidationError(flow_mod)

    def get_flow_mod_msg():
        return self.flow_mod

    def validate_flow_mod(flow_mod):
        valid_fm = {}
        valid_fm["origin"] = int(origin)
        if "id" in flow_mod:
            valid_fm["id"] = int(flow_mod)
            if ("mod_type" in flow_mod and flow["mod_type"] in self.mod_types):
                valid_fm["mod_type"] = flow_mod["mod_type"]
                if ("rule_type" in flow_mod and flow["rule_type"] in self.rule_types):
                    valid_fm["rule_type"] = flow_mod["rule_type"]
                    if "match" in flow_mod:
                        valid_fm["match"] = validate_match(flow_mod["match"])
                    if "action" in flow_mod:
                        valid_fm["action"] = validate_action(flow_mod["action"])
                    if valid_fm["action"] and valid_fm["match"]:
                        self.flow_mod = valid_fm
                        return True
        return False

    def validate_match(matches):
        validated_matches = {}

        for match, value in matches.iteritems():
            if match == "ipv4_src":
                validated_matches[match] = value
                if "eth_type" not in validated_matches:
                    validated_matches["eth_type"] = ether.ETH_TYPE_IP
            elif match == "ipv4_dst":
                validated_matches[match] = value
                if "eth_type" not in validated_matches:
                    validated_matches["eth_type"] = ether.ETH_TYPE_IP
            elif match == "tcp_src":
                validated_matches[match] = value
                if "eth_type" not in validated_matches:
                    validated_matches["eth_type"] = ether.ETH_TYPE_IP
                if "ip_proto" not in validated_matches:
                    validated_matches["ip_proto"] = inet.IPPROTO_TCP
            elif match == "tcp_dst":
                validated_matches[match] = value
                if "eth_type" not in validated_matches:
                    validated_matches["eth_type"] = ether.ETH_TYPE_IP
                if "ip_proto" not in validated_matches:
                    validated_matches["ip_proto"] = inet.IPPROTO_TCP
            elif match == "udp_src":
                validated_matches[match] = value
                if "eth_type" not in validated_matches:
                    validated_matches["eth_type"] = ether.ETH_TYPE_IP
                if "ip_proto" not in validated_matches:
                    validated_matches["ip_proto"] = inet.IPPROTO_UDP
            elif match == "udp_dst":
                validated_matches[match] = value
                if "eth_type" not in validated_matches:
                    validated_matches["eth_type"] = ether.ETH_TYPE_IP
                if "ip_proto" not in validated_matches:
                    validated_matches["ip_proto"] = inet.IPPROTO_UDP
        return validated_matches

    def validate_action(actions):
        validated_actions = {}
        for action, value in actions.iteritems():
            if action == "fwd":
                validated_actions[action] = int(value)
        return validated_actions

class FlowModValidationError(Exception):
    def __init__(self, flow_mod):
        self.flow_mod = flow_mod
    def __str__(self):
        return repr(self.flow_mod) 
