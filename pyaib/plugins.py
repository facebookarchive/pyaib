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
import inspect
import sys

from .components import *

#Use this as an indicator of a class to inspect later
CLASS_MARKER = '_PYAIB_PLUGIN'

if sys.version_info.major == 2:
    str = unicode  # noqa


def plugin_class(cls):
    """
        Let the component loader know to load this class
        If they pass a string argument to the decorator use it as a context
        name for the instance
    """
    if isinstance(cls, str):
        context = cls

        def wrapper(cls):
            setattr(cls, CLASS_MARKER, context)
            return cls
        return wrapper

    elif inspect.isclass(cls):
        setattr(cls, CLASS_MARKER, True)
        return cls

plugin_class.requires = component_class.requires


@component_class('plugins')
@component_class.requires('triggers')
class PluginManager(ComponentManager):
    def __init__(self, context, config):
        ComponentManager.__init__(self, context, config)

        #Load all configured plugins
        self.load_configured()

    def load(self, name):
        #Pull from the global config
        basename = name.split('.').pop()
        config = self.context.config.setdefault("plugin.%s" % basename, {})
        print("Loading Plugin %s..." % name)
        ns = self._process_component(name, self.config.base, CLASS_MARKER,
                                     self.context, config)
        self._loaded_components["plugin.%s" % basename].set(ns)
