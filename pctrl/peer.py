#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)
#  Arpit Gupta (Princeton)

import json
import os
import sqlite3
from threading import RLock as lock
from ribm import rib
from decision_process import decision_process, best_path_selection

LOG = False

class BGPPeer():

    def __init__(self, id, asn, ports, peers_in, peers_out):
        self.id = id
        self.asn = asn
        self.ports = ports
        self.prefix_lock = {}
        ips = []
        for port in ports:
            ips.append(port["IP"])

        # TODO: Get rid of this hardcoding
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))

        self.rib = {"input": rib(str(self.asn),"input", path),
                    "local": rib(str(self.asn),"local", path),
                    "output": rib(str(self.asn),"output", path)}

        # peers that a participant accepts traffic from and sends advertisements to
        self.peers_in = peers_in
        # peers that the participant can send its traffic to and gets advertisements from
        self.peers_out = peers_out


    def update(self,route):
        updates = []
        key = {}

        origin = None
        as_path = None
        med = None
        atomic_aggregate = None
        community = None

        route_list = []
        # Extract out neighbor information in the given BGP update
        neighbor = route["neighbor"]["ip"]

        if ('state' in route['neighbor'] and route['neighbor']['state']=='down'):
            #TODO WHY NOT COMPLETELY DELETE LOCAL?
            routes = self.rib['input'].get_all()

            for route_item in routes:
                self.rib['local'].delete(route_item['prefix'])
            self.rib['local'].commit()

            self.rib["input"].delete_all()
            self.rib["input"].commit()

        if ('update' in route['neighbor']['message']):
            if ('attribute' in route['neighbor']['message']['update']):
                attribute = route['neighbor']['message']['update']['attribute']

                origin = attribute['origin'] if 'origin' in attribute else ''

                as_path = attribute['as-path'] if 'as-path' in attribute else ''
                #as_path = ' '.join(map(str,temp_as_path)).replace('[','').replace(']','').replace(',','')

                #print "AS PATH SYNTAX:: ",as_path
                med = attribute['med'] if 'med' in attribute else ''

                community = attribute['community'] if 'community' in attribute else ''
                communities = ''
                for c in community:
                    communities += ':'.join(map(str,c)) + " "

                atomic_aggregate = attribute['atomic-aggregate'] if 'atomic-aggregate' in attribute else ''

            if ('announce' in route['neighbor']['message']['update']):
                announce = route['neighbor']['message']['update']['announce']
                if ('ipv4 unicast' in announce):
                    for next_hop in announce['ipv4 unicast'].keys():
                        for prefix in announce['ipv4 unicast'][next_hop].keys():
                            #print "::::PREFIX:::::", prefix, type(prefix)
                            # TODO: Check if this appending the accounced route to the input rib?
                            # Why not use the `add_route` function?
                            atrributes = (neighbor, next_hop, origin, as_path,
                                         communities, med, atomic_aggregate)
                            self.add_route("input", prefix, atrributes)
                            # TODO: Avoid multiple interactions with the DB
                            announce_route = self.get_route_with_neighbor("input", prefix, neighbor)
                            route_list.append({'announce': announce_route})

            elif ('withdraw' in route['neighbor']['message']['update']):
                withdraw = route['neighbor']['message']['update']['withdraw']
                if ('ipv4 unicast' in withdraw):
                    for prefix in withdraw['ipv4 unicast'].keys():
                        deleted_route = self.get_route_with_neighbor("input", prefix, neighbor)
                        if deleted_route != None:
                            self.delete_route_with_neighbor("input", prefix, neighbor)
                            route_list.append({'withdraw': deleted_route})

        return route_list


    def decision_process_local(self, update):
        'Update the local rib with new best path'
        if ('announce' in update):


            # TODO: Make sure this logic is sane.
            '''Goal here is to get all the routes in participant's input
            rib for this prefix. '''

            # NOTES:
            # Currently the logic is that we push the new update in input rib and then
            # make the best path decision. This is very efficient. This is how it should be
            # done:
            # (1) For announcement: We need to compare between the entry for that
            # prefix in the local rib and new announcement. There is not need to scan
            # the entire input rib. The compare the new path with output rib and make
            # deicision whether to announce a new path or not.
            # (2) For withdraw: Check if withdraw withdrawn route is same as
            # best path in local, if yes, then delete it and run the best path
            # selection over entire input rib, else just ignore this withdraw
            # message.

            announce_route = update['announce']
            #print "decision process local:: ", announce_route
            prefix = announce_route['prefix']
            if LOG: print " Peer Object for: ", self.id, "--- processing update for prefix: ", prefix
            current_best_route = self.get_route('local', prefix)
            if current_best_route:
                # This is what should be fed to the desicion process
                routes = [announce_route, current_best_route]
                new_best_route = best_path_selection(routes)
            else:
                # This is the first time for this prefix
                new_best_route = announce_route

            if LOG: print " Peer Object for: ", self.id, "---Best Route after Selection: ", prefix, new_best_route
            if bgp_routes_are_equal(new_best_route, current_best_route):
                if LOG: print " Peer Object for: ", self.id, "--- No change in Best Path...move on", prefix
            else:
                #print new_best_route, type(new_best_route)
		self.update_route('local', prefix, new_best_route)
                # Check
                updated_best_path = self.get_route('local', prefix)
                if LOG: print " Peer Object for: ", self.id, "Pushed: ", new_best_route, " Observing: ", updated_best_path
                if LOG: print " Peer Object for: ", self.id, "--- Best Path changed: ", prefix, new_best_route, " Older best route: ", current_best_route

        elif('withdraw' in update):
            deleted_route = update['withdraw']
            prefix = deleted_route['prefix']
            if LOG: print " Peer Object for: ", self.id, "---processing withdraw for prefix: ", prefix
            if (deleted_route is not None):
                # delete route if being used
                current_best_route = self.get_route('local',prefix)
                if (current_best_route):
                    # Check if current_best_route and deleted_route are advertised by the same guy
                    if deleted_route['neighbor'] == current_best_route['neighbor']:
                        # TODO: Make sure this logic is sane.
                        '''Goal here is to get all the routes in participant's input
                        rib for this prefix. '''
                        self.delete_route('local',prefix)
                        routes = []
                        routes.extend(self.get_routes('input',prefix))
                        if routes:
                            best_route = best_path_selection(routes)
                            self.update_route('local', prefix, best_route)
                        else:
                            if LOG: print " Peer Object for: ", self.id, "---No best route available for prefix ", prefix, " after receiving withdraw message."
                    else:
                        if LOG: print " Peer Object for: ", self.id, "---BGP withdraw for prefix ", prefix," has no impact on best path"
                else:
                    if LOG: print " Peer Object for: ", self.id, "--- This is weird. How can we not have any delete object in this function"


    def bgp_update_peers(self, updates, prefix_2_VNH, ports, idp):
        # TODO: Verify if the new logic makes sense
        changed_vnhs = []
        announcements = []
        for update in updates:
            if 'announce' in update:
                prefix = update['announce']['prefix']
            else:
                prefix = update['withdraw']['prefix']

            prev_route = self.get_route("output", prefix)
            #prev_route["next_hop"] = str(prefix_2_VNH[prefix])

            best_route = self.get_route("local", prefix)
            if LOG: print " Peer Object for: ", self.id, " -- Previous Outbound route: ", prev_route, " New Best Path: ", best_route
            #print  idp, "**********best route for: ", prefix, "route:: ", best_route
            #best_route["next_hop"] = str(prefix_2_VNH[prefix])

            #print idp, "## DEBUG: best route: ", best_route

            if ('announce' in update):
                # Check if best path has changed for this prefix
                if not bgp_routes_are_equal(best_route, prev_route):
                    # store announcement in output rib
                    # print best_route, prev_route
		    self.update_route("output", prefix, best_route)
                    # add the VNH to the list of changed VNHs
                    changed_vnhs.append(prefix_2_VNH[prefix])
                    if best_route:

                        # announce the route to each router of the participant
                        for port in ports:
                            # TODO: Create a sender queue and import the announce_route function
                            #print  idp, "********** Failure: ", port["IP"], prefix, "route::failure ", best_route

                            announcements.append(announce_route(port["IP"], prefix,
                                                prefix_2_VNH[prefix], best_route["as_path"]))
                    else:
                        continue
                        #print "Race condition problem for prefix: ", prefix

            elif ('withdraw' in update):
                # A new announcement is only needed if the best path has changed
                if best_route:
                    "There is a best path available for this prefix"
                    if not bgp_routes_are_equal(best_route, prev_route):
                        "There is a new best path available now"
                        # store announcement in output rib
                        self.update_route("output", prefix, best_route)


                        # add the VNH to the list of changed VNHs
                        if LOG: print " Peer Object for: ", self.id, "^^^bgp_update_peers:: ", best_route
                        changed_vnhs.append(prefix_2_VNH[prefix])

                        for port in ports:
                            announcements.append(announce_route(port["IP"],
                                                 prefix, prefix_2_VNH[prefix],
                                                 best_route["as_path"]))

                else:
                    "Currently there is no best route to this prefix"
                    if prev_route:
                        # Clear this entry from the output rib
                        if prefix in prefix_2_VNH:
                            self.delete_route("output", prefix)
                            for port in self.ports:
                                # TODO: Create a sender queue and import the announce_route function
                                announcements.append(withdraw_route(port["IP"],
                                                                    prefix,
                                                                    prefix_2_VNH[prefix]))

        return changed_vnhs, announcements

    def getlock(self, prefix):
        if prefix not in self.prefix_lock:
            self.prefix_lock[prefix] = lock()
        return self.prefix_lock[prefix]

    def process_notification(self,route):
        if ('shutdown' == route['notification']):
            self.rib["input"].delete_all()
            self.rib["input"].commit()
            self.rib["local"].delete_all()
            self.rib["local"].commit()
            self.rib["output"].delete_all()
            self.rib["output"].commit()
            # TODO: send shutdown notification to participants

    def add_route(self,rib_name,prefix,attributes):
        with self.getlock(prefix):
            self.rib[rib_name][prefix] = attributes
            self.rib[rib_name].commit()

    def add_many_routes(self,rib_name,routes):
        self.rib[rib_name].add_many(routes)
        self.rib[rib_name].commit()

    def get_route(self,rib_name,prefix):
        with self.getlock(prefix):
            return self.rib[rib_name].get(prefix)

    def get_route_with_neighbor(self,rib_name,prefix, neighbor):
        with self.getlock(prefix):
            return self.rib[rib_name].get_prefix_neighbor(prefix, neighbor)

    def get_routes(self,rib_name,prefix):
        with self.getlock(prefix):
            return self.rib[rib_name].get_all(prefix)

    def get_all_routes(self, rib_name):

        return self.rib[rib_name].get_all()

    def delete_route(self,rib_name,prefix):
        with self.getlock(prefix):
            self.rib[rib_name].delete(prefix)
            self.rib[rib_name].commit()

    def delete_route_with_neighbor(self,rib_name,prefix, neighbor):
        with self.getlock(prefix):
            self.rib[rib_name].delete_prefix_neighbor(prefix, neighbor)
            self.rib[rib_name].commit()

    def delete_all_routes(self,rib_name):
        with self.getlock(prefix):
            self.rib[rib_name].delete_all()
            self.rib[rib_name].commit()

    def filter_route(self,rib_name,item,value):

        return self.rib[rib_name].filter(item,value)

    def update_route(self,rib_name,prefix,attributes):
        with self.getlock(prefix):
            #self.rib[rib_name].delete(prefix)
            #self.rib[rib_name][prefix] = attributes
	    #neighbor = attributes["neighbor"]
            self.rib[rib_name].update_with_prefix_neighbor(prefix, attributes)
	    self.rib[rib_name].commit()

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




''' main '''
if __name__ == '__main__':

    mypeer = peer('172.0.0.22')

    route = '''{ "exabgp": "2.0", "time": 1387421714, "neighbor": { "ip": "172.0.0.21", "update": { "attribute": { "origin": "igp", "as-path": [ [ 300 ], [ ] ], "med": 0, "atomic-aggregate": false }, "announce": { "ipv4 unicast": { "140.0.0.0/16": { "next-hop": "172.0.0.22" }, "150.0.0.0/16": { "next-hop": "172.0.0.22" } } } } } }'''

    mypeer.update(route)

    print mypeer.filter_route('input', 'as_path', '300')
