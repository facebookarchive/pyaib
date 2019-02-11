Python Async IrcBot framework (pyaib)
=====================================

pyaib is an easy to use framework for writing irc bots. pyaib uses gevent
for its Asynchronous bits.

Features
========
* SSL/IPv6
* YAML config
* plugin system
* simple nickserv auth
* simple abstract database system

Setup
=====
<pre><code>pip install pyaib</code></pre>

or 
<pre><code>python setup.py build
python setup.py install</code></pre>

Example
========

Take a look at the example directory for an example bot called 'botbot'

Run:
<pre><code>python example/botbot.py</code></pre>

Try adding your own plugins in example/plugins.

Take a look at the [wiki](https://github.com/facebook/pyaib/wiki) for information about plugin writing and using the db component. 

See the [CONTRIBUTING](CONTRIBUTING.md) file for how to help out.

License
=======
pyaib is Apache licensed, as found in the LICENSE file.
