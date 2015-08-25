#  Author:
#  Arpit Gupta (Princeton)
#  Robert MacDavid (Princeton)

import os
import sys
import time

from multiprocessing.connection import Listener
import json
from netaddr import *
import argparse
from peer import BGPPeer as BGPPeer
from supersets2 import SuperSets

from ss_rule_scheme import *

from lib import *

LOG = True

MULTISWITCH = 0
MULTITABLE  = 1

SUPERSETS = 0
MDS       = 1



class ParticipantController():
    def __init__(self, id, config_file, policy_file):
        # participant id
        self.id = id

        # Initialize participant params
        self.cfg = PConfig(config_file)
        # Vmac encoding mode
        # self.cfg.vmac_mode = config_file["vmac_mode"]
        # Dataplane mode---multi table or multi switch
        # self.cfg.dp_mode = config_file["dp_mode"]


        self.load_policies(policy_file)


        # The port 0 MAC is used for tagging outbound rules as belonging to us
        self.port0_mac = self.cfg.port0_mac

        self.nexthop_2_part = self.cfg.get_nexthop_2_part()

        # VNHs related params
        self.num_VNHs_in_use = 0
        self.VNH_2_prefix = {}
        self.prefix_2_VNH = {}


        # Superset related params
        if self.cfg.vmac_mode == SUPERSETS:
            if LOG: print "Initializing SuperSets class"
            self.supersets = SuperSets(self)
        else:
            # TODO: create similar class and variables for MDS
            if LOG: print "Initializing MDS class"
            self.mds = None

        # Keep track of flow rules pushed
        self.dp_pushed = []
        # Keep track of flow rules which are scheduled to be pushed
        self.dp_queued = []
       


    def start(self):
        # Start all clients/listeners/whatevs
        if LOG: print "Starting controller for participant", self.id

        # ExaBGP Peering Instance
        self.bgp_instance = self.cfg.get_bgp_instance()

        # Route server client, Reference monitor client, Arp Proxy client
        self.xrs_client = self.cfg.get_xrs_client()
        self.arp_client = self.cfg.get_arp_client()
        self.refmon_client = self.cfg.get_refmon_client()
         # class for building flow mod msgs to the reference monitor
        self.fm_builder = FlowModMsgBuilder(self.id, self.refmon_client.key)

        # Start the event handler
        eh_socket = self.cfg.get_eh_info()
        self.listener_eh = Listener(eh_socket, authkey=None)
        ps_thread = Thread(target=self.start_eh)
        ps_thread.daemon = True
        ps_thread.start()


        # Send flow rules for initial policies to the SDX's Reference Monitor
        self.initialize_dataplane()
        self.push_dp()


        
    def load_policies(self, policy_file):
        # Load policies from file

        with open(policy_file, 'r') as f:
            self.policies = json.load(f)

        port_count = len(self.cfg.ports)

        # sanitize the input policies
        if 'inbound' in policies:
            for policy in policies['inbound']:
                if 'action' not in policy:
                    continue
                if 'fwd' in policy['action']:
                    continue
                if int(policy['action']['fwd']) >= port_count:
                    policy['action']['fwd'] = 0




    def initialize_dataplane(self):
        "Read the config file and update the queued policy variable"

        rule_msgs = init_inbound_rules(self.id, self.policies, self.supersets)

        self.dp_queued.extend(rule_msgs[changes])



    def push_dp(self):
        '''
        (1) Check if there are any policies queued to be pushed
        (2) Send the queued policies to reference monitor
        '''

        if LOG: print "Pushing current flow mod queue."

        # it is crucial that dp_queued is traversed chronologically
        for flowmod in self.dp_queued:

            self.fm_builder.add_flow_mod(**mod)

            self.dp_pushed.append(mod)

        self.dp_queued = []
        self.refmon_client.send(self.fm_builder.get_msg())



    def stop(self):
        "Stop the Participants' SDN Controller"
        if LOG: print "Ending controller for participant", self.id

        # TODO: confirm that this isn't silly
        self.xrs_client = None
        self.refmon_client = None
        self.arp_client = None

        # TODO: Think of better way of terminating this listener
        self.listener_eh.close()


    def start_eh(self):
        '''Socket listener for network events '''
        if LOG: print "Event Handler started for", self.id
        while True:
            conn_eh = self.listener_eh.accept()
            tmp = conn.recv()
            data = json.loads(tmp)

            # Starting a thread for independently processing each incoming network event
            event_processor_thread = Thread(target = process_event, args = [data])
            event_processor_thread.daemon = True
            event_processor_thread.start()

            # Send a message back to the sender.
            reply = "Event Received"
            conn_eh.send(reply)
            conn_eh.close()


    def process_event(self, data):
        "Locally process each incoming network event"

        if 'bgp' in data:
            route = data['bgp']
            # Process the incoming BGP updates from XRS
            self.process_bgp_route(route)

        elif 'policy' in data:
            # Process the event requesting change of participants' policies
            change_info = data['policy']
            '''
            change_info = 
            {
                removal_cookies = [cookie1, ...], # Cookies of deleted policies
                new_policies = 
                {
                    <policy file format>
                }

            }
            '''
            self.process_policy_changes(change_info)

        elif 'arp' in data:
            requested_vnh = data['arp']
            self.process_arp_request(requested_vnh)



    def process_policy_changes(self, change_info):
        "Process the changes in participants' policies"
        # TODO: Implement the logic of dynamically changing participants' outbound and inbound policy

        if self.cfg.vmac_mode == SUPERSETS:
            dp_msgs = ss_process_policy_change(self.supersets, add_policies, remove_policies, policies, 
                                                self.port_count, self.port0_mac)
        else:
            dp_msgs = []

        self.dp_queued.extend(dp_msgs)

        self.push_dp()

        return 0


    def process_arp_request(self, requested_vnh):
        vmac = ""
        if self.cfg.vmac_mode == SUPERSETS:
            vmac = self.supersets.get_vmac(self, vnh)
        else:
            vmac = "whoa" # MDS vmac goes here

        # send an arp response to each of our routers
        for port in self.cfg.ports:
            part_ip = port["IP"]
            part_mac = port["MAC"]
            arp_fields = {"vnhip":vnh,
                          "vmac_addr":vmac,
                          "dstip":part_ip,
                          "dst_mac":part_mac}

            self.arp_client.send(arp_fields)



    def process_bgp_route(self, route):
        "Process each incoming BGP advertisement"
        reply = ''
        # Map to update for each prefix in the route advertisement.
        updates = self.bgp_instance.update(route)

        # TODO: This step should be parallelized
        # TODO: The decision process for these prefixes is going to be same, we
        # should think about getting rid of such redundant computations.
        for update in updates:
            self.bgp_instance.decision_process_local(update)
            self.vnh_assignment(update)

        if self.cfg.vmac_mode == 0:
        ################## SUPERSET RESPONSE TO BGP ##################
            # update supersets
            "Map the set of BGP updates to a list of superset expansions."
            ss_changes, ss_changed_prefs = self.supersets.update_supersets(self, updates)
            # ss_changed_prefs are prefixes for which the VMAC bits have changed
            # these prefixes must have gratuitous arps sent


            "Map the superset expansions to a list of new flow rules."
            flow_msgs = update_outbound_rules(ss_changes, self.policies,
                                              self.supersets, self.port0_mac)

            "If a recomputation event was needed, wipe out the flow rules."
            if flow_msgs["type"] == "new":
                wipe_msgs = self.msg_clear_all_outbound()
                self.dp_queued.extend(wipe_msgs)

                #if a recomputation was needed, all VMACs must be reARPed (is that a word?)
                garp_required_vnhs = self.VNH_2_prefix.keys()
            else:
                # if recomputation wasn't needed, only garp next-hops with changed VMACs
                garp_required_vnhs = [prefix_2_VNH[prefix] for prefix in ss_changed_prefs]

            "Dump the new rules into the dataplane queue."
            self.dp_queued.extend(flow_msgs["changes"])


        ################## END SUPERSET RESPONSE ##################

        else:
            # TODO: similar logic for MDS
            if LOG: print "Creating ctrlr messages for MDS scheme"


        changed_vnhs, announcements = self.bgp_instance.bgp_update_peers(updates, 
                                        self.prefix_2_VNH, self.cfg.ports)

        """ Combine the VNHs which have changed BGP default routes with the
            VNHs which have changed supersets.
        """
        changed_vnhs = set(changed_vnhs)
        changed_vnhs.update(garp_required_vnhs)

        # Send gratuitous ARP responses for all them
        for vnh in changed_vnhs:
            self.process_arp_request(vnh)


        # Tell Route Server that it needs to announce these routes
        for announcement in announcements:
            # TODO: Complete the logic for this function
            self.send_announcements(announcement)

        return reply



    def send_announcements(self, announcement):
        "Send the announcements to XRS"
        print "Sending the announcements"

    def vnh_assignment(self, update):
        "Assign VNHs for the advertised prefixes"
        if self.cfg.vmac_mode == 0:
            " Superset"
            # TODO: Do we really need to assign a VNH for each advertised prefix?
            if ('announce' in update):
                prefix = update['announce']['prefix']

            if (prefix not in self.prefix_2_VNH):
                # get next VNH and assign it the prefix
                self.num_VNHs_in_use += 1
                vnh = str(self.cfg.VNHs[self.num_VNHs_in_use])

                self.prefix_2_VNH[prefix] = vnh
                self.VNH_2_prefix[vnh] = prefix
        else:
            "Disjoint"
            # TODO: @Robert: Place your logic here for VNH assignment for MDS scheme
            if LOG: print "VNH assignment called for disjoint vmac_mode"



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='the directory of the example')
    parser.add_argument('id', type=int,
                   help='participant id (integer)')
    parser.add_argument('vmac_mode', type=int,
                  help='VMAC encoding scheme: 0--Super Set, 1---Disjoint Set')
    parser.add_argument('dp_mode', type=int,
                    help='Data Plane Topology: 0--Multi Switch, 1---Multi Table')
    args = parser.parse_args()

    # locate config file
    # TODO: Separate the config files for each participant
    config_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    config_file = os.path.join(config_path, "pctrlr.cfg")





    # locate the participant's policy file as well
    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..","examples",args.dir,"controller","sdx_config"))

    policy_filenames_file = os.path.join(base_path, "sdx_policies.cfg")
    with open(policy_filenames_file, 'r') as f:
        policy_filenames = json.load(f)
    policy_filename = policy_filenames[str(args.id)]


    policy_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            "..","examples",args.dir,"controller","participant_policies"))

    policy_file = os.path.join(policy_path, policy_filename)

    print "Starting the controller ", str(args.id), " with config file: ", config_file
    print "And policy file: ", policy_file

    sender = None

    # start controller
    ctrlr = ParticipantController(args.id, args.vmac_mode, sender, args.dp_mode, config_file, policy_file)
    ctrlr_thread = Thread(target=ctrlr.start)
    ctrlr_thread.daemon = True
    ctrlr_thread.start()

    while ctrlr_thread.is_alive():
        try:
            ctrlr_thread.join(1)
        except KeyboardInterrupt:
            ctrlr.stop()
