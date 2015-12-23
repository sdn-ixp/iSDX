#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Arpit Gupta

from multiprocessing.connection import Client
import os
import sys
from threading import Thread

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
import util.log


sendLogger = util.log.getLogger('XRS-send')
recvLogger = util.log.getLogger('XRS-recv')

'''Write output to stdout'''
def _write(stdout,data):
    stdout.write(data + '\n')
    stdout.flush()

''' Sender function '''
def _sender(conn,stdin):
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

            sendLogger.debug(line)

        except:
            pass

''' Receiver function '''
def _receiver(conn,stdout):

    while True:
        try:
            line = conn.recv()

            if line == "":
                continue

            _write(stdout, line)
            ''' example: announce route 1.2.3.4 next-hop 5.6.7.8 as-path [ 100 200 ] '''

            recvLogger.debug(line)

        except:
            pass

''' main '''
if __name__ == '__main__':

    conn = Client(('localhost', 6000), authkey='xrs')

    sender = Thread(target=_sender, args=(conn,sys.stdin))
    sender.start()

    receiver = Thread(target=_receiver, args=(conn,sys.stdout))
    receiver.start()

    sender.join()
    receiver.join()
