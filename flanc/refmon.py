#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import os

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER 
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import WSGIApplication
from ryu import cfg

from lib import MultiSwitchController, MultiTableController, Config, InvalidConfigError
from ofp10 import FlowMod as OFP10FlowMod, FlowModValidationError
from ofp13 import FlowMod as OFP13FlowMod

LOG = False

class RefMon(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(RefMon, self).__init__(*args, **kwargs)

        # retrieve command line arguments
        CONF = cfg.CONF
        config_file_path = CONF['refmon']['config']

        config_file = os.path.abspath(config_file_path)

        # load config from file
        try:
            self.config = Config(config_file)
        except InvalidConfigError as e:
            print "Invalid Config:\n"+e

        # start controller
        if (self.config.mode == 0):
            self.controller = MultiSwitchController(config)
        elif (self.config.mode == 1):
            self.config.controller = MultiTableController(config)

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
        # authorization
        if "auth_info" in msg:
            auth_info = msg["auth_info"]

            # TODO: FLANC authorization here
           
            origin = auth_info["participant"]

            if "flow_mods" in msg:
                for flow_mod in msg["flow_mods"]:
                    try:
                        if self.config.ofv = "1.0":
                            fm = OFP10FlowMod(origin, flow_mod)
                        elif self.config.ofv = "1.3":
                            fm = OFP13FlowMod(origin, flow_mod)
                    except FlowModValidationError as e:
                        return e

                    self.controller.process_flow_mod(fm)
