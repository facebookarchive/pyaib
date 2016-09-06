"""Karma Plugin (crushinator.plugins.karma)"""
# Copyright 2016 Facebook
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from pyaib.plugins import observe, keyword, plugin_class
import re
import functools

# allow for yoda style karam
kregex = re.compile(r'^(\+\+|--)?(.+?)(\+\+|--)?$')


@plugin_class
@plugin_class.requires('db')
class Karma(object):
    def __init__(self, irc_context, config):
        self.db = irc_context.db.get('plugin.karma')
        self.scanner = True
        self.pronoun = config.get('pronoun', 'her')
        self.scanner_refresh = config.get('scanner_refresh', 3600 * 12)
        print("Karma Plugin Loaded!")

    @keyword('karma')
    def stats(self, irc_c, msg, trigger, args, kargs):
        """ get karma for something / defaults to your karma lookup """

        if not self.scanner:
            msg.reply("Sorry {}, I crushed my karma scanner."
                      .format(msg.nick))
            return

        if not args:
            karma = self.get_karma(msg.nick.user)
            who = msg.nick
        else:
            karma = self.get_karma(args[0])
            who = args[0]

        if karma > 9000:
            msg.reply("\001ACTION removes {} karma scanner.\001"
                      .format(self.pronoun))
            msg.reply("It's Over 9000!")
            msg.reply("\001ACTION crushes the karma scanner in {} clenched "
                      "fist.\001".format(self.pronoun))
            self.scanner = False
            self.where = msg.channel
            irc_c.timers.set('ORDER-KARMA-SCANNER',
                             functools.partial(self.get_scanner, msg.reply),
                             at=msg.timestamp + self.scanner_refresh)
        else:
            msg.reply("Karma for {} is {}".format(who, karma))

    def get_scanner(self, reply, irc_c, alarm):
        if self.scanner:
            return
        self.scanner = True
        reply('\001ACTION receives a karma scanner and equips it '
              'over {} left eye.\001'.format(self.pronoun))

    def get_karma(self, thing):
        item = self.db.get(thing)
        if item.value is None:
            item.value = 0
        item.commit()
        return item.value

    def set_karma(self, thing, value):
        item = self.db.get(thing)
        item.value = value
        item.commit()

    @observe('IRC_MSG_PRIVMSG')
    def gift(self, irc_c, msg):
        if not msg.channel:
            return
        p = '^\x01ACTION gives {} (?:a|his|her|its) karma scanner(?:.|!)?\x01$'
        if re.search(p.format(irc_c.botnick), msg.message, re.IGNORECASE):
            if self.scanner:
                msg.reply("No Thanks {} I have one!".format(msg.nick))
            else:
                self.scanner = True
                msg.reply("Thanks {} I needed that!".format(msg.nick))

    @observe('IRC_MSG_PRIVMSG')
    def log(self, irc_c, msg):
        if not msg.channel:
            return

        # Collect all the karma changes
        changes = {}
        for word in re.split("\s", msg.message):
            match = kregex.match(word)
            if match:
                pre, thing, post = match.groups()
                for mod in [pre, post]:
                    if not mod:
                        continue
                    if mod == '++':
                        changes[thing] = changes.setdefault(thing, 0) + 1
                    else:
                        changes[thing] = changes.setdefault(thing, 0) - 1

        # Apply the Karma
        for thing, change in changes.items():
            if msg.sender.user == thing:   # Don't allow to bump your own karma
                continue
            self.set_karma(thing, self.get_karma(thing) + change)
