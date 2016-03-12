#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (ETH Zurich)

import argparse
import logging
import time
import redis
import math

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
    "INBOUND_B1": "InBound",
    "INBOUND_C1": "InBound",
    "INBOUND_C2": "InBound",
    "ARP": "Main",
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
    "arp_v": "arp_v",
    "default": "default",
    "default_v": "default",
    "b1_v": "b1",
    "c1_v": "c1",
    "c2_v": "c2",
}

messages = {
    "network_graph": {
        "type": "difference",
        "values": [("Outbound", "Main", []),
                   ("Main", "Outbound", []),
                   ("InBound", "Main", []),
                   ("Main", "InBound", []),
                   ("Main", "Router-A", []),
                   ("Router-A", "Main", []),
                   ("Main", "Router-B", []),
                   ("Router-B", "Main", []),
                   ("Main", "Router-C1", []),
                   ("Router-C1", "Main", []),
                   ("Main", "Router-C2", []),
                   ("Router-C2", "Main", []),
                   ("Main", "ARP-Proxy", []),
                   ("ARP-Proxy", "Main", []),
                   ("Main", "BGP-Proxy", []),
                   ("BGP-Proxy", "Main", []),
                   ("Outbound", "InBound", []),
                   ("InBound", "Outbound", []),
                   ],
    },
    "time_series": {
        "type": "total",
        "values": [("Main", "Router-B", ["default"]),
                   ("Main", "Router-C1", ["default"]),
                   ("Main", "Router-C2", ["default"])],
    },
}


class LogReplay(object):
    def __init__(self, log_history, publisher, time_step=1, debug=False):
        self.logger = logging.getLogger("LogReplay")
        if debug:
            self.logger.setLevel(logging.DEBUG)

        self.log_history = log_history
        self.time_step = time_step
        self.publisher = publisher

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
                #self.publisher.publish(message)

            sleep_time = self.time_step - time.time() + start_time
            if sleep_time < 0:
                sleep_time = 0
                self.logger.debug("processing took longer than the time step")
            self.logger.info("sleep for " + str(sleep_time) + "s")
            time.sleep(sleep_time)

    def stop(self):
        self.run = False


