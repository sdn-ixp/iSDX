#!/usr/bin/env python

import os, sys
import argparse
import json

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
from multiprocessing.connection import Client
from socket import error as SocketError

import util.log

class PolicyLoader(object):
        def __init__(self, address, port, key, logger, sname):
                self.client = GenericClient2(address, port, key, logger, sname)

        def send_file(self, f):
	        data = json.load(f)
                self.client.send(data)

class GenericClient2(object):
    def __init__(self, address, port, key, logger, sname):
        self.address = address
        self.port = int(port)
        self.key = key
        self.logger = logger
        self.serverName = sname

        while True: # keep going until we break out inside the loop
            try:
                self.logger.debug('Attempting to connect to '+self.serverName+' server at '+str(self.address)+' port '+str(self.port))
                self.conn = Client((self.address, self.port))
                self.logger.debug('Connect to '+self.serverName+' successful.')
                break
            except SocketError as serr:
                if serr.errno == errno.ECONNREFUSED:
                    self.logger.debug('Connect to '+self.serverName+' failed because connection was refused (the server is down). Trying again.')
                else:
                    # Not a recognized error. Treat as fatal.
                    self.logger.debug('Connect to '+self.serverName+' gave socket error '+str(serr.errno))
                    raise serr
            except:
                self.logger.exception('Connect to '+self.serverName+' threw unknown exception')
                raise

    def send(self, msg):
        self.conn.send(json.dumps(msg))
        self.logger.debug('send message: ' + str(msg))

    def poll(self, t):
        return self.conn.poll(t)

    def recv(self):
        return self.conn.recv()

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send policy changes to a participant.')
    parser.add_argument('-H', '--Host', help='host (default is localhost)')
    parser.add_argument('port', type=int)
    parser.add_argument('policy_file', type=argparse.FileType('r'))
    args = parser.parse_args()

#print 'args ' + str(args)

logger = util.log.getLogger('loader')
pol_loader = PolicyLoader('localhost', args.port, '', logger, 'policy server')

pol_loader.send_file(args.policy_file)
