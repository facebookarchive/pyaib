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

import random

from pyaib.plugins import keyword, plugin_class


@plugin_class
class Jokes(object):
    def __init__(self, irc_context, config):
        self.r = Roulette()
        self.ballresp = config.ballresp
        print("Jokes Plugin Loaded!")

    @keyword('roulette')
    @keyword.nosubs
    @keyword.autohelp_noargs
    def roulette_root(self, irc_c, msg, trigger, args, kargs):
        """[spin|reload|stats|clearstats] :: Play russian roulette.
 One round in a six chambered gun.
 Take turns to spin the cylinder until somebody dies."""
        pass

    @keyword('roulette')
    @keyword.sub('spin')
    @keyword.autohelp
    def roulette_spin(self, irc_c, msg, trigger, args, kargs):
        ''':: spins the cylinder'''
        if self.r.fire(msg.nick):
            msg.reply("BANG! %s %s" % (msg.nick, Roulette.unluckyMsg()))
        else:
            msg.reply("%s %s" % (msg.nick, Roulette.luckyMsg()))

    @keyword('roulette')
    @keyword.sub('reload')
    @keyword.autohelp
    def roulette_reload(self, irc_c, msg, trigger, args, kargs):
        ''':: force the gun to reload'''
        self.r.reload()

    @keyword('roulette')
    @keyword.sub('stats')
    @keyword.autohelp
    def roulette_stats(self, irc_c, msg, trigger, args, kargs):
        '''[player] :: show stats from all games'''
        if len(args) == 0:
            stats = self.r.getGlobalStats()
            msg.reply("In all games there were %d misses and %d kills"
                      % (stats['misses'], stats['hits']))
        else:
            stats = self.r.getStats(args[0])
            if stats:
                msg.reply("%s dodged %d times, died %d times"
                          % (args[0], stats['misses'], stats['hits']))

    @keyword('roulette')
    @keyword.sub('clearstats')
    @keyword.autohelp
    def roulette_clearstats(self, irc_c, msg, trigger, args, kargs):
        ''':: clear stats'''
        self.r.clear()

    @keyword('8ball')
    @keyword.autohelp_noargs
    def magic_8ball(self, irc_c, msg, trigger, args, kargs):
        """[question]? :: Ask the magic 8 ball a question."""
        if not msg.message.endswith('?'):
            msg.reply("%s: that does not look like a question to me" %
                      msg.nick)
            return
        msg.reply("%s: %s" % (msg.nick, random.choice(self.ballresp)))


class Roulette(object):

    luckyQuotes = [
        "got lucky!",
        "is safe... for now.",
        "lived to see another day!"
    ]
    unluckyQuotes = [
        "swallowed a bullet!",
        "snuffed it!",
        "kicked the bucket!",
        "just died!"
    ]

    def __init__(self):
        self.loaded = False
        self.fired = False
        self.chamber = None
        self.position = 0
        self.stats = {}

    @staticmethod
    def luckyMsg():
        return random.choice(Roulette.luckyQuotes)

    @staticmethod
    def unluckyMsg():
        return random.choice(Roulette.unluckyQuotes)

    def clear(self):
        self.stats = {}

    def reload(self):
        self.chamber = random.choice([0, 1, 2, 3, 4, 5])
        self.position = 0
        self.loaded = True

    def getStats(self, nick):
        if nick in self.stats:
            return self.stats[nick]

    def getGlobalStats(self):
        stats = {'hits': 0, 'misses': 0}
        for name in self.stats.keys():
            stats['hits'] += self.stats[name]['hits']
            stats['misses'] += self.stats[name]['misses']
        return stats

    def fire(self, nick):
        if not self.loaded:
            self.reload()

        if nick not in self.stats:
            self.stats[nick] = {'hits': 0, 'misses': 0}

        if(self.position == self.chamber):
            self.loaded = False
            self.fired = True
            self.stats[nick]['hits'] += 1
            return True
        else:
            self.position += 1
            self.stats[nick]['misses'] += 1
            return False
