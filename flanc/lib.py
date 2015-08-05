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
