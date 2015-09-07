#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import logging
import json

from threading import Thread
from multiprocessing import Queue

from time import sleep, time, strptime, mktime

''' Server of Reference Monitor to Receive Flow Mods '''
class Server():

    def __init__(self, refmon, input_file):
        self.logger = logging.getLogger('RefMon Server')
        self.logger.info('server: start')

        self.refmon = refmon

        self.input_file = input_file

        self.real_start_time = time()
        self.simulation_start_time = 0

        self.flow_mod_queue = Queue()

    def start(self):
        self.run = True
        self.fp_thread = Thread(target=self.file_processor)
        self.fp_thread.start()

        self.fs_thread = Thread(target=self.flow_mod_sender)
        self.fs_thread.start()

    def stop(self):
        self.run = False
        
        self.fs_thread.join()
        self.logger.debug('flow mod sender terminated')

        self.fp_thread.join()
        self.logger.debug('file processor terminated')

        self.flow_mod_queue.close()

    ''' receiver '''
    def file_processor(self):
        with open(self.input_file) as infile:
            for line in infile:
                if not self.run:
                    break

                self.update_queue.put(tmp)

                while self.update_queue.qsize() > 1000:
                    self.logger.debug('queue is full - taking a break')
                    sleep(self.sleep_time(tmp["time"])/2)

    def flow_mod_sender(self):
        while self.run:
            try:
                flow_mod = json.loads(self.flow_mod_queue.get(True, 1))
            except Empty:
                continue

            if self.simulation_start_time == 0:
                self.real_start_time = time()
                self.simulation_start_time = flow_mod["time"]

            sleep_time = self.sleep_time(flow_mod["time"])

            self.logger.debug('sleep for ' + str(sleep_time) + ' seconds')

            sleep(sleep_time)

            self.refmon.process_flow_mods(flow_mod)


    def sleep_time(self, flow_modtime):
        time_diff = flow_mod_time - self.simulation_start_time
        wake_up_time = self.real_start_time + time_diff
        sleep_time = wake_up_time - time()

        if sleep_time < 0:
            sleep_time = 0

        return sleep_time
