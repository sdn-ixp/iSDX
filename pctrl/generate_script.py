import os
import json
import argparse

LOG = True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    parser.add_argument('script', help='the name of the output pctrl script')
    args = parser.parse_args()

    # locate config file
    # TODO: Separate the config files for each participant
    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..","examples",args.dir,"config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")


    with open(config_file, 'r') as f:
        config = json.load(f)


    participant_ids = [int(part) for part in config["Participants"].keys()]

    with open(args.script, 'w') as output:
    	for part_id in participant_ids:


    		script_line = "sudo python participant_controller.py test-ms"

    		script_line += ' ' + str(part_id) + ' &'


    		output.write(script_line)
    		output.write('\n')



    		