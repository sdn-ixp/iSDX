#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

from netaddr import *
import math


def bitsRequired(supersets):
    """ How many bits are needed to represent any set in this construction?
    """
    if supersets is None:
    	return 0

    logM = 1
    if len(supersets) > 1:
        logM = math.ceil(math.log(len(supersets), 2))
    maxS = max(len(superset) for superset in supersets)

    return int(logM + maxS)



def rulesRequired(supersets, rulecounts):
    """ How many rules will be needed by this superset construction?
    """
    if supersets is None:
    	return 0

    total = 0
    for superset in supersets:
        for part in superset:
            total += rulecounts[part]
    return total



def minimize_ss_rules_greedy(peerSets, ruleCounts, max_bits):
    """ Given a list of supersets and the number of rules needed regarding
        each participant in an outbound policy, greedily minimize
        the number of rules that will result from the superset grouping.
    """

    # defensive copy
    peerSets = [set(peerSet) for peerSet in peerSets]
    # smallest sets first
    peerSets.sort(key=len, reverse=True)
    # how many bits are allowed?


    # the longest superset determines the current mask size
    maxLength = max([len(prefix) for prefix in peerSets])

    while (len(peerSets) > 1):
        m = len(peerSets)

        bits = bitsRequired(peerSets)

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

def best_ss_to_expand_greedy(new_set, supersets, ruleWeights, max_mask):
    """ Returns index of the best superset to expand, given the rule
        weights and the maximum allowed mask size. -1 if none possible.
    """

    bestSuperset = None
    bestCost = float('inf')

    new_set = set(new_set)

    for superset in supersets:
        # if this merge would exceed the current mask size limit, skip it
        if len(new_set.union(superset)) > max_mask:
            continue

        # the rule increase is the sum of all rules that involve each part added to the superset
        cost = sum(ruleWeights[part] for part in new_set.difference(superset))
        if cost < bestCost:
            bestCost = cost
            bestSuperset = superset

    # if no merge is possible, return -1
    if bestSuperset == None:
        return -1

    return supersets.index(bestSuperset)





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
    activePeers = set(activePeers)

    return [activePeers.intersection(prefix) for prefix in prefixSets]



#
### VMAC AND VMAC MASK BUILDERS
#

# constructs a match VMAC for checking reachability
def vmac_participant_match(superset_id, participant_index, ss_instance):

    # add superset identifier
    vmac_bitstring = '{num:0{width}b}'.format(num=int(superset_id), width=(ss_instance.id_size))

    # set bit of participant
    vmac_bitstring += '{num:0{width}b}'.format(num=1, width=(participant_index+1))

    # padding
    vmac_bitstring += '{num:0{width}b}'.format(num=0, width=(ss_instance.VMAC_size-len(vmac_bitstring)))

    # convert bitstring to hexstring and then to a mac address
    vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=ss_instance.VMAC_size/4)
    vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,ss_instance.VMAC_size/4,2)])

    return vmac_addr

# constructs the accompanying mask for reachability checks
def vmac_participant_mask(participant_index, ss_instance):
    # a superset which is all 1's
    superset_bits = (1 << ss_instance.id_size) - 1

    return vmac_participant_match(superset_bits, participant_index, ss_instance)


# constructs a match VMAC for checking next-hop
def vmac_next_hop_match(participant_name, ss_instance, inbound_bit = False):

    # add participant identifier
    vmac_bitstring = '{num:0{width}b}'.format(num=participant_name, width=(ss_instance.VMAC_size))

    # set the 'inbound policy required' bit
    if inbound_bit:
        vmac_bitstring = '1' + vmac_bitstring[1:]

    # convert bitstring to hexstring and then to a mac address
    vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=ss_instance.VMAC_size/4)
    vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,ss_instance.VMAC_size/4,2)])

    return vmac_addr

# returns a mask on just participant bits
def vmac_next_hop_mask(ss_instance, inbound_bit = False):
    part_bits_only = (1 << ss_instance.best_path_size) - 1

    bitmask = vmac_next_hop_match(part_bits_only, ss_instance, inbound_bit)

    return bitmask


