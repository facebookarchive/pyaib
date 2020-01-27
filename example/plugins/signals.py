"""Example file for signals."""

from pyiab.plugins import plugin_class
from pyaib.components import observe, awaits_signal
from pyaib.signals import emit_signal, await_signal
import re

@plugin_class('names')
class Names:
    """This plugin provides a command ('names') that outputs a list of all
    nicks currently in the channel."""
    def __init__(self, irc_c, config):
        print("Names plugin loaded")

    @keyword('names')
    def get_list_of_names(self, irc_c, message, trigger, args, kwargs):
        # Sends a NAMES request to the server, to get a list of nicks for the
        # current channel.
        # Issue the NAMES request:
        irc_c.RAW("NAMES %s" % message.channel)
        # The request has been sent.
        # pyaib is asynchronous, so another function will recieve the response
        # from this request.
        # That function must send the data here via a signal.
        try:
            # Wait for the signal (up to 10 seconds).
            response = await_signal(irc_c, 'NAMES_RESPONSE', timeout=10.0)
            # await_signal returns whatever data we choose to send, or True.
        except TimeoutError:
            message.reply("The request timed out.")
            return
        # The NAMES response is now saved.
        channel = response[0]
        names = response[1]
        assert channel == message.channel
        message.reply("List of channel members: %s" % ", ".join(names))

    @observe('IRC_MSG_353') # 353 indicates a NAMES response.
    def recieve_names(self, irc_c, message):
        # The response is in message.args as a single string.
        # "MYNICK = #channel :nick1 nick2 nick3"
        # Split that up into individual names:
        response = re.split(r"\s:?", message.args.strip())[2:]
        channel = response.pop(0)
        names = response[:]
        # Great, we've caught the NAMES response.
        # Now send it back to the function that wanted it.
        emit_signal(irc_c, 'NAMES_RESPONSE', data=(channel, names))
        # The signal name can be anything, so long as emit_signal and
        # await_signal use the same one.
