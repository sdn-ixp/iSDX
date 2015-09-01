#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Robert MacDavid (Princeton)

import json

from ss_lib import *


LOG = True

class SuperSets():
    def __init__(self, pctrl, config_file = None):
        self.max_bits = 31
        self.max_initial_bits = 26
        self.best_path_size = 16
        self.VMAC_size = 48
        self.port_size = 8
        if config_file is not None:

            if LOG: print pctrl.idp, "Initializing SuperSets with config file."

            with open(config_file, 'r') as f:
                config = json.load(f)
                config = config["VMAC"]["Options"]
                #self.max_bits =         int(config["Superset Bits"])
                #self.max_initial_bits = self.max_bits - 4
                self.best_path_size =   int(config["Next Hop Bits"])
                self.VMAC_size =        int(config["VMAC Size"])
                self.port_size =        int(config["Port Bits"])

                self.max_bits = self.VMAC_size - self.best_path_size - 1
                self.max_initial_bits = self.max_bits - 4

        else:
            if LOG: print pctrl.idp, "Initializing SuperSets WITHOUT config file."
        if LOG:
            print pctrl.idp, "Max bits:", self.max_bits, "Best path bits:", self.best_path_size
            print pctrl.idp, "VMAC size:", self.VMAC_size, "Port size:", self.port_size

        # this is decided each time a recomputation occurs
        self.mask_size = 0
        self.id_size = 0
        self.supersets = []


    def initial_computation(self, pctrl):
        if LOG: print pctrl.idp, "Superset intial computation running..",

        self.recompute_all_supersets(pctrl)

        changes = []

        for ss_id, superset in enumerate(self.supersets):
            for part_index, participant in enumerate(superset):
                changes.append({"participant_id": participant,
                                           "superset": ss_id,
                                           "position": part_index})
        sdx_msgs = {"type":"new", "changes":changes}

        if LOG: 
            print pctrl.idp, "Superset computation complete. Supersets:"
            print pctrl.idp, ">>", self.supersets

        return sdx_msgs


    def recompute_rulecounts(self, pctrl):
        policies = pctrl.policies

        rulecounts = {}
        # construct the participant weight matrix
        if ('outbound' in policies):
            out_policies = policies['outbound']
            for policy in out_policies:
                if ('fwd' in policy['action']):

                    fwd_part = int(policy['action']['fwd'])
                    if fwd_part not in rulecounts:
                        rulecounts[fwd_part] = 0
                    rulecounts[fwd_part] += 1

        return rulecounts


    def update_supersets(self, pctrl, updates):
        policies = pctrl.policies

        if LOG: print pctrl.idp, "Updating supersets..."

        sdx_msgs = {"type": "update", "changes": []}

        # the list of prefixes who will have changed VMACs
        impacted_prefixes = []

        self.rulecounts = self.recompute_rulecounts(pctrl)

        # if supersets haven't been computed at all yet
        if len(self.supersets) == 0:
            sdx_msgs = self.initial_computation(pctrl)
            return (sdx_msgs, impacted_prefixes)


        for update in updates:
            if ('withdraw' in update):
                prefix = update['withdraw']['prefix']
                # withdraws always change the bits of a VMAC
                impacted_prefixes.append(prefix)
            if ('announce' not in update):
                continue
            prefix = update['announce']['prefix']

            # get set of all participants advertising that prefix
            new_set = get_all_participants_advertising(pctrl, prefix)

            # clean out the inactive participants
            new_set = set(new_set)
            new_set.intersection_update(self.rulecounts.keys())

            # if the prefix group is still a subset, no update needed
            if is_subset_of_superset(new_set, self.supersets):
                continue

            expansion_index = best_ss_to_expand_greedy(new_set, self.supersets,
                                                self.rulecounts, self.mask_size)


            # if no merge is possible, recompute from scratch
            if expansion_index == -1:
                if LOG: print pctrl.idp, "No SS merge was possible. Recomputing."
                self.recompute_all_supersets(pctrl)

                sdx_msgs = {"type": "new", "changes": []}

                for superset in self.supersets:
                    for participant in superset:
                        sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": self.supersets[superset_index].index(participant)})
                break



            # if merge is possible, do the merge and add the new rules required
            else:
                # an expansion means the VMAC for this prefix changed
                impacted_prefixes.append(prefix)

                bestSuperset = self.supersets[expansion_index]

                new_members = list(new_set.difference(bestSuperset))
                bestSuperset.extend(new_members)

                if LOG: 
                    print pctrl.idp, "Merge possible. Merging", new_set, "into superset", bestSuperset,
                    print "with new members", new_members

                for participant in new_members:
                    sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": expansion_index,
                                                   "position": bestSuperset.index(participant)})



        # check which participants joined a new superset and communicate to the SDX controller
        return (sdx_msgs, impacted_prefixes)



    def recompute_all_supersets(self, pctrl):

        if LOG: print pctrl.idp, "~Recomputing all Supersets...",

        self.rulecounts = self.recompute_rulecounts(pctrl)
        # get all sets of participants advertising the same prefix
        peer_sets = get_prefix2part_sets(pctrl)
        peer_sets = clear_inactive_parts(peer_sets, self.rulecounts.keys())
        peer_sets = removeSubsets(peer_sets)

        self.supersets = minimize_ss_rules_greedy(peer_sets, self.rulecounts, self.max_initial_bits)

        # impose an ordering on each superset by converting sets to lists
        for i in range(len(self.supersets)):
            self.supersets[i] = list(self.supersets[i])

        # fix the mask size after a recomputation event
        self.mask_size = self.max_bits - 1
        self.id_size = 1

        # if there is more than one superset, set the field sizes appropriately
        if len(self.supersets) > 1:
            self.id_size = int(math.ceil(math.log(len(self.supersets), 2)))
            self.mask_size -= self.id_size

        if LOG: 
            print "done.~"
            print pctrl.idp, "Supersets:"
            print pctrl.idp, ">>", self.supersets



    def get_vmac(self, pctrl, vnh):
        """ Returns a VMAC for advertisements.
        """
        bgp_instance = pctrl.bgp_instance
        nexthop_2_part = pctrl.nexthop_2_part
        VNH_2_prefix = pctrl.VNH_2_prefix


        vmac_bitstring = ""
        vmac_addr = ""

        if vnh not in VNH_2_prefix:
            if LOG: print "VNH", vnh, "not found in get_vmac call!"
            return vmac_addr
        prefix = VNH_2_prefix[vnh]


        # first part of the returned tuple is next hop
        route = bgp_instance.get_route('local', prefix)
        next_hop = route[1]
        if next_hop not in nexthop_2_part:
            if LOG: print "Next Hop", next_hop, "not found in get_vmac call!"
            return vmac_addr
        nexthop_part = nexthop_2_part[next_hop]

        # the participants who are involved in policies
        active_parts = self.recompute_rulecounts(pctrl).keys()

        # the set of participants which advertise this prefix
        prefix_set = set(get_all_participants_advertising(pctrl, prefix))

        # remove everyone but the active participants!
        prefix_set.intersection_update(active_parts)

        # find the superset it belongs to
        ss_id = -1
        for i, superset in enumerate(self.supersets):
            if prefix_set.issubset(superset):
                ss_id = i
                break
        if ss_id == -1:
            if LOG: print pctrl.idp, "In get_vmac: Prefix", prefix, "doesn't belong to any superset (This should never happen) >>"
            if LOG: print pctrl.idp, ">> Supersets at the moment of failure:", self.supersets
            if LOG: print pctrl.idp, ">> Set of advertisers of prefix", prefix, "is", prefix_set
            return vmac_addr


        # build the mask bits
        set_bitstring = ""
        for part in self.supersets[i]:
            if part in prefix_set and part in pctrl.cfg.peers_out:
                set_bitstring += '1'
            else:
                set_bitstring += '0'

        if (len(set_bitstring) < self.mask_size):
            pad_len = self.mask_size - len(set_bitstring)
            set_bitstring += '0' * pad_len


        # debug
        #if LOG: print "****DEBUG: Next Hop part", type(nexthop_part), self.best_path_size, type(ss_id), self.id_size

        id_bitstring = '{num:0{width}b}'.format(num=ss_id, width=self.id_size)

        nexthop_bitstring = '{num:0{width}b}'.format(num=nexthop_part, width=self.best_path_size)

        vmac_bitstring = '1' + id_bitstring + set_bitstring + nexthop_bitstring


        if len(vmac_bitstring) != 48:
            print "BAD VMAC SIZE!! FIELDS ADD UP TO", len(vmac_bitstring)

        # convert bitstring to hexstring and then to a mac address
        vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=self.VMAC_size/4)
        vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,self.VMAC_size/4,2)])

        return vmac_addr




