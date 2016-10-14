#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Robert MacDavid (Princeton)

from threading import RLock
import math
from ss_lib import minimize_ss_rules_greedy, best_ss_to_expand_greedy, is_subset_of_superset, removeSubsets, clear_inactive_parts

import json

lock = RLock()

class SuperSets(object):
    def __init__(self, pctrl, config):
        self.best_path_size =   int(config["Next Hop Bits"])
        self.VMAC_size =        int(config["VMAC Size"])
        self.port_size =        int(config["Port Bits"])

        self.max_bits = self.VMAC_size - self.best_path_size - 1
        self.max_initial_bits = self.max_bits - 4

        self.logger = pctrl.logger

        self.logger.debug("Max bits: "+str(self.max_bits)+" Best path bits: "+str(self.best_path_size))
        self.logger.debug("VMAC size: "+str(self.VMAC_size)+" Port size: "+str(self.port_size))

        # this is decided each time a recomputation occurs
        self.mask_size = 0
        self.id_size = 0
        self.supersets = []


    def initial_computation(self, pctrl):
        self.logger.debug("Superset intial computation running..")

        self.recompute_all_supersets(pctrl)

        changes = []

        for ss_id, superset in enumerate(self.supersets):
            for part_index, participant in enumerate(superset):
                changes.append({"participant_id": participant,
                                           "superset": ss_id,
                                           "position": part_index})
        sdx_msgs = {"type":"new", "changes":changes}

        self.logger.debug("Superset computation complete. Supersets: >> "+str(self.supersets)+" sdx_msgs: "+str(sdx_msgs))

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
        self.logger.debug(": RuleCounts:: "+str(rulecounts))

        return rulecounts


    def update_supersets(self, pctrl, updates):
        with lock:
            policies = pctrl.policies

            self.logger.debug("Updating supersets...")

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
                    prefix = update['withdraw'].prefix
                    # withdraws always change the bits of a VMAC
                    impacted_prefixes.append(prefix)
                if ('announce' not in update):
                    continue
                prefix = update['announce'].prefix

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
                    # Maybe can replace this with call to initial_computation()
                    self.logger.debug("No SS merge was possible. Recomputing.")
                    self.logger.debug('pre-recompute:  ' + str(self.supersets))
                    self.recompute_all_supersets(pctrl)
                    self.logger.debug('post-recompute: ' + str(self.supersets))

                    sdx_msgs = {"type": "new", "changes": []}

                    for superset_index, superset in enumerate(self.supersets):
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

                    self.logger.debug("Merge possible. Merging "+str(new_set)+" into superset "+str(bestSuperset))
                    self.logger.debug("with new members "+str(new_members))

                    for participant in new_members:
                        sdx_msgs["changes"].append({"participant_id": participant,
                            "superset": expansion_index,
                            "position": bestSuperset.index(participant)})

            return (sdx_msgs, impacted_prefixes)


    def recompute_all_supersets(self, pctrl):

        self.logger.debug("~Recomputing all Supersets...")

        self.rulecounts = self.recompute_rulecounts(pctrl)
        # get all sets of participants advertising the same prefix
        peer_sets = get_prefix2part_sets(pctrl)
        peer_sets = clear_inactive_parts(peer_sets, self.rulecounts.keys())
        peer_sets = removeSubsets(peer_sets)

        self.supersets = minimize_ss_rules_greedy(peer_sets, self.rulecounts, self.max_initial_bits)

        # impose an ordering on each superset by converting sets to lists
        for i in range(len(self.supersets)):
            self.supersets[i] = list(self.supersets[i])

        # if there is more than one superset, set the id size appropriately
        self.id_size = 1
        if len(self.supersets) > 1:
            self.id_size = int(math.ceil(math.log(len(self.supersets), 2)))
            
        # fix the mask size based on the id size
        self.mask_size = self.max_bits - self.id_size

        # in the unlikely case that there are more participants for a prefix than can fit in
        # the mask, truncate the list of participants (this may still be very broken)
        for superset in self.supersets:
            if len(superset) > self.mask_size:
                self.logger.warn('Superset too big!  Dropping participants.')
                del(superset[self.mask_size:])

        self.logger.debug("done.~")
        self.logger.debug("Supersets: >> "+str(self.supersets))



    def get_vmac(self, pctrl, vnh):
        """ Returns a VMAC for advertisements.
        """
        bgp_instance = pctrl.bgp_instance
        nexthop_2_part = pctrl.nexthop_2_part
        VNH_2_prefix = pctrl.VNH_2_prefix


        vmac_bitstring = ""
        vmac_addr = ""

        if vnh not in VNH_2_prefix:
            self.logger.debug("VNH "+str(vnh)+" not found in get_vmac call!")
            return vmac_addr
        prefix = VNH_2_prefix[vnh]


        # first part of the returned tuple is next hop
        route = bgp_instance.get_route('local', prefix)
        if route is None:
            self.logger.debug("prefix "+str(prefix)+" not found in local")
            bgp_instance.rib['local'].dump(self.logger)
            return vmac_addr

        next_hop = route.next_hop
        if next_hop not in nexthop_2_part:
            self.logger.debug("Next Hop "+str(next_hop)+" not found in get_vmac call!")
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
            self.logger.error("In get_vmac: Prefix "+str(prefix)+" doesn't belong to any superset (This should never happen) >>")
            self.logger.error(">> Supersets at the moment of failure: "+str(self.supersets))
            self.logger.error(">> Set of advertisers of prefix "+str(prefix)+" is "+str(prefix_set))
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
        elif (len(set_bitstring) > self.mask_size):
            self.logger.error('Superset is too big! This shouldnt happen')

        #self.logger.debug("****DEBUG: nexthop_part: %d, best_path_size: %d, ss_id: %d, id_size: %d", nexthop_part, self.best_path_size, ss_id, self.id_size)

        id_bitstring = '{num:0{width}b}'.format(num=ss_id, width=self.id_size)

        nexthop_bitstring = '{num:0{width}b}'.format(num=nexthop_part, width=self.best_path_size)

        vmac_bitstring = '1' + id_bitstring + set_bitstring + nexthop_bitstring

        if len(vmac_bitstring) != 48:
            self.logger.error("BAD VMAC SIZE!! FIELDS ADD UP TO "+str(len(vmac_bitstring)))

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

    pctrl.logger.debug("Prefix2Part called. Returning "+str(groups[:5])+"(this should not be empty) "+str(len(groups)))

    return groups


