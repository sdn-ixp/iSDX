#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json

from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Client

LOG = False

class RefMonClient():
    def __init__(self, address, port, key):
        self.address = address
        self.port = int(port)
        self.key = key

    def send(self, msg):
        #conn = Client((self.address, self.port), authkey=str(self.key))
        conn = Client((self.address, self.port))

        conn.send(json.dumps(msg))

        conn.close()
