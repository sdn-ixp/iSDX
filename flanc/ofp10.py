#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from ryu.ofproto import ether
from ryu.ofproto import inet

class FlowMod(object):
    def __init__(self, config, origin, flow_mod):
        self.mod_types = ["insert", "remove"]
        self.rule_types = ["inbound", "outbound", "main", "main-in", "main-out"]
        
        self.config = config
        self.parser = None

        self.mod_type = None
        self.rule_type = None

        self.origin = origin
        self.datapath = None
        self.priority = None
        self.cookie = None
        self.matches = {}
        self.actions = []

        self.validate_flow_mod(flow_mod)

    def get_flow_mod_msg(self):
        return self.flow_mod

    def validate_flow_mod(self, flow_mod):
        if "id" in flow_mod:
            self.cookie = int('{0:08b}'.format(int(self.origin))+'{0:08b}'.format(int(flow_mod["id"])),2)
            if ("mod_type" in flow_mod and flow_mod["mod_type"] in self.mod_types):
                self.mod_type = flow_mod["mod_type"]
                if ("rule_type" in flow_mod and flow_mod["rule_type"] in self.rule_types):
                    if flow_mod["rule_type"] in self.config.dp_alias:
                        self.rule_type = self.config.dp_alias[flow_mod["rule_type"]]
                    else:
                        self.rule_type = flow_mod["rule_type"]

                    if ("priority" in flow_mod):
                        self.priority = flow_mod["priority"]
                        if "match" in flow_mod:
                            self.match = self.validate_match(flow_mod["match"])
                        if "action" in flow_mod:
                            self.actions = self.validate_action(flow_mod["action"])

    def validate_match(self, matches):
        validated_matches = {}

        for match, value in matches.iteritems():

            if match == "eth_type":
                validated_matches["dl_type"] = value
            elif match == "in_port":
                if isinstance( value, int ) or value.isdigit():
                    validated_matches["in_port"] = value
                else:
                    if self.rule_type in self.config.datapath_ports and value in self.config.datapath_ports[self.rule_type]:
                        validated_matches["in_port"] = self.config.datapath_ports[self.rule_type][value]
            elif match == "arp_tpa":
                validated_matches[match] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_ARP
            elif match == "eth_dst":
                validated_matches["dl_dst"] = value
            elif match == "eth_src":
                validated_matches["dl_src"] = value
            elif match == "ipv4_src":
                validated_matches["nw_src"] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_IP
            elif match == "ipv4_dst":
                validated_matches["nw_dst"] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_IP
            elif match == "tcp_src":
                validated_matches["tp_src"] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_IP
                if "nw_proto" not in validated_matches:
                    validated_matches["nw_proto"] = inet.IPPROTO_TCP
            elif match == "tcp_dst":
                validated_matches["tp_dst"] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_IP
                if "nw_proto" not in validated_matches:
                    validated_matches["nw_proto"] = inet.IPPROTO_TCP
            elif match == "udp_src":
                validated_matches["tp_src"] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_IP
                if "nw_proto" not in validated_matches:
                    validated_matches["nw_proto"] = inet.IPPROTO_UDP
            elif match == "udp_dst":
                validated_matches["tp_dst"] = value
                if "dl_type" not in validated_matches:
                    validated_matches["dl_type"] = ether.ETH_TYPE_IP
                if "nw_proto" not in validated_matches:
                    validated_matches["nw_proto"] = inet.IPPROTO_UDP
        return validated_matches

    def make_actions(self):
        temp_actions = []

        for action, value in self.actions.iteritems():
            if action == "fwd":
                for port in value:
                    if isinstance( port, int ) or port.isdigit():
                        temp_actions.append(self.parser.OFPActionOutput(int(port)))
                    else:
                        if port in self.config.dp_alias:
                            port = self.config.dp_alias[port]
                        temp_actions.append(self.parser.OFPActionOutput(self.config.datapath_ports[self.rule_type][port]))
            elif action == "set_eth_src":
                temp_actions.append(self.parser.OFPActionSetDlSrc(str(value)))
            elif action == "set_eth_dst":
                temp_actions.append(self.parser.OFPActionSetDlDst(str(value)))

        return temp_actions

    def validate_action(self, actions):
        validated_actions = {}

        for action, value in actions.iteritems():
            if action == "fwd":
                temp_fwds = []
                for val in value:
                    if isinstance( val, int ) or val.isdigit():
                        if val == 0xfffffffb:
                            val = 0xffb 
                        temp_fwds.append(int(val))
                    elif val in self.rule_types:
                        temp_fwds.append(val)
                validated_actions[action] = temp_fwds
            elif action == "set_eth_src":
                validated_actions[action] = value
            elif action == "set_eth_dst":
                validated_actions[action] = value
        return validated_actions

    def get_flow_mod(self, config):
        self.config = config
        self.parser = config.parser

        match = self.parser.OFPMatch(**self.matches)

        datapath = self.config.datapaths[self.rule_type]

        if self.mod_type == "insert":
            actions = self.make_actions()
            return self.parser.OFPFlowMod(datapath=datapath, 
                                          match=match, 
                                          cookie=self.cookie, 
                                          command=self.config.ofproto.OFPFC_ADD, 
                                          priority=self.priority, actions=actions)
        else:
            return self.parser.OFPFlowMod(datapath=datapath, 
                                          match=match, 
                                          cookie=self.cookie,
                                          command=self.config.ofproto.OFPFC_DELETE, 
                                          out_group=self.config.ofproto.OFPG_ANY, 
                                          out_port=self.config.ofproto.OFPP_ANY)

    def get_dst_dp(self):
        return self.rule_type 
