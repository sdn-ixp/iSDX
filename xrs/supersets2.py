#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from bgp_interface import *

LOG = False

class SuperSets():
    def __init__(self, sdx, participant_name):
        # TODO: @Rudiger, we can parse this from a config file
        self.max_bits = 26
        self.max_initial_bits = 22
        self.best_path_size = 16
        self.VMAC_size = 48

        # this is decided each time a recomputation occurs
        self.mask_size = 0
        self.supersets = []

        self.sdx = sdx
        self.participant_name = participant_name

        self.rulecounts = {}
        recompute_rulecounts()



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



	def bitsRequired(self):
	    """ How many bits are needed to represent any set in this construction?
	    """
	    supersets = self.supersets
	    if supersets is None:
	    	return 0

	    logM = 0
	    if len(supersets) > 1:
	        logM = math.ceil(math.log(len(supersets) - 1, 2))
	    maxS = max(len(superset) for superset in supersets)

	    return int(logM + maxS)



	def rulesRequired(self):
	    """ How many rules will be needed by this superset construction?
	    """
	    rulecounts = self.rulecounts
	    supersets = self.supersets
	    if supersets is None:
	    	return 0

	    total = 0
	    for superset in supersets:
	        for part in superset:
	            total += rulecounts[part]
	    return total



	def minimize_rules_greedy(self, peerSets, ruleCounts):
	    """ Given a list of supersets and the number of rules needed regarding
	        each participant in an outbound policy, greedily minimize
	        the number of rules that will result from the superset grouping.
	    """

	    # defensive copy
	    peerSets = [set(peerSet) for peerSet in peerSets]
	    # smallest sets first
	    peerSets.sort(key=len, reverse=True)
	    # how many bits are allowed?
	    max_bits = self.max_initial_bits


	    # the longest superset determines the current mask size
	    maxLength = max([len(prefix) for prefix in peerSets])

	    while (len(peerSets) > 1):
	        m = len(peerSets)

	        bits = bitsRequired()

	        # if M is 1 + 2^X for some X, logM will decrease after a merge
	        if ((m - 1) & (m - 2)) == 0:
	            bits = bits - 1


	        # bestSet1 and bestSet2 are our top choices for merging
	        bestImpact = 0
	        bestSet1 = None
	        bestSet2 = None

	        # for every pair of sets
	        for set1 in peerSets:
	            for set2 in peerSets:
	                if (set1 == set2):
	                    continue
	                
	                unionSize = len(set1.union(set2))

	                # if the merge would cause us to exceed the bit limit
	                if bits + max(0, unionSize - maxLength) > max_bits:
	                    continue


	                # choose the pair with the biggest impact on rulecount
	                impact = 0
	                for part in set1.intersection(set2):
	                    if part not in ruleCounts:
	                        a = list(ruleCounts.keys())
	                        b = list(set1.intersection(set2))
	                        c = list(set1)
	                        d = list(set2)
	                        a.sort()
	                        b.sort()
	                        c.sort()
	                        d.sort()
	                        print part, "not in", a
	                        print "Intersection:", b
	                        print "Set 1:", c
	                        print "Set 2:", d
	                    impact += ruleCounts[part]
	                
	                if (impact > bestImpact):
	                    bestImpact = impact
	                    bestSet1 = set1
	                    bestSet2 = set2

	        # if the best change is an increase, break
	        if (bestImpact == 0):
	            break
	        # merge the two best sets
	        bestSet1.update(bestSet2)
	        peerSets.remove(bestSet2)
	        # update the mask size if necessary
	        maxLength = max(len(bestSet1), maxLength)

	    return peerSets


    def update(self, updates):
        sdx_msgs = {"type": "update",
                    "changes": []}

        recompute_rulecounts()

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
                recompute_all_supersets(self)

                sdx_msgs = {"type": "new",
                            "changes": []}

                for superset in self.supersets:
                    for participant in superset:
                        sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": self.supersets[superset_index].index(participant)})



            # if merge is possible, do the merge and add the new rules required
            else:
            	superset_index = self.supersets.index(bestSuperset)
            	new_members = list(new_set.difference(bestSuperset))
            	bestSuperset.append(new_members)

            	for participant in new_members:
            		sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": self.supersets[superset_index].index(participant)})



        # check which participants joined a new superset and communicate to the SDX controller
        return sdx_msgs


    def recompute_all_supersets(self):
    	recompute_rulecounts()
        # get all sets of participants advertising the same prefix
        peer_sets = get_all_participant_sets(self)
        peer_sets = clear_inactive_parts(peer_sets)
        peer_sets = removeSubsets(peer_sets)

        self.supersets = minimize_rules_greedy(peer_sets)

        # impose an ordering on each superset by converting sets to lists
        for i in range(len(self.supersets)):
        	self.supersets[i] = list(self.supersets[i])

        # fix the mask size after a recomputation event
        self.mask_size = self.max_bits
        if len(self.supersets) > 1:
            self.mask_size -= math.ceil(math.log(len(self.supersets)-1, 2))



def is_subset_of_superset(subset, supersets):
    for superset in supersets:
        if ((set(superset)).issuperset(subset)):
            return True
    return False



def removeSubsets(sets):
    """ Removes all subsets from a list of sets.
    """
    final_answer = []

    # defensive copy
    sets = [set(_set) for _set in sets]
    sets.sort(key=len, reverse=True)
    i = 0
    while i < len(sets):
        final_answer.append(sets[i])

        for j in reversed(range(i+1, len(sets))):
            if sets[j].issubset(sets[i]):
                del sets[j]

        i += 1

    return final_answer



def clear_inactive_parts(prefixSets, activePeers):
	for group in prefixSets:
		group.intersection_update(activePeers)
	return prefixSets






