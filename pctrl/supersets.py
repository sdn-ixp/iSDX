#!/usr/bin/env python
#  Author:
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

LOG = False

class SuperSets():
    def __init__():
        # TODO: @Rudiger, we can parse this from a config file
        self.supersets = []
        self.superset_threshold = 10
        self.max_superset_size = 30
        self.best_path_size = 12
        self.VMAC_size = 48

    def update_supersets(self, updates):
        sdx_msgs = {"type": "update",
                    "changes": []}

        for update in updates:
            if ('announce' in update):
                prefix = update['announce']['prefix']

                # get set of all participants advertising that prefix
                # TODO: Needs more thinking
                basic_set = get_all_participants_advertising(prefix, self.participants)

                # check if this set is a subset of one of the existing supersets
                if not is_subset_of_superset(basic_set, self.supersets):
                    # since it is not a subset, we have to either extend an existing superset (if possible)
                    # or add a new subset

                    diffs = [len(basic_set.difference(set(superset))) for superset in self.supersets]
                    unions  = [len(basic_set.union(set(superset))) for superset in self.supersets]
                    sorted_diff = sorted(diffs)

                    new_members = None
                    superset_index = None
                    add_superset = True

                    # check to which superset the minimal number of participants has to be added while
                    # staying within the maximum size
                    for i in range(0, len(sorted_diff)):
                        index = diffs.index(sorted_diff[i])
                        if (unions[index] <= self.max_superset_size):
                            new_members = list(basic_set.difference(set(self.supersets[i])))
                            self.supersets[i].extend(new_members)
                            add_superset = False
                            superset_index = index
                            break

                    # if it is not possible to extend a superset, a new superset has to be created
                    if add_superset:
                        self.supersets.append(list(basic_set))
                        superset_index = len(self.supersets) - 1
                        for participant in self.supersets[-1]:
                            # changes in the superset are prepared to be sent to the controller
                            sdx_msgs["changes"].append({"participant_id": participant,
                                                       "superset": superset_index,
                                                       "position": self.supersets[superset_index].index(participant)})
                    else:
                        for participant in new_members:
                            # changes in the superset are prepared to be sent to the controller
                            sdx_msgs["changes"].append({"participant_id": participant,
                                                       "superset": superset_index,
                                                       "position": self.supersets[superset_index].index(participant)})

                    # if preconfigured threshold is exceeded, then start completely from scratch
                    if (len(self.supersets) > self.superset_threshold):
                        recompute_all_supersets(self)

                        sdx_msgs = {"type": "new",
                                    "changes": []}

                        for superset in self.supersets:
                            for participant in superset:
                                sdx_msgs["changes"].append({"participant_id": participant,
                                                           "superset": superset_index,
                                                           "position": self.supersets[superset_index].index(participant)})

            elif ('withdraw' in update):
                continue

        # check which participants joined a new superset and communicate to the SDX controller
        return sdx_msgs

    def recompute_all_supersets(self):
        # get all sets of participants advertising the same prefix
        peer_sets = get_all_participant_sets(self)

        # remove all subsets
        peer_sets.sort(key=len, reverse=True)
        for i in range(0, len(peer_sets)):
            for j in reversed(range(i+1, len(peer_sets))):
                if (peer_sets[i].issuperset(peer_sets[j])):
                    peer_sets.remove(peer_sets[j])

        # start combining sets to supersets
        supersets = []

        # start building the supersets by combining the sets with the largest intersections
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
        if (len(superset) > self.superset_threshold):
            self.superset_threshold = self.superset_threshold*2

        self.supersets = supersets


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