def get_prefix2part_sets(pctrl):
    prefixes = pctrl.prefix_2_VNH.keys()

    groups = []

    for prefix in prefixes:
        group = get_all_participants_advertising(pctrl, prefix)
        groups.append(group)

    if LOG: print pctrl.idp, "Prefix2Part called. Returning", groups[:50], "(this should not be empty)"

    return groups




def get_all_participants_advertising(pctrl, prefix):
    bgp_instance = pctrl.bgp_instance
    nexthop_2_part = pctrl.nexthop_2_part

    routes = bgp_instance.get_routes('input',prefix)

    parts = set([])


    for route in routes:
        # first part of the returned tuple is next hop
        next_hop = route[1]

        if next_hop in nexthop_2_part:
            parts.add(nexthop_2_part[next_hop])
        else:
            if LOG: print pctrl.idp, "In subcall of prefix2part: Next hop", next_hop, "NOT in nexthop_2_part"

    return parts





""" placeholder funcs ## UNCOMMENT THESE FOR UNIT TESTS

def get_all_participants_advertising(crap1, crap2):
    if crap1 == 'poot':
        return [2,3,4,8]
    return [1,2,3,4,5,6]


def get_all_participant_sets():
    return [[1,2,3], [2,3,4], [4,5,6], [1,2,3,7], [3,4,7,8]]

"""


if __name__ == '__main__':
    """ Unit testing.
    """
    part_name = 3

    out =   {
    "outbound": [
                    {"action":{"fwd": 1}},
                    {"action":{"fwd": 2}},
                    {"action":{"fwd": 2}},
                    {"action":{"fwd": 3}},
                    {"action":{"fwd": 3}},
                    {"action":{"fwd": 3}},
                    {"action":{"fwd": 4}},
                    {"action":{"fwd": 7}},
                    {"action":{"fwd": 8}},
                ]
            }


    class FakeSDX():
        def __init__(self):
            self.VMAC_size = 48
            self.superset_id_size = 5
            self.best_path_size = 16
            self.port_size = 10
            self.max_initial_bits = 5
            self.bitsRequired = bitsRequired


            self.participants = {part_name:{'policies':out}}
            self.policies = out

    sdx = FakeSDX()



    ss = SuperSets(sdx, None, part_name)
    print ss.initial_computation()
    print ss.supersets

    updates = [{'announce':{'prefix':'poot'}}]

    print ss.update_supersets(updates)

    print ss.supersets
