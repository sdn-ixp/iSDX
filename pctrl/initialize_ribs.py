
import os
import json
import sqlite3

from rib import rib
from decision_process import decision_process, best_path_selection

rib_fname = "rrc03.bview.20150820.0000.temp.txt"

def initialize_ribs(part):
    tmp = {"AS1273": {"2001:7f8:1::a500:1273:1": 5}}

def parse_ribs(fname):
    ribs = []
    with open(fname,'r') as f:
        for line in f:
            #print line
            if line.startswith("TIME"):
                tmp = {}
                x = line.split("\n")[0].split(": ")
                tmp[x[0]] = x[1]

            elif line.startswith("\n"):
                ribs.append(tmp)
            else:
                x = line.split("\n")[0].split(": ")
                if len(x) >= 2:
                    tmp[x[0]] = x[1]
    print "Total entries: ", len(ribs)
    return ribs

class Peer:
    def __init__(self, id, asn_2_ip):
        self.id = id
        self.asn_2_ip = asn_2_ip
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))
        print path
        self.prefixes = {}

        self.rib = {"input": rib(str(id),"input", path, in_memory=True),
                    "local": rib(str(id),"local", path, in_memory=True),
                    "output": rib(str(id),"output", path, in_memory=True)}

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
                    if ind > 10000:
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
            origin = elem['ORIGIN'] if 'ORIGIN' in elem else ''

            as_path = elem['ASPATH'] if 'ASPATH' in elem else ''

            med = elem["MULTI_EXIT_DISC"] if "MULTI_EXIT_DISC" in elem else ''

            communities = elem["COMMUNITY"] if "COMMUNITY" in elem else ''

            atomic_aggregate = ''
            neighbor = elem["FROM"].split(" ")[0]
            # TODO: Current logic currently misses the case where there are two next hops
            next_hop = elem["NEXT_HOP"]
            atrributes = (neighbor, next_hop, origin, as_path,
                         communities, med, atomic_aggregate)

            #print prefix, atrributes

            # Add this entry to the input rib for this participant
            self.rib["input"].add(prefix, atrributes)
            self.rib["input"].commit()

    def updateLocalOutboundRib(self):
        for prefix in self.prefixes:
            routes = self.get_route('input', prefix)
            #print "For prefix ", prefix, " # of routes ", len(routes)
            best_route = best_path_selection(routes)
            #print "Best route: ", best_route

            # Update the local rib
            self.add_route('local', prefix, best_route)

            # Update the output rib
            self.add_route('output', prefix, best_route)


''' main '''
if __name__ == '__main__':

    print "Completed parsing the ribs"
    asn_2_ip = json.load(open("asn_2_ip.json", 'r'))
    #asn_2_ip = {"AS12306": {"80.249.208.161": 6}}
    peers = {}
    asn_2_ip_small = {"AS12306": {"80.249.208.161": 6}}


    path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))


    for id in asn_2_ip_small:
        peers[id] = Peer(id, asn_2_ip)
        peers[id].updateInputRib()
        peers[id].updateLocalOutboundRib()

        peers[id].rib["input"].save_rib(path, str(id))
        peers[id].rib["output"].save_rib(path, str(id))
        peers[id].rib["local"].save_rib(path, str(id))

    base_fname = 'ribs/AS12306.db'

    # Copy .db files for all participants
    for part in asn_2_ip:
        new_fname = "ribs/"+part+".db"
        os.system('cp '+base_fname+" "+new_fname)

    # Clean the db files
