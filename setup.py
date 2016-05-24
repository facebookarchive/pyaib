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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

#Pull version out of the module
from pyaib import __version__

setup(name='pyaib',
      version=__version__,
      packages=['pyaib', 'pyaib.dbd', 'pyaib.util'],
      url='http://github.com/facebook/pyaib',
      license='Apache 2.0',
      author='Jason Fried, Facebook',
      author_email='fried@fb.com',
      description='Python Framework for writing IRC Bots using gevent',
      classifiers=[
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Communications :: Chat :: Internet Relay Chat',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'Intended Audience :: Developers',
          'Development Status :: 5 - Production/Stable',
      ],
      install_requires=[
          'pyOpenSSL >= 0.12',
          'gevent >= 1.1.0',
          'PyYAML >= 3.09',
      ])
