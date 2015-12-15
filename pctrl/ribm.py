#!usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Arpit Gupta (arpitg@cs.princeton.edu)

from collections import namedtuple
import os
import sys
import globs
import socket,struct
from pymongo import MongoClient

# have all the rib implementations return a consistent interface
labels = ('prefix', 'neighbor', 'next_hop', 'origin', 'as_path', 'communities', 'med', 'atomic_aggregate')
RibTuple = namedtuple('RibTuple', labels)

def ip_to_long(ip):
    return struct.unpack('!L', socket.inet_aton(ip))[0]

class rib():

    def __init__(self,table_suffix,name):
        self.name = name + "_" + str(table_suffix)
        self.client = MongoClient(globs.MONGODB_HOST, globs.MONGODB_PORT)
        self.db = self.client['demo']
        self.session = self.db[self.name]


    def save_rib(self, path, outfile_name = "rib.db"):
        print "stub function"


    def __del__(self):
        #self.cluster.shutdown()
        pass


    def __getitem__(self,key):
        return self.get(key)


    def add(self, item):
        print "Add new row: ", item
        assert(isinstance(item, RibTuple))

        in_stmt = {}
        for i,v in enumerate(labels):
            in_stmt[v] = item[i]

        # avoid adding duplicates
        rows = self.session.find(in_stmt)
        if rows.count() == 0:
            self.session.insert_one(in_stmt)


    def get_prefixes(self):
        rows = self.session.find()
        output_rows = []
        for row in rows:
            output_rows.append(row['prefix'])
        return output_rows


    def get(self,key):
        key = str(key)
        rows = self.session.find({"prefix": key})
        if rows.count() == 0:
            return None
        items = rows[0]
        return RibTuple(*[items[l] for l in labels])


    def get_prefix_neighbor(self,key, neighbor):
        key = str(key)
        row = self.session.find_one({"prefix": key, "neighbor": neighbor})
        if row is None:
            return row
        return RibTuple(*[row[l] for l in labels])


    def get_all(self,key=None):
        rows = []
        if (key is not None):
            rows = self.session.find({"prefix": key})
        else:
            rows = self.session.find()

        return [RibTuple(*[row[l] for l in labels]) for row in rows]


    def filter(self,item,value):
        rows = self.session.find({item: value})
        return [RibTuple(*[row[l] for l in labels]) for row in rows]


    def update_with_prefix_neighbor(self, item):
        assert(isinstance(item, RibTuple))
        if self.get_prefix_neighbor(item.prefix, item.neighbor) is not None:
            in_stmt = dict((k,v) for k,v in zip(labels, item))
            rows = self.session.update_one({"prefix": item.prefix, "neighbor": item.neighbor},{"$set": in_stmt})
            #print rows.matched_count
        else:
            self.add(item)


    def delete(self,key):
        # TODO: Add more granularity in the delete process i.e., instead of just prefix,
        # it should be based on a conjunction of other attributes too.
        self.session.delete_many({"prefix": key})


    def delete_prefix_neighbor(self, prefix, neighbor):
        # Deleting one entry in prefix's column that matches on neighbor
        self.session.delete_one({"prefix": prefix, "neighbor": neighbor})


    def delete_all(self):
        self.session.delete_many({})


    def commit(self):
        #print "previous commit, does nothing"
        pass


    def rollback(self):
        print "previous rollback, does nothing"


    def dump(self):
        # dump of db for debugging
        rows = self.session.find()
        print rows.count()
        for row in rows:
            print tuple(k+'='+str(row[k]) for k in labels)


''' main '''
if __name__ == '__main__':
    #TODO Update test

    myrib = rib('ashello', 'test', False)
    print type(myrib)
    #(prefix, neighbor, next_hop, origin, as_path, communities, med,atomic_aggregate)
    myrib['100.0.0.1/16'] = ('172.0.0.2','172.0.0.2', 'igp', '100, 200, 300', '0', 0,'false')
    #myrib['100.0.0.1/16'] = ['172.0.0.2', 'igp', '100, 200, 300', '0', 'false']
    #myrib['100.0.0.1/16'] = {'next_hop':'172.0.0.2', 'origin':'igp', 'as_path':'100, 200, 300',
    #                          'med':'0', 'atomic_aggregate':'false'}
    myrib.commit()

    myrib.update('100.0.0.1/16', 'next_hop', '190.0.0.2')
    myrib.commit()

    val = myrib.filter('prefix', '100.0.0.1/16')
    print val
    print val['next_hop']
    val2 = myrib.get_prefix_neighbor('100.0.0.1/16', '172.0.0.2')
    print val2
