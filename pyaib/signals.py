#!/usr/bin/env python

import collections
import gevent.event

from . import irc

def emit_signal(irc_c, name):
    """Emits the signal of the given name."""
    # TODO create signal if it doesn't already exist

def await_signal(irc_c, name, timeout=None):
    """Blocks until the signal of the given name is recieved."""
    # TODO create signal if it doesn't already exist
    # add myself to the list of observers
    event = irc_c.signals(name)._event
    recieved = event.wait(timeout)
    if not recieved:
        raise TimeoutError("Waiting for signal %s timed out" % name)
    return recieved
    # remove myself from the list of observers

def awaits_signal(irc_c, name):
    """Decorator; call this function when the signal is recieved."""
    # XXX this shouldn't have irc_c? How do other decorators work
    # TODO create signal if it doesn't already exist
    # add this function to the list of observers
    def wrapper(func):
        pass
    return wrapper

def _unfire_signal(name, irc_c):
    """Resets emitted signals for later reuse."""
    irc_c.signals[name].unfire()

class Signal:
    def __init__(self):
        self.__observers = [] # list of stuff waiting on this event
        self._event = gevent.event.Event()

    def observe(self, observer):
        # XXX this is ok for decorators but not normal waiters
        if isinstance(observer, collections.Callable):
            self.__observers.append(observer)
        else:
            # XXX should throw?
            raise TypeError("%s not callable" % repr(observer))
        return self

    def unobserve(self, observer):
        self.__observers.remove(observer)
        return self

    def fire(self, irc_c, *args, **keywargs):
        assert isinstance(irc_c, irc.Context)
        # initiate or resume each observer
        for observer in self.__observers:
            if isinstance(observer, collections.Callable):
                irc_c.bot_greenlets.spawn(observer, *args, **keywargs)
            elif False:
                # TODO resume existing wating greenlets
                pass
            else:
                raise TypeError("%s not callable" % repr(observer))

    def unfire(self):
        # reset the gevent event
        self._event.clear()

    def getObserverCount(self):
        return len(self.__observers)

    def observers(self):
        return self.__observers

    def __bool__(self):
        return self.getObserverCount() > 0

    __nonzero__ = __bool__  # 2.x compat
    __iadd__ = observe
    __isub__ = unobserve
    __call__ = fire
    __len__ = getObserverCount

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
            self.__signals[name.lower()] = Signal()
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
