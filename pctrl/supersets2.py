#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from bgp_interface import *
from ss_lib import *

LOG = False

class SuperSets():
    def __init__(self, sdx, participant_name, config_file=None):
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

        self.rulecounts = {}
        self.recompute_rulecounts()



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
        sdx_msg = {"type": "update",
                    "changes": []}

        self.recompute_rulecounts()

        for update in updates:
            if ('announce' not in update):
            	continue
            prefix = update['announce']['prefix']

            # get set of all participants advertising that prefix
            new_set = get_all_participants_advertising(prefix, self.sdx.participants)
            # clean out the inactive participants
            new_set.intersection_update(set(rulecounts.keys()))

            # if the prefix group is still a subset, no update needed
            if is_subset_of_superset(new_set, self.supersets):
            	continue

        	# else, find the best superset to merge
            bestSuperset = None
            bestCost = 1000000
            
            for superset in self.supersets:
                # if this merge would exceed the current mask size limit, skip it
                if len(new_set.union(superset)) > self.mask_size:
                    continue

                # the rule increase is the sum of all rules that involve each part added to the superset
                cost = sum(ruleWeights[part] for part in new_set.difference(superset))
                if cost < bestCost:
                    bestCost = cost
                    bestSuperset = superset

            # if no merge is possible, recompute from scratch
            if bestSuperset == None:
                self.recompute_all_supersets()

                sdx_msg = {"type": "new",
                            "changes": []}

                for superset in self.supersets:
                    for participant in superset:
                        sdx_msg["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": self.supersets[superset_index].index(participant)})



            # if merge is possible, do the merge and add the new rules required
            else:
            	superset_index = self.supersets.index(bestSuperset)
            	new_members = list(new_set.difference(bestSuperset))
            	bestSuperset.append(new_members)

            	for participant in new_members:
            		sdx_msg["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": self.supersets[superset_index].index(participant)})



        # check which participants joined a new superset and communicate to the SDX controller
        return [sdx_msgs]


    def recompute_all_supersets(self):
    	self.recompute_rulecounts()
        # get all sets of participants advertising the same prefix
        peer_sets = get_all_participant_sets(self)
        peer_sets = clear_inactive_parts(peer_sets)
        peer_sets = removeSubsets(peer_sets)

        self.supersets = self.minimize_rules_greedy(peer_sets)

        # impose an ordering on each superset by converting sets to lists
        for i in range(len(self.supersets)):
        	self.supersets[i] = list(self.supersets[i])

        # fix the mask size after a recomputation event
        self.mask_size = self.max_bits
        if len(self.supersets) > 1:
            self.mask_size -= math.ceil(math.log(len(self.supersets)-1, 2))






