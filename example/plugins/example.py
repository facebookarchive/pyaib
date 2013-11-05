""" Example Plugin (dice roller) (botbot plugins.example) """
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

import re

from pyaib.plugins import keyword
from random import SystemRandom


def statsCheck(stats):
    total = sum([(s - 10) / 2 for s in stats])
    avg = total / 6
    return  avg > 0 and max(stats) > 13


def statsGen():
    rand = SystemRandom()
    while True:
        stats = []
        for s in range(0, 6):  # Six Stats
            rolls = []
            for d in range(0, 4):  # Four Dice
                roll = rand.randint(1, 6)
                if roll == 1:  # Reroll 1's once
                    roll = rand.randint(1, 6)
                rolls.append(roll)
            rolls.sort()
            rolls.reverse()
            stats.append(rolls[0] + rolls[1] + rolls[2])
        if statsCheck(stats):
            return stats
    return None


@keyword('stats')
def stats(irc_c, msg, trigger, args, kargs):
    msg.reply("%s: Set 1: %r" % (msg.nick, statsGen()))
    msg.reply("%s: Set 2: %r" % (msg.nick, statsGen()))


rollRE = re.compile(r'((\d+)?d((?:\d+|%))([+-]\d+)?)', re.IGNORECASE)
modRE = re.compile(r'([+-]\d+)')

def roll(count, sides):
    results = []
    rand = SystemRandom()
    for x in range(count):
        if sides == 100 or sides == 1000:
            #Special Case for 100 sized dice
            results.append(rand.randint(1, 10))
            results.append(rand.randrange(0, 100, 10))
            if sides == 1000:
                results.append(rand.randrange(0, 1000, 100))
        else:
            results.append(rand.randint(1, sides))
    return results


@keyword('roll')
def diceroll(irc_c, msg, trigger, args, kargs):

    def help():
        txt = ("Dice expected in form [<count>]d<sides|'%'>[+-<modifer>] or "
               "+-<modifier> for d20 roll. No argument rolls d20.")
        msg.reply(txt)

    if 'help' in kargs or 'h' in kargs:
        help()
        return
    rolls = []
    if not args:
        rolls.append(['d20', 1, 20, 0])
    else:
        for dice in args:
            m = rollRE.match(dice) or modRE.match(dice)
            if m:
                group = m.groups()
                if len(group) == 1:
                    dice = ['d20%s' % group[0], 1, 20, int(group[0])]
                    rolls.append(dice)
                else:
                    dice = [group[0], int(group[1] or 1),
                            100 if group[2] == '%' else int(group[2]),
                            int(group[3] or 0)]
                    rolls.append(dice)
                    if dice[1] > 100 or (dice[2] > 100 and dice[2] != 1000):
                        msg.reply("%s: I don't play with crazy power gamers!"
                                  % msg.nick)
                        return
            else:
                help()
                return

    for dice in rolls:
        results = roll(dice[1], dice[2])
        total = sum(results) + int(dice[3])
        if len(results) > 10:
            srolls = '+'.join([str(x) for x in results[:10]])
            srolls += '...'
        else:
            srolls = '+'.join([str(x) for x in results])
        msg.reply("%s: (%s)[%s] = %d" % (
            msg.nick, dice[0], srolls, total))


print("Example Plugin Done")
