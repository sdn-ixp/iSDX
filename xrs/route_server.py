#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)


import argparse
from collections import namedtuple
import json
from multiprocessing.connection import Listener, Client
import os
import Queue
import sys
from threading import Thread
import time

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from server import server as Server


logger = util.log.getLogger('XRS')

Config = namedtuple('Config', 'ah_socket')
XRSPeer = namedtuple('XRSPeer', 'peers_in peers_out eh_socket')

config = None

participants = {}
portip_2_participant = {}


class PctrlListener(object):
    def __init__(self):
        logger.info("Initializing the BGP PctrlListener")

        self.listener = Listener(config.ah_socket, authkey=None, backlog=100)
        self.run = True


    def start(self):
        logger.info("Announcement Handler started.")

        while self.run:
            conn = self.listener.accept()
            announcement = conn.recv()

            logger.debug("Received an announcement.")

            bgpListener.send(announcement)
            reply = "Announcement processed"
            conn.send(reply)
            conn.close()


    def send(self, id, route):
        logger.debug('Sending a route update to participant %d', id)
        conn = Client(tuple(participants[id].eh_socket), authkey = None)
        conn.send(json.dumps({'bgp': route}))
        conn.recv()
        conn.close()


    def stop(self):
        logger.info("Stopping PctrlListener.")
        self.run = False


class BGPListener(object):
    def __init__(self):
        logger.info("Initializing the BGP BGPListener")

        # Initialize XRS Server
        self.server = Server(logger)
        self.run = True


    def start(self):
        logger.info("Starting the Server to handle incoming BGP Updates.")
        self.server.start()

        waiting = 0
        while self.run:
            # get BGP messages from ExaBGP via stdin in client.py,
            # which is routed to server.py via port 6000,
            # which is routed to here via receiver_queue.
            try:
                route = self.server.receiver_queue.get(True, 1)
            except Queue.Empty:
                if waiting == 0:
                    logger.debug("Waiting for BGP update...")
                waiting = (waiting+1) % 30
                continue

            waiting = 0
            route = json.loads(route)

            logger.debug("Got route from ExaBGP: %s", route)

            # Received BGP route advertisement from ExaBGP
            try:
                advertise_id = portip_2_participant[route['neighbor']['ip']]
                peers_out = participants[advertise_id].peers_out
            except KeyError:
                continue

            for id, peer in participants.iteritems():
                # Apply the filtering logic
                if id in peers_out and advertise_id in peer.peers_in:
                    # Now send this route to participant `id`'s controller'
                    pctrlListener.send(id, route)

    def send(self, announcement):
        announcement = json.loads(announcement)
        self.server.sender_queue.put(announcement)


    def stop(self):
        logger.info("Stopping BGPListener.")
        self.run = False


def parse_config(config_file):
    "Parse the config file"

    # loading config file
    logger.debug("Begin parsing config...")

    with open(config_file, 'r') as f:
        config = json.load(f)

    ah_socket = tuple(config["Route Server"]["AH_SOCKET"])

    for pname,participant in config["Participants"].items():
        iname = int(pname)

        for port in participant["Ports"]:
            portip_2_participant[port['IP']] = iname

        peers_out = [peer for peer in participant["Peers"]]
        # TODO: Make sure this is not an insane assumption
        peers_in = peers_out

        addr, port = participant["EH_SOCKET_XRS"]
        eh_socket = (str(addr), int(port))

        # create peer and add it to the route server environment
        participants[iname] = XRSPeer(peers_in, peers_out, eh_socket)

    for i,p in participants.items():
        logger.debug('Trace: participants[%d] = %s', i, p)
    for i,p in portip_2_participant.items():
        logger.debug('Trace: portip_2_participant[%s] = %s', i, p)

    logger.debug("Done parsing config")
    return Config(ah_socket)


def main():
    global bgpListener, pctrlListener, config

    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    args = parser.parse_args()

    # locate config file
    config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","examples",args.dir,"config","sdx_global.cfg")

    logger.info("Reading config file %s", config_file)
    config = parse_config(config_file)

    bgpListener = BGPListener()
    bp_thread = Thread(target=bgpListener.start)
    bp_thread.start()

    pctrlListener = PctrlListener()
    pp_thread = Thread(target=pctrlListener.start)
    pp_thread.start()

    while bp_thread.is_alive():
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            bgpListener.stop()

    bp_thread.join()
    pctrlListener.stop()
    pp_thread.join()


if __name__ == '__main__':
    main()
