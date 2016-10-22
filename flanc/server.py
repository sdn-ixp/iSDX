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
        self.queue = hub.Queue()
        self.receive_thread = hub.spawn(self.receiver)
        self.logger.info('server: receiver thread spawned')
        self.processor_thread = hub.spawn(self.service_queue)
        self.logger.info('server: processor thread spawned')

    ''' receiver '''
    def receiver(self):
        stream_server = RefMonStreamServer(self, (self.address, self.port), conn_factory)
        self.logger.info('Starting StreamServer')
        stream_server.serve_forever()

    def stop(self):
        self.receive = False
        self.receiver.join(1)

    def service_queue(self):
        while True:
            msg = self.queue.get()
            self.refmon.process_flow_mods(json.loads(msg))


class RefMonStreamServer(StreamServer):
    def __init__(self, main_server, listen_info, conn_factory):
        StreamServer.__init__(self, listen_info, conn_factory, backlog=None)
        self.main_server = main_server
        self.logger = main_server.logger
        
    def serve_forever(self):
        self.logger.info('RefMonStreamServer: serve_forever')
        while True:
            sock, addr = self.server.accept()
            
            # Spawning thread here seemed like a good idea, but we end up
            # running out of file descriptors, so we now just work serially
            #hub.spawn(self.handle, self.main_server, sock, addr)
            self.handle(self.main_server, sock, addr)


def conn_factory(main_server, socket, address):
    main_server.logger.info('server: accepted connection')

    msg = ''
    while True:
        buf = socket.recv(2048)
        msg += buf
        if len(buf) == 0:
            break
    
    main_server.logger.info('server: received message: ' + str(msg))
    
    main_server.queue.put(msg)
    main_server.logger.info('server: msg queued')
    # expect other end will close the connection
        


