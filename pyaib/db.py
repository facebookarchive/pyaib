#!/usr/bin/env python
#
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
"""
Generic DB Component

Provide a simple key value store.

The Backend data store can be changed out via a driver intermediate.
Must support the following methods, object is a dict or list or mixture

[key(plain text), payload] should be the return value for operations that
return objects

Driver Methods:

getObject(key=, bucket=)
setObject(object, key=, bucket=)
updateObject(object, key=, bucket=)
updateObjectKey(bucket=, oldkey=, newkey=)
updateObjectBucket(key=, oldbucket=, newbucket=)
getAllObjects(bucket=)  (iter)
deleteObject(key=, bucket=) #One at a time for safety
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import hashlib
import json
import inspect
from importlib import import_module

from .components import component_class

CLASS_MARKER = '_PYAIB_DB_DRIVER'


def sha256(msg):
    """ return the hex digest for a givent msg """
    if not isinstance(msg, bytes):
        msg = msg.encode('utf-8')
    return hashlib.sha256(msg).hexdigest()

hash = sha256


def jsonify(thing):
    return json.dumps(thing, sort_keys=True, separators=(',', ':'))


def dejsonify(jsonstr):
    return json.loads(jsonstr)


def db_driver(cls):
    """Mark a class def as a db driver"""
    setattr(cls, CLASS_MARKER, True)
    return cls


@component_class('db')
class ObjectStore(object):
    """ Generic Key Value Store """

    # Database Driver is not loaded
    _driver = None

    def __init__(self, irc_c, config):
        self.config = config
        self._load_driver()
        # Small Sanity Test
        if not self._driver:
            raise RuntimeError('Can not load DB component driver not loaded')

    def _load_driver(self):
        """ Loads the configured driver config.db.backend """
        name = self.config.backend
        if not name:
            #Raise some exception, bail out we are done.
            raise RuntimeError('config item db.backend not set')
        if '.' in name:
            importname = name
        else:
            importname = 'pyaib.dbd.%s' % name
        basename = name.split('.').pop()
        driver_ns = import_module(importname)
        for name, cls in inspect.getmembers(driver_ns, inspect.isclass):
            if hasattr(cls, CLASS_MARKER):
                #Load up the driver
                self._driver = cls(self.config.driver.setdefault(basename, {}))
                break
        else:
            raise RuntimeError('Unable to instance db driver %r' % name)

    #Define easy data access methods
    def get(self, bucket, key=None):
        """Get a Bucket or if key is provided get a Item from the db"""
        if key is None:
            return Bucket(self, bucket)
        key, payload = self._driver.getObject(key, bucket)
        return Item(self._driver, bucket, key, payload)

    def getAll(self, bucket):
        """Get all items in the bucket ITERATOR"""
        for key, payload in self._driver.getAllObjects(bucket):
            yield Item(self._driver, bucket, key, payload)

    def set(self, bucket, key, obj):
        """Store an object in the db by bucket and key, return an Item"""
        self._driver.setObject(obj, key, bucket)
        return Item(self._driver, bucket, key, obj)

    def delete(self, bucket, key):
        """Delete an object in the store"""
        self._driver.deleteObject(key, bucket)


class Item(object):
    """ Represents a item stored in the key value store, with easy methods """
    def __init__(self, driver, bucket, key, payload):
        self._driver = driver
        #Store some meta to determine changes for commit
        self._meta = {'bucket': bucket, 'key': key,
                      'objectHash': hash(jsonify(payload))}
        self.bucket = bucket
        self.key = key
        self.value = payload

    def reload(self):
        self.key, self.value = self._driver.getObject(self._meta['key'],
                                                      self._meta['bucket'])
        self.bucket = self._meta['bucket']

    def delete(self):
        self._driver.deleteObject(self.key, self.bucket)

    def commit(self):
        if hash(jsonify(self.value)) != self._meta['objectHash']:
            if not self.value:
                self.delete()
            else:
                self._driver.updateObject(self.value, self._meta['key'],
                                          self._meta['bucket'])
        elif self._meta['bucket'] != self.bucket:
            if not self.bucket:
                self.delete()
            else:
                self._driver.updateObjectBucket(self._meta['key'],
                                                self._meta['bucket'],
                                                self.bucket)
        elif self._meta['key'] != self.key:
            if not self.key:
                self.delete()
            else:
                self._driver.updateObjectKey(self._meta['bucket'],
                                             self._meta['key'], self.key)
        #Nothing left to commit


class Bucket(object):
    """ An class tied to a bucket """
    def __init__(self, db, bucket):
        self._db = db
        self._bucket = bucket

    def __repr__(self):
        return 'Bucket(%r)' % self._bucket

    def get(self, key):
        return self._db.get(self._bucket, key)

    def getAll(self):
        return self._db.getAll(self._bucket)

    def set(self, key, obj):
        return self._db.set(self._bucket, key, obj)

    def delete(self, key):
        return self._db.delete(self._bucket, key)
