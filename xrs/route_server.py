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
from threading import Thread, Lock
import time

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from server import server as Server


logger = util.log.getLogger('XRS')

Config = namedtuple('Config', 'ah_socket')

bgpListener = None
config = None

participantsLock = Lock()
participants = dict()
portip2participant = dict()

clientPoolLock = Lock()
clientActivePool = dict()
clientDeadPool = set()


class PctrlClient(object):
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

        self.id = None
        self.peers_in = []
        self.peers_out = []

    def start(self):
        logger.info('BGP PctrlClient started for client ip %s.', self.addr)
        while True:
            try:
                rv = self.conn.recv()
            except EOFError as ee:
                break

            logger.debug('Trace: Got rv: %s', rv)
            if not (rv and self.process_message(**json.loads(rv))):
                break

        self.conn.close()

        # remove self
        with clientPoolLock:
            logger.debug('Trace: PctrlClient.start: clientActivePool before: %s', clientActivePool)
            logger.debug('Trace: PctrlClient.start: clientDeadPool before: %s', clientDeadPool)
            t = clientActivePool[self]
            del clientActivePool[self]
            clientDeadPool.add(t)
            logger.debug('Trace: PctrlClient.start: clientActivePool after: %s', clientActivePool)
            logger.debug('Trace: PctrlClient.start: clientDeadPool after: %s', clientDeadPool)

        with participantsLock:
            logger.debug('Trace: PctrlClient.start: portip2participant before: %s', portip2participant)
            logger.debug('Trace: PctrlClient.start: participants before: %s', participants)
            found = [k for k,v in portip2participant.items() if v == self.id]
            for k in found:
                del portip2participant[k]

            found = [k for k,v in participants.items() if v == self]
            for k in found:
                del participants[k]
            logger.debug('Trace: PctrlClient.start: portip2participant after: %s', portip2participant)
            logger.debug('Trace: PctrlClient.start: participants after: %s', participants)


    def process_message(self, msgType=None, **data):
        if msgType == 'hello':
            rv = self.process_hello_message(**data)
        elif msgType == 'bgp':
            rv = self.process_bgp_message(**data)
        else:
            logger.warn("Unrecognized or absent msgType: %s. Message ignored.", msgType)
            rv = True

        return rv


    def process_hello_message(self, id=None, peers_in=None, peers_out=None, ports=None, **data):
        if not (id is not None and isinstance(ports, list) and
                isinstance(peers_in, list) and isinstance(peers_out, list)):
            logger.warn("hello message from %s is missing something: id: %s, ports: %s, peers_in: %s, peers_out: %s. Closing connection.", self.addr, id, ports, peers_in, peers_out)
            return False

        self.id = id = int(id)
        self.peers_in = set(peers_in)
        self.peers_out = set(peers_out)

        with participantsLock:
            logger.debug('Trace: PctrlClient.hello: portip2participant before: %s', portip2participant)
            logger.debug('Trace: PctrlClient.hello: participants before: %s', participants)
            for port in ports:
                portip2participant[port] = id
            participants[id] = self
            logger.debug('Trace: PctrlClient.hello: portip2participant after: %s', portip2participant)
            logger.debug('Trace: PctrlClient.hello: participants after: %s', participants)

        return True


    def process_bgp_message(self, announcement=None, **data):
        if announcement:
            bgpListener.send(announcement)
        return True


    def send(self, route):
        logger.debug('Sending a route update to participant %d', self.id)
        self.conn.send(json.dumps({'bgp': route}))


class PctrlListener(object):
    def __init__(self):
        logger.info("Initializing the BGP PctrlListener")
        self.listener = Listener(config.ah_socket, authkey=None, backlog=100)
        self.run = True


    def start(self):
        logger.info("Starting the BGP PctrlListener")

        while self.run:
            conn = self.listener.accept()

            pc = PctrlClient(conn, self.listener.last_accepted)
            t = Thread(target=pc.start)

            with clientPoolLock:
                logger.debug('Trace: PctrlListener.start: clientActivePool before: %s', clientActivePool)
                logger.debug('Trace: PctrlListener.start: clientDeadPool before: %s', clientDeadPool)
                clientActivePool[pc] = t

                # while here, join dead threads.
                while clientDeadPool:
                    clientDeadPool.pop().join()
                logger.debug('Trace: PctrlListener.start: clientActivePool after: %s', clientActivePool)
                logger.debug('Trace: PctrlListener.start: clientDeadPool after: %s', clientDeadPool)

            t.start()


    def stop(self):
        logger.info("Stopping PctrlListener.")
        self.run = False


class BGPListener(object):
    def __init__(self):
        logger.info('Initializing the BGPListener')

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
                advertise_ip = route['neighbor']['ip']
            except KeyError:
                continue

            found = []
            with participantsLock:
                try:
                    advertise_id = portip2participant[advertise_ip]
                    peers_out = participants[advertise_id].peers_out
                except KeyError:
                    continue

                for id, peer in participants.iteritems():
                    # Apply the filtering logic
                    if id in peers_out and advertise_id in peer.peers_in:
                        found.append(peer)

            for peer in found:
                # Now send this route to participant `id`'s controller'
                peer.send(route)


    def send(self, announcement):
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
