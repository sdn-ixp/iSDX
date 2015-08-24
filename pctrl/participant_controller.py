#  Author:
#  Arpit Gupta (Princeton)
#  Robert MacDavid (Princeton)

import os
import sys
import time

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
    def __init__(self, id, vmac_mode, dp_mode, sender, config_file, policy_file):
        # participant id
        self.id = id

        # Vmac encoding mode
        self.vmac_mode = vmac_mode
        # Dataplane mode---multi table or multi switch
        self.dp_mode = dp_mode

        # Initialize participant params
        self.cfg = PConfig(config_file)

        # ExaBGP Peering Instance
        self.bgp_instance = self.cfg.get_bgp_instance()

        self.nexthop_2_part = self.cfg.get_nexthop_2_part()

        with open(policy_file, 'r') as f:
            self.policies = json.load(f)


        # used for tagging outbound rules as belonging to us
        self.port0_mac = self.cfg.port0_mac


        # Reference Monitor
        self.refmon_client = self.cfg.get_refmon_client()


        # VNHs related params
        self.num_VNHs_in_use = 0
        self.VNH_2_prefix = {}
        self.prefix_2_VNH = {}
        # TODO: Read from config file
        self.VNHs = IPNetwork(self.cfg.vnh_prefix)

        # Superset related params
        if self.vmac_mode == SUPERSETS:
            if LOG: print "Initializing SuperSets class"
            self.supersets = SuperSets(self)
        else:
            # TODO: create similar class and variables for MDS
            if LOG: print "Initializing MDS class"

            self.prefix_mds = []
            self.mds_old=[]

        # Keep track of flow rules pushed
        self.dp_pushed = []
        # Keep track of flow rules scheduled for push
        self.dp_queued = []

        # Fetch information about XRS Listener
        #TODO: read from a config file
        self.xrs_client = self.cfg.get_xrs_client()
        self.eh_client = self.cfg.get_eh_client()
        self.refmon_client = self.cfg.get_refmon_client()
        self.arp_client = self.cfg.get_arp_client()

        # class for building flow mod msgs to the reference monitor
        # TODO: read the key from the config file , we don't have config object right now.
        self.fm_builder = FlowModMsgBuilder(self.id, self.refmon_client.key)
        # thing that actually sends messages to the reference monitor
        self.sender = sender


    def start(self):
        # Start arp proxy
        # TODO: This needs immediate fixture
        self.sdx_ap = (self)
        self.ap_thread = Thread(target=self.sdx_ap.start)
        self.ap_thread.daemon = True
        self.ap_thread.start()

        # Start the event Handler Module
        self.set_event_handler()

        # Send flow rules for initial policies to the SDX's Reference Monitor
        self.initialize_dataplane()
        self.push_dp()

    def initialize_dataplane(self):
        "Read the config file and update the queued policy variable"
        # TODO: @Robert: Bring your logic of pushing initial inbound policies for each participant here

        port_count = len(self.cfg["Ports"])

        rule_msgs = init_inbound_rules(self.id, self.policies, self.supersets, port_count)

        self.dp_queued.extend(rule_msgs[changes])

        return 0

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
        self.sender.send(self.fm_builder.get_msg())

        return 0


    def stop(self):
        "Stop the Participants' SDN Controller"
        self.sdx_ap.stop()
        self.ap_thread.join()

        # TODO: Think of better way of terminating this listener
        self.listener_eh.close()



    def set_event_handler(self):
        '''Start the listener socket for network events'''
        self.listener_eh = Listener(tuple(self.cfg["EH_SOCKET"]), authkey=None)
        ps_thread = Thread(target=self.start_eh)
        ps_thread.daemon = True
        ps_thread.start()

    def start_eh(self):
        '''Socket listener for network events '''
        print "Event Handler started for", self.id
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
        reply = ''
        if 'bgp' in data:
            route = data['bgp']
            # Process the incoming BGP updates from XRS
            self.process_bgp_route(route)
        elif 'policy_change' in data:
            # Process the event requesting change of participants' policies
            self.process_policy_changes(data['policy_change'])

        return reply



    def process_policy_changes(self, add_policies, remove_policies,policies):
        "Process the changes in participants' policies"
        # TODO: Implement the logic of dynamically changing participants' outbound and inbound policy

        if self.vmac_mode == SUPERSETS:
            dp_msgs = ss_process_policy_change(self.supersets, add_policies, remove_policies, policies, 
                                                self.port_count, self.port0_mac)
        else:
            dp_msgs = []

        self.dp_queued.extend(dp_msgs)

        return 0


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

        if self.vmac_mode == 0:
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
                ss_changed_prefs = self.prefix_2_VNH.keys()

            "Dump the new rules into the dataplane queue."
            self.dp_queued.extend(flow_msgs["changes"])


        ################## END SUPERSET RESPONSE ##################

        else:
            # TODO: similar logic for MDS
            if LOG: print "Creating ctrlr messages for MDS scheme"

        # TODO: This should go
        if sdn_ctrlr_msgs:
            "Send sdn_ctrlr_msgs to participant's SDN controller as a network event"
            self.send_nw_event(sdn_ctrlr_msgs, 'vmac')

        changes, announcements = self.bgp_update_peers(updates)

        # Send gratuitous ARP responses for changed routes
        for change in changes:
            self.sdx_ap.send_gratuitous_arp(change)

        # Also send gratuitous ARP responses for changed VMACs
        for prefix in ss_changed_prefs:
            self.sdx_ap.send_gratuitous_arp(prefix)

        # Tell Route Server that it needs to announce these routes
        for announcement in announcements:
            # TODO: Complete the logic for this function
            self.send_announcements(announcement)

        return reply


    def send_nw_event(self, sdn_ctrlr_msgs, tag):
        # TODO: Do we really need this?
        "Send the sdn_ctrlr_msgs back to event handler"
        out = {}
        out['vmac'] = msgs
        # TODO: Add the logic to send this message to Participant's event handler


    def send_announcements(self, announcement):
        "Send the announcements to XRS"
        print "Sending the announcements"

    def vnh_assignment(self, update):
        "Assign VNHs for the advertised prefixes"
        if self.vmac_mode == 0:
            " Superset"
            # TODO: Do we really need to assign a VNH for each advertised prefix?
            if ('announce' in update):
                prefix = update['announce']['prefix']

            if (prefix not in self.prefix_2_VNH):
                # get next VNH and assign it the prefix
                self.num_VNHs_in_use += 1
                vnh = str(self.VNHs[self.num_VNHs_in_use])

                self.prefix_2_VNH[prefix] = vnh
                self.VNH_2_prefix[vnh] = prefix
        else:
            "Disjoint"
            # TODO: @Robert: Place your logic here for VNH assignment for MDS scheme
            if LOG: print "VNH assignment called for disjoint vmac_mode"

    def bgp_update_peers(self, updates):
        # TODO: Verify if the new logic makes sense
        changes = []
        announcements = []
        for update in updates:
            if 'announce' in update:
                prefix = update['announce']['prefix']
            else:
                prefix = update['withdraw']['prefix']
            prev_route = self.rib["output"][prefix]
            best_route = self.rib["local"][prefix]
            best_route["next_hop"] = str(self.prefix_2_VNH[prefix])

            if ('announce' in update):
                # Check if best path has changed for this prefix
                if not bgp_routes_are_equal(best_route, prev_route):
                    # store announcement in output rib
                    self.delete_route("output", prefix)
                    self.add_route("output", prefix, best_route)

                    if prev_route:
                        changes.append({"participant": self.id,
                                        "prefix": prefix,
                                        "VNH": self.prefix_2_VNH[prefix]})

                    # announce the route to each router of the participant
                    for port in self.cfg["Ports"]:
                        # TODO: Create a sender queue and import the announce_route function
                        announcements.append(announce_route(port["IP"], prefix,
                                            route["next_hop"], route["as_path"]))

            elif ('withdraw' in update):
                # A new announcement is only needed if the best path has changed
                if best_route:
                    "There is a best path available for this prefix"
                    if not bgp_routes_are_equal(best_route, prev_route):
                        "There is a new best path available now"
                        # store announcement in output rib
                        self.delete_route("output", prefix)
                        self.add_route("output", prefix, best_route)
                        if prev_route:
                            changes.append({"participant": self.id,
                                            "prefix": prefix,
                                            "VNH": self.prefix_2_VNH[prefix]})
                        for port in self.cfg["Ports"]:
                                announcements.append(announce_route(port["IP"],
                                                     prefix, best_route["next_hop"],
                                                     best_route["as_path"]))

                else:
                    "Currently there is no best route to this prefix"
                    if prev_route:
                        # Clear this entry from the output rib
                        self.delete_route("output", prefix)
                        for port in self.cfg["Ports"]:
                            # TODO: Create a sender queue and import the announce_route function
                            announcements.append(withdraw_route(port["IP"],
                                                                prefix,
                                                                self.prefix_2_VNH[prefix]))

        return changes, announcements


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
    base_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "..","examples",args.dir,"controller","sdx_config"))
    config_file = os.path.join(base_path, "sdx_global.cfg")

    # locate the participant's policy file as well
    policy_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            "..","examples",args.dir,"controller","participant_policies"))

    policy_filenames_file = os.path.join(base_path, "sdx_policies.cfg")
    with open(policy_filenames_file, 'r') as f:
        policy_filenames = json.load(f)
    policy_filename = policy_filenames[str(args.id)]

    policy_file = os.path.join(base_path, policy_filename)

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
