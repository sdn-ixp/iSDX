#!/usr/bin/env python
#  Author:
#  Florian Kaufmann (DE-CIX)

import json
from multiprocessing.connection import Listener
from threading import Thread

import os
import sys

''' server for participants to handle policy updates '''
class ParticipantServer(object):

    def __init__(self, address, port, logger):
        self.logger = logger
        self.listener = Listener((address, port), backlog=100)

    def start(self, participant_controller):
        self.receive = True
        self.controller = participant_controller

        self.id = self.controller.id
        self.logger.debug('participant_server(%s): start server' % self.id)

        self.receiver = Thread(target=self.receiver)
        self.receiver.start()

    def receiver(self):
        while self.receive:
            conn = self.listener.accept()
            self.logger.debug('participant_server(%s) accepted connection from %s' % (self.id, self.listener.last_accepted))

            msg = None
            while msg is None:
                try:
                    msg = conn.recv()
                except:
                    pass
            self.logger.debug('participant_server(%s): received policy message %s' % (self.id, msg))
            self.controller.process_policy_changes(json.loads(msg))

            conn.close()
            self.logger.debug('participant_server(%s): closed connection' % self.id)

    def stop(self):
        self.receive = False
        self.receiver.join(1)
