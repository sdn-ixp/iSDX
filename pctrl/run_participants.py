import os
import json
import argparse

''' main '''
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('base', help='Base Installation Directory')
	parser.add_argument('server', help='server we are running this code on')
	parser.add_argument('example_name', help='Example Name Directory')
	parser.add_argument('output_file', help='Output file name')
	args = parser.parse_args()

	print args
	
	server_filename = "server_settings.cfg"
	server_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "examples", args.example_name))
	server_file = os.path.join(server_path, server_filename)
	server_settings = json.load(open(server_file, 'r'))
	print server_settings

	from_id = int(server_settings[args.server]["FROM"])
	to_id = int(server_settings[args.server]["TO"]) + 1

	for i in range(from_id, to_id):
		cmd = "cd " + args.base + "/pctrl ; python participant_controller.py " + args.example_name + " " + str(i) + " " + args.output_file + " > /dev/null 2>&1 &"
		print cmd
		os.system(cmd)



