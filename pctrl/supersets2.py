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
    def __init__(self, sdx, xrs, participant_name, config_file=None):
        self.max_bits = 26
        self.max_initial_bits = 22
        self.best_path_size = 16
        self.VMAC_size = 48
        if config_file is not None:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.max_bits =         config["max_bits"]
                self.max_initial_bits = config["max_initial_bits"]
                self.best_path_size =   config["best_path_size"]
                self.VMAC_size =        config["vmac_size"]

        # this is decided each time a recomputation occurs
        self.mask_size = 0
        self.supersets = []

        self.sdx = sdx
        self.participant_name = participant_name
        self.xrs = xrs

        self.rulecounts = {}
        self.recompute_rulecounts()


    def initial_computation(self):
        self.recompute_all_supersets()

        sdx_msgs = {"type": "new",
                    "changes": []}

        for i in range(len(self.supersets)):
            superset = self.supersets[i]
            for participant in superset:
                sdx_msgs["changes"].append({"participant_id": participant,
                                           "superset": i,
                                           "position": superset.index(participant)})

        return sdx_msgs



    def recompute_rulecounts(self):
        self.rulecounts = {}
        # construct the participant weight matrix
        participant = self.sdx.participants[self.participant_name]
        if ('outbound' in participant['policies']):
            policies = participant['policies']['outbound']
            for policy in policies:
                if ('fwd' in policy['action']):

                    fwd_part = int(policy['action']['fwd'])
                    if fwd_part not in self.rulecounts:
                        self.rulecounts[fwd_part] = 0
                    self.rulecounts[fwd_part] += 1



    def update_supersets(self, updates):
        sdx_msgs = {"type": "update",
                    "changes": []}

        self.recompute_rulecounts()

        for update in updates:
            if ('announce' not in update):
                continue
            prefix = update['announce']['prefix']

            # get set of all participants advertising that prefix
            new_set = get_all_participants_advertising(prefix, self.sdx.participants)
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
                bestSuperset = self.supersets[expansion_index]

                new_members = list(new_set.difference(bestSuperset))
                bestSuperset.extend(new_members)

                for participant in new_members:
                    sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": expansion_index,
                                                   "position": bestSuperset.index(participant)})



        # check which participants joined a new superset and communicate to the SDX controller
        return sdx_msgs


    def recompute_all_supersets(self):
        self.recompute_rulecounts()
        # get all sets of participants advertising the same prefix
        peer_sets = get_all_participant_sets(self.xrs)
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

    sdx = FakeSDX()



    ss = SuperSets(sdx, None, part_name)
    print ss.initial_computation()
    print ss.supersets

    updates = [{'announce':{'prefix':'poot'}}]

    print ss.update_supersets(updates)

    print ss.supersets











