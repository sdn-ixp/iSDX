#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import os

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER 
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import WSGIApplication
from ryu import cfg

from lib import MultiSwitchController, MultiTableController, FlowMod
from rest import RESTHandler

LOG = False

class RefMon(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION, ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = { 'wsgi': WSGIApplication }

    def __init__(self, *args, **kwargs):
        super(RefMon, self).__init__(*args, **kwargs)

        # register REST API handler
        wsgi = kwargs['wsgi']
        wsgi.register(RESTHandler, self)

        # retrieve command line arguments
        CONF = cfg.CONF
        mode = CONF['refmon']['mode']
        controller = CONF['refmon']['instance']

        if (mode == 0):
            self.controller = MultiSwitchController()
        elif (mode == 1):
            self.controller = MultiTableController()

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
                        fm = FlowMod(origin, flow_mod)
                    except FlowModValidationError as e:
                        return e

                    self.controller.process_flow_mod(fm)
