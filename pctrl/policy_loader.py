import os, sys
import json

np = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if np not in sys.path:
    sys.path.append(np)
from multiprocessing.connection import Client
from netaddr import IPNetwork
from socket import error as SocketError

import util.log

class PolicyLoader(object):
        def __init__(self, address, port, key, logger, sname):
                self.client = GenericClient2(address, port, key, logger, sname)

        def send_file(self, pol_file):
                with open(pol_file, 'r') as f:
	                data = json.load(f)
                f.close
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


                
script, pol_file = sys.argv

logger = util.log.getLogger('loader')
pol_loader = PolicyLoader('localhost', 5551, '', logger, 'pol_loader')

pol_loader.send_file(pol_file)
