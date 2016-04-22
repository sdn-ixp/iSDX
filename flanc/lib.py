#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
import logging

from Queue import Queue

import os
import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log


from ofdpa20 import OFDPA20

# COOKIES
NO_COOKIE = 0


class Config(object):

    MULTISWITCH = 0
    MULTITABLE = 1
    ONESWITCH = 2

    def __init__(self, config_file):
        self.server = None

        self.mode = None
        self.ofdpa = set()
        self.ofv = None
        self.tables = None
        self.loops = None
        self.dpids = None
        self.dp_alias = []
        self.dpid_2_name = {}
        self.datapath_ports = None

        self.priorities = None

        self.datapaths = {}
        self.parser = None
        self.ofproto = None

        # loading config file
        config = json.load(open(config_file, 'r'))

        # read from file
        if "Mode" in config:
            if config["Mode"] == "Multi-Switch":
                self.mode = self.MULTISWITCH
            elif config["Mode"] == "Multi-Table":
                self.mode = self.MULTITABLE
            elif config["Mode"] == "One-Switch":
                self.mode = self.ONESWITCH
        if "RefMon Settings" in config:
            if "fabric options" in config["RefMon Settings"]:
                if "tables" in config["RefMon Settings"]["fabric options"]:
                    self.tables = config["RefMon Settings"]["fabric options"]["tables"]
                if "dpids" in config["RefMon Settings"]["fabric options"]:
                    self.dpids = config["RefMon Settings"]["fabric options"]["dpids"]
                    for k,v in self.dpids.iteritems():
                        self.dpid_2_name[v] = k
                if "loops" in config["RefMon Settings"]["fabric options"]:
                    self.loops = config["RefMon Settings"]["fabric options"]["loops"]
                if "dp alias" in config["RefMon Settings"]["fabric options"]:
                    self.dp_alias = config["RefMon Settings"]["fabric options"]["dp alias"]
                if "OF version" in config["RefMon Settings"]["fabric options"]:
                    self.ofv = config["RefMon Settings"]["fabric options"]["OF version"]
                if "ofdpa" in config["RefMon Settings"]["fabric options"]:
                    self.ofdpa = set(config["RefMon Settings"]["fabric options"]["ofdpa"])
            if "priorities" in config["RefMon Settings"]:
                self.priorities = config["RefMon Settings"]["priorities"]

            if "fabric connections" in config["RefMon Settings"]:
                self.datapath_ports = config["RefMon Settings"]["fabric connections"]

        if "RefMon Server" in config:
            self.server = config["RefMon Server"]
        else:
            raise InvalidConfigError(config)

        # check if valid config
        if self.isMultiSwitchMode():
            if not (self.ofv and self.dpids and self.datapath_ports):
                raise InvalidConfigError(config)
        elif self.isMultiTableMode():
            if not (self.ofv == "1.3" and self.tables and self.datapath_ports):
                raise InvalidConfigError(config)
        elif self.isOneSwitchMode():
            if not (self.ofv == "1.3" and self.loops):
                raise InvalidConfigError(config)
        else:
            raise InvalidConfigError(config)

    def isMultiSwitchMode(self):
        return self.mode == self.MULTISWITCH

    def isMultiTableMode(self):
        return self.mode == self.MULTITABLE

    def isOneSwitchMode(self):
        return self.mode == self.ONESWITCH


class InvalidConfigError(Exception):
    def __init__(self, flow_mod):
        self.flow_mod = flow_mod
    def __str__(self):
        return repr(self.flow_mod)


