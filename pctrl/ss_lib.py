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

def bitstring_2_mac(vmac_bitstring, ss_instance):
    vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=ss_instance.VMAC_size/4)
    vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,ss_instance.VMAC_size/4,2)])

    return vmac_addr

# constructs a match VMAC for checking reachability
def vmac_participant_match(superset_id, participant_index, ss_instance, inbound_bit = False):
    
    # inbound bit
    in_bit = '0'
    # this should never happen but maybe someone will need it!
    if inbound_bit:
        in_bit = '1'

    # first chunk is the superset identifier
    vmac_bitstring_part1 = '{num:0{width}b}'.format(num=int(superset_id), width=(ss_instance.id_size))

    # second chunk is the bit corresponding to the participant reachability check
    mask_bits = ['0'] * ss_instance.mask_size
    mask_bits[participant_index] = '1'
    vmac_bitstring_part2 =  ''.join(mask_bits)

    # final chunk is padding which is vmac_size minus current buildstring size
    current_size = len(in_bit) + len(vmac_bitstring_part1) + len(vmac_bitstring_part2)
    padding_size = ss_instance.VMAC_size - current_size
    vmac_bitstring_part3 = '0' * padding_size

    # add the inbound bit and the three chunks together
    vmac_bitstring = in_bit + vmac_bitstring_part1 + vmac_bitstring_part2 + vmac_bitstring_part3

    # convert bitstring to hexstring and then to a mac address
    return bitstring_2_mac(vmac_bitstring, ss_instance)


# constructs the accompanying mask for reachability checks
def vmac_participant_mask(participant_index, ss_instance, inbound_bit = False):
    # a superset which is all 1's
    superset_bits = (1 << ss_instance.id_size) - 1

    return vmac_participant_match(superset_bits, participant_index, ss_instance, inbound_bit)


# constructs a match VMAC for checking next-hop
def vmac_next_hop_match(participant_name, ss_instance, inbound_bit = False):

    # add participant identifier
    vmac_bitstring = '{num:0{width}b}'.format(num=participant_name, width=(ss_instance.VMAC_size))

    # set the 'inbound policy required' bit
    if inbound_bit:
        vmac_bitstring = '1' + vmac_bitstring[1:]

    # convert bitstring to hexstring and then to a mac address
    return bitstring_2_mac(vmac_bitstring, ss_instance)

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
    return bitstring_2_mac(vmac_bitstring, ss_instance)


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




def get_vmac_test(prefix_set, ss_instance):
    " Returns a VMAC for advertisements. use this for debugging only"
    self = ss_instance


    vmac_bitstring = ""
    vmac_addr = ""

    nexthop_part = 5



    # the participants who are involved in policies
    active_parts = [1,2,3,4,5,6]


    # remove everyone but the active participants!
    prefix_set.intersection_update(active_parts)

    # find the superset it belongs to
    ss_id = -1
    for i, superset in enumerate(self.supersets):
        if prefix_set.issubset(superset):
            ss_id = i
            break
    if ss_id == -1:
        if LOG: print pctrl.idp, "Prefix", prefix, "doesn't belong to any superset? >>"
        if LOG: print pctrl.idp, ">> Supersets:", self.SuperSets
        if LOG: print pctrl.idp, ">> Set of prefix", prefix, "=", prefix_set
        return vmac_addr

    peers_out = [1,2,3,4,5,6]

    # build the mask bits
    set_bitstring = ""
    for part in self.supersets[i]:
        if part in prefix_set and part in peers_out:
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

    # convert bitstring to hexstring and then to a mac address
    return bitstring_2_mac(vmac_bitstring, ss_instance)



if __name__ == '__main__':
    "--Unit testing--"

    supersets = [[1,2], [2,3], [3,4,5,6]]

    class FakeSS():
        def __init__(self):
            self.max_bits = 31
            self.max_initial_bits = 27
            self.VMAC_size = 48

            self.best_path_size = 16
            self.port_size = 16

            self.mask_size = 16
            self.id_size = 15

            self.supersets = supersets

    part_name = 5
    ss_id = 4
    port_num = 10
    part_index = 20

    ss_instance = FakeSS()
    #print "--next_hop vmacs--"
    #print vmac_next_hop_match(part_name, ss_instance)
    #print vmac_next_hop_mask(ss_instance)


    prefix_set = set([3,5,6])

    print "VMAC format: II:II:MM:MM:HH:HH"

    print "Get vmac 3,4,5,6:", get_vmac_test(set([3,4,5,6]), ss_instance)
    print "Get vmac 3,5,6,_:", get_vmac_test(set([3,5,6]), ss_instance)
    print "Get vmac 2,3,_,_:", get_vmac_test(set([2,3]), ss_instance)
    print "Get vmac 1,2,_,_:", get_vmac_test(set([1,2]), ss_instance)
    print 'get reachabilibuddy mask 2,3:', vmac_participant_match(2, 3, ss_instance)
    print 'get reachabilibuddy mask 2,2:', vmac_participant_match(2, 2, ss_instance)
    print 'get reachabilibuddy mask 2,1:', vmac_participant_match(2, 1, ss_instance)
    print 'get reachabilibuddy mask 2,0:', vmac_participant_match(2, 0, ss_instance)

    print 'get reachabilibuddy mask 3,0:', vmac_participant_match(3, 0, ss_instance)
    print 'get reachabilibuddy mask 2,0:', vmac_participant_match(2, 0, ss_instance)
    print 'get reachabilibuddy mask 1,0:', vmac_participant_match(1, 0, ss_instance)
    print 'get reachabilibuddy mask 0,0:', vmac_participant_match(0, 0, ss_instance)
                                                            #ss_id, part_index





    a = set([1,2])
    b = set([2,3,4])

    '''
    print "--Is subset--"
    print is_subset_of_superset(a, ss_instance.supersets)
    print is_subset_of_superset(b, ss_instance.supersets)

    print "--part_port vmacs--"
    print vmac_part_port_mask(ss_instance, True)
    print vmac_part_port_match(part_name, port_num, ss_instance, True)
    print vmac_part_port_match(part_name, port_num, ss_instance, False)

    print "--next_hop vmacs--"
    print vmac_next_hop_mask(ss_instance, True)
    print vmac_next_hop_match(part_name, ss_instance, False)

    print "--reachability vmacs--"
    print vmac_participant_match(ss_id, part_index, ss_instance)
    print vmac_participant_mask(part_index, ss_instance)

    
    activePeers = [1,3,4,5]
    print clear_inactive_parts(supersets, activePeers)

    print vmac_only_first_bit(ss_instance)

    supersets = [[1,2,3], [2,3,4,5], [5,6], [4,5,6]]
    weights = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7}

    new_set = [4,5,6,7]
    print best_ss_to_expand_greedy(new_set, supersets, weights, 4)
    new_set = [2,3,4,5,6]
    print best_ss_to_expand_greedy(new_set, supersets, weights, 4)


    print rulesRequired(supersets, weights)
    print bitsRequired(supersets)
    supersets = minimize_ss_rules_greedy(supersets, weights, ss_instance.max_initial_bits)
    print supersets
    print rulesRequired(supersets, weights)
    print bitsRequired(supersets)
    '''
