#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

class GSS(object):
    def __init__(self, sender, config):
        self.sender = sender
        self.config = config

class GSSmS(GSS):
    def __init__(self, sender, config):
        super(GSSmS, self).__init__(sender, config)

    def init_fabric(self):
        pass

class GSSmT(GSS):
    def __init__(self, sender, config):
        super(GSSmT, self).__init__(sender, config)

    def init_fabric(self):
        pass

