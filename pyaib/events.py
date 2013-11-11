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
import gevent
import gevent.pool

from . import irc


class Event(object):
    """ An Event Handler """
    def __init__(self):
        self.__observers = []

    def observe(self, observer):
        if isinstance(observer, collections.Callable):
            self.__observers.append(observer)
        else:
            print("Event Error: %s not callable" % repr(observer))
        return self

    def unobserve(self, observer):
        self.__observers.remove(observer)
        return self

    def fire(self, *args, **keywargs):
        #Pull the irc_c from the args
        irc_c = args[0]
        if not isinstance(irc_c, irc.Context):
            print("Error first argument should be the irc context")
            #Maybe DIE here
            return

        for observer in self.__observers:
            if isinstance(observer, collections.Callable):
                irc_c.bot_greenlets.spawn(observer, *args, **keywargs)
            else:
                print("Event Error: %s not callable" % repr(observer))

    def clearObjectObservers(self, inObject):
        for observer in self.__observers:
            if observer.__self__ == inObject:
                self.unobserve(observer)

    def getObserverCount(self):
        return len(self.__observers)

    def observers(self):
        return self.__observers

    def __bool__(self):
        return self.getObserverCount() > 0

    __nonzero__ = __bool__  # 2.x compat
    __iadd__ = observe
    __isub__ = unobserve
    __call__ = fire
    __len__ = getObserverCount


class Events(object):
    """ Manage events allow observers before events are defined"""
    def __init__(self, irc_c):
        self.__events = {}
        self.__nullEvent = NullEvent()
        #A place to track all the running events
        #Events load first so this seems logical
        irc_c.bot_greenlets = gevent.pool.Group()

    def list(self):
        return self.__events.keys()

    def isEvent(self, name):
        return name.lower() in self.__events

    def getOrMake(self, name):
        if not self.isEvent(name):
            #Make Event if it does not exist
            self.__events[name.lower()] = Event()
        return self.get(name)

    #Do not create the event on a simple get
    #Return the null event on non existent events
    def get(self, name):
        event = self.__events.get(name.lower())
        if event is None:  # Only on undefined events
            return self.__nullEvent
        return event

    __contains__ = isEvent
    __call__ = getOrMake
    __getitem__ = get


class NullEvent(object):
    """ Null Object Pattern: Don't Do Anything Silently"""
    def fire(self, *args, **keywargs):
        pass

    def clearObjectObservers(self, obj):
        pass

    def getObserverCount(self):
        return 0

    def __bool__(self):
        return False

    __nonzero__ = __bool__  # Diff between 3.x and 2.x

    def observe(self, observer):
        raise TypeError('Null Events can not have Observers!')

    def unobserve(self, observer):
        raise TypeError('Null Events do not have Observers!')

    __iadd__ = observe
    __isub__ = unobserve
    __call__ = fire
    __len__ = getObserverCount
