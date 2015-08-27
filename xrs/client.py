#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Arpit Gupta

import sys
from threading import Thread
from multiprocessing.connection import Client
import os
home_path = os.environ['HOME']
logfile = home_path+'/sdx-ryu/xrs/client.log'

'''Write output to stdout'''
def _write(stdout,data):
    stdout.write(data + '\n')
    stdout.flush()

''' Sender function '''
def _sender(conn,stdin,log):
    # Warning: when the parent dies we are seeing continual
    # newlines, so we only access so many before stopping
    counter = 0

    while True:
        try:
            line = stdin.readline().strip()

            if line == "":
                counter += 1
                if counter > 100:
                    break
                continue
            counter = 0

            conn.send(line)

            log.write(line + '\n')
            log.flush()

        except:
            pass

''' Receiver function '''
def _receiver(conn,stdout,log):

    while True:
        try:
            line = conn.recv()

            if line == "":
                continue

            _write(stdout, line)
            ''' example: announce route 1.2.3.4 next-hop 5.6.7.8 as-path [ 100 200 ] '''

            log.write(line + '\n')
            log.flush()

        except:
            pass

''' main '''
if __name__ == '__main__':

    log = open(logfile, "w")
    log.write('Open Connection \n')

    conn = Client(('localhost', 6000), authkey='xrs')

    sender = Thread(target=_sender, args=(conn,sys.stdin,log))
    sender.start()

    receiver = Thread(target=_receiver, args=(conn,sys.stdout,log))
    receiver.start()

    sender.join()
    receiver.join()

    log.close()
