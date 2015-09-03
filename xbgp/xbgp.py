#!/usr/bin/env python
#  Author:
#  Rudiger Birkner(ETH Zurich)

from time import sleep, time
from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Client

class ExaBGPEmulator(object):
    def __init__(self, address, port, authkey, input_file):
        self.input_file = input_file
        
        self.real_start_time = time()
        self.simulation_start_time = 0 
        
        self.run = True
        
        self.update_queue = Queue()
        
        self.conn = Client((address, port), authkey=authkey)

    def file_processor():
        with open(self.input_file) as infile:
            for line in infile:
                if line.startswith("TIME") and flag == 0:
                    flag = 1
                    tmp = {}
                    x = line.split("\n")[0].split(": ")
                    tmp[x[0]] = x[1]
                    
                elif flag == 1:
                    x = line.split("\n")[0].split(": ")
                    if len(x) >= 2:
                        tmp[x[0]] = x[1]
                    if 'Keepalive' in line:
                        # Only process Update Messages
                        tmp = {}
                        flag = 0
                    elif line.startswith("ANNOUNCE"):
                        tmp["ANNOUNCE"] = []
                        flag = 2
                    elif line.startswith("WITHDRAW"):
                        tmp["WITHDRAW"] = []
                        flag = 2

                elif flag == 2:
                    if line.startswith("\n"):
                        self.update_queue.put(tmp)
                        
                        if self.update_queue.qsize() > 50:
                            sleep(sleep_time(tmp["time"])/2)
                            
                        if not self.run:
                            break
                            
                        flag = 0
                    else:
                        x = line.split("\n")[0].split()[0]
                        if "ANNOUNCE" in tmp:
                            tmp["ANNOUNCE"].append(x)
                        else:
                            tmp["WITHDRAW"].append(x)
             
        self.run = False
                
    def bgp_update_sender():
        while self.run:
            bgp_update = self.update_queue.get()        
              
            if simulation_start_time == 0:
                self.real_start_time = time()
                self.simulation_start_time = bgp_update["time"]
                
            sleep(sleep_time(bgp_update["time"]))
            
            self.send_update(bgp_update)

    def sleep_time(update_time):
        time_diff = update_time - self.simulation_start_time
        wake_up_time = self.real_start_time + time_diff
        sleep_time = wake_up_time - time()
        
        return sleep_time
        
    def parse_update():
        update = {"exabgp": "3.4.8"}
        update["time"] = None
        update["type"] = None
        update["neighbor"] = {}
        
        
    def send_update():
        self.conn.send(line)
        
    def start(): 
        fp_thread = Thread(target=self.file_processor())
        fp_thread.daemon = True
        fp_thread.start()
        
        us_thread = Thread(target=self.bgp_update_sender())
        us_thread.daemon = True
        us_thread.start()
        
    def stop():
        self.run = False
        fp_thread.join()
        us_thread.join()
        self.conn.close()

def main(argv):
    exabgp_instance = ExaBGPEmulator(args.ip, args.port, args.authkey, args.input)

    eb_thread = Thread(target=exabgp_instance.start)
    eb_thread.daemon = True
    eb_thread.start()
    
    while eb_thread.is_alive():
        try:
            eb_thread.join(1)
        except KeyboardInterrupt:
            eb_thread.stop()        
        
''' main '''
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('ip', help='ip address of the xrs')
    parser.add_argument('port', help='port of the xrs')
    parser.add_argument('key', help='authkey of the xrs')
    parser.add_argument('input', help='bgp input file')
    args = parser.parse_args()

    main(args)
    
    
#{ "exabgp": "3.4.8", "time": 1437908090, "host" : "sdx-ryu", "pid" : "29575", "ppid" : "21680", "counter": 1, "type": "update", "neighbor": { "ip": "172.0.0.1", "address": { "local": "172.0.255.254", "peer": "172.0.0.1"}, "asn": { "local": "65000", "peer": "100"}, "message": { "update": { "attribute": { "origin": "igp", "as-path": [ 100 ], "confederation-path": [], "med": 0 }, "announce": { "ipv4 unicast": { "172.0.0.1": { "20.0.0.0/8": {  } } } } } }} }
#{ "exabgp": "3.4.8", "time": 1437908279, "host" : "sdx-ryu", "pid" : "29575", "ppid" : "21680", "counter": 1, "type": "notification", "notification": "shutdown"}
#{ "exabgp": "3.4.8", "time": 1437908274, "host" : "sdx-ryu", "pid" : "29575", "ppid" : "21680", "counter": 5, "type": "update", "neighbor": { "ip": "172.0.0.3", "address": { "local": "172.0.255.254", "peer": "172.0.0.3"}, "asn": { "local": "65000", "peer": "300"}, "message": { "update": { "withdraw": { "ipv4 unicast": { "10.0.0.0/8": {  }, "20.0.0.0/8": {  }, "30.0.0.0/8": {  } } } } }} }

