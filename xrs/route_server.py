#!/usr/bin/env python

import os
import json
import sys
import argparse
import time

import Queue
from threading import Thread,Event
from server import server as Server
from core import parse_config, XRS
from decision_process import decision_process
from lib import vnh_assignment, update_sdx_controller
from supersets import update_supersets
from bgp_interface import bgp_update_peers
from arp_proxy import arp_proxy

LOG = False

class route_server():
    
    def __init__(self, config_file):
        print "Initialize the Route Server"
    
        # Init the Route Server
        ## Parse Config
        self.xrs = parse_config(config_file)
        
        self.xrs.server = Server()
        self.run = True
        
        # Start arp proxy
        self.sdx_ap = arp_proxy(self.xrs)
        self.ap_thread = Thread(target=self.sdx_ap.start)
        self.ap_thread.daemon = True
        self.ap_thread.start()
        
    def start(self):
        print "Start Server"
        self.xrs.server.start()
    
        while self.run:
            # get BGP messages from ExaBGP via stdin
            try:
                route = self.xrs.server.receiver_queue.get(True, 1)
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
            except Queue.Empty:
                if LOG:
                    print "Empty Queue"
          
    def stop(self):
        self.run = False
        self.sdx_ap.stop()
        self.ap_thread.join()
        
def main(argv):
    # locate config file
    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","examples",args.dir,"controller","sdx_config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")
    
    # start route server    
    sdx_rs = route_server(config_file)
    rs_thread = Thread(target=sdx_rs.start)
    rs_thread.daemon = True
    rs_thread.start()
    
    while rs_thread.is_alive():
        try:
            rs_thread.join(1)
        except KeyboardInterrupt:
            sdx_rs.stop()
    
''' main '''    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    args = parser.parse_args() 
    
    main(args)

    
    
