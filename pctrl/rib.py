#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Arpit Gupta (arpitg@cs.princeton.edu)

import os
import sqlite3
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement
from threading import RLock as lock
from StringIO import StringIO
import globs
import socket,struct

def ip_to_long(ip):
    return struct.unpack('!L', socket.inet_aton(ip))[0]

class rib():

    def __init__(self,table_suffix,name,path, in_memory=False):

        with lock():
            if not in_memory:
                self.cluster = Cluster(
                                contact_points=globs.CASSANDRA_HOST
                                )
                self.session = self.cluster.connect(globs.CASSANDRA_SPACE)
            else:
                print "Reading", name, "rib from database file", db_file + "...",
                # Read database to tempfile
                con = sqlite3.connect(db_file,check_same_thread=False)
                tempfile = StringIO()
                for line in con.iterdump():
                    tempfile.write('%s\n' % line)
                con.close()
                tempfile.seek(0)
                print "Writing to memory database...",

                # Create a database in memory and import from tempfile
                self.db = sqlite3.connect(":memory:")
                self.db.cursor().executescript(tempfile.read())
                self.db.commit()

                print "done."

            #initialize table name using ip + type(local, input, output)
            self.name = name + "_" + str(table_suffix)
            print self.name
            # Use cassandra session object
            query = '''CREATE TABLE IF NOT EXISTS '''+ str(self.name) +''' (prefix text PRIMARY KEY, neighbor text, next_hop text, origin text, as_path text, communities text, med text, atomic_aggregate text);'''
            print query
            prep = self.session.prepare(query)
            self.session.execute(prep)


    def save_rib(self, path, outfile_name = "rib.db"):

        print "stub function"

    def __del__(self):
        with lock():
            print "Cluster Type: ", type(self.cluster)
            self.cluster.shutdown()

    def __setitem__(self,key,item):

        self.add(key,item)

    def __getitem__(self,key):

        return self.get(key)

    def add(self,key,item):

        with lock():
            #print '''insert into ''' + self.name + ''' (prefix, next_hop, origin, as_path, communities, med,atomic_aggregate) values(?,?,?,?,?,?,?)''',(key,item[0],item[1],item[2],item[3],item[4],item[5])
            #print "Add: ", key, item
            key = str(key)
            if (isinstance(item,tuple) or isinstance(item,list)):
                assert (len(item) == 7)
                # Use cassandra session object
                query = "insert into " + self.name + "(prefix, neighbor, next_hop, origin, as_path, communities, med,atomic_aggregate) values('" + key + "','" + str(item[0]) +"','" + str(item[1]) +"','" + str(item[2])+"','" + str(item[3])+"','"+ str(item[4])+"','" + str(item[5])+ "','" + str(item[6])+"');"
                prep = self.session.prepare(query)
                self.session.execute(prep)
            elif (isinstance(item,dict) or isinstance(item,sqlite3.Row)):
                query = '''insert into ''' + self.name + ''' (prefix, neighbor, next_hop, origin, as_path, communities, med,
                        atomic_aggregate) values(?,?,?,?,?,?,?,?)''',(key,item['neighbor'], item['next_hop'],item['origin'],item['as_path'],item['communities'],item['med'],item['atomic_aggregate'])
                prep = self.session.prepare(query)
                self.session.execute(prep)
        #TODO: Add support for selective update

    def add_many(self,items):

        with lock():
            if (isinstance(items,list)):
                insert_tuple = self.session.prepare("INSERT INTO "+ self.name +" (prefix, neighbor, next_hop, origin, as_path, communities, med, atomic_aggregate) VALUES (?,?,?,?,?,?,?,?)")
                batch = BatchStatement()

                for item in items:
                    batch.add(insert_tuple, item)

                self.session.execute(batch)

    def get(self,key):

        with lock():
            #print "## DEBUG: Binding Param: ", self.name, key, type(key)
            key = str(key)
            query = "select * from " + self.name + " where prefix = '" + key + "'"
            prep = self.session.prepare(query)
            rows = self.session.execute(prep)
            return rows

    def get_prefix_neighbor(self,key, neighbor):

        with lock():
            key = str(key)
            query = '''select * from ''' + self.name + ''' where prefix = ? AND neighbor = ? limit 1''', (key, neighbor)
            prep = self.session.prepare(query)
            row = self.session.execute(prep)

            return row

    def get_all(self,key=None):

        with lock():
            rows = []
            if (key is not None):
                query = '''select * from ''' + self.name + ''' where prefix = ?''', (key,)
                prep = self.session.prepare(query)
                rows = self.session.execute(prep)
            else:
                query = '''select * from ''' + self.name
                prep = self.session.prepare(query)
                rows = self.session.execute(prep)

            return rows

    def filter(self,item,value):

        with lock():
            query = "select * from " + self.name + " where " + item + " = '" + value + "' ALLOW FILTERING"
            print query
            prep = self.session.prepare(query)
            rows = self.session.execute(prep)

            return rows

    def update(self,key,item,value):

        with lock():
            query = "update " + self.name + " set " + item + " = '" + value + "' where prefix = '" + key + "'"
            prep = self.session.prepare(query)
            rows = self.session.execute(prep)

    def update_many(self,key,item):

        with lock():
            cursor = self.db.cursor()

            if (isinstance(item,tuple) or isinstance(item,list)):
                query = '''update ''' + self.name + ''' set next_hop = ?, origin = ?, as_path = ?,
                            communities = ?, med = ?, atomic_aggregate = ? where prefix = ?''',(item[0],item[1],item[2],item[3],item[4],item[5],key)
                prep = self.session.prepare(query)
                rows = self.session.execute(prep)
            elif (isinstance(item,dict) or isinstance(item,sqlite3.Row)):
                query = '''update ''' + self.name + ''' set next_hop = ?, origin = ?, as_path = ?,
                            communities = ?, med = ?, atomic_aggregate = ? where prefix = ?''',(item['next_hop'],item['origin'],item['as_path'],item['communities'],item['med'],
                             item['atomic_aggregate'],key)
                prep = self.session.prepare(query)
                rows = self.session.execute(prep)

    def delete(self,key):

        with lock():
            # TODO: Add more granularity in the delete process i.e., instead of just prefix,
            # it should be based on a conjunction of other attributes too.
            query = '''delete from ''' + self.name + ''' where prefix = ?''', (key,)
            prep = self.session.prepare(query)
            rows = self.session.execute(prep)

    def delete_prefix_neighbor(self, prefix, neighbor):

        with lock():
            # Deleting one entry in prefix's column that matches on neighbor

            query = '''delete from ''' + self.name + ''' where prefix = ? AND neighbor = ?''', (prefix, neighbor)
            prep = self.session.prepare(query)
            rows = self.session.execute(prep)

    def delete_all(self):

        with lock():
            cursor = self.db.cursor()
            query = '''delete from ''' + self.name
            prep = self.session.prepare(query)
            rows = self.session.execute(prep)

    def commit(self):

        print "previous commit, does nothing"

    def rollback(self):

        print "previous rollback, does nothing"


''' main '''
if __name__ == '__main__':

    #TODO Update test

    myrib = rib('1.2.3.4', 'test', False)
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
    print val[0].next_hop
