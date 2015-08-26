#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import sys
sys.path.insert(0, '../xrs/')

from bgp_interface import *

#from ..xrs.bgp_interface import *

from ss_lib import *


LOG = False

class SuperSets():
    def __init__(self, pctrl, config = None):
        self.max_bits = 30
        self.max_initial_bits = 26
        self.best_path_size = 16
        self.VMAC_size = 48
        if config is not None:
            self.max_bits = config()
            {
                "Participant Field": 31,
                "Next Hop Field": 12,
                "Port Field": 10,
                "VMAC Size": 48
        }
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.max_bits =         config["max_bits"]
                self.max_initial_bits = config["max_initial_bits"]
                self.best_path_size =   config["best_path_size"]
                self.VMAC_size =        config["vmac_size"]

        # this is decided each time a recomputation occurs
        self.mask_size = 0
        self.supersets = []


    def initial_computation(self, pctrl):

        self.recompute_all_supersets(pctrl)

        sdx_msgs = {"type": "new",
                    "changes": []}

        for ss_id, superset in enumerate(self.supersets):
            for part_index, participant in enumerate(superset):
                sdx_msgs["changes"].append({"participant_id": participant,
                                           "superset": ss_id,
                                           "position": part_index})

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

        sdx_msgs = {"type": "update",
                    "changes": [], "prefixes": []}

        # the list of prefixes who will have changed VMACs
        impacted_prefixes = []

        self.rulecounts = self.recompute_rulecounts(policies)

        # if supersets haven't been computed at all yet
        if len(self.supersets) == 0:
            sdx_msgs = initial_computation(pctrl)
            return sdx_msgs


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

            sdx_msgs["prefixes"].append(prefix)

            expansion_index = best_ss_to_expand_greedy(new_set, self.supersets,
                                                self.rulecounts, self.mask_size)


            # if no merge is possible, recompute from scratch
            if expansion_index == -1:
                self.recompute_all_supersets()

                sdx_msgs = {"type": "new",
                            "changes": []}

                for superset in self.supersets:
                    for participant in superset:
                        sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": self.supersets[superset_index].index(participant)})



            # if merge is possible, do the merge and add the new rules required
            else:
                # an expansion means the VMAC for this prefix changed
                impacted_prefixes.append(prefix)

                bestSuperset = self.supersets[expansion_index]

                new_members = list(new_set.difference(bestSuperset))
                bestSuperset.extend(new_members)

                for participant in new_members:
                    sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": expansion_index,
                                                   "position": bestSuperset.index(participant)})



        # check which participants joined a new superset and communicate to the SDX controller
        return sdx_msgs, impacted_prefixes



    def recompute_all_supersets(self, pctrl):
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
        self.mask_size = self.max_bits
        if len(self.supersets) > 1:
            self.mask_size -= math.ceil(math.log(len(self.supersets)-1, 2))




    def get_prefix2part_sets(self, pctrl):
        prefixes = pctrl.prefix_2_VNH.keys()

        groups = []

        for prefix in prefixes:
            group = get_all_participants_advertising(pctrl, prefix)
            groups.append(group)

        return groups




    def get_all_participants_advertising(self, pctrl, prefix):
        bgp_instance = pctrl.bgp_instance
        nexthop_2_part = pctrl.nexthop_2_part

        routes = bgp_instance.get_routes(self,'input',prefix)

        parts = set([])


        for route in routes:
            # first part of the returned tuple is next hop
            next_hop = route[0]

            if next_hop in nexthop_2_part:
                parts.add(nexthop_2_part[next_hop])

        return parts


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
        next_hop = bgp_instance.get_route('local', prefix)[0]
        if next_hop not in nexthop_2_part:
            if LOG: print "Next Hop", next_hop, "not found in get_vmac call!"
            return vmac_addr
        nexthop_part = nexthop_2_part[next_hop]


        prefix_set = set(get_all_participants_advertising(pctrl, prefix))

        # find the superset it belongs to
        ss_id = -1
        for i, superset in enumerate(self.supersets):
            if prefix_set.issubset():
                ss_id = i
                break
        if ss_id == -1:
            if LOG: print "Prefix", prefix, "doesn't belong to any superset?"
            return vmac_addr


        # build the mask bits
        set_bitstring = ""
        for part in self.supersets[i]:
            if part in prefix_set and part in pctrl.cfg["Peers"]:
                set_bitstring += '1'
            else:
                set_bitstring += '0'

        if (len(set_bitstring) < self.mask_size):
            pad_len = self.mask_size - len(set_bitstring)
            set_bitstring += '0' * pad_len

        # bits for the ss ID is total - inbound bit - mask - next hop
        id_size = self.VMAC_size - 1 - self.mask_size - self.best_path_size

        id_bitstring = '{num:0{width}b}'.format(num=ss_id, width=id_size)

        nexthop_bitstring = '{num:0{width}b}'.format(num=nexthop_part,
                                                    width=self.best_path_size)

        vmac_bitstring = '1' + id_bitstring + set_bitstring + nexthop_bitstring

        # convert bitstring to hexstring and then to a mac address
        vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=self.VMAC_size/4)
        vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,self.VMAC_size/4,2)])

        return vmac_addr





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
