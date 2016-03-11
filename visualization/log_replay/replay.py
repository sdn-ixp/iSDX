#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (ETH Zurich)

import argparse
import logging
import time
import redis

from collections import namedtuple, defaultdict
from threading import Thread


name_mapping = {
    "MAIN": "Main",
    "MAIN_DFLT": "Main",
    "MAIN_C_DFLT": "Main",
    "MAIN_C1": "Main",
    "MAIN_C2": "Main",
    "OUTBOUND": "Outbound",
    "OUTBOUND4IN": "Outbound",
    "INBOUND": "InBound",
    "INBOUND_DFLT": "InBound",
    "ARP": "ARP-Proxy",
    "ARPPXY": "ARP-Proxy",
    "BGP": "BGP-Proxy",
    "BGP_ARP": "BGP-Proxy",
    "A1": "Router-A",
    "A1_BGP": "Router-A",
    "A1_ARP": "Router-A",
    "VA1": "Router-A",
    "VA1_ARP": "Router-A",
    "B1": "Router-B",
    "B1_BGP": "Router-B",
    "B1_ARP": "Router-B",
    "VB1": "Router-B",
    "VB1_ARP": "Router-B",
    "C1": "Router-C1",
    "C1_BGP": "Router-C1",
    "C1_ARP": "Router-C1",
    "VC1": "Router-C1",
    "VC1_ARP": "Router-C1",
    "C2": "Router-C2",
    "C2_BGP": "Router-C2",
    "C2_ARP": "Router-C2",
    "VC2": "Router-C2",
    "VC2_ARP": "Router-C2",
    "BAD": "bad",
}

traffic_mapping = {
    "bgp": "bgp",
    "arp": "arp",
    "arp_v": "arp",
    "default": "default",
    "default_v": "default",
    "b1_v": "b1",
    "c1_v": "c1",
    "c2_v": "c2",
}


class LogReplay(object):
    def __init__(self, log_history, publisher, time_step=1):
        self.logger = logging.getLogger("LogReplay")
        self.logger.setLevel(logging.DEBUG)

        self.log_history = log_history
        self.time_step = time_step
        #self.publisher = publisher

        self.run = False

    def start(self):
        self.run = True

        while self.run:
            start_time = time.time()
            data = self.log_history.next_values(self.time_step)

            # publish data
            for d in data:
                message = "|".join(d)
                self.logger.debug(message)
                self.publisher.publish(message)

            sleep_time = time.time() - start_time
            self.logger.info("sleep for " + str(sleep_time) + "s")
            time.sleep(sleep_time)

    def stop(self):
        self.run = False


class LogHistory(object):
    def __init__(self, config, flows_dir, ports_dir, num_timesteps):
        self.log_entry = namedtuple("LogEntry", "source destination type")
        self.ports = dict()
        self.flows = dict()

        self.data = defaultdict(list)
        self.current_timestep = 0

        self.parse_config(config)
        self.parse_logs(num_timesteps, flows_dir, ports_dir)

    def parse_config(self, config):
        with open(config, 'r') as infile:
            for line in infile:
                # catch comment lines and empty lines
                if line[0] == "#" or line.isspace():
                    continue

                # build data structure which we can use to assign the logs to the correct edge and traffic type
                data = line.split("\t")
                from_node = name_mapping[data[0]]
                to_node = name_mapping[data[1]]
                traffic_type = traffic_mapping[data[2]]

                if "PORT" in data[3]:
                    # Format: PORT_<dpid>_<port>
                    dpid = int(data[3].split("_")[1])
                    port = int(data[3].split("_")[2])
                    self.ports[(dpid, port)] = self.log_entry(from_node, to_node, traffic_type)
                else:
                    # Format: <cookie>,<cookie>,...,<cookie>
                    print str(line)
                    print str(data[3])
                    cookies = [int(x) for x in data[3].split(",")]
                    for cookie in cookies:
                        self.flows[cookie] = self.log_entry(from_node, to_node, traffic_type)

    def parse_logs(self, num_timesteps, flows_dir, ports_dir):
        for i in range(0, num_timesteps):
            file_name = '{num:03d}'.format(num=i)

            flow_file = flows_dir + "/" + file_name + ".flow"
            self.parse_flow_log(flow_file, i)

            port_file = ports_dir + "/" + file_name + ".ports"
            self.parse_port_log(port_file, i)

    def parse_flow_log(self, file, step):
        with open(file, 'r') as infile:
            for line in infile:
                data = line.split(" ")
                cookie = int(data[0])
                byte_count = int(data[-1])

                entry_label = self.flows[cookie]

                if len(self.data[entry_label]) == step + 1:
                    self.data[entry_label][step] += byte_count
                else:
                    self.data[entry_label].append(byte_count)

    def parse_port_log(self, file, step):
        with open(file, 'r') as infile:
            for line in infile:
                data = line.split(" ")
                dpid = int(''.join(c for c in data[0] if c.isdigit()))
                port = int(data[3]) if data[3].isdigit() else -1
                byte_count = int(data[-1])

                entry_label = self.ports[(dpid, port)]

                if len(self.data[entry_label]) == step + 1:
                    self.data[entry_label][step] += byte_count
                else:
                    self.data[entry_label].append(byte_count)

    def next_values(self, step=1):
        data = list()

        for key, value in self.data.iteritems():
            source = str(key.source)
            destination = str(key.destination)
            type = str(key.type)
            value = str(value[self.current_timestep + step] - value[self.current_timestep])

            data.append((source,
                         destination,
                         type,
                         value))

        self.current_timestep += step

        return data


class Publisher(object):
    def __init__(self, channel, address, port, db):
        self.redis_client = redis.StrictRedis(host=address, port=port, db=db)
        self.channel = channel

    def publish(self, message):
        self.redis_client.publish(self.channel, message)


def main(argv):
    log_history = LogHistory(argv.config, argv.flow_dir, argv.port_dir, argv.num_steps)

    channel = "sdx_stats"
    address = "192.168.99.100"
    port = 6379
    db = 0

    publisher = Publisher(channel, address, port, db)

    log_replay = LogReplay(log_history, publisher, 1)

    # start replay
    replay_thread = Thread(target=log_replay.start)
    replay_thread.daemon = True
    replay_thread.start()

    while replay_thread.is_alive():
        try:
            replay_thread.join(1)
        except KeyboardInterrupt:
            replay_thread.stop()

''' main '''
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    parser.add_argument('flow_dir', help='path of flow stats')
    parser.add_argument('port_dir', help='path of port stats')
    parser.add_argument('num_steps', help='number of timesteps')
    args = parser.parse_args()

    main(args)