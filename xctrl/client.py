#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
from multiprocessing import Queue
from multiprocessing.connection import Client
from threading import Thread

LOG = False

class RefMonClient(object):
    def __init__(self, address, port, key):
        self.address = address
        self.port = int(port)
        self.key = key

    def send(self, msg):
        #conn = Client((self.address, self.port), authkey=str(self.key))
        conn = Client((self.address, self.port))

        conn.send(json.dumps(msg))

        conn.close()
