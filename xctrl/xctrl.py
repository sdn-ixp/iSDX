#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import argparse
import os

import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log

from client import RefMonClient  # Socket
from gss import GSSmS, GSSmT, GSSoS
from lib import Config
from mds import MDSmS, MDSmT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    args = parser.parse_args()

    # locate config file
    config_file = os.path.abspath(args.config)

    # start central sdx controller
    logger = util.log.getLogger('xctrl')
    logger.info('init')

    config = Config(config_file)

    logger.info('REFMON client: ' + str(config.refmon["IP"]) + ' ' + str(config.refmon["Port"]))
    client = RefMonClient(config.refmon["IP"], config.refmon["Port"], config.refmon["key"])

    if config.isMDSMode():
        if config.isMultiSwitchMode():
            controller = MDSmS(client, config)
            logger.info('mode MDSmS - OF v1.0')
        elif config.isMultiTableMode():
            controller = MDSmT(client, config)
            logger.info('mode MDSmT - OF v1.3')
    elif config.isSupersetsMode():
        if config.isMultiSwitchMode():
            controller = GSSmS(client, config)
            logger.info('mode GSSmS - OF v1.3')
        elif config.isMultiTableMode():
            controller = GSSmT(client, config)
            logger.info('mode GSSmT - OF v1.3')
        elif config.isOneSwitchMode():
            controller = GSSoS(client, config)
            logger.info('mode GSSoS - OF v1.3')

    logger.info('start')
    controller.start()


if __name__ == '__main__':
    main()
