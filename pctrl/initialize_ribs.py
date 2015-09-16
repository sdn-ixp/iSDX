
import os
import json
import sqlite3
import time
import multiprocessing as mp
from multiprocessing import Process, Queue

from ribm import rib
from decision_process import decision_process, best_path_selection

rib_fname = "rib1.txt"

def initialize_ribs(part):
    tmp = {"AS1273": {"2001:7f8:1::a500:1273:1": 5}}


class Peer:
    def __init__(self, id, asn_2_ip):
        self.id = id
        self.asn_2_ip = asn_2_ip
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))
        #print path
        self.prefixes = {}

        self.rib = {"input": rib(str(id),"input", path),
                    "local": rib(str(id),"local", path),
                    "output": rib(str(id),"output", path)}

        self.local_rib = {"input":{}, "local":{}, "output":{}}

    def get_route(self,rib_name,prefix):

        return self.rib[rib_name].get(prefix)

    def add_route(self,rib_name,prefix,attributes):
        self.rib[rib_name][prefix] = attributes
        #self.rib[rib_name].commit()

    def updateInputRib(self):
        path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "examples", "test-largeIX"))
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
                        print "## ",self.id, " entry: ", ind
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
            neighbor = elem["FROM"].split(" ")[0]
            #print [str(x) for x in self.asn_2_ip[self.id].keys()], neighbor
            if neighbor in [str(x) for x in self.asn_2_ip[self.id]]:
                #if 1==0:
                y = 1
                #print "MATCH", [str(x) for x in self.asn_2_ip[self.id].keys()], neighbor
            else:
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

                # TODO: Current logic currently misses the case where there are two next hops
                next_hop = elem["NEXT_HOP"]

                atrributes = {"neighbor":neighbor, "next_hop":next_hop, "origin":origin,
                                "as_path":as_path, "communities":communities,
                                "med":med, "atomic_aggregate":atomic_aggregate}

                #print prefix, atrributes

                # Add this entry to the input rib for this participant
                self.add_route("input", prefix, atrributes)
                #self.rib["input"].commit()
                """
                if prefix not in self.local_rib["input"]:
                    self.local_rib["input"][prefix] = []
                self.local_rib["input"][prefix].append(atrributes)
                """


    def updateLocalOutboundRib(self):
        for prefix in self.prefixes:
            routes = self.get_route('input', prefix)
            #routes = self.local_rib["input"][prefix]
            #print routes
            #print "For prefix ", prefix, " # of routes ", len(routes)
            best_route = best_path_selection(routes)
            #print "Best route: ", best_route

            # Update the local rib
            self.add_route('local', prefix, best_route)
            #self.local_rib["local"][prefix] = best_route

            # Update the output rib
            self.add_route('output', prefix, best_route)
            #self.local_rib["output"][prefix] = best_route

    def test_ribs(self):
        for prefix in self.prefixes:

            routes = self.get_route("input", prefix)
            best_route = self.get_route("local", prefix)
            #print self.id, "For prefix: ", prefix, " ribs has ", len(routes), " routes"
            #print routes
            #print self.id, "For prefix: ", prefix, " best route is:", best_route




    def save_ribs(self):
        ind = 0
        start = time.time()
        for rib_name in ["input", "local", "output"]:
            items = []
            for prefix in self.local_rib[rib_name]:
                if rib_name == "input":
                    for route in self.local_rib[rib_name][prefix]:
                        #self.add_route(rib_name, prefix, route)
                        #prefix text, neighbor text, next_hop text,
                        #       origin text, as_path text, communities text, med integer, atomic_aggregate boolean
                        items.append(tuple([prefix, route["neighbor"], route["next_hop"],
                                            '', route["as_path"], '', '', '']))

                        ind += 1
                else:
                    route = self.local_rib[rib_name][prefix]
                    #self.add_route(rib_name, prefix, route)
                    items.append(tuple([prefix, route["neighbor"], route["next_hop"],
                                        '', route["as_path"], '', '', '']))
                    ind += 1
            #Coalsecing multiple add insertion operations into one transaction
            # using add_many() function
            print "$$", self.id, "Adding ", len(items), " entries"
            self.rib[rib_name].add_many(items)
            self.rib[rib_name].commit()
        print "##", self.id, "Completed write operations for ", ind, " rows in ", time.time()-start


def processRibIter(id, asn_2_ip):

    peer = Peer(id, asn_2_ip)
    start = time.time()
    peer.updateInputRib()
    print "##", id, "Time to update the input Rib ", time.time()-start
    start = time.time()
    peer.updateLocalOutboundRib()
    print "##", id, "Time to update the local/output Rib ", time.time()-start
    #peer.save_ribs()
    #peer.test_ribs()


''' main '''
if __name__ == '__main__':

    asn_2_ip = json.load(open("asn_2_ip.json", 'r'))
    asn_2_id = json.load(open("asn_2_id.json", 'r'))
    #asn_2_ip = {"AS12306": {"80.249.208.161": 6}}
    peers = {}
    asn = [k for k,v in asn_2_id.iteritems() if v is 1]
    print "ASN: 1: ", asn[0]

    asn_2_ip_small = {}
    asn_2_ip_small[asn[0]] = asn_2_ip[asn[0]]

    #print asn_k_small
    #asn_2_ip_small = {"AS12306": {"80.249.208.161": 6},"AS1273": {"2001:7f8:1::a500:1273:1": 5}}


    path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ribs"))

    process = []
    queue = []
    iter = 0
    for id in asn_2_ip_small:
        process.append(Process(target = processRibIter, args = (id, asn_2_ip)))
        process[iter].start()
        iter += 1

    for p in process:
        p.join()

    """

    base_fname = 'ribs/AS12306.db'
    # Copy .db files for all participants
    for part in asn_2_ip:
        if part not in base_fname:
            new_fname = "ribs/"+part+".db"
            os.system('cp '+base_fname+" "+new_fname)
    """
