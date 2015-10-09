#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Robert MacDavid (Princeton)

import json

from mds_lib import decompose_sequential
from threading import RLock as lock


LOG = False

class MDS():
    def __init__(self, pctrl, config_file = None):
        self.VMAC_size = 48
        if config_file is not None:

            if LOG: print pctrl.idp, "Initializing MDS with config file."

            with open(config_file, 'r') as f:
                config = json.load(f)
                self.VMAC_size = int(config["VMAC"]["Options"]["VMAC Size"])

        else:
            if LOG: print pctrl.idp, "Initializing MDS WITHOUT config file."


        self.mds = {}
        self.prefix_2_fec = {}
        self.num_fecs = 0


    def get_active_participants(self, pctrl):
        """ Return all participants which appear in this participant's
            outbound forwarding policies.
        """
        policies = pctrl.policies

        active_parts = set([])
        # construct the participant weight matrix
        if ('outbound' in policies):
            out_policies = policies['outbound']
            for policy in out_policies:
                if ('fwd' in policy['action']):
                    fwd_part = int(policy['action']['fwd'])
                    active_parts.add(fwd_part)

        return active_parts


    def initial_computation(self, pctrl):
        if LOG: print pctrl.idp, "Running MDS initial computation..",

        self.recompute_mds(pctrl)

        changes = []

        # generate messages which will be consumed by the rule generator
        for participant, prefix_group_set in self.mds.iteritems():
            for prefix_group in prefix_group_set:
                # the VMAC for all prefixes in this group
                vmac = get_vmac_from_prefix(prefix_group[0])

                changes.append({"participant_id": participant,
                                "vmac": vmac})

        sdx_msgs = {"type":"new", "changes":changes}


        if LOG:
            print pctrl.idp, "MDS computation complete. MDS:"
            print pctrl.idp, ">>", self.mds, 
            print pctrl.idp, ">> SDX Update Messages:"
            print pctrl.idp, ">>", sdx_msgs

        return sdx_msgs



    def update_mds(self, pctrl, updates):
        with lock():

            if LOG: print pctrl.idp, "Updating MDS..."

            sdx_msgs = {"type": "update", "changes": []}

            # the list of prefixes who will have changed VMACs
            # (gratuitous ARPs gotta be sent for them)
            impacted_prefixes = []

            # if the MDS haven't been computed at all yet
            if len(self.mds) == 0:
                sdx_msgs = self.initial_computation(pctrl)
                return (sdx_msgs, impacted_prefixes)


            changes = []

            for update in updates:
                if ('withdraw' in update):
                    prefix = update['withdraw']['prefix']
                else if ('announce' in update):
                    prefix = update['announce']['prefix']
                else:
                    continue

                # TODO: we need to handle the case of the next-hop changing
                # it must be checked, and rules must be pushed. non-trivial

                # break the prefix off into its own FEC
                # TODO: write a better update protocol
                prefix_2_fec[prefix] = self.num_fecs
                self.num_fecs += 1


                impacted_prefixes.append(prefix)
                vmac = get_vmac_from_prefix(prefix)

                changes.append({"participant_id": participant,
                                "vmac": vmac})


            sdx_msgs = {"type": "update", "changes": changes}
            # check which participants joined a new superset and communicate to the SDX controller
            return (sdx_msgs, impacted_prefixes)



    def recompute_mds(self, pctrl):

        if LOG: print pctrl.idp, "~Recomputing MDS scheme...",

        prefix_columns = get_all_prefix_columns(pctrl)

        self.mds = decompose_sequential(prefix_columns)

        prefixGroup_2_fec = {}
        self.prefix_2_fec = {}
        self.num_fecs = 0

        # A prefix group corresponds to a Forwarding Equivalence Class (FEC)
        # we now iterate over each group and assign it a FEC ID
        for prefix_group_set in self.mds.values():
            for prefix_group in prefix_group_set:

                # make the prefix group hashsable
                frozen_group = frozenset(prefix_group)

                # if we haven't seen this prefix group yet
                if frozen_group not in prefixGroup_2_fec:
                    prefixGroup_2_fec[frozen_group] = self.num_fecs

                    # map all the prefixes in the group to the ID
                    for prefix in prefix_group:
                        self.prefix_2_fec[prefix] = self.num_fecs

                    self.num_fecs += 1



        if LOG:
            print "done.~"
            #print pctrl.idp, "MDS:"
            #print pctrl.idp, ">>", self.mds



    def get_vmac(self, pctrl, vnh):
        """ Returns a VMAC for advertisements.
        """
        bgp_instance = pctrl.bgp_instance
        nexthop_2_part = pctrl.nexthop_2_part
        VNH_2_prefix = pctrl.VNH_2_prefix


        vmac_addr = ""

        if vnh not in VNH_2_prefix:
            if LOG: print "VNH", vnh, "not found in get_vmac call!"
            return vmac_addr

        prefix = VNH_2_prefix[vnh]

        return get_vmac_from_prefix(prefix)



    def get_vmac_from_prefix(self, prefix):
        """ Returns a VMAC for advertisements, from a prefix instead of a VNH.
        """

        # which FEC does this prefix belong to?
        fec_id = self.prefix_2_fec[prefix]

        # make a 48-bit bitstring corresponding to the FEC ID
        vmac_bitstring = '{num:0{width}b}'.format(num=fec_id, width=self.VMAC_size)

        # convert bitstring to hexstring and then to a mac address
        vmac_addr = '{num:0{width}x}'.format(num=int(vmac_bitstring,2), width=self.VMAC_size/4)
        vmac_addr = ':'.join([vmac_addr[i]+vmac_addr[i+1] for i in range(0,self.VMAC_size/4,2)])

        return vmac_addr





def get_all_prefix_columns(pctrl):
    """ Returns the data structure required as input for the MDS algorithm.
        Looks like {prefix1:[partA, partB], prefix2:[partB,partC], ... }
    """
    prefixes = pctrl.prefix_2_VNH.keys()

    prefix_2_columns = []

    for prefix in prefixes:
        column = get_prefix_column(pctrl, prefix)
        prefix_2_columns[prefix] = column

    if LOG: print pctrl.idp, "Prefix2Column called. Returning", groups[:5], "(this should not be empty)", len(groups)

    return prefix_2_columns




def get_prefix_column(pctrl, prefix):
    """ Subcall to get_all_prefix_columns(). Returns a single column.
        Column does not include participants which are not involved
        in outbound policies (AKA inactive participants).
    """
    bgp_instance = pctrl.bgp_instance
    nexthop_2_part = pctrl.nexthop_2_part

    routes = bgp_instance.get_routes('input',prefix)
    #print "Supersets all routes:: ", routes
    parts = set([])

    # build the reachability entries of the column first
    for route in routes:
        # first part of the returned tuple is next hop
        next_hop = route['next_hop']

        if next_hop in nexthop_2_part:
            parts.add(nexthop_2_part[next_hop])
        else:
            if LOG: print pctrl.idp, "In subcall of prefix2part: Next hop", next_hop, "NOT in nexthop_2_part"


    # chop out the inactive participants from the column
    active_parts = get_active_participants(pctrl)
    parts.intersection_update(active_parts)

    # get the default BGP route for this prefix
    best_path = bgp_instance.get_route('local',prefix)
    bgp_next_hop = best_path['next_hop']

    # add the BGP next-hop to the column
    if next_hop in nexthop_2_part:
        parts.add("BGP" + nexthop_2_part[bgp_next_hop])
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
