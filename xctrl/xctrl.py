#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import argparse
import os
from threading import Thread

import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from client import RefMonClient # Socket
from gss import GSSmS, GSSmT
from lib import Config
from mds import MDSmS, MDSmT


class xCtrl(object):
    def __init__(self, config_file):
        self.logger = util.log.getLogger('xctrl')
        self.logger.info('init')

        self.config = Config(config_file)

        #self.client = FlowModSender(self.config.refmon["url"]) # REST API
        self.client = RefMonClient(self.config.refmon["IP"], self.config.refmon["Port"], self.config.refmon["key"])

        if self.config.isMDSMode():
            if self.config.isMultiSwitchMode():
                self.controller = MDSmS(self.client, self.config)
                self.logger.info('mode MDSmS - OF v1.0')
            elif self.config.isMultiTableMode():
                self.controller = MDSmT(self.client, self.config)
                self.logger.info('mode MDSmT - OF v1.3')
        elif self.config.isSupersetsMode():
            if self.config.isMultiSwitchMode():
                self.controller = GSSmS(self.client, self.config)
                self.logger.info('mode GSSmS - OF v1.3')
            elif self.config.isMultiTableMode():
                self.controller = GSSmT(self.client, self.config)
                self.logger.info('mode GSSmT - OF v1.3')

    def start(self):
        self.logger.info('start')
        self.controller.start()

    def stop(self):
        self.logger.info('stop')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    args = parser.parse_args() 

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


if __name__ == '__main__':
    main()
