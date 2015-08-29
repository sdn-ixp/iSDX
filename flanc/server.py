#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import logging
import json

from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Listener

''' Server of Reference Monitor to Receive Flow Mods '''
class Server():

    def __init__(self, refmon, address, port, key):
        self.logger = logging.getLogger('RefMon Server')
        self.logger.info('server: start')

        self.refmon = refmon
        #self.listener = Listener((address, port), authkey=str(key))
        self.listener = Listener((address, port))

    def start(self):
        self.receive = True
        self.receiver = Thread(target=self.receiver)
        self.receiver.start()

    ''' receiver '''
    def receiver(self):
        while self.receive:
            conn = self.listener.accept()
            self.logger.info('server: accepted connection from ' + str(self.listener.last_accepted))

            msg = None
            while msg is None:
                try:
                    msg = conn.recv()
                except:
                    pass
            self.logger.info('server: received message')
            self.refmon.process_flow_mods(json.loads(msg))

            conn.close()
            self.logger.info('server: closed connection')

    def stop(self):
        self.receive = False
	self.receiver.join(1)
