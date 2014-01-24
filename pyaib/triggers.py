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

import re
from .events import Events
from .components import component_class, observes, keyword


@component_class
class Triggers(Events):
    """ Handle Trigger Words """
    def __init__(self, irc_c, config):
        Events.__init__(self, irc_c)

        self.prefix = config.prefix or '!'

        #Install self in context
        irc_c['triggers'] = self

        #How to parse trigger arguments
        self._keywordRE = re.compile(r'^--?([a-z]\w*)(?:\s*(=))?\s*(.*)$',
                                     re.I)
        self._argRE = re.compile(r"""^(?:(['"])((?:\\\1|.)*?)\1"""
                                 r"""|(\S+))\s*(.*)$""")
        print("Triggers Loaded")

    def _generate_command_words(self, commands, msg):
        """
            Generate an array of arrays, of command words
            Length of each array, is max irc messages length
        """
        def _size(alist):
            size = 0
            for words in alist:
                for word in words:
                    size += len(word) + 2  # Room for formating
            return size

            #Smarter Line Wrap
        messages = [['Command List:']]  # List of commands to send
        prefix_len = len('PRVMSG %s :' % msg.nick)
        for word in sorted(commands):
            show = False
            event_handler = self.get(word)
            if event_handler:
                for observer in event_handler.observers():
                    if observer.__doc__:
                        show = True
                        break
            if show:  # Hidden Commands Stay Hidden
                if _size(messages[-1]) + len(word) + prefix_len <= 510:
                    messages[-1].append(word)
                else:
                    messages.append([word])
        return messages

    def _clean_doc(self, doc):
        """ Cleanup Multi-line Doc Strings """
        return ' '.join([s.strip() for s in doc.strip().split('\n')])

    def _generate_long_help(self, commands, msg):
        for k in sorted(commands):
            event_handler = self.get(k)
            if event_handler:
                for observer in event_handler.observers():
                    if observer.__doc__:
                        doc = self._clean_doc(observer.__doc__)
                        if hasattr(observer, '_subs'):
                            for sub in observer._subs:
                                msg.reply("%s %s %s"
                                          % (k, sub, doc))
                        else:
                            msg.reply("%s %s" % (k, doc))

    @keyword('help')
    @keyword.autohelp
    def autohelp(self, irc_c, msg, trigger, args, kargs):
        """[<command>]+ [--list|--full] :: get docs"""
        if args:
            commands = args
        else:
            commands = self.list()

        if msg.channel and not args:  # Was this issued in channel without args
            #Force short mode
            if 'full' in kargs:  # If you ask for full we send your the list
                msg.reply_target = msg.nick
            else:
                kargs['list'] = True

        if 'list' in kargs and 'full' not in kargs:
            messages = self._generate_command_words(commands, msg)
            for words in messages:
                msg.reply('%s' % ' '.join(words))
        else:
            self._generate_long_help(commands, msg)

    def parse(self, next):
        """ Take a string of arguments and parse them into args and kwargs """
        args = []
        kwargs = {}
        while next:
            getnext = None
            keymatch = self._keywordRE.search(next)
            if keymatch:
                name, getnext, next = keymatch.groups()
                kwargs[name] = True
                if not getnext:  # So keywords don't get lost
                    continue

            argmatch = self._argRE.search(next)
            if argmatch:
                quotetype, quoted, naked, next = argmatch.groups()
                #Could be a empty string
                arg = quoted if quoted is not None else naked
                #Get rid of any escaped strings
                arg = re.sub(r"""\\(['"])""", r'\1', arg)
                if getnext:
                    kwargs[name] = arg
                else:
                    args.append(arg)
        return [args, kwargs]

    #Just privmsg, rfc forbids automatic responces to notice
    @observes('IRC_MSG_PRIVMSG')
    def _handler(self, irc_c, msg):
        #Addressed Keywords like '<botnick>: keyword'
        address = '%s:' % irc_c.botnick

        #Cleanup the message for parsing
        message = msg.message.strip()
        if (message.startswith(self.prefix)
                or message.lower().startswith(address)
                or msg.channel is None):
            #Lets strip directed addressed messages
            if message.lower().startswith(address):
                message = message[len(address):].strip()

            #Get the trigger and everything else
            parts = message.split(None, 1)
            if parts:
                word = parts.pop(0).lstrip(self.prefix)
            else:
                #WTF empty screw it
                return

            #Try to get the args
            if parts:
                allargs = parts.pop(0)
            else:
                allargs = ''  # Empty NO ARGS provided

            #Get the trigger if it exists
            trigger = self.get(word)

            if trigger:
                args, keywords = self.parse(allargs)
                #Call the trigger with parsed args
                msg.unparsed = allargs
                trigger(irc_c, msg, word, args, keywords)
