#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


from ss_lib import *

LOG = True

# PRIORITIES (Values can be in [0,65535], 0 is miss)
FLOW_MISS_PRIORITY = 0


# outbound switch priorities
OUTBOUND_HIT_PRIORITY = 2

# inbound switch priorities
INBOUND_HIT_PRIORITY = 4
INBOUND_MISS_PRIORITY = 1



# create new outbound rules in response to superset changes
def update_outbound_rules(sdx_msgs, policies, ss_instance, my_mac):
    supersets = ss_instance.supersets

    rules = []
    if 'outbound' not in policies:
        return rules

    outbound = policies['outbound']

    # map each participant to a list of our policies which forward to them
    part_2_policy = {}

    # build this mapping
    for policy in outbound:
        if "fwd" in policy["action"]:
            part = int(policy["action"]["fwd"])
            if part not in part_2_policy:
                part_2_policy[part] = []
            part_2_policy[part].append(policy)



    updates = sdx_msgs["changes"]

    for update in updates:
        part = int(update["participant_id"])
        superset_id = int(update["superset"])
        bit_position = int(update["position"])

        # if we have no rules regarding this participant, skip
        if part not in part_2_policy:
            continue

        # for all policies involving this participant
        for policy in part_2_policy[part]:

            # vmac and mask which check if part is reachable
            vmac = vmac_participant_match(superset_id, bit_position, ss_instance)
            vmac_bitmask = vmac_participant_mask(bit_position, ss_instance)

            # the vmac which will be written on a policy match
            next_hop_mac = vmac_next_hop_match(part, ss_instance, inbound_bit = True)

            match_args = policy["match"]
            match_args["eth_dst"] = (vmac, vmac_bitmask)
            match_args["eth_src"] = my_mac

            actions = {"set_eth_dst":next_hop_mac, "fwd":["inbound"]}

            rule = {"rule_type":"outbound", "priority":OUTBOUND_HIT_PRIORITY,
                    "match":match_args , "action":actions, "mod_type":"insert",
                    "cookie":(policy["cookie"],2**16-1)}
            rules.append(rule)

    return rules


def build_outbound_rules_for(out_policies, ss_instance, my_mac):
    "Given a subset of outbound policies, return all the resulting rules."

    rules = []

    part_2_superset = {}
    for ss_id, superset in enumerate(ss_instance.supersets):
        for part_index, part in enumerate(superset):

            if part not in part_2_superset:
                part_2_superset[part] = []

            part_2_superset.append((ss_id, part_index))


    for policy in out_policies:
        if "fwd" not in policy["action"]:
            continue

        part = policy["action"]["fwd"]

        for ss_id, part_index in part_2_superset[part]:
            vmac = vmac_participant_match(ss_id,
                            part_index, ss_instance)
            vmac_bitmask = vmac_participant_mask(part_index, ss_instance)

            match_args = policy["match"]
            match_args["eth_dst"] = (vmac, vmac_bitmask)
            match_args["eth_src"] = my_mac

            actions = {"set_eth_dst":next_hop_mac, "fwd":["inbound"]}

            rule = {"rule_type":"outbound", "priority":OUTBOUND_HIT_PRIORITY,
                    "match":match_args , "action":actions, "mod_type":"insert",
                    "cookie":(policy["cookie"],2**16-1)}

            rules.append(rule)

        return rules


def build_inbound_rules_for(participant_id, in_policies, ss_instance, final_switch):
    "Given a subset of inbound policies, return all the resulting rules."

    rules = []


    for policy in in_policies:
        if "fwd" not in policy["action"]:
            continue

        port_num = policy["action"]["fwd"]

        # match on the next-hop
        vmac_bitmask = vmac_next_hop_mask(ss_instance)
        vmac = vmac_next_hop_match(participant_id, ss_instance)


        match_args = policy["match"]
        match_args["eth_dst"] = (vmac, vmac_bitmask)


        port_num = policy["action"]["fwd"]
        new_vmac = vmac_part_port_match(participant_id, port_num, ss_instance)


        actions = {"set_eth_dst":new_vmac, "fwd":[final_switch]}

        rule = {"rule_type":"inbound", "priority":INBOUND_HIT_PRIORITY,
                "match":match_args, "action":actions, "mod_type":"insert",
                "cookie":(policy["cookie"],2**16-1)}    

        rules.append(rule)

    return rules



# initialize all inbound rules
def init_inbound_rules(participant_id, policies, ss_instance, final_switch):
    dp_msgs = {"type": "new",
                    "changes": []}


    # do we even have inbound policies?
    if ('inbound' not in policies):
        return {}
    else:

        in_policies = policies['inbound']

        rules = build_inbound_rules_for(participant_id, in_policies, 
                                        ss_instance, final_switch)

        dp_msgs["changes"] = rules

        return dp_msgs



def msg_clear_all_outbound(policies, port0_mac):
    "Construct and return a flow mod which removes all our outbound rules"
    mods = []

    if 'outbound' not in policies:
        return mods

    # compile all cookies used by our policies
    cookies = []
    for policy in policies['outbound']:
        cookies.append(policy['cookie'])

    match_args = {"eth_src":port0_mac}

    for cookie in cookies:
        mod = {"rule_type":"outbound", "priority":0,
                "match":match_args , "action":{},
                "cookie":(cookie, 2**16-1), "mod_type":"remove"}
        mods.append(mod)

    return mods


def ss_process_policy_change(supersets, add_policies, remove_policies, policies, port_count, port0_mac):
        "Process the changes in participants' policies"
        return 0
"""
        # TODO: Implement the logic of dynamically changing participants' outbound and inbound policy
        # Partially done. Need to handle expansion of active set

        # has the set of active participants expanded?
        old_rulecounts = supersets.recompute_rulecounts(self.policies)
        new_rulecounts = supersets.recompute_rulecounts(complete_policies)

        new_active = set(new_rulecounts.keys())
        # new_parts will contain all participants that now appear that did not appear previously
        new_parts = new_active.difference(old_rulecounts.keys())

        port_count = len(self.participant_2_portmac[self.id])

        # we remove rules first, because the supersets might change when adding rules

        removal_rules = []

        if 'outbound' in remove_policies:
            removal_out = build_outbound_rules_for(remove_policies['outbound'],
                                     self.supersets, self.port0_mac)
            removal_rules.extend(removal_out)

        if 'inbound' in remove_policies:
            removal_in = build_inbound_rules_for(self.id, remove_policies['outbound'],
                                            self.supersets, port_count)
            removal_rules.extend(removal_in)

        # set the mod type of these rules to make them deletions, not additions
        for rule in removal_rules:
            rule['mod_type'] = "remove"

        self.dp_queued.extend(removal_rules)

        addition_rules = []

        if 'outbound' in add_policies:
            addition_out = build_outbound_rules_for(add_policies['outbound'],
                                     self.supersets, self.port0_mac)
            addition_rules.extend(removal_out)

        if 'inbound' in add_policies:
            addition_in = build_inbound_rules_for(self.id, add_policies['outbound'],
                                            self.supersets, port_count)
            addition_rules.extend(removal_in)


        return 0
"""
