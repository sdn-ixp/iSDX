#!/usr/bin/env python
#  Author:
#  Rudiger Birkner(ETH Zurich)

import logging
import argparse
import json
import os
from time import sleep, time, strptime, mktime
from threading import Thread
from netaddr import IPAddress
from multiprocessing import Queue
import multiprocessing as mp
from Queue import Empty
from multiprocessing.connection import Client

update_minutes = 300
LOG=False

class ExaBGPEmulator(object):
    def __init__(self, address, port, authkey, input_file, speed_up, rate, mode, example_name, debug = False):
        self.logger = logging.getLogger('xbgp')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug('init')

        self.input_file = input_file

        self.real_start_time = time()
        self.simulation_start_time = 0

        self.speed_up = speed_up
	self.mode = int(mode)
        self.fp_thread = None
        self.us_thread = None
	self.send_rate = int(rate)
        self.run = True
	server_filename = "server_settings.cfg"
        server_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "examples", example_name))
        server_file = os.path.join(server_path, server_filename)
        self.server_settings = json.load(open(server_file, 'r'))	

        self.update_queue = mp.Manager().Queue()

        self.conn = Client((address, port), authkey=authkey)

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
                    tmp["time"] = int(time/self.speed_up)

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
			if LOG: print "Adding Update to queue..."
                        self.update_queue.put(tmp)
                        while self.update_queue.qsize() > 32000:

                            self.logger.debug('queue is full - taking a break')

                            sleep(self.sleep_time(tmp["time"])/2)

                            if not self.run:
                                break

                        flag = 0
                    else:
                        x = line.split("\n")[0].split()[0]
                        if "announce" in tmp["neighbor"]["message"]["update"]:
                            tmp["neighbor"]["message"]["update"]["announce"]["ipv4 unicast"][next_hop][x] = {}
                        else:
                            tmp["neighbor"]["message"]["update"]["withdraw"]["ipv4 unicast"][x] = {}

        self.run = False

    def bgp_update_sender(self):
        while self.run or not self.update_queue.empty():
            try:
                bgp_update = self.update_queue.get(True, 1)
            except Empty:
                continue

            if self.simulation_start_time == 0:
                self.real_start_time = time()
                self.simulation_start_time = bgp_update["time"]

	    current_bgp_update = bgp_update["time"]
            elapsed = current_bgp_update - self.simulation_start_time
            if elapsed > update_minutes:
                print "start: current", self.simulation_start_time, current_bgp_update
                break

            sleep_time = self.sleep_time(bgp_update["time"])

            self.logger.debug('sleep for ' + str(sleep_time) + ' seconds')

            sleep(sleep_time)

            self.send_update(bgp_update)

    def bgp_update_rate_sender(self):
	current_count = 0
	count = 0
	#print "Queue Empty: ", self.update_queue.empty()
	#sleep(2)
        while not self.update_queue.empty() or self.run:
            try:
                bgp_update = self.update_queue.get(True, 1)
            except Empty:
                continue
	    if self.simulation_start_time == 0: 
		self.simulation_start_time = bgp_update["time"]		

	    current_bgp_update = bgp_update["time"]
	    elapsed = current_bgp_update - self.simulation_start_time
	    if elapsed > update_minutes:
		print "start: current", self.simulation_start_time, current_bgp_update
		break

	    if current_count == self.send_rate:
            	current_count = 0
		#print "Current Count: ", current_count
		sleep(1)
	    current_count += 1
	    count += 1
	    #print "Current Count: ", current_count
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

	print "mode: ", self.mode
        self.logger.debug('start update sender')
        if self.mode == 0:
		self.us_thread = Thread(target=self.bgp_update_sender)
        	self.us_thread.start()
	if self.mode == 1:
		self.us_thread = Thread(target=self.bgp_update_rate_sender)
        	self.us_thread.start()

    def stop(self):
	server1 = tuple([self.server_settings["server1"]["IP"], int(self.server_settings["server1"]["PORT"])])
	server2 = tuple([self.server_settings["server2"]["IP"], int(self.server_settings["server2"]["PORT"])])

	conn = Client(tuple(server1, authkey = None)
        data = 'terminate'
        conn.send(json.dumps(data))
        conn.close()

	conn = Client(tuple(server2, authkey = None)
        data = 'terminate'
        conn.send(json.dumps(data))
        conn.close()

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

    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","examples",args.dir,"config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")
    config = json.load(open(config_file, 'r'))
    #ah_socket = tuple(config["Route Server"]["AH_SOCKET"])

    if args.speedup:
        speedup = args.speedup
    else:
        speedup = 1

    exabgp_instance = ExaBGPEmulator(config["Route Server"]["XRS_SOCKET"][0], config["Route Server"]["XRS_SOCKET"][1], args.key, args.input, speedup, args.rate, args.mode, args.dir, args.debug)

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
    parser.add_argument('port', help='port of the xrs', type=int)
    parser.add_argument('key', help='authkey of the xrs')
    parser.add_argument('input', help='bgp input file')
    parser.add_argument('rate', help='bgp updates rate/second')
    parser.add_argument('mode', help='xbgp mode 0: bgp update time based 1: bgp update rate based')
    parser.add_argument('dir', help='Example directory name')
    parser.add_argument('-d', '--debug', help='enable debug output', action="store_true")
    parser.add_argument('--speedup', help='speed up of replay', type=float)
    args = parser.parse_args()

    main(args)
