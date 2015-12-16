#!/usr/bin/env python
#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)
#  Arpit Gupta (arpitg@cs.princeton.edu)

from collections import namedtuple
import os
import sqlite3
from threading import RLock

lock = RLock()

# have all the rib implementations return a consistent interface
labels = ('prefix', 'neighbor', 'next_hop', 'origin', 'as_path', 'communities', 'med',     'atomic_aggregate')
types  = ('text',   'text',     'text',     'text',   'text',    'text',        'integer', 'boolean')
RibTuple = namedtuple('RibTuple', labels)

class rib(object):

    def __init__(self,ip,name):
        with lock:
            # Create a database in RAM
            self.db = sqlite3.connect('/home/vagrant/iSDX/xrs/ribs/'+ip+'.db',check_same_thread=False)
            self.db.row_factory = sqlite3.Row
            self.name = name

            qs = ', '.join(['?']*len(labels))
            self.insertStmt = 'insert into %s values (%s)' % (self.name, qs)

            stmt = (
                    'create table if not exists '+self.name+
                    ' ('+ ', '.join([l+' '+t for l,t in zip(labels, types)])+')'
                    )

            cursor = self.db.cursor()
            cursor.execute(stmt)
            self.db.commit()


    def __del__(self):
        with lock:
            self.db.close()


    # special case for as_path: externally it is list of ints, but internally (in the db) a string.
    def _as_path_list2str(self, as_path):
        return ' '.join(str(ap) for ap in as_path)

    def _as_path_str2list(self, as_path):
        return [int(ap) for ap in as_path.split()]

    def _as_path_kwargs(self, kwargs):
        if 'as_path' in kwargs:
            kwargs['as_path'] = self._as_path_list2str(kwargs['as_path'])

    def _ri2db(self, item):
        return tuple(item[:4]) + (self._as_path_list2str(item[4]),) + tuple(item[5:])

    def _db2ri(self, item):
        item = tuple(item)
        return RibTuple(*(item[:4]) + (self._as_path_str2list(item[4]),) + tuple(item[5:]))

    def _doSelectUnsafe(self, kwargs):
        cursor = self.db.cursor()

        if kwargs:
            self._as_path_kwargs(kwargs)
            keys, values = zip(*kwargs.items())
            stmt = (
                    'select * from '+self.name+' where ' +
                    ' and '.join(k+' = ?' for k in keys)
                    )
            cursor.execute(stmt, values)
        else:
            stmt = 'select * from '+self.name
            cursor.execute(stmt)

        return cursor


    def add(self, item):
        assert isinstance(item, RibTuple)

        with lock:
            #print "Add:", item
            # see if already present
            cursor = self._doSelectUnsafe(item._asdict())
            row = cursor.fetchone()
            if row is not None:
                return

            # not present; insert
            item = self._ri2db(item)
            cursor.execute(self.insertStmt, item)
            self.db.commit()

    def get(self, **kwargs):
        assert len(kwargs)
        assert set(kwargs.keys()).issubset(set(labels))

        with lock:
            cursor = self._doSelectUnsafe(kwargs)
            row = cursor.fetchone()
            if row is None:
                return row
            return self._db2ri(row)


    def get_all(self, **kwargs):
        assert set(kwargs.keys()).issubset(set(labels))

        with lock:
            cursor = self._doSelectUnsafe(kwargs)
            return [self._db2ri(c) for c in cursor.fetchall()]


    def get_prefixes(self):
        with lock:
            cursor = self._doSelectUnsafe({})

            output = [c['prefix'] for c in cursor.fetchall()]
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

        ds = dict((name, value) for name, value in item._asdict().items() if name in names)

        with lock:
            # get rows with given parameters
            cursor = self._doSelectUnsafe(ds)
            row = cursor.fetchone()
            if row is None:
                # not present, so insert
                cursor.execute(self.insertStmt, self._ri2db(item))
            else:
                # present, so update
                # make custom update statement based on search criteria
                others = tuple(label for label in labels if label not in names)
                updateStmt = (
                        'update '+self.name+' set ' +
                        ', '.join(other+' = ?' for other in others) +
                        ' where ' +
                        ' and '.join(name+' = ?' for name in names)
                        )
                item = RibTuple(*self._ri2db(item))
                ovalues = tuple(getattr(item, other) for other in others)
                nvalues = tuple(getattr(item, name) for name in names)
                cursor.execute(updateStmt, ovalues + nvalues)
            self.db.commit()


    def delete(self, **kwargs):
        assert set(kwargs.keys()).issubset(set(labels))

        with lock:
            cursor = self.db.cursor()

            if kwargs:
                self._as_path_kwargs(kwargs)
                keys, values = zip(*kwargs.items())
                stmt = (
                        'delete from '+self.name+' where ' +
                        ' and '.join(k+' = ?' for k in keys)
                        )
                cursor.execute(stmt, values)
            else:
                stmt = 'delete from '+self.name
                cursor.execute(stmt)

            self.db.commit()


    def dump(self):
        # dump of db for debugging
        with lock:
            cursor = self.db.cursor()
            cursor.execute('''select * from ''' + self.name)
            rows = cursor.fetchall()
        print len(rows)
        for row in rows:
            print row
