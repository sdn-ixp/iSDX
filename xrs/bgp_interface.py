#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

def get_all_participants_advertising(prefix, participants):
    participant_set = set()
   
    for participant_name in participants:
        route = participants[participant_name].get_route('input', prefix)
        if route:
            participant_set.add(participant_name)
            
    return participant_set
    
def get_all_as_paths(prefix, participants):
    as_sets = {}
   
    for participant_name in participants:
        route = participants[participant_name].get_routes('input', prefix)
        if route:
            as_sets[participant_name] = route['as_path']
            
    return as_sets
    
def get_all_participant_sets(xrs):
    participant_sets = []
     
    for prefix in xrs.prefix_2_VNH:
        participant_sets.append(get_all_participants_advertising(prefix, xrs.participants))
            
    return participant_sets    
    
def bgp_update_peers(updates, xrs):
    changes = []

    for update in updates:
        if ('announce' in update):
            as_sets = {}
            prefix = update['announce']['prefix']
            
            # get the as path from every participant that advertised this prefix
            for participant_name in xrs.participants:
                route = xrs.participants[participant_name].get_route('input', prefix)
                if route:
                    as_sets[participant_name] = route['as_path']
            
            # send custom route advertisements based on peerings
            for participant_name in xrs.participants:
                as_set = set()
                for peer in xrs.participants[participant_name].peers_out:
                    if peer in as_sets:
                        as_set.update(set(as_sets[peer].split()))
                    
                # only announce route if at least one of the peers advertises it to that participant
                if as_set:
                    route = {"next_hop": str(xrs.prefix_2_VNH[prefix]),
                             "origin": "",
                             "as_path": ' '.join(map(str,as_set)),
                             "communities": "",
                             "med": "",
                             "atomic_aggregate": ""}
                             
                    # check if we have already announced that route
                    prev_route = xrs.participants[participant_name].rib["output"][prefix]
                    
                    if not bgp_routes_are_equal(route, prev_route):
                        # store announcement in output rib
                        xrs.participants[participant_name].delete_route("output",prefix)
                        xrs.participants[participant_name].add_route("output",prefix,route)
                        
                        if prev_route:
                            changes.append({"participant": participant_name,
                                            "prefix": prefix,
                                            "VNH": xrs.prefix_2_VNH[prefix]})
                        
                        # announce the route to each router of the participant
                        for neighbor in xrs.participant_2_portip[participant_name]:
                            xrs.server.sender_queue.put(announce_route(neighbor, prefix, route["next_hop"], route["as_path"]))
        
        elif ('withdraw' in update):
            as_sets = {}
            prefix = update['withdraw']['prefix']
            
            # get the as path from every participant that advertised this prefix
            for participant_name in xrs.participants:
                route = xrs.participants[participant_name].get_route('input', prefix)
                if route:
                    as_sets[participant_name] = route['as_path']
            
            # send custom route advertisements based on peerings
            for participant_name in xrs.participants:
                # only modify route advertisement if this route has been advertised to the participant
                prev_route = xrs.participants[participant_name].rib["output"][prefix]
                if prev_route: 
                    as_set = set()
                    for peer in xrs.participants[participant_name].peers_out:
                        if peer in as_sets:
                            as_set.update(set(as_sets[peer].split()))
                        
                    # withdraw if no one advertises that route, else update reachability
                    if as_set:
                        route = {"next_hop": str(xrs.prefix_2_VNH[prefix]),
                                 "origin": "",
                                 "as_path": ' '.join(map(str,as_set)),
                                 "communities": "",
                                 "med": "",
                                 "atomic_aggregate": ""}
                                 
                        # check if we have already announced that route
                        if not bgp_routes_are_equal(route, prev_route):
                            # store announcement in output rib
                            xrs.participants[participant_name].delete_route("output",prefix)
                            xrs.participants[participant_name].add_route("output",prefix,route)
                            
                            changes.append({"participant": participant_name,
                                            "prefix": prefix,
                                            "VNH": xrs.prefix_2_VNH[prefix]})
                            
                            # announce the route to each router of the participant
                            for neighbor in xrs.participant_2_portip[participant_name]:
                                xrs.server.sender_queue.put(announce_route(neighbor, prefix, route["next_hop"], route["as_path"]))
                    else:
                        delete_route("output", prefix)
                        for neighbor in xrs.participant_2_portip[participant_name]:
                            xrs.server.sender_queue.put(withdraw_route(neighbor, prefix, xrs.prefix_2_VNH[prefix]))
    return changes
                        
def bgp_routes_are_equal(route1, route2):
    if route1 is None:
        return False
    if route2 is None:
        return False
    if (route1['next_hop'] != route2['next_hop']):
        return False
    if (route1['as_path'] != route2['as_path']):
        return False
    return True
        
def announce_route(neighbor, prefix, next_hop, as_path):
           
    msg = "neighbor " + neighbor + " announce route " + prefix + " next-hop " + str(next_hop)
    msg += " as-path [ ( " + as_path + " ) ]"

    return msg

def withdraw_route(neighbor, prefix, next_hop):

    msg = "neighbor " + neighbor + " withdraw route " + prefix + " next-hop " + str(next_hop)

    return msg
