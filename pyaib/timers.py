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
import time

#TODO Look into replacing timers with some kind of gevent construct


class Timers(object):
    """ A Timers Handler """
    def __init__(self, context):
        self.__timers = []

    def __call__(self, irc_c):
        for timer in self.__timers:
            timer(time.time(), irc_c)
            if not timer:
                self.__timers.remove(timer)

    #Returns the timer
    def set(self, *args, **keywargs):
        timer = Timer(*args, **keywargs)
        if timer:
            self.__timers.append(timer)
        return bool(timer)

    def reset(self, message, callable):
        for timer in self.__timers:
            if timer.message == message and timer.callable == callable:
                if timer.every:
                    timer.at = time.time() + timer.every
                else:
                    self.__timers.remove(timer)

    def clear(self, message, callable):
        for timer in self.__timers:
            if timer.message == message and timer.callable == callable:
                self.__timers.remove(timer)

    def __len__(self):
        return len(self.__timers)


class Timer(object):
    """A Single Timer"""
    # message = Message That gets passed to the callable
    # at = Time when trigger will ring
    # every = How long to push the 'at' time after timer rings
    # count = Number of times the timer will fire before clearing
    # callable = a callable object
    def __init__(self, message, callable, at=None, every=None, count=None):
        self.expired = False
        self.message = message
        if at is None:
            self.at = time.time()
            if every:
                self.at += every
        else:
            self.at = at
        self.count = count
        self.every = every
        if isinstance(callable, collections.Callable):
            self.callable = callable
        else:
            print('Timer Error: %s not callable' % repr(callable))
            self.expired = True

    def __bool__(self):
        return self.expired is False

    __nonzero__ = __bool__

    #Ring Check
    def __call__(self, timestamp, irc_c):
        if not isinstance(self.callable, collections.Callable):
            print('Timer Error: (%r:%r) not callable'
                  % (self.message, callable))
            return

        if not self:  # Sanity test for expired alarms
            return

        if timestamp >= self.at:
            #Throw it into a greenlit
            irc_c.bot_greenlets.spawn(self.callable, irc_c, self.message)

            #Reset the timer
            if self.every:
                self.at = time.time() + self.every
                if self.count:
                    if self.count <= 1:
                        self.expired = True
                    else:
                        self.count -= 1
            else:
                self.expired = True