# constructs stage-2 VMACs (for both matching and assignment)
def vmac_part_port_match(participant_name, port_num, ss_instance, inbound_bit = False):
    part_bits = ss_instance.best_path_size
    remainder = ss_instance.VMAC_size - part_bits

    # padding and port identifier on the left
    vmac_bitstring_part1 = '{num:0{width}b}'.format(num=port_num, width=remainder)
    # participant identifier on the right
    vmac_bitstring_part2 = '{num:0{width}b}'.format(num=participant_name, width=part_bits)
    # combined
    vmac_bitstring = vmac_bitstring_part1 + vmac_bitstring_part2

    # set the 'inbound policy required' bit
    if inbound_bit:
        vmac_bitstring = '1' + vmac_bitstring[1:]

    # convert bitstring to hexstring and then to a mac address
    vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=ss_instance.VMAC_size/4)
    vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,ss_instance.VMAC_size/4,2)])

    return vmac_addr


# returns a mask on participant and port bits
def vmac_part_port_mask(ss_instance, inbound_bit = False):
    part_port_size = ss_instance.best_path_size + ss_instance.port_size
    part_port_bits = (1 << part_port_size) - 1

    bitmask = vmac_next_hop_match(part_port_bits, ss_instance, inbound_bit)

    return bitmask

# looks like 100000000000000
def vmac_only_first_bit(ss_instance):

    # return a match on participant 0 with inbound bit set to 1
    return vmac_next_hop_match(0, ss_instance, inbound_bit=True)


def get_all_participants_advertising(prefix, participants):
    participant_set = set()

    for participant_name in participants:
        route = participants[participant_name].get_route('input', prefix)
        if route:
            participant_set.add(participant_name)

    return participant_set


def get_all_participant_sets(xrs):
    participant_sets = []

    for prefix in xrs.prefix_2_VNH:
        participant_sets.append(get_all_participants_advertising(prefix, xrs.participants))

    return participant_sets


if __name__ == '__main__':
    "--Unit testing--"
    class FakeSS():
        def __init__(self):
            self.VMAC_size = 48
            self.superset_id_size = 5
            self.best_path_size = 16
            self.port_size = 10
            self.max_initial_bits = 20
            self.bitsRequired = bitsRequired

    part_name = 5
    ss_id = 4
    port_num = 10
    part_index = 20

    supersets = FakeSS()
    print vmac_participant_match(ss_id, part_name, supersets)
    print vmac_participant_mask(part_name, supersets)
    supersets = [[1,2], [2,3], [3,4]]
    a = set([1,2])
    b = set([2,3,4])
    print is_subset_of_superset(a, supersets)
    print is_subset_of_superset(b, supersets)
    print vmac_part_port_mask(supersets, True)
    print vmac_part_port_match(part_name, port_num, supersets, True)
    print vmac_part_port_match(part_name, port_num, supersets, False)
    print vmac_next_hop_mask(supersets, True)
    print vmac_next_hop_match(part_name, supersets, False)
    print vmac_participant_match(ss_id, part_index, supersets)
    print vmac_participant_mask(part_index, supersets)

    activePeers = [1,3,4,5]
    print clear_inactive_parts(supersets, activePeers)

    print vmac_only_first_bit(supersets)

    supersets = [[1,2,3], [2,3,4,5], [5,6], [4,5,6]]
    weights = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}

    new_set = [4,5,6,7]
    print best_ss_to_expand_greedy(new_set, supersets, weights, 4)
    new_set = [2,3,4,5,6]
    print best_ss_to_expand_greedy(new_set, supersets, weights, 4)


    print rulesRequired(supersets, weights)
    print bitsRequired(supersets)
    supersets = minimize_ss_rules_greedy(supersets, weights, supersets.max_initial_bits)
    print supersets
    print rulesRequired(supersets, weights)
    print bitsRequired(supersets)
