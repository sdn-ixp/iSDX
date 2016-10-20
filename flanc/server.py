#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import json

import os
import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from ryu.lib import hub
from ryu.lib.hub import StreamServer

''' Server of Reference Monitor to Receive Flow Mods '''
class Server(object):

    def __init__(self, refmon, address, port, key):
        self.logger = util.log.getLogger('RefMon_Server')
        self.logger.info('server: start')

        self.address = address
        self.port = port
        self.refmon = refmon

    def start(self):
        self.receive = True
        self.receive_thread = hub.spawn(self.receiver)
        self.logger.info('server: thread spawned')

    ''' receiver '''
    def receiver(self):
        server = RefMonStreamServer(self.refmon, (self.address, self.port), conn_factory)
        self.logger.info('Starting StreamServer')
        server.serve_forever()

    def stop(self):
        self.receive = False
        self.receiver.join(1)


class RefMonStreamServer(StreamServer):
    def __init__(self, refmon, listen_info, conn_factory):
        StreamServer.__init__(self, listen_info, conn_factory, backlog=None)
        self.refmon = refmon
        self.logger = refmon.logger
        
    def serve_forever(self):
        self.logger.info('RefMonStreamServer: serve_forever')
        while True:
            sock, addr = self.server.accept()
            hub.spawn(self.handle, self.refmon, sock, addr)

def conn_factory(refmon, socket, address):
    refmon.logger.info('server: accepted connection')

    msg = ''
    while True:
        buf = socket.recv(1024)
        msg += buf
        if len(buf) == 0:
            break
    socket.close()
    
    refmon.logger.info('server: closed connection')

    refmon.logger.info('server: received message: ' + str(msg))
    refmon.process_flow_mods(json.loads(msg))
        


