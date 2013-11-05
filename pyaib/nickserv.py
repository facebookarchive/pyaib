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
from .components import component_class, observes


@component_class('nickserv')
class Nickserv(object):
    """ track channels and stuff """
    def __init__(self, irc_c, config):
        self.config = config
        self.password = config.password

    @observes('IRC_ONCONNECT')
    def AUTO_IDENTIFY(self, irc_c):
        if irc_c.config.debug:
            return
        self.identify(irc_c)

        #Spawn off a watcher that makes sure we have the nick we want
        irc_c.timers.clear('nickserv', self.watcher)
        irc_c.timers.set('nickserv', self.watcher, every=90)

    def watcher(self, irc_c, timertext):
        if irc_c.botnick != irc_c.config.irc.nick:
            self.identify(irc_c)

    def identify(self, irc_c):
        if irc_c.botnick != irc_c.config.irc.nick:
            print("TRYING TO GET MY NICK BACK")
            irc_c.PRIVMSG('nickserv', 'GHOST %s %s' % (irc_c.config.irc.nick,
                                                       self.password))
            irc_c.NICK(irc_c.config.irc.nick)

        #Identify
        print("Identifying with nickserv")
        irc_c.PRIVMSG('nickserv', 'IDENTIFY %s' % self.password)
