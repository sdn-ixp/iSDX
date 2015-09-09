#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import logging
import json

from threading import Thread
from Queue import Empty
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

        self.fp_thread = None
        self.fs_thread = None

        self.flow_mod_queue = Queue()

    def start(self):
        self.run = True
        print "FP START"
        self.fp_thread = Thread(target=self.file_processor)
        self.fp_thread.setDaemon(True)
        self.fp_thread.start()
        print "FP START FERTIG"

        print "FS START"
        self.fs_thread = Thread(target=self.flow_mod_sender)
        self.fs_thread.setDaemon(True)
        self.fs_thread.start()
        print "FS START FERTIG"

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
            flag = 0
            tmp = {}

            for line in infile:
                if line.startswith("BURST"):
                    flag = 1
                    tmp = {"flow_mods": []}
                    
                    x = line.split("\n")[0].split(": ")[1]
                    tmp["time"] = float(x)

                elif line.startswith("PARTICIPANT") and flag == 1:
                    flag = 2

                    x = line.split("\n")[0].split(": ")[1]

                    tmp["auth_info"] = {"participant": int(x), "auth_key": "secrect"}

                elif flag == 2:
                    if line.startswith("\n"):
                        if not self.run:
                            break

                        self.flow_mod_queue.put(tmp)

                        while self.flow_mod_queue.qsize() > 1000:
                            self.logger.debug('queue is full - taking a break')
                            sleep(self.sleep_time(tmp["time"])/2)

                        flag = 0

                    else:
                        tmp["flow_mods"].append(json.loads(line))
        print "Finished Reading the Log"

    def flow_mod_sender(self):
        while self.run:
            try:
                flow_mod = self.flow_mod_queue.get(True, 1)
            except Empty:
                continue

            if self.simulation_start_time == 0:
                self.real_start_time = time()
                self.simulation_start_time = flow_mod["time"]

            sleep_time = self.sleep_time(flow_mod["time"])

            self.logger.debug('sleep for ' + str(sleep_time) + ' seconds')

            sleep(sleep_time)

            self.refmon.process_flow_mods(flow_mod)


    def sleep_time(self, flow_mod_time):
        time_diff = flow_mod_time - self.simulation_start_time
        wake_up_time = self.real_start_time + time_diff
        sleep_time = wake_up_time - time()

        if sleep_time < 0:
            sleep_time = 0

        return sleep_time