def get_all_participants_advertising(pctrl, prefix):
    bgp_instance = pctrl.bgp_instance
    nexthop_2_part = pctrl.nexthop_2_part

    routes = bgp_instance.get_routes('input',prefix)
    pctrl.logger.debug("Supersets all routes:: "+ str(routes))

    parts = set([])

    for route in routes:
        next_hop = route.next_hop

        if next_hop in nexthop_2_part:
            parts.add(nexthop_2_part[next_hop])
        else:
            pctrl.logger.debug("In subcall of prefix2part: Next hop "+str(next_hop)+" NOT in nexthop_2_part")

    return parts


if __name__ == '__main__':
    """ Unit testing.
    """

    def get_all_participants_advertising(crap1, crap2):
        if crap1 == 'poot':
            return [2,3,4,8]
        return [1,2,3,4,5,6]

    def get_all_participant_sets():
        return [[1,2,3], [2,3,4], [4,5,6], [1,2,3,7], [3,4,7,8]]

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

    class FakeSDX(object):
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

    config = {
            "VMAC Size"     : "48",
            "Next Hop Bits" : "16",
            "Port Bits"     : "10",
            }
    ss = SuperSets(sdx, config)
    print ss.initial_computation()
    print ss.supersets

    updates = [{'announce':{'prefix':'poot'}}]

    print ss.update_supersets(updates)

    print ss.supersets
