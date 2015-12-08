#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)

from collections import namedtuple
import os
import sqlite3
from threading import RLock

lock = RLock()

labels = ('prefix', 'next_hop', 'origin', 'as_path', 'communities', 'med',     'atomic_aggregate')
types  = ('text',   'text',     'text',   'text',    'text',        'integer', 'boolean')
RibTuple = namedtuple('RibTuple', labels)

class rib():

    def __init__(self,ip,name):

        with lock:
            # Create a database in RAM
            self.db = sqlite3.connect('/home/vagrant/iSDX/xrs/ribs/'+ip+'.db',check_same_thread=False)
            self.db.row_factory = sqlite3.Row
            self.name = name

            # Get a cursor object
            cursor = self.db.cursor()
            stmt = (
                    'create table if not exists '+self.name+
                    ' ('+ ', '.join([l+' '+t for l,t in zip(labels, types)])+')'
                    )
            cursor.execute(stmt)
            self.db.commit()

    def __del__(self):

        with lock:
            self.db.close()

    def __setitem__(self,key,item):

        self.add(key,item)

    def __getitem__(self,key):

        return self.get(key)

    def add(self,key,item):

        with lock:
            assert(len(item) == 6)
            cursor = self.db.cursor()
            #print "Add: ", key, item
            values = '"'+str(key)+'", '
            if (isinstance(item,tuple) or isinstance(item,list)):
                values += ', '.join(['"'+str(x)+'"' for x in item])
            elif (isinstance(item,dict) or isinstance(item,sqlite3.Row)):
                values += ', '.join(['"'+str(x)+'"' for x in [item[l] for l in labels[1:]]])
            else:
                print 'Fatal error: item is not a recognized type'
                sys.exit(1)

            llabels = ', '.join(labels)
            stmt = 'insert into %s (%s) values (%s)' % (self.name, llabels, values)
            cursor.execute(stmt)

        #TODO: Add support for selective update

    def get(self,key):

        with lock:
            cursor = self.db.cursor()
            #print "## DEBUG: Binding Param: ", self.name, key, type(key)
            key = str(key)
            cursor.execute('select * from ' + self.name + ' where prefix = "' + key + '"')

            row = cursor.fetchone()
            if row is None:
                return row
            return RibTuple(*row)

    def get_all(self,key=None):

        with lock:
            cursor = self.db.cursor()

            if (key is not None):
                cursor.execute('select * from ' + self.name + ' where prefix = "' + key + '"')
            else:
                cursor.execute('''select * from ''' + self.name)

            return [RibTuple(*c) for c in cursor.fetchall()]

    def filter(self,item,value):

        with lock:
            cursor = self.db.cursor()

            script = "select * from " + self.name + " where " + item + " = '" + value + "'"

            cursor.execute(script)

            return [RibTuple(*c) for c in cursor.fetchall()]

    def update(self,key,item,value):

        with lock:
            cursor = self.db.cursor()

            script = "update " + self.name + " set " + item + " = '" + value + "' where prefix = '" + key + "'"

            cursor.execute(script)

    def update_many(self,key,item):

        with lock:
            cursor = self.db.cursor()

            if (isinstance(item,tuple) or isinstance(item,list)):
                cursor.execute('''update ''' + self.name + ''' set next_hop = ?, origin = ?, as_path = ?,
                            communities = ?, med = ?, atomic_aggregate = ? where prefix = ?''',
                            (item[0],item[1],item[2],item[3],item[4],item[5],key))
            elif (isinstance(item,dict) or isinstance(item,sqlite3.Row)):
                cursor.execute('''update ''' + self.name + ''' set next_hop = ?, origin = ?, as_path = ?,
                            communities = ?, med = ?, atomic_aggregate = ? where prefix = ?''',
                            (item['next_hop'],item['origin'],item['as_path'],item['communities'],item['med'],
                             item['atomic_aggregate'],key))

    def delete(self,key):

        with lock:
            # TODO: Add more granularity in the delete process i.e., instead of just prefix,
            # it should be based on a conjunction of other attributes too.

            cursor = self.db.cursor()
            cursor.execute('delete from '+self.name+' where prefix = "'+str(key)+'"')

    def delete_all(self):

        with lock:
            cursor = self.db.cursor()
            cursor.execute('delete from '+self.name)

    def commit(self):

        with lock:
            self.db.commit()

    def rollback(self):

        with lock:
            self.db.rollback()

    def dump(self):
        # dump of db for debugging
        with lock:
            cursor = self.db.cursor()
            cursor.execute('''select * from ''' + self.name)
            rows = cursor.fetchall()
        print len(rows)
        for row in rows:
            print row

''' main '''
if __name__ == '__main__':

    #TODO Update test

    myrib = rib('1.2.3.4', 'test')

    myrib['100.0.0.1/16'] = ('172.0.0.2', 'igp', '100, 200, 300', '0', 'false')
    #myrib['100.0.0.1/16'] = ['172.0.0.2', 'igp', '100, 200, 300', '0', 'false']
    #myrib['100.0.0.1/16'] = {'next_hop':'172.0.0.2', 'origin':'igp', 'as_path':'100, 200, 300',
    #                          'med':'0', 'atomic_aggregate':'false'}
    myrib.commit()

    myrib.update('100.0.0.1/16', 'next_hop', '190.0.0.2')
    myrib.commit()

    val = myrib.filter('as_path', '300')

    print val[0]['next_hop']
