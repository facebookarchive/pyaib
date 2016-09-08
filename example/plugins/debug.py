""" Debug Plugin (botbot plugins.debug) """
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

import time

from pyaib.plugins import observe, keyword, plugin_class, every


#Let pyaib know this is a plugin class and to
# Store the address of the class instance at
# 'debug' in the irc_context obj
@plugin_class('debug')
class Debug(object):

    #Get a copy of the irc_context, and a copy of your config
    # So for us it would be 'plugin.debug' in the bot config
    def __init__(self, irc_context, config):
        print("Debug Plugin Loaded!")

    @observe('IRC_RAW_MSG', 'IRC_RAW_SEND')
    def debug(self, irc_c, msg):
        print("[%s] %r" % (time.strftime('%H:%M:%S'), msg))

    @observe('IRC_MSG_PRIVMSG')
    def auto_reply(self, irc_c, msg):
        if msg.channel is None:
            msg.reply(msg.message)

    @keyword('die')
    def die(self, irc_c, msg, trigger, args, kargs):
        msg.reply('Ok :(')
        irc_c.client.die()

    @keyword('raw')
    def raw(self, irc_c, msg, trigger, args, kargs):
        irc_c.RAW(args)

    @keyword('test')
    def argtest(self, irc_c, msg, trigger, args, kargs):
        msg.reply('Trigger: %r' % trigger)
        msg.reply('ARGS: %r' % args)
        msg.reply('KEYWORDS: %r' % kargs)
        msg.reply('Unparsed: %r' % msg.unparsed)

    @keyword('test')
    @keyword.sub('sub')
    def argsubtest(self, irc_c, msg, trigger, args, kargs):
        msg.reply('Triggers: %r' % trigger)
        msg.reply('ARGS: %s' % args)
        msg.reply('KEYWORDS: %r' % kargs)
        msg.reply('Unparsed: %r' % msg.unparsed)

    @keyword('join')
    def join(self, irc_c, msg, trigger, args, kargs):
        if len(args) > 0:
            irc_c.JOIN(args)

    @keyword('part')
    def part(self, irc_c, msg, trigger, args, kargs):
        if len(args) > 0:
            irc_c.PART(args, message='%s asked me to leave.' % msg.nick)

    @keyword('invite')
    def invite(self, irc_c, msg, trigger, args, kargs):
        if len(args) > 0 and args[0].startswith('#'):
            irc_c.RAW('INVITE %s :%s' % (msg.nick, args[0]))

    @observe('IRC_MSG_INVITE')
    def follow_invites(self, irc_c, msg):
        if msg.target == irc_c.botnick:  # Sanity
            irc_c.JOIN(msg.message)
            irc_c.PRIVMSG(msg.message, '%s: I have arrived' % msg.nick)
