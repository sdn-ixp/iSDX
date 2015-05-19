#!/usr/bin/env python

import os
import json
import sys
import argparse

from threading import Thread,Event
from server import server as Server
from core import parse_config, XRS
from decision_process import decision_process
from lib import vnh_assignment, update_sdx_controller
from supersets import update_supersets
from bgp_interface import bgp_update_peers
from arp_proxy import arp_proxy

class route_server():
    
    def __init__(self, config_file):
        print "Initialize the Route Server"
    
        # Init the Route Server
        ## Parse Config
        self.xrs = parse_config(config_file)
        
        self.xrs.server = Server()
        
        # Start arp proxy
        self.sdx_ap = arp_proxy(self.xrs)
        ap_thread = Thread(target=self.sdx_ap.start)
        ap_thread.start()
        
    def start(self):
        print "Start Server"
        self.xrs.server.start()
    
        while True:
            # get BGP messages from ExaBGP via stdin
            route = self.xrs.server.receiver_queue.get()
            route = json.loads(route)
                
            # process route advertisements - add/remove routes to/from rib of respective participant (neighbor)
            updates = None
            
            if ('neighbor' in route):
                if ('ip' in route['neighbor']):
                    updates = self.xrs.participants[self.xrs.portip_2_participant[route['neighbor']['ip']]].update(route)
            elif ('notification' in route):
                for participant in self.xrs.participants:
                    self.xrs.participants[participant].process_notification(route)
            
            if updates is not None:
                # update local ribs - select best route for each prefix
                for update in updates:
                    decision_process(self.xrs.participants,update)
            
                # assign VNHs
                vnh_assignment(updates, self.xrs)
            
                # update supersets
                sdx_msgs = update_supersets(updates, self.xrs)
            
                # send supersets to SDX controller
                update_sdx_controller(sdx_msgs, self.xrs.rest_api_url)
            
                # BGP updates
                changes = bgp_update_peers(updates, self.xrs)
            
                # Send Gratuitous ARPs
                if changes:
                    for change in changes:
                        self.sdx_ap.send_gratuitous_arp(change)
            
        ap_thread.join()
        
def usage():
    print "Options:"
    print "     -d / --dir      Specify the directory where the example resides"
    
''' main '''    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    args = parser.parse_args() 

    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","examples",args.dir,"controller","sdx_config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")
    
    # start route server    
    sdx_rs = route_server(config_file)
    sdx_rs.start
    rs_thread = Thread(target=sdx_rs.start)
    rs_thread.start()
    
    rs_thread.join()
    