class MultiTableController(object):
    def __init__(self, config):
        self.config = config
        self.logger = util.log.getLogger('MultiTableController')
        self.logger.info('mt_ctrlr: creating an instance of MultiTableController')

        self.message_queue = Queue()

    def init_fabric(self):
        # install table-miss flow entry
        self.logger.info("mt_ctrlr: init fabric")
        match = self.config.parser.OFPMatch()
        actions = [self.config.parser.OFPActionOutput(self.config.ofproto.OFPP_CONTROLLER, self.config.ofproto.OFPCML_NO_BUFFER)]
        instructions = [self.config.parser.OFPInstructionActions(self.config.ofproto.OFPIT_APPLY_ACTIONS, actions)]

        for name, table_properties in self.config.tables.iteritems():
            table_id = table_properties["id"]

            mod = self.config.parser.OFPFlowMod(datapath=self.config.datapaths["main"],
                                                cookie=NO_COOKIE, cookie_mask=1,
                                                table_id=table_id,
                                                command=self.config.ofproto.OFPFC_ADD,
                                                priority=self.config.priorities[name]["flow_miss"],
                                                match=match, instructions=instructions)
            self.config.datapaths["main"].send_msg(mod)

        mod = self.config.parser.OFPFlowMod(datapath=self.config.datapaths["arp"],
                                            cookie=NO_COOKIE, cookie_mask=1,
                                            command=self.config.ofproto.OFPFC_ADD,
                                            priority=self.config.priorities["arp"]["flow_miss"],
                                            match=match, instructions=instructions)
        self.config.datapaths["arp"].send_msg(mod)

    def switch_connect(self, dp):
        dp_name = self.config.dpid_2_name[dp.id]

        self.config.datapaths[dp_name] = dp

        if self.config.ofproto is None:
            self.config.ofproto = dp.ofproto
        if self.config.parser is None:
            self.config.parser = dp.ofproto_parser

        self.logger.info('mt_ctrlr: switch connect: ' + dp_name)

        if self.is_ready():
            self.init_fabric()

            while not self.message_queue.empty():
                self.process_ofp_message(self.message_queue.get())

    def switch_disconnect(self, dp):
        if dp.id in self.config.dpid_2_name:
            dp_name = self.config.dpid_2_name[dp.id]
            self.logger.info('mt_ctrlr: switch disconnect: ' + dp_name)
            del self.config.datapaths[dp_name]

    def process_ofp_message(self, ofp_message, queue=True):
        if not self.is_ready():
            if queue:
                self.message_queue.put(ofp_message)
        else:
            mod = ofp_message.get_ofp_message()

            print str(mod)

            self.config.datapaths[ofp_message.get_dst_dp()].send_msg(mod)

    def packet_in(self, ev):
        self.logger.info("mt_ctrlr: packet in")

    def is_ready(self):
        if len(self.config.datapaths) == len(self.config.dpids):
            return True
        return False

    def send_barrier_request(self):
        request = self.config.parser.OFPBarrierRequest(self.config.datapaths["main"])
        self.config.datapaths["main"].send_msg(request)

    def handle_barrier_reply(self, datapath):
        if self.config.datapaths["main"] == datapath:
            return True
        return False


class MultiSwitchController(object):
    def __init__(self, config):
        self.logger = util.log.getLogger('MultiSwitchController')
        self.logger.info('ms_ctrlr: creating an instance of MultiSwitchController')

        self.datapaths = {}
        self.config = config

        self.message_queue = Queue()
        self.last_command_type = {}

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

            while not self.message_queue.empty():
                self.process_ofp_message(self.message_queue.get())

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

        for name, datapath in self.config.datapaths.iteritems():
            if self.config.ofv == "1.3":
                mod = self.config.parser.OFPFlowMod(datapath=datapath,
                                                    cookie=NO_COOKIE, cookie_mask=3,
                                                    command=self.config.ofproto.OFPFC_ADD,
                                                    priority=self.config.priorities[name]["flow_miss"],
                                                    match=match, instructions=instructions)
            else:
                mod = self.config.parser.OFPFlowMod(datapath=datapath,
                                                    cookie=NO_COOKIE,
                                                    command=self.config.ofproto.OFPFC_ADD,
                                                    priority=self.config.priorities[name]["flow_miss"],
                                                    match=match, actions=actions)
            datapath.send_msg(mod)

    def process_ofp_message(self, ofp_message, queue=True):
        if not self.is_ready():
            if queue:
                self.message_queue.put(ofp_message)
        else:
            dp = self.config.datapaths[ofp_message.get_dst_dp()]
            if self.config.dpid_2_name[dp.id] in self.config.ofdpa:
                ofdpa = OFDPA20(self.config)
                message, group_mods = ofp_message.get_flow_and_group_mods(self.config)
                for gm in group_mods:
                    if not ofdpa.is_group_mod_installed_in_switch(dp, gm):
                        dp.send_msg(gm)
                        ofdpa.mark_group_mod_as_installed(dp, gm)
            else:
                message = ofp_message.get_ofp_message()
            if (not dp.id in self.last_command_type or (self.last_command_type[dp.id] != message.command)):
                self.logger.info('refmon: sending barrier')
                self.last_command_type[dp.id] = message.command
                dp.send_msg(self.config.parser.OFPBarrierRequest(dp))
            dp.send_msg(message)

    def packet_in(self, ev):
        pass

    def is_ready(self):
        if len(self.config.datapaths) == len(self.config.dpids) or self.config.always_ready:
            return True
        return False

    def send_barrier_request(self):
        if self.is_ready():
            dp = self.config.datapaths["outbound"]
            request = self.config.parser.OFPBarrierRequest(dp)
            dp.send_msg(request)
            return True
        else:
            return False

    def handle_barrier_reply(self, datapath):
        if self.config.datapaths["outbound"] == datapath:
            return True
        return False


