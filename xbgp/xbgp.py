#!/usr/bin/env python
#  Author:
#  Rudiger Birkner(ETH Zurich)

import logging
import argparse
import json

from time import sleep, time, strptime, mktime
from threading import Thread
from netaddr import IPAddress
from multiprocessing import Queue
from Queue import Empty
from multiprocessing.connection import Client

class ExaBGPEmulator(object):
    def __init__(self, address, port, authkey, input_file, debug = False):
        self.logger = logging.getLogger('xbgp')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug('init')

        self.input_file = input_file
        
        self.real_start_time = time()
        self.simulation_start_time = 0 

        self.fp_thread = None
        self.us_thread = None
        
        self.run = True
        
        self.update_queue = Queue()
        
        self.conn = Client((address, int(port)), authkey=authkey)

    def file_processor(self):
        with open(self.input_file) as infile:
            tmp = {}
            next_hop = ""
            flag = 0
            
            for line in infile:
                if line.startswith("TIME"):
                
                    flag = 1
                    
                    tmp = {"exabgp": "3.4.8", "type": "update"}
                    next_hop = ""
                    
                    x = line.split("\n")[0].split(": ")[1]
                    time = mktime(strptime(x, "%m/%d/%y %H:%M:%S"))
                    tmp["time"] = int(time)
                    
                elif flag == 1:
                    if 'Keepalive' in line or line.startswith("\n"):
                        # Only process Update Messages
                        flag = 0

                    else:
                        x = line.split("\n")[0].split(": ")

                        if "neighbor" not in tmp:
                             tmp["neighbor"] = {"address": {}, "asn": {}, "message": {"update": {}}}
                        
                        elif line.startswith("FROM"):
                            x = x[1].split(" ")
                            if IPAddress(x[0]).version == 4:
                                tmp["neighbor"]["ip"] = x[0]
                                tmp["neighbor"]["address"]["peer"] = x[0]
                                tmp["neighbor"]["asn"]["peer"] = x[1][2:]
                            else:
                                flag = 0
                        elif line.startswith("TO"):
                            x = x[1].split(" ")
                            if IPAddress(x[0]).version == 4:
                                tmp["neighbor"]["address"]["local"] = x[0]
                                tmp["neighbor"]["asn"]["local"] = x[1][2:]                          
                            else:
                                flag = 0                        
                        elif line.startswith("ORIGIN"):
                            if "attribute" not in tmp["neighbor"]["message"]["update"]:
                                tmp["neighbor"]["message"]["update"]["attribute"] = {}
                            tmp["neighbor"]["message"]["update"]["attribute"]["origin"] = x[1].lower()
                        
                        elif line.startswith("ASPATH"):
                            if "attribute" not in tmp["neighbor"]["message"]["update"]:
                                tmp["neighbor"]["message"]["update"]["attribute"] = {}
                            tmp["neighbor"]["message"]["update"]["attribute"]["as-path"] = "[ " + x[1] + " ]"
                            
                        elif line.startswith("MULTI_EXIT_DISC"):
                            if "attribute" not in tmp["neighbor"]["message"]["update"]:
                                tmp["neighbor"]["message"]["update"]["attribute"] = {}
                            tmp["neighbor"]["message"]["update"]["attribute"]["med"] = x[1]
                            
                        elif line.startswith("NEXT_HOP"):
                            if "announce" not in tmp["neighbor"]["message"]["update"]:
                                tmp["neighbor"]["message"]["update"]["announce"] = {}
                            tmp["neighbor"]["message"]["update"]["announce"] = {"ipv4 unicast": {x[1]: {}}}
                            next_hop = x[1]
                            
                        elif line.startswith("ANNOUNCE"):
                            if "announce" not in tmp["neighbor"]["message"]["update"]:
                                tmp["neighbor"]["message"]["update"]["announce"] = {"ipv4 unicast": {}}
                            flag = 2
                        elif line.startswith("WITHDRAW"):
                            tmp["neighbor"]["message"]["update"]["withdraw"] = {"ipv4 unicast": {}}
                            flag = 2

                elif flag == 2:
                    if line.startswith("\n"):
                        if not self.run:
                            break
                            
                        self.update_queue.put(tmp)
                        
                        while self.update_queue.qsize() > 1000:
                            
                            self.logger.debug('queue is full - taking a break')

                            sleep(self.sleep_time(tmp["time"])/2)
                            
                        flag = 0
                    else:
                        x = line.split("\n")[0].split()[0]
                        if "announce" in tmp["neighbor"]["message"]["update"]:
                            tmp["neighbor"]["message"]["update"]["announce"]["ipv4 unicast"][next_hop][x] = {}
                        else:
                            tmp["neighbor"]["message"]["update"]["withdraw"]["ipv4 unicast"][x] = {}
             
        self.run = False
                
    def bgp_update_sender(self):
        while self.run:
            try:
                bgp_update = self.update_queue.get(True, 1)        
            except Empty:
                continue

            if self.simulation_start_time == 0:
                self.real_start_time = time()
                self.simulation_start_time = bgp_update["time"]

            sleep_time = self.sleep_time(bgp_update["time"])

            self.logger.debug('sleep for ' + str(sleep_time) + ' seconds')
                
            sleep(sleep_time)
            
            self.send_update(bgp_update)

    def sleep_time(self, update_time):
        time_diff = update_time - self.simulation_start_time
        wake_up_time = self.real_start_time + time_diff
        sleep_time = wake_up_time - time()
        
        if sleep_time < 0:
            sleep_time = 0

        return sleep_time      
        
    def send_update(self, update):
        self.conn.send(json.dumps(update))
        
    def start(self): 
        self.logger.debug('start file processor')
        self.fp_thread = Thread(target=self.file_processor)
        self.fp_thread.start()
        
        self.logger.debug('start update sender')
        self.us_thread = Thread(target=self.bgp_update_sender)
        self.us_thread.start()
        
    def stop(self):
        self.logger.debug('terminate')

        self.run = False

        self.us_thread.join()
        self.logger.debug('bgp update sender terminated')

        self.fp_thread.join()
        self.logger.debug('file processor terminated')

        self.update_queue.close()

        self.conn.close()


def main(argv):
    # logging - log level
    logging.basicConfig(level=logging.INFO)

    exabgp_instance = ExaBGPEmulator(args.ip, args.port, args.key, args.input, True)

    exabgp_instance.start()

    while exabgp_instance.run:
        try:
            sleep(0.5)
        except KeyboardInterrupt:
            exabgp_instance.stop()        
    
''' main '''
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('ip', help='ip address of the xrs')
    parser.add_argument('port', help='port of the xrs')
    parser.add_argument('key', help='authkey of the xrs')
    parser.add_argument('input', help='bgp input file')
    args = parser.parse_args()

    main(args)
