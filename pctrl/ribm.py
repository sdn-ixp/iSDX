#!usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Arpit Gupta (arpitg@cs.princeton.edu)

from collections import namedtuple
from pymongo import MongoClient

import globs

# have all the rib implementations return a consistent interface
labels = ('prefix', 'neighbor', 'next_hop', 'origin', 'as_path', 'communities', 'med', 'atomic_aggregate')
RibTuple = namedtuple('RibTuple', labels)

class rib(object):

    def __init__(self,table_suffix,name):
        self.name = name + "_" + str(table_suffix)
        self.client = MongoClient(globs.MONGODB_HOST, globs.MONGODB_PORT)
        self.db = self.client['demo']
        self.session = self.db[self.name]


    def __del__(self):
        #self.cluster.shutdown()
        pass


    def add(self, item):
        assert(isinstance(item, RibTuple))

        in_stmt = {}
        for i,v in enumerate(labels):
            in_stmt[v] = item[i]

        # avoid adding duplicates
        rows = self.session.find(in_stmt)
        if rows.count() == 0:
            self.session.insert_one(in_stmt)


    def get(self, **kwargs):
        assert len(kwargs)
        assert set(kwargs.keys()).issubset(set(labels))

        rows = self.session.find(kwargs)
        if rows.count() == 0:
            return None
        items = rows[0]
        return RibTuple(*[items[l] for l in labels])


    def get_all(self, **kwargs):
        assert set(kwargs.keys()).issubset(set(labels))

        rows = self.session.find(kwargs)
        return [RibTuple(*[row[l] for l in labels]) for row in rows]


    def get_prefixes(self):
        output = [row['prefix'] for row in self.session.find()]
        return sorted(output)


    def update(self, names, item):
        # validate names
        if isinstance(names, str):
            names = (names,)
        assert names
        assert isinstance(names, tuple) or isinstance(names, list)
        assert set(names).issubset(set(labels))
        # validate item
        assert isinstance(item, RibTuple)

        ds = dict((k,v) for k,v in zip(labels, item) if k in names)
        in_stmt = dict((k,v) for k,v in zip(labels, item))

        rows = self.session.find(ds)
        if rows.count() == 0:
            self.session.insert_one(in_stmt)
        else:
            self.session.update_many(ds, {"$set": in_stmt})


    def delete(self, **kwargs):
        assert set(kwargs.keys()).issubset(set(labels))

        self.session.delete_many(kwargs)


    def dump(self, logger):
        # dump of db for debugging
        rows = self.session.find()
        logger.debug(str(rows.count()))
        for row in rows:
            logger.debug(str(tuple(k+'='+str(row[k]) for k in labels)))


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
