#!/usr/bin/env python

import collections
import gevent.event
from copy import copy

from . import irc

def emit_signal(irc_c, name, *, data=None):
    """Emits the signal of the given name."""
    if not isinstance(irc_c, irc.Context):
        raise TypeError("First argument must be IRC context")
    # create signal if it doesn't already exist
    signal = irc_c.signals(name)
    signal.fire(irc_c, data)

def await_signal(irc_c, name, *, timeout=None):
    """Blocks until the signal of the given name is recieved."""
    if not isinstance(irc_c, irc.Context):
        raise TypeError("First argument must be IRC context")
    # create signal if it doesn't already exist
    signal = irc_c.signals(name)
    recieved = signal._event.wait(timeout)
    if recieved is False:
        raise TimeoutError("Waiting for signal %s timed out" % name)
    data = copy(signal._data)
    return data

def clear_signal(irc_c, name):
    """Stop emitting the signal of the given name."""
    if not isinstance(irc_c, irc.Context):
        raise TypeError("First argument must be IRC context")
    if not name in irc_c.signals.list():
        raise ValueError("Signal %s doesn't exist" % name)
    signal = irc_c.signals[name]
    signal.unfire()

class Signal:
    def __init__(self, name):
        self.__observers = [] # list of stuff waiting on this event
        self._event = gevent.event.Event()
        self._data = None
        self.name = name

    def observe(self, observer):
        if isinstance(observer, collections.Callable):
            self.__observers.append(observer)
        else:
            raise TypeError("%s not callable" % repr(observer))
        return self

    def unobserve(self, observer):
        self.__observers.remove(observer)
        return self

    def fire(self, irc_c, data):
        assert isinstance(irc_c, irc.Context)
        # activate the event for waiting existing greenlets
        self._data = data
        self._event.set()
        # manually initiate decorated observers
        for observer in self.__observers:
            if isinstance(observer, collections.Callable):
                irc_c.bot_greenlets.spawn(observer, irc_c, copy(data))
            else:
                raise TypeError("%s not callable" % repr(observer))
        # signal now needs to be unfired by the user

    def unfire(self):
        # reset the gevent event
        self._event.clear()
        self._data = None

    # Observer counts are inaccurate: no way to tell how many existing waiters
    # def getObserverCount(self):
    #     return len(self.__observers)

    # def observers(self):
    #     return self.__observers

    # def __bool__(self):
    #     return self.getObserverCount() > 0

    # __nonzero__ = __bool__  # 2.x compat
    __iadd__ = observe
    __isub__ = unobserve
    # __call__ = fire
    # __len__ = getObserverCount

class Signals:
    # Stores all the different signals.
    # There are no pre-defined signals - they will be created by the end user.
    def __init__(self, irc_c):
        self.__signals = {}
        self.__nullSignal = NullSignal() # is this necessary?

    def list(self):
        return self.__signals.keys()

    def isSignal(self, name):
        return name.lower() in self.__signals

    def getOrMake(self, name):
        if not self.isSignal(name):
            #Make Event if it does not exist
            self.__signals[name.lower()] = Signal(name)
        return self.get(name)

    #Return the null signal on non existent signal
    def get(self, name):
        signal = self.__signals.get(name.lower())
        if signal is None:  # Only on undefined events
            return self.__nullSignal
        return signal

    __contains__ = isSignal
    __call__ = getOrMake
    __getitem__ = get

class NullSignal:
    # not sure this is even needed
    pass
