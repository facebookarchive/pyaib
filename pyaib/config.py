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
import sys
import os
import yaml

from .util import data

if sys.version_info.major == 2:

    def construct_yaml_str(self, node):
        return self.construct_scalar(node)

    yaml.SafeLoader.add_constructor('tag:yaml.org,2002:str',
                                    construct_yaml_str)


class Config(object):
    def __init__(self, configFile=None, configPath=None):
        print("Config Module Loaded.")
        if configFile is None:
            raise RuntimeError("YOU MUST PASS 'configFile' DURING BOT INIT")
        (config, searchpaths) = self.__load(configFile, configPath)
        if config is None:
            msg = ("You need a valid main config (searchpaths: %s)" %
                   searchpaths)
            raise RuntimeError(msg)
        #Wrap the config dict
        self.config = data.CaseInsensitiveObject(config)

        #Files can be loaded from the 'CONFIG' section
        #Load the load statement if any
        for section, file in self.config.setdefault('config.load', {}).items():
            config = self.__load(file,
                                 [configPath, self.config.get('config.path')])
            #Badly syntax configs will be empty
            if config is None:
                config = {}
            self.config.set(section, config)

    #Attempt to load a config file name print exceptions
    def __load(self, configFile, path=None):
        data = None
        (filepath, searchpaths) = self.__findfile(configFile, path)
        if filepath:  # If the file is found lets try to load it
            try:
                with open(filepath, 'r') as file:
                    data = yaml.safe_load(file)
                    print("Loaded Config from %s." % configFile)
            except yaml.YAMLError as exc:
                print("Error in configuration file (%s): %s" % (filepath, exc))
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    print("Error position: (%s:%s)" % (mark.line + 1,
                                                       mark.column + 1))
        return (data, searchpaths)

    #Find the requested file in the path (for PARs)
    #If configFile is a list then do lookup for each
    #First Found is returned
    def __findfile(self, configFile, path=None):
        searchpaths = []
        if isinstance(path, list):
            searchpaths.extend(path)  # Optional Config path
        elif path:
            searchpaths.append(path)
        searchpaths.extend(sys.path)
        for path in searchpaths:
            if not os.path.isdir(path):
                path = os.path.dirname(path)
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    if configFile in files:
                        return (os.path.join(root, configFile), searchpaths)
        return (None, searchpaths)
