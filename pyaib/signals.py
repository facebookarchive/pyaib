def emit_signal(signal_name):
    """Emits the signal of the given name."""

def await_signal(signal_name):
    """Blocks until the signal of the given name is recieved."""

def awaits_signal(signal_name):
    """Decorator; call this function when the signal is recieved."""
    def wrapper(func):
        pass
    return wrapper

class Signal:
    def __init__(self):
        pass

class Signals:
    # Stores all the different signals.
    # There are no pre-defined signals - they will be created by the end user.
    pass
