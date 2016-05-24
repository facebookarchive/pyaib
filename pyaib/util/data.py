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

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import weakref
import sys


if sys.version_info.major == 2:
    str = unicode  # noqa


class Raw(object):
    """Wrapper to tell Object not to rewrap but just store the value"""
    def __init__(self, value):
        self.value = value

#A Sentinel value because None is a valid value
sentinel = object()


class Object(dict):
    """
        Pretty DataStructure Objects with lots of magic
        All Collections added to this object will be converted to
        data.Collection if they are not already and instance of that type

        All Dicts added to this class will be converted to data.Object's if
        they are not currently instances of data.Object

        To prevent any conversions from taking place in a value place in a
        data.Object use data.Raw(myobject) to tell data.Object to store it
        as is.

    """
    #dir(self) causes these to be getattr'ed
    #Its a weird python artifact
    __members__ = None
    __methods__ = None

    def __init__(self, *args, **kwargs):
        #Look to see if this object should be somebodies child once not empty
        if kwargs.get('__PARENT__'):
            self.__dict__['__PARENT__'] = kwargs.pop('__PARENT__')
        super(Object, self).__init__(*args, **kwargs)
        #A place to store future children before they are actually children
        self.__dict__['__CACHE__'] = weakref.WeakValueDictionary()
        #Read Only Keys
        self.__dict__['__PROTECTED__'] = set()
        #Make sure all children are Object not dict
        #Also handle 'a.b.c' style keys
        for k in self.keys():
            self[k] = self.pop(k)

    def __wrap(self, value):
        if isinstance(value, (tuple, set, frozenset)):
            return type(value)([self.__wrap(v) for v in value])
        elif isinstance(value, list) and not isinstance(value, Collection):
            return Collection(value, self.__class__)
        elif isinstance(value, Object):
            return value  # Don't Rewrap if already this class.
        elif isinstance(value, Raw):
            return value.value
        elif isinstance(value, dict):
            if isinstance(self, CaseInsensitiveObject):
                return CaseInsensitiveObject(value)
            else:
                return Object(value)
        else:
            return value

    def __protect__(self, key, value=sentinel):
        """Protected keys add its parents, not sure if useful"""
        if not isinstance(key, list):
            key = key.split('.') if isinstance(key, str) else [key]
        key, path = key.pop(0), key
        if len(path) > 0:
            self.get(key).protect(path, value)
        elif value is not sentinel:
            self[key] = value
        if key not in self:
            raise KeyError('key %s has no value to protect' % key)
        self.__PROTECTED__.add(key)

    #Object.key sets
    def __setattr__(self, name, value):
        bad_ids = dir(self)
        #Add some just for causion
        bad_ids.append('__call__')
        bad_ids.append('__dir__')

        if name in self.__PROTECTED__:
            raise KeyError('key %r is read only' % name)

        if name not in bad_ids:
            if self.__dict__.get('__PARENT__'):
                #Do all the black magic with making sure my parents exist
                parent, pname = self.__dict__.pop('__PARENT__')
                parent[pname] = self

            #Get rid of cached future children that match name
            if name in self.__CACHE__:
                del self.__CACHE__[name]

            dict.__setitem__(self, name, self.__wrap(value))
        else:
            print("%s is an invalid identifier" % name)
            print("identifiers can not be %r" % bad_ids)
            raise KeyError('bad identifier')

    #Object.key gets
    def __getattr__(self, key):
        return self.get(key)

    #Dict like functionality and xpath like access
    def __getitem__(self, key, default=sentinel):
        if not isinstance(key, list):
            key = key.split('.') if isinstance(key, str) else [key]
        key, path = key.pop(0), key
        if len(path) > 0:
            return self.get(key).__getitem__(path, default)
        elif key not in self:
            if default is sentinel:
                #Return a parentless object (this might be evil)
                #CACHE it
                return self.__CACHE__.setdefault(
                    key, self.__class__(__PARENT__=(self, key)))
            else:
                return default
        else:
            return dict.get(self, key)

    get = __getitem__

    def __contains__(self, key):
        """ contains method with key paths support """
        if not isinstance(key, list):
            key = key.split('.') if isinstance(key, str) else [key]
        this, next = key.pop(0), key
        if this in self.keys():
            if len(next) > 0:
                return next in self.get(this)
            else:
                return True
        else:
            return False

    has_key = __contains__

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self.get(key)

    #Allow address keys 'key.key.key'
    def __setitem__(self, key, value):
        if not isinstance(key, list):
            key = key.split('.') if isinstance(key, str) else [key]
        key, path = key.pop(0), key
        if len(path) > 0:
            self.setdefault(key, {}).__setitem__(path, value)
        else:
            self.__setattr__(key, value)

    set = __setitem__

    #Allow del by 'key.key.key'
    def __delitem__(self, key):
        if not isinstance(key, list):
            key = key.split('.') if isinstance(key, str) else [key]
        key, path = key.pop(0), key
        if len(path) > 0:
            self.get(key).__delitem__(path)  # Pass the delete down
        else:
            if key not in self:
                pass  # This should handle itself
            else:
                dict.__delitem__(self, key)

    __delattr__ = __delitem__


class CaseInsensitiveObject(Object):
    """A Case Insensitive Version of data.Object"""
    def __protect__(self, key, value=sentinel):
        Object.__protect__(self, key.lower(), value)

    def __getitem__(self, key, default=sentinel):
        if isinstance(key, list):
            key = [x.lower() if isinstance(x, str) else x for x in key]
        elif isinstance(key, str):
            key = key.lower()
        return Object.__getitem__(self, key, default)
    get = __getitem__

    def __setattr__(self, key, value):
        if isinstance(key, str):
            key = key.lower()
        return Object.__setattr__(self, key, value)

    def __contains__(self, key):
        if not isinstance(key, list):
            key = key.split('.') if isinstance(key, str) else [key]
        if isinstance(key[0], str):
            key[0] = key[0].lower()
        return Object.__contains__(self, key)

    has_key = __contains__

    def __getattr__(self, key):
        if key in self:
            return self.get(key)
        else:
            return Object.__getattr__(self, key)

    def __delattr__(self, key):
        if isinstance(key, str):
            key = key.lower()
        return Object.__delattr__(self, key)

    __delitem__ = __delattr__


class Collection(list):
    """Special Lists so [dicts,[dict,dict]] within get converted"""
    def __init__(self, alist=None, default=Object):
        if alist is None:
            alist = ()
        super(Collection, self).__init__(alist)
        self.__default = default
        #Makes sure all the conversions happen
        for i in range(0, len(self)):
            self[i] = self[i]

    def __wrap(self, value):
        if isinstance(value, dict):
            return self.__default(value)
        elif isinstance(value, self.__class__):
            return value  # Do Not Re-wrap
        elif isinstance(value, list):
            return self.__class__(value, self.__default)
        else:
            return value

    def __setitem__(self, key, value):
        super(Collection, self).__setitem__(key, self.__wrap(value))

    def __getslice__(self, s, e):
        return self.__class__(super(Collection, self).__getslice__(s, e),
                              self.__default)

    def append(self, value):
        list.append(self, self.__wrap(value))

    def extend(self, alist):
        for i in alist:
            self.append(i)

    def insert(self, key, value):
        list.insert(self, key, self.__wrap(value))

    def shift(self):
        return self.pop(0)

    def unshift(self, value):
        self.insert(0, value)

    push = append
