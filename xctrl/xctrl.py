#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import os
import argparse
import logging

from threading import Thread

#from flowmodsender import FlowModSender # REST API
from client import RefMonClient # Socket
from lib import Config
from gss import GSSmS, GSSmT
from mds import MDSmS, MDSmT

class xCtrl(object):
    def __init__(self, config_file):
        self.logger = logging.getLogger('xctrl')
        self.logger.info('init')

        self.config = Config(config_file)

        #self.client = FlowModSender(self.config.refmon["url"]) # REST API
        self.client = RefMonClient(self.config.refmon["IP"], self.config.refmon["Port"], self.config.refmon["key"])

        if self.config.vmac_mode == 0:
            if self.config.mode == 0:
                self.controller = MDSmS(self.client, self.config)
                self.logger.info('mode MDSmS - OF v1.0')
            elif self.config.mode == 1:
                self.controller = MDSmT(self.client, self.config)
                self.logger.info('mode MDSmT - OF v1.3')
        elif self.config.vmac_mode == 1:
            if self.config.mode == 0:
                self.controller = GSSmS(self.client, self.config)
                self.logger.info('mode GSSmS - OF v1.3')
            elif self.config.mode == 1:
                self.controller = GSSmT(self.client, self.config)
                self.logger.info('mode GSSmT - OF v1.3')

    def start(self):
        self.logger.info('start')
        self.controller.start()

    def stop(self):
        self.logger.info('stop')

def main(argv):
    # logging - log level
    logging.basicConfig(level=logging.INFO)
 
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
