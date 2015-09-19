import os
import json
import argparse
from multiprocessing.connection import Listener

''' main '''
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('server', help='server we are running this code on')
	parser.add_argument('example_name', help='Example Name Directory')
	args = parser.parse_args()

	#print args
	
	server_filename = "server_settings.cfg"
	server_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "examples", args.example_name))
	server_file = os.path.join(server_path, server_filename)
	server_settings = json.load(open(server_file, 'r'))
	#print server_settings
	address = "0.0.0.0"
	port = int(server_settings[args.server]["PORT"])
	key = None
	listener = Listener(tuple([address, port]), authkey=key)
	while True:
		conn = listener.accept()
		#print 'Connection accepted from', listener.last_accepted
		line = conn.recv()
		#print line
		if "terminate" in line: 
			print "terminate"
			conn.close()
			break
