#!/usr/bin/env python

LOG = False

def update_supersets(updates, xrs):
    sdx_msgs = {"type": "update",
                "changes": []}

    for update in updates:
        if ('announce' in update):
            prefix = update['announce']['prefix']
            
            # get set of all participants advertising that prefix
            basic_set = get_all_participants_advertising(prefix, xrs.participants)
            
            # check if this set is a subset of one of the supersets
            if not is_subset_of_superset(basic_set, xrs.supersets):
                # if possible extend one of the supersets by adding the missing participants
                diffs = [len(basic_set.difference(set(superset))) for superset in xrs.supersets]
                unions  = [len(basic_set.union(set(superset))) for superset in xrs.supersets]
                sorted_diff = sorted(diffs)
                
                new_members = None
                superset_index = None
                add_superset = True
                for i in range(0, len(sorted_diff)):
                    index = diffs.index(sorted_diff[i])
                    if (unions[index] <= xrs.max_superset_size):
                        new_members = list(basic_set.difference(set(xrs.supersets[i])))
                        xrs.supersets[i].extend(new_members)
                        add_superset = False
                        superset_index = index
                        break
                        
                # if no superset can be extend, add a new superset
                if add_superset:
                    xrs.supersets.append(list(basic_set))
                    superset_index = len(xrs.supersets) - 1
                    for participant in xrs.supersets[-1]:
                        sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": xrs.supersets[superset_index].index(participant)})
                else:
                    for participant in new_members:
                        sdx_msgs["changes"].append({"participant_id": participant,
                                                   "superset": superset_index,
                                                   "position": xrs.supersets[superset_index].index(participant)})
                
                # if preconfigured threshold is exceeded, then start completely from scratch
                if (len(xrs.supersets) > xrs.superset_threshold):
                    recompute_all_supersets(xrs)
                    
                    sdx_msgs = {"type": "new",
                                "changes": []}
                                
                    for superset in xrs.supersets:
                        for participant in superset:
                            sdx_msgs["changes"].append({"participant_id": participant,
                                                       "superset": superset_index,
                                                       "position": xrs.supersets[superset_index].index(participant)})

        elif ('withdraw' in update):
            continue
    
    # check which participants joined a new superset and communicate to the SDX controller
    return sdx_msgs

def recompute_all_supersets(xrs):
    # get all sets of participants advertising the same prefix
    peer_sets = get_all_participant_sets(xrs)
    
    # remove all subsets
    peer_sets.sort(key=len, reverse=True)
    for i in range(0, len(peer_sets)):
        for j in reversed(range(i+1, len(peer_sets))):
            if (peer_sets[i].issuperset(peer_sets[j])):
                peer_sets.remove(peer_sets[j])
                
    # start combining sets to supersets
    supersets = []

    for tmp_set in peer_sets:
        peer_sets.remove(tmp_set)
        superset = tmp_set
        
        intersects = [len(superset.intersection(s)) for s in peer_sets]

        for i in range(0, len(intersects)):
            index = intersects.index(max(intersects))
            if (len(superset) == max_size) or (intersects[index] == -1):
                break
            if (len(superset.union(peer_sets[index])) <= max_size):
                superset = superset.union(peer_sets[index])
                intersects[index] = -1
        for i in reversed(range(0, len(intersects))):
            if (intersects[i] == -1):
                peer_sets.remove(peer_sets[i])
        supersets.append(list(superset))     
    # check if threshold is still exceeded and if so adjust it
    if (len(superset) > xrs.superset_threshold):
        xrs.superset_threshold = xrs.superset_threshold*2

    xrs.supersets = supersets
            
def is_subset_of_superset(subset, supersets):
    for superset in supersets:
        if ((set(superset)).issuperset(subset)):
            return True
    return False

def get_all_participants_advertising(prefix, participants):
    participant_set = set()
   
    for participant_name in participants:
        route = participants[participant_name].get_routes('input', prefix)
        if route:
            participant_set.add(participant_name)
            
    return participant_set