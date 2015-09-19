import os
import json

''' main '''
if __name__ == '__main__':
	asn_2_ip = json.load(open("../asn_2_ip.json", 'r'))

	for asn in asn_2_ip:
		cmd = "ln -s ../ribs.txt ribs_" + asn + ".txt"
		print cmd
		os.system(cmd)
