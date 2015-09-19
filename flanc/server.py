#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)

from threading import Thread
from multiprocessing import Queue
from multiprocessing.connection import Listener

''' bgp server '''
class server():

    def __init__(self, ref_socket, key):
	print ref_socket
        self.listener = Listener(ref_socket, authkey=key)
        self.sender_queue = Queue()
        self.receiver_queue = Queue()

    def start(self):
        #print 'Connection accepted from', self.listener.last_a

        #self.sender = Thread(target=_sender, args=(self.sender_queue))
        #self.sender.start()

        self.receiver = Thread(target=_receiver, args=(self.receiver_queue,self.listener))
        self.receiver.start()

''' sender '''
def _sender(queue):
    while True:
        try:
	    conn = listener.accept()
            line = queue.get()
            conn.send(line)
	    conn.close()
        except:
            pass

''' receiver '''
def _receiver(queue, listener):
    while True:	
        try:
            conn = listener.accept()
	    print 'Connection accepted from', listener.last_accepted
            line = conn.recv()
            queue.put(line)
	    conn.close()
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
