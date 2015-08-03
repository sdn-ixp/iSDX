#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Rudiger Birkner (Networked Systems Group ETH Zurich)

import json
import sqlite3

from rib import rib
from decision_process import decision_process

class peer():

    def __init__(self, id, asn, ports, peers_in, peers_out):
        self.id = id
        self.asn = asn
        self.ports = ports

        ips = []
        for port in ports:
            ips.append(port["IP"])

        self.rib = {"input": rib("-".join(ips),"input"),
                    "local": rib("-".join(ips),"local"),
                    "output": rib("-".join(ips),"output")}

        # peers that a participant accepts traffic from and sends advertisements to
        self.peers_in = peers_in
        # peers that the participant can send its traffic to and gets advertisements from
        self.peers_out = peers_out

    def decision_process_local(self, update):
        'Update the local rib with new best path'
        if ('announce' in update):
            announce_route = update['announce']

            # TODO: Make sure this logic is sane.
            '''Goal here is to get all the routes in participant's input
            rib for this prefix. '''
            routes = []
            routes.extend(self.get_routes('input',announce_route['prefix']))

            if routes:
                best_route = best_path_selection(routes)

                # TODO: can be optimized? check to see if current route == best_route?
                self.delete_route("local",announce_route['prefix'])
                self.add_route("local",best_route['prefix'],best_route)

        elif('withdraw' in update):
            deleted_route = update['withdraw']

            if (deleted_route is not None):

                # delete route if being used
                if (self.get_routes('local',deleted_route['prefix'])):
                    self.delete_route("local",deleted_route['prefix'])

                    # TODO: Make sure this logic is sane.
                    '''Goal here is to get all the routes in participant's input
                    rib for this prefix. '''
                    routes = []
                    routes.extend(self.get_routes('input',deleted_route['prefix']))

                    if routes:
                        best_route = best_path_selection(routes)
                        participants[participant_name].add_route("local",best_route['prefix'],best_route)

    def update(self,route):
        updates = []
        key = {}

        origin = None
        as_path = None
        med = None
        atomic_aggregate = None
        community = None

        route_list = []

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

                temp_as_path = attribute['as-path'] if 'as-path' in attribute else ''
                as_path = ' '.join(map(str,temp_as_path)).replace('[','').replace(']','').replace(',','')

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
                            self.rib["input"][prefix] = (next_hop,
                                                         origin,
                                                         as_path,
                                                         communities,
                                                         med,
                                                         atomic_aggregate)
                            self.rib["input"].commit()
                            announce_route = self.rib["input"][prefix]

                            route_list.append({'announce': announce_route})

            elif ('withdraw' in route['neighbor']['message']['update']):
                withdraw = route['neighbor']['message']['update']['withdraw']
                if ('ipv4 unicast' in withdraw):
                    for prefix in withdraw['ipv4 unicast'].keys():
                        deleted_route = self.rib["input"][prefix]
                        self.rib["input"].delete(prefix)
                        self.rib["input"].commit()
                        route_list.append({'withdraw': deleted_route})

        return route_list

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
        self.rib[rib_name][prefix] = attributes
        self.rib[rib_name].commit()

    def add_many_routes(self,rib_name,routes):
        self.rib[rib_name].add_many(routes)
        self.rib[rib_name].commit()

    def get_route(self,rib_name,prefix):

        return self.rib[rib_name][prefix]

    def get_routes(self,rib_name,prefix):

        return self.rib[rib_name].get_all(prefix)

    def get_all_routes(self, rib_name):

        return self.rib[rib_name].get_all()

    def delete_route(self,rib_name,prefix):

        self.rib[rib_name].delete(prefix)
        self.rib[rib_name].commit()

    def delete_all_routes(self,rib_name):

        self.rib[rib_name].delete_all()
        self.rib[rib_name].commit()

    def filter_route(self,rib_name,item,value):

        return self.rib[rib_name].filter(item,value)

''' main '''
if __name__ == '__main__':

    mypeer = peer('172.0.0.22')

    route = '''{ "exabgp": "2.0", "time": 1387421714, "neighbor": { "ip": "172.0.0.21", "update": { "attribute": { "origin": "igp", "as-path": [ [ 300 ], [ ] ], "med": 0, "atomic-aggregate": false }, "announce": { "ipv4 unicast": { "140.0.0.0/16": { "next-hop": "172.0.0.22" }, "150.0.0.0/16": { "next-hop": "172.0.0.22" } } } } } }'''

    mypeer.udpate(route)

    print mypeer.filter_route('input', 'as_path', '300')
