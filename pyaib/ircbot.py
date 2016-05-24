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

#WE want the ares resolver, screw thread-pool
import os
os.environ['GEVENT_RESOLVER'] = 'ares'
import gevent.monkey
gevent.monkey.patch_all()

#Screw you python, lets try this for unicode support
import sys
if sys.version_info.major == 2:
    import imp
    imp.reload(sys)
    sys.setdefaultencoding('utf-8')
import signal
import gevent

from .config import Config
from .events import Events
from .timers import Timers
from .components import ComponentManager
from . import irc


class IrcBot(object):
    """ A easy framework to make useful bots """
    def __init__(self, *args, **kargs):
        #Shortcut
        install = self._install

        #Irc Context the all purpose data structure
        install('irc_c', irc.Context(), False)

        #Load the Config
        install('config', Config(*args, **kargs).config)

        #Install most basic fundamental functionality
        install('events', self._loadComponent(Events, False))
        install('timers', self._loadComponent(Timers, False))

        #Load the ComponentManager and load components
        autoload = ['triggers', 'channels', 'plugins']  # Force these to load
        install('components', self._loadComponent(ComponentManager))\
            .load_configured(autoload)

    def run(self):
        """ Starts the Event loop for the bot """
        client = irc.Client(self.irc_c)

        #Tell the client to run inside a greenlit
        signal.signal(signal.SIGINT, client.signal_handler)
        gevent.spawn(client.run).join()

    # Assign things to self and Context
    def _install(self, name, thing, inContext=True):
        setattr(self, name, thing)
        if inContext:
            self.irc_c[name] = thing
        return thing

    def _loadComponent(self, cname, passConfig=True):
        """ Load a Component passing it the context and its config """
        #I am using != instead of is not because of space limits :P
        config = cname.__name__ if cname != ComponentManager else "Components"
        if passConfig:
            return cname(self.irc_c, self.config.setdefault(config, {}))
        else:
            return cname(self.irc_c)
