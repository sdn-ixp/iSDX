#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import os
import argparse

from client import Client
from lib import Config
from gss import GSSmS, GSSmT
from mds import MDS

class xCtrl(object):
    def __init__(self, config_file):
        self.config = Config(config_file)

        self.client = Client(self.config.refmon["address"], self.config.refmon["port"], self.config.refmon["key"])

        if self.config.vmac_mode == 0:
            self.controller = MDS(self.client, self.config)
        elif self.config.vmac_mode == 1:
            if self.config.mode == 0:
                self.controller = GSSmS(self.client, self.config)
            elif self.config.mode == 1:
                self.controller = GSSmT(self.client, self.config)

    def start():
        self.controller.start()

    def stop():
        pass

def main(argv):
    # locate config file
    config_file = os.path.abspath(args.config)
    
    # start central sdx controller
    xctrl = xCtrl(config_file)

    xctrl_thread = Thread(target=xctrl.start)
    xctrl_thread.daemon = True
    xctrl_thread.start()
    
    while xctrl_thread.is_alive():
        try:
            xctrl_thread.join(1)
        except KeyboardInterrupt:
            xctrl.stop()
    
''' main '''    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    args = parser.parse_args() 
    
    main(args)
