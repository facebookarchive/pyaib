# Copyright 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sqlite3
import zlib

from pyaib.db import db_driver, hash

try:
    #Try to make use of ujson if we have it
    import ujson as json
    import pyaib.db
    pyaib.db.json = json
    pyaib.db.jsonify = json.dumps
except ImportError:
    pass

from pyaib.db import jsonify, dejsonify


def compress(message):
    if not isinstance(message, bytes):
        message = message.encode('utf-8')
    return zlib.compress(message)


decompress = zlib.decompress


@db_driver
class SqliteDriver(object):
    """ A Sqlite3 Pyaib DB Driver """

    def __init__(self, config):
        path = config.path
        if not path:
            raise RuntimeError('Missing "path" config for sqlite driver')
        try:
            self.conn = sqlite3.connect(path)
        except sqlite3.OperationalError as e:
            #Can't open DB
            raise
        print("Sqlite DB Driver Loaded!")

    def _bucket_exists(self, bucket):
        c = self.conn.execute("SELECT name from sqlite_master "
                              "WHERE type='table' and name=?",
                              (hash(bucket),))
        if c.fetchone():
            return True
        else:
            return False

    def _has_keys(self, bucket):
        c = self.conn.execute("SELECT count(*) from `{}`".format(hash(bucket)))
        row = c.fetchone()
        if row[0]:
            return True
        else:
            return False

    def _create_bucket(self, bucket):
        self.conn.execute("CREATE TABLE `{}` (key blob UNIQUE, value blob)"
                          .format(hash(bucket)))

    def getObject(self, key, bucket):
        if not self._bucket_exists(bucket):
            return key, None
        c = self.conn.execute("SELECT key, value from `{}` WHERE key=?"
                              .format(hash(bucket)), (key,))
        row = c.fetchone()
        if row:
            k, v = row
            return (k, dejsonify(decompress(v)))
        else:
            return key, None

    def setObject(self, obj, key, bucket):
        if not self._bucket_exists(bucket):
            self._create_bucket(bucket)
        self.conn.execute("REPLACE INTO `{}` (key, value) VALUES (?, ?)"
                          .format(hash(bucket)),
                          (key, memoryview(compress(jsonify(obj)))))
        self.conn.commit()

    def updateObject(self, obj, key, bucket):
        self.setObject(obj, key, bucket)

    def updateObjectKey(self, bucket, oldkey, newkey):
        self.conn.execute("UPDATE `{}` set key = ? where key=?"
                          .format(hash(bucket)), (newkey, oldkey))
        self.conn.commit()

    def updateObjectBucket(self, key, oldbucket, newbucket):
        _, v = self.getObject(key, oldbucket)
        self.deleteObject(key, oldbucket, commit=False)
        self.setObject(v, key, newbucket)

    def getAllObjects(self, bucket):
        if not self._bucket_exists(bucket):
            return
        for k, v in self.conn.execute("SELECT key, value from `{}`"
                                      .format(hash(bucket))):
            yield (k, dejsonify(decompress(v)))

    def deleteObject(self, key, bucket, commit=True):
        if self._bucket_exists(bucket):
            self.conn.execute("DELETE from `{}` where key = ?"
                              .format(hash(bucket)), (key,))
            if not self._has_keys(bucket):
                self.conn.execute("DROP TABLE IF EXISTS `{}`"
                                  .format(hash(bucket)))
            if commit:
                self.conn.commit()
