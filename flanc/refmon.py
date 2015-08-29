#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import os
import logging

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER 
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0, ofproto_v1_3
# REST API from ryu.app.wsgi import WSGIApplication
from ryu import cfg

from lib import MultiSwitchController, MultiTableController, Config, InvalidConfigError
from ofp10 import FlowMod as OFP10FlowMod
from ofp13 import FlowMod as OFP13FlowMod

# REST API from rest import FlowModReceiver

from server import Server

LOG = False

class RefMon(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_3.OFP_VERSION]
    # REST API _CONTEXTS = { 'wsgi': WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(RefMon, self).__init__(*args, **kwargs)

        # Used for REST API
        #wsgi = kwargs['wsgi']
        #wsgi.register(FlowModReceiver, self)

        self.logger = logging.getLogger('ReferenceMonitor')
        self.logger.info('refmon: start')

        # retrieve command line arguments
        CONF = cfg.CONF
        config_file_path = CONF['refmon']['config']

        config_file = os.path.abspath(config_file_path)

        # load config from file
        self.logger.info('refmon: load config')
        try:
            self.config = Config(config_file)
        except InvalidConfigError as e:
            self.logger.info('refmon: invalid config '+str(e))

        # start controller
        if (self.config.mode == 0):
            self.controller = MultiSwitchController(self.config)
        elif (self.config.mode == 1):
            self.controller = MultiTableController(self.config)

        # start server receiving flowmod requests
        self.server = Server(self, self.config.server["IP"], self.config.server["Port"], self.config.server["key"])
        self.server.start()

    def close(self):
        self.logger.info('refmon: stop')

        #self.server.stop()

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def dp_state_change_handler(self, ev):
        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:
            self.controller.switch_connect(datapath)
        elif ev.state == DEAD_DISPATCHER:
            self.controller.switch_disconnect(datapath)
        
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        self.controller.packet_in(ev)

    def process_flow_mods(self, msg):
        self.logger.info('refmon: received flowmod request')

        # authorization
        if "auth_info" in msg:
            auth_info = msg["auth_info"]

            # TODO: FLANC authorization here
           
            origin = auth_info["participant"]

            if "flow_mods" in msg:
                self.logger.info('refmon: process ' + str(len(msg["flow_mods"])) + ' flowmods from ' + str(origin))
                for flow_mod in msg["flow_mods"]:
                    if self.config.ofv == "1.0":
                        fm = OFP10FlowMod(self.config, origin, flow_mod)
                    elif self.config.ofv == "1.3":
                        fm = OFP13FlowMod(self.config, origin, flow_mod)

                    self.controller.process_flow_mod(fm)

