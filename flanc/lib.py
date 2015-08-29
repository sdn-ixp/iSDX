#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
import logging

from Queue import Queue

from ryu.ofproto import ether
from ryu.ofproto import inet

# PRIORITIES
FLOW_MISS_PRIORITY = 0

# COOKIES
NO_COOKIE = 0

class Config(object):
    def __init__(self, config_file):
        self.server = None

        self.mode = None
        self.ofv = None
        self.tables = None
        self.dpids = None
        self.dp_alias = []
        self.dpid_2_name = {}
        self.datapath_ports = None

        self.datapaths = {}
        self.parser = None
        self.ofproto = None

        # loading config file
        config = json.load(open(config_file, 'r'))

        # read from file
        if "Mode" in config:
            if config["Mode"] == "Multi-Switch":
                self.mode = 0
            elif config["Mode"] == "Multi-Table":
                self.mode = 1
        if "RefMon Settings" in config:
            if "fabric options" in config["RefMon Settings"]:
                if self.mode == 1 and "tables" in config["RefMon Settings"]["fabric options"]:
                    self.tables = config["RefMon Settings"]["fabric options"]["tables"]
                if self.mode == 0 and "dpids" in config["RefMon Settings"]["fabric options"]:
                    self.dpids = config["RefMon Settings"]["fabric options"]["dpids"]
                    for k,v in self.dpids.iteritems():
                        self.dpid_2_name[v] = k
                if "dp alias" in config["RefMon Settings"]["fabric options"]:
                    self.dp_alias = config["RefMon Settings"]["fabric options"]["dp alias"]
                if "OF version" in config["RefMon Settings"]["fabric options"]:
                    self.ofv = config["RefMon Settings"]["fabric options"]["OF version"]

            if "fabric connections" in config["RefMon Settings"]:
                self.datapath_ports = config["RefMon Settings"]["fabric connections"]

        if "RefMon Server" in config:
            self.server = config["RefMon Server"]
        else:
            raise InvalidConfigError(config)

        # check if valid config
        if self.mode == 0:
            if not (self.ofv and self.dpids and self.datapath_ports):
                raise InvalidConfigError(config)
        elif self.mode == 1:
            if not (self.ofv == "1.3" and self.tables and self.datapath_ports):
                raise InvalidConfigError(config)
        else:
            raise InvalidConfigError(config)

class InvalidConfigError(Exception):
    def __init__(self, flow_mod):
        self.flow_mod = flow_mod
    def __str__(self):
        return repr(self.flow_mod)

class MultiTableController():
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('MultiTableController')
        self.logger.info('mt_ctrlr: creating an instance of MultiTableController')

        self.fm_queue = Queue()

    def init_fabric(self):    
        # install table-miss flow entry
        self.logger.info("mt_ctrlr: init fabric")
        match = self.config.parser.OFPMatch()
        actions = [self.config.parser.OFPActionOutput(self.config.ofproto.OFPP_CONTROLLER, self.config.ofproto.OFPCML_NO_BUFFER)]
        instructions = [self.config.parser.OFPInstructionActions(self.config.ofproto.OFPIT_APPLY_ACTIONS, actions)]

        for table in self.config.tables.values():
            mod = self.config.parser.OFPFlowMod(datapath=self.config.datapaths["main"], 
                                                cookie=NO_COOKIE, cookie_mask=1, 
                                                table_id=table, 
                                                command=self.config.ofproto.OFPFC_ADD, 
                                                priority=FLOW_MISS_PRIORITY, 
                                                match=match, instructions=instructions)
            self.config.datapaths["main"].send_msg(mod)

    def switch_connect(self, dp):
        self.config.datapaths["main"] = dp
        self.config.ofproto = dp.ofproto
        self.config.parser = dp.ofproto_parser
        self.logger.info("mt_ctrlr: main switch connected")
        self.init_fabric()

        if self.is_ready():
            while not self.fm_queue.empty():
                self.process_flow_mod(self.fm_queue.get())

    def switch_disconnect(self, dp):
        if self.config.datapaths["main"] == dp:
            self.logger.info("mt_ctrlr: main switch disconnected")
            del self.config.datapaths["main"]

    def process_flow_mod(self, fm):
        if not self.is_ready():
            self.fm_queue.put(fm)
        else:
            mod = fm.get_flow_mod(self.config)
            self.config.datapaths["main"].send_msg(mod)
           
    def packet_in(self, ev):
        self.logger.info("mt_ctrlr: packet in")

    def is_ready(self):
        if "main" in self.config.datapaths:
            return True
        return False

class MultiSwitchController(object):
    def __init__(self, config):
        self.logger = logging.getLogger('MultiSwitchController')
        self.logger.info('ms_ctrlr: creating an instance of MultiSwitchController')

        self.datapaths = {}
        self.config = config

        self.fm_queue = Queue()

    def switch_connect(self, dp):
        dp_name = self.config.dpid_2_name[dp.id]

        self.config.datapaths[dp_name] = dp

        if self.config.ofproto is None:
            self.config.ofproto = dp.ofproto
        if self.config.parser is None:
            self.config.parser = dp.ofproto_parser

        self.logger.info('ms_ctrlr: switch connect: ' + dp_name)

        if self.is_ready():
            self.init_fabric()

            while not self.fm_queue.empty():
                self.process_flow_mod(self.fm_queue.get())

    def switch_disconnect(self, dp):
        if dp.id in self.config.dpid_2_name:
            dp_name = self.config.dpid_2_name[dp.id]
            self.logger.info('ms_ctrlr: switch disconnect: ' + dp_name)
            del self.config.datapaths[dp_name]

    def init_fabric(self):
        # install table-miss flow entry
        self.logger.info('ms_ctrlr: init fabric')
        match = self.config.parser.OFPMatch()

        if self.config.ofv  == "1.3":
            actions = [self.config.parser.OFPActionOutput(self.config.ofproto.OFPP_CONTROLLER, self.config.ofproto.OFPCML_NO_BUFFER)]
            instructions = [self.config.parser.OFPInstructionActions(self.config.ofproto.OFPIT_APPLY_ACTIONS, actions)]
        else:
            actions = [self.config.parser.OFPActionOutput(self.config.ofproto.OFPP_CONTROLLER)]

        for datapath in self.config.datapaths.values():
            if self.config.ofv  == "1.3":
                mod = self.config.parser.OFPFlowMod(datapath=datapath, 
                                                    cookie=NO_COOKIE, cookie_mask=3, 
                                                    command=self.config.ofproto.OFPFC_ADD, 
                                                    priority=FLOW_MISS_PRIORITY, 
                                                    match=match, instructions=instructions)
            else:
                mod = self.config.parser.OFPFlowMod(datapath=datapath, 
                                                    cookie=NO_COOKIE, 
                                                    command=self.config.ofproto.OFPFC_ADD, 
                                                    priority=FLOW_MISS_PRIORITY, 
                                                    match=match, actions=actions)
            datapath.send_msg(mod)

    def process_flow_mod(self, fm):
        if not self.is_ready():
            self.fm_queue.put(fm)
        else:
            mod = fm.get_flow_mod(self.config)
            self.config.datapaths[fm.get_dst_dp()].send_msg(mod)

    def packet_in(self, ev):
        pass

    def is_ready(self):
        if len(self.config.datapaths) > 2:
            return True
        return False
