"""Console client

Provides sensible things for a CLI client
"""

import sys

from .terminal import Terminal


class Client(object):
    """QI Console client"""

    def __init__(self, **kwargs):
        """Constructor"""
        if "terminal" in kwargs:
            self.terminal = kwargs["terminal"]
        else:
            self.terminal = Terminal()

    def display_message(self, message, force_new_line=True, color=2):
        end = "\n" if force_new_line else ""
        sys.stdout.write(
            self.terminal.setaf(color) + message + self.terminal.op() + end
        )

    def display_warning(self, message, force_new_line=True):
        return self.display_message(message, force_new_line, color=1)

    def display_error(self, message):
        return self.terminal.prettyMessage(message, 7, 1)
