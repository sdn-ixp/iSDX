
import os
import json
import sqlite3
import time

from rib import rib
from decision_process import decision_process, best_path_selection

rib_fname = "rrc03.bview.20150820.0000.temp.txt"

def initialize_ribs(part):
    tmp = {"AS1273": {"2001:7f8:1::a500:1273:1": 5}}


class Peer:
    def __init__(self, id, asn_2_ip):
        self.id = id
        self.asn_2_ip = asn_2_ip
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))
        #print path
        self.prefixes = {}

        self.rib = {"input": rib(str(id),"input", path, in_memory=False),
                    "local": rib(str(id),"local", path, in_memory=False),
                    "output": rib(str(id),"output", path, in_memory=False)}

        self.local_rib = {"input":{}, "local":{}, "output":{}}

    def get_route(self,rib_name,prefix):

        return self.rib[rib_name].get(prefix)

    def add_route(self,rib_name,prefix,attributes):
        self.rib[rib_name][prefix] = attributes
        self.rib[rib_name].commit()

    def updateInputRib(self):
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "examples", "test-amsix"))
        rib_file = os.path.join(path, rib_fname)
        tmp = {}
        with open(rib_file, 'r') as f:
            ind = 0
            for line in f:
                #print line
                if line.startswith("TIME"):
                    tmp = {}
                    x = line.split("\n")[0].split(": ")
                    tmp[x[0]] = x[1]

                elif line.startswith("\n"):
                    # Parsed one entry from the RIB text file
                    if ind%100000 == 0:
                        print "entry: ", ind
                    self.updateRibEntry(tmp)
                    if ind > 1000:
                        break
                    ind += 1
                else:
                    x = line.split("\n")[0].split(": ")
                    if len(x) >= 2:
                        tmp[x[0]] = x[1]

    def updateRibEntry(self, elem):
        if "IPV4_UNICAST" in elem["TYPE"]:
            #print "Updating the rib entry ", elem
            # Get the prefix
            prefix = elem["PREFIX"]
            self.prefixes[prefix] = 0

            # Get the attributes
            #origin = elem['ORIGIN'] if 'ORIGIN' in elem else ''
            origin = ''
            as_path = elem['ASPATH'] if 'ASPATH' in elem else ''

            #med = elem["MULTI_EXIT_DISC"] if "MULTI_EXIT_DISC" in elem else ''
            med = ''

            #communities = elem["COMMUNITY"] if "COMMUNITY" in elem else ''
            communities = ''

            atomic_aggregate = ''
            neighbor = elem["FROM"].split(" ")[0]
            # TODO: Current logic currently misses the case where there are two next hops
            next_hop = elem["NEXT_HOP"]
            #prefix text, neighbor text, next_hop text,
            #       origin text, as_path text, communities text, med integer, atomic_aggregate boolean
            atrributes = {"neighbor":neighbor, "next_hop":next_hop, "origin":origin,
                            "as_path":as_path, "communities":communities,
                            "med":med, "atomic_aggregate":atomic_aggregate}

            #print prefix, atrributes

            # Add this entry to the input rib for this participant
            #self.rib["input"].add(prefix, atrributes)
            #self.rib["input"].commit()
            if prefix not in self.local_rib["input"]:
                self.local_rib["input"][prefix] = []
            self.local_rib["input"][prefix].append(atrributes)


    def updateLocalOutboundRib(self):
        for prefix in self.prefixes:
            #routes = self.get_route('input', prefix)
            routes = self.local_rib["input"][prefix]
            #print routes
            #print "For prefix ", prefix, " # of routes ", len(routes)
            best_route = best_path_selection(routes)
            #print "Best route: ", best_route

            # Update the local rib
            #self.add_route('local', prefix, best_route)
            self.local_rib["local"][prefix] = best_route

            # Update the output rib
            #self.add_route('output', prefix, best_route)
            self.local_rib["output"][prefix] = best_route

    def save_ribs(self):
        ind = 0
        start = time.time()
        for rib_name in ["input", "local", "output"]:
            for prefix in self.local_rib[rib_name]:
                if rib_name == "input":
                    for route in self.local_rib[rib_name][prefix]:
                        self.add_route(rib_name, prefix, route)
                        ind += 1
                else:
                    route = self.local_rib[rib_name][prefix]
                    self.add_route(rib_name, prefix, route)
                    ind += 1
        print "Completed write operations for ", id, " rows in ", time.time()-start


''' main '''
if __name__ == '__main__':


    asn_2_ip = json.load(open("asn_2_ip.json", 'r'))
    #asn_2_ip = {"AS12306": {"80.249.208.161": 6}}
    peers = {}
    asn_2_ip_small = {"AS12306": {"80.249.208.161": 6}}


    path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))


    for id in asn_2_ip_small:

        peers[id] = Peer(id, asn_2_ip)
        start = time.time()
        peers[id].updateInputRib()
        print "Time to update the input Rib ", time.time()-start
        start = time.time()
        peers[id].updateLocalOutboundRib()
        print "Time to update the local/output Rib ", time.time()-start
        peers[id].save_ribs()


    base_fname = 'ribs/AS12306.db'

    # Copy .db files for all participants
    for part in asn_2_ip:
        if part not in base_fname:
            new_fname = "ribs/"+part+".db"
            os.system('cp '+base_fname+" "+new_fname)

    # Clean the db files
