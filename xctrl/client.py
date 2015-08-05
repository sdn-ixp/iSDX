#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Client

LOG = False

class Client():
    def __init__(self, address, port, key):
        self.address = address
        self.port = port
        self.key = key

    def send(self, msg):
        conn = Client((address, port), authkey='xrs')

        conn.send(msg)

        conn.close()
