#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)

from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Listener

''' bgp server '''
class server():

    def __init__(self, ah_socket):
        self.listener = Listener((ah_socket[0], ah_socket[1]), authkey='xrs')

        self.sender_queue = Queue()
        self.receiver_queue = Queue()

    def start(self):
        self.conn = self.listener.accept()
        print 'Connection accepted from', self.listener.last_accepted

        self.sender = Thread(target=_sender, args=(self.conn,self.sender_queue))
        self.sender.start()

        self.receiver = Thread(target=_receiver, args=(self.conn,self.receiver_queue))
        self.receiver.start()

''' sender '''
def _sender(conn,queue):
    while True:
        try:
            line = queue.get()
            conn.send(line)
        except:
            pass

''' receiver '''
def _receiver(conn,queue):
    while True:
        try:
            line = conn.recv()
            queue.put(line)
        except:
            pass

''' main '''
if __name__ == '__main__':
    while True:
        server = server()
        while True:
            try:
                print server.receiver_queue.get()
                server.sender_queue.put('announce route %s next-hop %s as-path [ %s ]' % ('200.0.0.0/16','172.0.0.1','100'))
            except:
                print 'thread ended'
                break
