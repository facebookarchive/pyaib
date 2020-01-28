#!/usr/bin/env python

import collections
import gevent.event
import gevent.queue
import gevent

from . import irc

def emit_signal(irc_c, name, *, data=None):
    """Emits the signal of the given name."""
    if not isinstance(irc_c, irc.Context):
        raise TypeError("First argument must be IRC context")
    if data is False:
        raise ValueError("Signalled data cannot be False")
    # create signal if it doesn't already exist
    signal = irc_c.signals(name)
    signal.fire(irc_c, data)

def await_signal(irc_c, name, *, timeout=None):
    """Blocks until the signal of the given name is recieved, returning any
    data that was passed to it."""
    if not isinstance(irc_c, irc.Context):
        raise TypeError("First argument must be IRC context")
    # create signal if it doesn't already exist
    signal = irc_c.signals(name)
    return signal.wait(timeout)

class Signal:
    def __init__(self, name):
        self.__event = gevent.event.Event()
        self.__observers = [] # decorated observers
        self.__waiters = [] # waiting greenlets
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
        # resume waiting greenlets
        waiters = list(self.__waiters)
        self.__waiters.clear()
        gevent.spawn(self._notify, waiters, data)
        # manually initiate decorated observers
        for observer in self.__observers:
            if isinstance(observer, collections.Callable):
                irc_c.bot_greenlets.spawn(observer, irc_c, copy(data))
            else:
                raise TypeError("%s not callable" % repr(observer))

    @staticmethod
    def _notify(waiters, data):
        for queue in waiters:
            queue.put_nowait(data)

    def wait(self, timeout):
        queue = gevent.queue.Channel()
        self.__waiters.append(queue)
        data = queue.get(timeout)
        if data is False:
            raise TimeoutError("The request timed out.")
        return data

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
