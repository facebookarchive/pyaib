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


@component_class('channels')
class Channels(object):
    """ track channels and stuff """
    def __init__(self, irc_c, config):
        self.channels = set()
        self.config = config
        self.db = None
        print("Channel Management Loaded")

    #Provide a little bit of magic
    def __contains__(self, channel):
        return channel.lower() in self.channels

    @observes('IRC_ONCONNECT')
    def _autojoin(self, irc_c):
        self.channels.clear()
        if self.config.autojoin:
            if isinstance(self.config.autojoin, basestring):
                self.config.autojoin = self.config.autojoin.split(',')
            if self.config.db and irc_c.db:
                print("Loading Channels from DB")
                self.db = irc_c.db.get('channels', 'autojoin')
                if self.db.value:
                    merge = list(set(self.db.value + self.config.autojoin))
                    self.config.autojoin = merge
                else:
                    self.db.value = []
                self.db.value = sorted(self.config.autojoin)
                self.db.commit()
            print("Channels Auto Joining: %r" % self.config.autojoin)
            irc_c.JOIN(self.config.autojoin)

    @observes('IRC_MSG_JOIN')
    def _join(self, irc_c, msg):
        #Only Our Joins
        if msg.nick.lower() == irc_c.botnick.lower():
            channel = msg.args.strip().lower()
            self.channels.add(channel)
            if self.db and channel not in self.db.value:
                self.db.value.append(channel)
                self.db.value.sort()
                self.db.commit()

    @observes('IRC_MSG_PART')
    def _part(self, irc_c, msg):
        channel, _, part_msg = msg.args.strip().partition(' ')
        #Only Our Parts
        if msg.nick.lower() == irc_c.botnick.lower():
            self.channels.remove(channel.lower())
            if self.db and channel.lower() in self.db.value:
                self.db.value.remove(channel.lower())
                self.db.value.sort()
                self.db.commit()

    @observes('IRC_MSG_KICK')
    def _kick(self, irc_c, msg):
        channel, nick, rmessage = msg.args.split(' ', 2)
        if irc_c.botnick.lower() == nick.lower():  # Case Insensitive match
            self.channels.remove(channel.lower())
