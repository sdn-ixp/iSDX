#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Listener

LOG = False

''' Server of Reference Monitor to Receive Flow Mods '''
class Server():

    def __init__(self, refmon, address, port, key):
        self.refmon = refmon
        self.listener = Listener((address, port), authkey=str(key))

    def start(self):
        self.receive = True
        self.receiver = Thread(target=self.receiver)
        self.receiver.start()

    ''' receiver '''
    def receiver(self):
        while self.receive:
            conn = self.listener.accept()

            try:
                msg = conn.recv()
                self.refmon.process_flow_mods(msg)
            except:
                pass
            conn.close()

    def stop(self):
        self.receive = False
	self.receiver.join(1)