class OneSwitchController(object):
    def __init__(self, config):
        self.config = config
        self.logger = util.log.getLogger('OneSwitchController')
        self.logger.info('os_ctrlr: creating an instance of OneSwitchController')

        self.message_queue = Queue()

    def init_fabric(self):
        # install table-miss flow entry
        self.logger.info("os_ctrlr: init fabric")
        match = self.config.parser.OFPMatch()
        actions = [self.config.parser.OFPActionOutput(self.config.ofproto.OFPP_CONTROLLER,
                                                      self.config.ofproto.OFPCML_NO_BUFFER)]
        instructions = [self.config.parser.OFPInstructionActions(self.config.ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = self.config.parser.OFPFlowMod(datapath=self.config.datapaths["main"],
                                            cookie=NO_COOKIE, cookie_mask=1,
                                            command=self.config.ofproto.OFPFC_ADD,
                                            priority=self.config.priorities["main-in"]["flow_miss"],
                                            match=match, instructions=instructions)
        self.config.datapaths["main"].send_msg(mod)

        match = self.config.parser.OFPMatch(in_port=self.config.loops["main-out"][1])
        mod = self.config.parser.OFPFlowMod(datapath=self.config.datapaths["main"],
                                            cookie=NO_COOKIE, cookie_mask=1,
                                            command=self.config.ofproto.OFPFC_ADD,
                                            priority=self.config.priorities["main-out"]["flow_miss"],
                                            match=match, instructions=instructions)
        self.config.datapaths["main"].send_msg(mod)

        match = self.config.parser.OFPMatch()
        mod = self.config.parser.OFPFlowMod(datapath=self.config.datapaths["arp"],
                                            cookie=NO_COOKIE, cookie_mask=1,
                                            command=self.config.ofproto.OFPFC_ADD,
                                            priority=self.config.priorities["arp"]["flow_miss"],
                                            match=match, instructions=instructions)

        self.config.datapaths["arp"].send_msg(mod)

    def switch_connect(self, dp):
        dp_name = self.config.dpid_2_name[dp.id]

        self.config.datapaths[dp_name] = dp

        if self.config.ofproto is None:
            self.config.ofproto = dp.ofproto
        if self.config.parser is None:
            self.config.parser = dp.ofproto_parser

        self.logger.info('os_ctrlr: switch connect: ' + dp_name)

        if self.is_ready():
            self.init_fabric()

            while not self.message_queue.empty():
                self.process_ofp_message(self.message_queue.get())

    def switch_disconnect(self, dp):
        if dp.id in self.config.dpid_2_name:
            dp_name = self.config.dpid_2_name[dp.id]
            self.logger.info('os_ctrlr: switch disconnect: ' + dp_name)
            del self.config.datapaths[dp_name]

    def process_ofp_message(self, ofp_message, queue=True):
        if not self.is_ready():
            if queue:
                self.message_queue.put(ofp_message)
        else:
            mod = ofp_message.get_ofp_message()
            self.config.datapaths[ofp_message.get_dst_dp()].send_msg(mod)

    def packet_in(self, ev):
        self.logger.info("os_ctrlr: packet in")

    def is_ready(self):
        if len(self.config.datapaths) == len(self.config.dpids):
            return True
        return False

    def send_barrier_request(self):
        request = self.config.parser.OFPBarrierRequest(self.config.datapaths["main"])
        self.config.datapaths["main"].send_msg(request)

    def handle_barrier_reply(self, datapath):
        if self.config.datapaths["main"] == datapath:
            return True
        return False
