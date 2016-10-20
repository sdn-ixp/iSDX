#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
import socket

class RefMonClient(object):
    def __init__(self, address, port, key):
        self.address = address
        self.port = int(port)
        self.key = key

    def send(self, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.address, self.port))
        sock.sendall(json.dumps(msg))
        sock.close()
