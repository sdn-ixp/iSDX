#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)

import os
import json
import sys
import argparse
import time

from multiprocessing.connection import Listener, Client

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

    def start(self):
        print "Start Server"
        self.xrs.server.start()

        """
        Start the announcement Listener which will receive announcements
        from participants's controller and put them in XRS's sender queue.
        """
        self.set_announcement_handler()

        while self.run:
            # get BGP messages from ExaBGP via stdin
            try:
                route = self.xrs.server.receiver_queue.get(True, 1)
                route = json.loads(route)

                # Received BGP route advertisement from ExaBGP
                for id, peer in self.participants.iteritems():
                    # Apply the filtering logic
                    advertiser_ip = route['neighbor']
                    advertise_id = self.portip_2_participant[advertiser_ip]
                    if id in self.participants[advertise_id].peers_out and advertise_id in self.participants[id].peers_in:
                        # Now send this route to participant `id`'s controller'
                        self.send_update(id, route):

            except Queue.Empty:
                if LOG:
                    print "Empty Queue"

    def set_announcement_handler(self):
        '''Start the listener socket for BGP Announcements'''
        self.listener_eh = Listener(self.ah_socket, authkey=None)
        ps_thread = Thread(target=self.start_ah)
        ps_thread.daemon = True
        ps_thread.start()

    def start_ah(self):
        '''Announcement Handler '''
        print "Event Handler started for", self.id
        while True:
            conn_ah = self.listener_eh.accept()
            tmp = conn.recv()
            announcement = json.loads(tmp)
            self.server.sender_queue.put(announcement)
            reply = "Announcement processed"
            conn_ah.send(reply)
            conn_ah.close()

    def send_update(self, id, route):
        "Send this BGP route to participant id's controller"
        conn = Client(self.participants[id].eh_socket, authkey = None)
        data = {}
        data['bgp'] = route
        conn.send(json.dumps(data))
        recv = conn.recv()
        conn.close()

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