class LogHistory(object):
    def __init__(self, config, flows_dir, ports_dir, num_timesteps, debug=False):
        self.logger = logging.getLogger("LogHistory")
        if debug:
            self.logger.setLevel(logging.DEBUG)

        self.log_entry = namedtuple("LogEntry", "source destination type")
        self.ports = defaultdict(list)
        self.flows = defaultdict(list)

        self.data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.current_timestep = 0
        self.total_timesteps = num_timesteps

        self.parse_config(config)
        self.parse_logs(num_timesteps, flows_dir, ports_dir)
        self.info()

    def parse_config(self, config):
        with open(config, 'r') as infile:
            for line in infile:
                # catch comment lines and empty lines
                if line[0] == "#" or line.isspace():
                    continue

                # build data structure which we can use to assign the logs to the correct edge and traffic type
                data = line.split()
                from_node = name_mapping[data[0]]
                to_node = name_mapping[data[1]]
                traffic_type = traffic_mapping[data[2]]

                if "PORT" in data[3]:
                    # Format: PORT_<dpid>_<port>
                    dpid = int(data[3].split("_")[1])
                    port = int(data[3].split("_")[2])
                    self.ports[(dpid, port)].append(self.log_entry(from_node, to_node, traffic_type))
                else:
                    # Format: <cookie>,<cookie>,...,<cookie>
                    cookies = [int(x) for x in data[3].split(",")]
                    for cookie in cookies:
                        self.flows[cookie].append(self.log_entry(from_node, to_node, traffic_type))

    def parse_logs(self, num_timesteps, flows_dir, ports_dir):
        for i in range(0, num_timesteps):
            file_name = '{num:03d}'.format(num=i)

            flow_file = flows_dir + "/" + file_name + ".flow"
            self.parse_flow_log(flow_file, i)

            port_file = ports_dir + "/" + file_name + ".ports"
            self.parse_port_log(port_file, i)

        # add missing values
        self.clean_logs()

    def parse_flow_log(self, file, step):
        with open(file, 'r') as infile:
            for line in infile:
                data = line.split()
                cookie = int(data[0])
                byte_count = int(data[-1])

                if cookie in self.flows:
                    entry_labels = self.flows[cookie]

                    for entry_label in entry_labels:
                        self.data[(entry_label.source, entry_label.destination)][entry_label.type][step] += byte_count

    def parse_port_log(self, file, step):
        with open(file, 'r') as infile:
            for line in infile:
                data = line.split()

                dpid = int(''.join(c for c in data[1] if c.isdigit()))
                port = int(data[3]) if data[3].isdigit() else -1
                byte_count = int(data[-1])

                if (dpid, port) in self.ports:
                    entry_labels = self.ports[(dpid, port)]

                    for entry_label in entry_labels:
                        self.data[(entry_label.source, entry_label.destination)][entry_label.type][step] += byte_count

    def next_values(self, step=1):
        data = list()

        for message_type, settings in messages.iteritems():
            label = str(message_type)

            for message in settings["values"]:

                source = str(message[0])
                destination = str(message[1])
                traffic_types = message[2]

                for traffic_type, values in self.data[(source, destination)].iteritems():
                    if not traffic_types or traffic_type in traffic_types:
                        type = str(traffic_type)
                        if settings["type"] == "difference":
                            value = values[self.current_timestep + step] - values[self.current_timestep]

                            if value < 0:
                                self.logger.info("negative value (" + str(value) + ") for " +
                                                 source + "-" + destination + "-" + traffic_type +
                                                 " at step " + str(self.current_timestep + step))
                                value = math.fabs(value)

                            value = str(value)
                        elif settings["type"] == "total":
                            value = str(values[self.current_timestep + step])

                        data.append((label,
                                     source,
                                     destination,
                                     type,
                                     value))

        self.current_timestep += step

        return data

    def clean_logs(self):
        lengths = []
        for edge, data in self.data.iteritems():
            for type, values in data.iteritems():
                lengths.append(len(values))
        max_length = max(lengths)

        for edge, data in self.data.iteritems():
            for type, values in data.iteritems():
                for i in range(0, max_length):
                    if i not in values:
                        values[i] = values[i - 1]

    def info(self):
        # data sources
        info_message = "data sources: got " + str(len(self.flows)) + " flows and " + str(len(self.ports)) + " ports, "
        debug_message = "data sources\n"
        for key, value in self.flows.iteritems():
            debug_message += str(key) + " " + str(value) + "\n"
        for key, value in self.ports.iteritems():
            debug_message += str(key) + " " + str(value) + "\n"

        # edges in the graph
        max_length = max([len(values) for values in self.data.values()])
        info_message += "graph edges: got " + str(len(self.data)) + " edges with " + str(max_length) + " values each"

        debug_message += "\ngraph edges\n"
        for key, values in self.data.iteritems():
            debug_message += str(key) + " with " + str(len(values)) + " values\n"

        self.logger.info(info_message)
        self.logger.debug(debug_message)


class Publisher(object):
    def __init__(self, channel, address, port, db):
        self.redis_client = redis.StrictRedis(host=address, port=port, db=db)
        self.channel = channel

    def publish(self, message):
        self.redis_client.publish(self.channel, message)


def main(argv):
    logging.basicConfig(level=logging.INFO)

    log_history = LogHistory(argv.config, argv.flow_dir, argv.port_dir, int(argv.num_steps), debug=False)

    channel = "sdx_stats"
    address = "192.168.99.100"
    port = 6379
    db = 0

    publisher = Publisher(channel, address, port, db)

    log_replay = LogReplay(log_history, publisher, int(argv.timestep), debug=False)

    # start replay
    replay_thread = Thread(target=log_replay.start)
    replay_thread.daemon = True
    replay_thread.start()

    while replay_thread.is_alive():
        try:
            replay_thread.join(1)
        except KeyboardInterrupt:
            log_replay.stop()

''' main '''
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path of config file')
    parser.add_argument('flow_dir', help='path of flow stats')
    parser.add_argument('port_dir', help='path of port stats')
    parser.add_argument('num_steps', help='number of steps')
    parser.add_argument('timestep', help='time step')
    args = parser.parse_args()

    main(args)