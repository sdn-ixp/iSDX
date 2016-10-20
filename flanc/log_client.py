#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import argparse
import json
from multiprocessing import Queue
from Queue import Empty
from threading import Thread
from time import sleep, time
import socket


import os
import sys
np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log


''' LogClient for Reference Monitor '''
class LogClient(object):

    def __init__(self, address, port, authkey, input_file, debug = False, timing = False):
        self.logger = util.log.getLogger('log_client')
        self.logger.info('server: start')

        self.timing = timing

        self.address = address
        self.port = int(port)
        self.authkey = authkey

        self.input_file = input_file

        self.real_start_time = time()
        self.simulation_start_time = 0

        self.fp_thread = None
        self.fs_thread = None

        self.flow_mod_queue = Queue()

    def start(self):
        self.run = True

        self.fp_thread = Thread(target=self.file_processor)
        self.fp_thread.setDaemon(True)
        self.fp_thread.start()
        self.logger.debug('file processor started')

        self.fs_thread = Thread(target=self.flow_mod_sender)
        self.fs_thread.setDaemon(True)
        self.fs_thread.start()
        self.logger.debug('flow mod sender started')

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

                        self.logger.debug('processed one burst')

                        self.flow_mod_queue.put(tmp)

                        while self.flow_mod_queue.qsize() > 32000:
                            self.logger.debug('queue is full - taking a break')
                            sleep(self.sleep_time(tmp["time"])/2)

                            if not self.run:
                                break

                        flag = 0

                    else:
                        tmp["flow_mods"].append(json.loads(line))

        self.logger.debug('finished processing the log')

    def flow_mod_sender(self):
        while self.run:
            try:
                flow_mod = self.flow_mod_queue.get(True, 0.5)
            except Empty:
                continue

            if self.timing:
                if self.simulation_start_time == 0:
                    self.real_start_time = time()
                    self.simulation_start_time = flow_mod["time"]

                sleep_time = self.sleep_time(flow_mod["time"])

                self.logger.debug('sleep for ' + str(sleep_time) + ' seconds')

                sleep(sleep_time)

            self.send(flow_mod)

    def send(self, flow_mod):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.address, self.port))
        sock.sendall(json.dumps(flow_mod))
        sock.close()

    def sleep_time(self, flow_mod_time):
        time_diff = flow_mod_time - self.simulation_start_time
        wake_up_time = self.real_start_time + time_diff
        sleep_time = wake_up_time - time()

        if sleep_time < 0:
            sleep_time = 0

        return sleep_time

def main(argv):
    log_client_instance = LogClient(args.ip, args.port, args.key, args.input, True, args.timing)
    log_client_instance.start()

    while log_client_instance.run:
        try:
            sleep(0.5)
        except KeyboardInterrupt:
            log_client_instance.stop()

''' main '''
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('ip', help='ip address of the refmon')
    parser.add_argument('port', help='port of the refmon')
    parser.add_argument('key', help='authkey of the refmon')
    parser.add_argument('input', help='flow mod input file')
    parser.add_argument('-t', '--timing', help='enable timed replay of flow mods', action='store_true')

    args = parser.parse_args()

    main(args)
