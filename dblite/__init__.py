#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   simple library for stroring python dictionaries in sqlite database
#


import os
import inspect
import sqlite3

from dblite.sql import WhereBuilder
from urlparse import urlparse


SUPPORTED_BACKENDS = ['sqlite',]


def open(item, uri, autocommit=False):
    ''' open sqlite database by uri and Item class
    '''
    if not uri or uri.find('://') <= 0:
        raise RuntimeError('Incorrect URI definition: {}'.format(uri))
    backend, rest_uri = uri.split('://')
    if backend not in SUPPORTED_BACKENDS:
        raise RuntimeError('Unknown backend: {}'.format(backend))
    database, table = rest_uri.split(':')

    return Storage(db=database, table=table, item=item, autocommit=autocommit)


class Storage(object):
    ''' Storage
    
    store simple dictionaries in sqlite database
    '''
    def __init__(self, db, table, item=None, indexes=[], autocommit=False):
        ''' __init__
        
        db          - filename to sqlite database
        fieldnames  - the list of fieldnames
        indexes     - NOT IMPLEMENTED YET
        autocommit  - few variations are possible: boolean (False/True) or integer
                     True - autocommit after each put()
                     False - no autocommit, commit() only manual
                     [integer] - autocommit after N[integer] put()
        '''
        # database file
        if db:
            self._db = db
        else:
            raise RuntimeError('Empty database name, "%s"' % db)
        # database table
        if table:
            self._table = table.split(' ')[0]
        else:
            raise RuntimeError('Empty table name, "%s"' % db)

        self._fieldnames = []
        if item is not None:
            fields = [m[1] for m in inspect.getmembers(item) if m[0] == 'fields']
            if len(fields) != 1:
                raise RuntimeError('Unknown item type, no fields: %s' % item)
            self._fieldnames = fields[0].keys()
        else:
            raise RuntimeError('Item class is not defined, %s' % item)
        
        # sqlite connection
        try:
            self._conn = sqlite3.connect(db)
        except sqlite3.OperationalError, err:
            raise RuntimeError("%s, database: %s" % (err, db))
            
        # sqlite cursor
        self._cursor = self._conn.cursor()
        # autocommit data after put()
        self._autocommit = autocommit
        # commit counter increased every time after put without commit()
        self._commit_counter = 0 

        self._create_table(self._table, self._fieldnames)

    @property
    def fieldnames(self):
        ''' return fieldnames
        '''
        return self._fieldnames

    def _create_table(self, table_name, fieldnames):
        ''' create sqlite's table for storing simple dictionaries
        '''
        if not fieldnames:
            raise RuntimeError('Item fieldnames are not defined')
        sql_fields = ','.join([f for f in fieldnames])
        SQL = 'CREATE TABLE IF NOT EXISTS %s (%s);' % (table_name, sql_fields)
        try:
            self._cursor.execute(SQL)
        except sqlite3.OperationalError, err:
            raise RuntimeError('%s, SQL: %s' % (err, SQL))

    def get(self, criteria=None):
        ''' returns dicts selected by criteria
        
        If the criteria is not defined, get() returns all documents.
        '''
        SQL = "SELECT rowid,* FROM %s" % self._table
        WHERE = WhereBuilder().parse(criteria)
        if WHERE:
            SQL = ' '.join((SQL, 'WHERE', WHERE, ';'))
        else:
            SQL = ''.join((SQL, ';'))

        self._cursor.execute(SQL)
        for r in self._cursor.fetchall():
            _id = r[0]
            fields = [f.split(' ')[0] for f in self._fieldnames]
            dict_res = dict([(fields[i], v) for i, v in enumerate(r[1:])])
            yield (_id, dict_res)
        
    def _do_autocommit(self):
        ''' perform autocommit
        '''
        # commit()
        self._commit_counter += 1
        # autocommit as boolean
        if isinstance(self._autocommit, bool) and self._autocommit:
            self.commit()
            self._commit_counter = 0
        
        # autocommit as counter
        elif isinstance(self._autocommit, int) and self._autocommit > 0:
            if (self._commit_counter % self._autocommit) == 0:
                self.commit()
                self._commit_counter = 0

    def put(self, dictionary):
        ''' store dictionary in sqlite database
        '''
        # prepare SQL
        fieldnames = ','.join([v for v in dictionary.keys()])
        fields_template = ','.join(['?' for f in dictionary])
        SQL = 'INSERT INTO %s (%s) VALUES (%s);' % (self._table, fieldnames, fields_template)
        try:
            self._cursor.execute(SQL, [v for v in dictionary.values()])
        except sqlite3.OperationalError, err:
            raise RuntimeError('%s, SQL: %s, values: %s' % (err, SQL, [v for v in dictionary.values()]) )
        self._do_autocommit()        

    def put_many(self, dictionaries):
        ''' store dictionaries in sqlite database
        '''
        for d in dictionaries:
            self.put(d)

    def delete(self, criteria=None, _all=False):
        ''' delete dictionary(ies) in sqlite database
        
        _all = True - delete all dictionaries
        '''
        SQL = 'DELETE FROM %s' % self._table
        WHERE = WhereBuilder().parse(criteria)
        if WHERE:
            SQL = ' '.join((SQL, 'WHERE', WHERE, ';'))
        elif not _all:
            raise RuntimeError('Criteria is not defined')
        
        if _all:    
            SQL = ''.join((SQL, ';'))
        
        self._cursor.execute(SQL)
                
    def __len__(self):
        ''' return size of storage
        '''
        SQL = 'SELECT count(*) FROM %s;' % self._table
        self._cursor.execute(SQL)
        return int(self._cursor.fetchone()[0])

    def commit(self):
        ''' commit changes
        '''
        self._conn.commit()

    def close(self):
        ''' close database
        '''
        self._conn.close()

        