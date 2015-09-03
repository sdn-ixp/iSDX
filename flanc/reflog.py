#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
from time import time
from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Listener

''' Reference Monitor that just store all received Flow Mods in a file'''
class RefLog():

    def __init__(self, address, port, key, logfile):
        self.listener = Listener((address, port))
        
        self.log = open(logfile, "w")

    def start(self):
        self.receive = True
        self.receiver()

    ''' receiver '''
    def receiver(self):
        while self.receive:
            conn = self.listener.accept()

            msg = None
            while msg is None:
                try:
                    msg = conn.recv()
                    msg = json.loads(msg)
                    msg["time"] = time()
                    self.log.write(json.dumps(msg) + '\n')
                except:
                    pass

            conn.close()

    def stop(self):
        self.receive = False
	    self.receiver.join(1)
        self.log.close()
        
        
def main(argv):
    reflog_instance = RefLog(address, port, key, logfile)

    rl_thread = Thread(target=reflog_instance.start)
    rl_thread.daemon = True
    rl_thread.start()
    
    while rl_thread.is_alive():
        try:
            rl_thread.join(1)
        except KeyboardInterrupt:
            rl_thread.stop() 


''' main '''
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', help='ip address of the refmon')
    parser.add_argument('port', help='port of the refmon')
    parser.add_argument('key', help='authkey of the refmon')
    parser.add_argument('input', help='log output file')
    args = parser.parse_args()

    main(args)
