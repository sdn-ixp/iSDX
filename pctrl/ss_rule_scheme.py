#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)


import ss_lib

LOG = True

# PRIORITIES (Values can be in [0,65535], 0 is miss)
FLOW_MISS_PRIORITY = 0


# outbound switch priorities
OUTBOUND_HIT_PRIORITY = 1

# inbound switch priorities
INBOUND_HIT_PRIORITY = 2
INBOUND_MISS_PRIORITY = 1



# create new outbound rules in response to superset changes
def update_outbound_rules(sdx_msgs, policies, supersets, my_mac):
    dp_msgs = {"type": "add",
                    "changes": []}

    if 'outbound' not in policies:
        return dp_msgs

    outbound = policies['outbound']

    # map each participant to a list of our policies which forward to them
    part_2_policy = {}

    # build this mapping
    for policy in outbound:
        if "fwd" in policy["action"]:
            part = policy["action"]["fwd"]
            if part not in part_2_policy:
                part_2_policy[part] = []
            part_2_policy[part].append(policy)


    # if the supersets needed to be recomputed
    if sdx_msgs["type"] == "new":
        dp_msgs["type"] = "new"

    updates = sdx_msgs["changes"]
    for update in updates:
        participant_id = update["participant_id"]
        superset_id = update["superset"]
        bit_position = update["position"]

        if participant_id not in part_2_policy:
            continue

        for policy in part_2_policy[participant_id]:
            vmac = vmac_participant_match(superset_id, participant_index, supersets):
            vmac_bitmask = vmac_participant_mask(participant_index, supersets)

            next_hop_mac = vmac_next_hop_match(participant_name, supersets, inbound_bit = True)

            match_args = policy["match"]
            match_args["eth_dst"] = (vmac, vmac_bitmask)
            match_args["eth_src"] = my_mac

            actions = {"set_eth_dst":next_hop_mac, "fwd":"inbound"}

            rule = {"rule_type":"outbound", "priority":OUTBOUND_HIT_PRIORITY,
                    "match":match_args , "action":actions, "mod_type":"insert"}

            dp_msgs["changes"].append(rule)





# initialize all inbound rules
def init_inbound_rules(participant_id, policies, port_count):
    dp_msgs = {"type": "new",
                    "changes": []}


    if LOG:
        self.logger.info("INIT: -- Installing inbound switch rules --")


    # do we even have inbound policies?
    if ('inbound' not in policies):
        return None


    for policy in policies:
    	port_num = policy["action"]["fwd"]

        # match on the next-hop
        vmac_bitmask = vmac_next_hop_mask(self.sdx)
        vmac = vmac_next_hop_match(participant_id, self.sdx)


        match_args = policy["match"]
        match_args["eth_dst"] = (vmac, vmac_bitmask)


        port_num = policy["action"]["fwd"]
        if (port_num >= port_count):
        	port_num = 0
		new_vmac = vmac_part_port_match(participant_id, port_num, self.sdx)                

                    
        actions = {"set_eth_dst":new_vmac, "fwd":"main"}

        rule = {"rule_type":"inbound", "priority":INBOUND_HIT_PRIORITY,
                "match":match_args, "action":actions, "mod_type":"insert"}

        dp_msgs["changes"].append(rule)

    return dp_msgs

    




