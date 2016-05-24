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
import collections
import inspect
import gevent
import functools
import copy
import sys

if sys.version_info.major == 2:
    str = unicode  # noqa



class EasyDecorator(object):
    """An attempt to make Decorating stuff easier"""
    _instance = None
    _thing = _othing = None

    def __init__(self, *args, **kwargs):
        """Figure how we are being called for decoration"""
        #Default to empty
        self.args = []
        self.kwargs = {}

        if len(args) == 1 and not kwargs \
           and (inspect.isclass(args[0]) or isinstance(args[0],
                                                       collections.Callable)):
            self._thing = args[0]
            self._mimic()
        else:
            # Save args so wrappers could use them
            self.args = args
            self.kwargs = kwargs

    def _mimic(self):
        """Mimic the base object so we have the same props"""
        for n in set(dir(self._thing)) - set(dir(self)):
            setattr(self, n, getattr(self._thing, n))
        #These have to happen
        self.__name__ = self._thing.__name__
        self.__doc__ = self._thing.__doc__

    def wrapper(self, *args, **kwargs):
        """Empty Wrapper: Overwride me"""
        return self.call(*args, **kwargs)

    def call(self, *args, **kwargs):
        """Call the decorated object"""
        return self._thing(*args, **kwargs)

    #Instance Methods
    def __get__(self, instance, klass):
        self._instance = instance

        #Before we bind the method lets capture the original
        if self._othing is None:
            self._othing = self._thing

        #Get a bound method from the original
        self._thing = self._othing.__get__(instance, klass)

        #Return a copy of self, for instance safety
        return copy.copy(self)

    #Functions / With args this gets the thing
    def __call__(self, *args, **kwargs):
        if self._thing:
            return self.wrapper(*args, **kwargs)
        else:
            self._thing = args[0]
            self._mimic()
            return self


def filterintree(adict, block, stype=str, history=None):
    """Execute block filter for all strings in a dict/list recusive"""
    if not adict:  # Don't go through the proccess for empty containers
        return adict
    if history is None:
        history = set()
    if id(adict) in history:
        return
    else:
        history.add(id(adict))

    if isinstance(adict, list):
        for i in range(len(adict)):
            if isinstance(adict[i], stype):
                adict[i] = block(adict[i])
            elif isinstance(adict[i], (set, tuple)):
                adict[i] = filterintree(adict[i], block, stype, history)
            elif isinstance(adict[i], (list, dict)):
                filterintree(adict[i], block, stype, history)
    elif isinstance(adict, (set, tuple)):
        c = list(adict)
        filterintree(c, block, stype, history)
        return type(adict)(c)
    elif isinstance(adict, dict):
        for k, v in adict.items():
            if isinstance(v, stype):
                adict[k] = block(v)
            elif isinstance(v, (dict, list)):
                filterintree(v, block, stype, history)
            elif isinstance(v, (set, tuple)):
                adict[k] = filterintree(v, block, stype, history)


class utf8Decode(EasyDecorator):
    """decode all arguments to unicode strings"""
    def wrapper(self, *args, **kwargs):
        def decode(s):
            return s.decode('utf-8', 'ignore')

        args = filterintree(args, decode, stype=bytes)
        filterintree(kwargs, decode, stype=bytes)
        #Call Method with converted args
        return self.call(*args, **kwargs)

    class returnValue(EasyDecorator):
        """decode the return value only"""
        def wrapper(self, *args, **kwargs):
            def decode(s):
                return s.decode('utf-8', 'ignore')

            value = [self.call(*args, **kwargs)]
            filterintree(value, decode, stype=bytes)
            return value[0]


class utf8Encode(EasyDecorator):
    """encode all unicode arguments to byte strings"""
    def wrapper(self, *args, **kwargs):
        def encode(s):
            return s.encode('utf-8', 'backslashreplace')

        args = filterintree(args, encode, stype=str)
        filterintree(kwargs, encode, stype=str)
        #Call Method with converted args
        return self.call(*args, **kwargs)

    class returnValue(EasyDecorator):
        """encode the return value"""
        def wrapper(self, *args, **kwargs):
            def encode(s):
                return s.encode('utf-8', 'backslashreplace')

            value = [self.call(*args, **kwargs)]
            filterintree(value, encode, stype=str)
            return value[0]


def raise_exceptions(func):
    """Wrap around for spawn to raise exceptions in current context"""
    caller = gevent.getcurrent()

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            caller.throw(ex)

    return wrapper
