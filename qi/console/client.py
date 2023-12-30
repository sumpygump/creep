"""Console client

Provides sensible things for a CLI client
"""

import sys


class Client(object):

    terminal = None
    """Terminal object"""

    def __init__(self, **kwargs):
        """Constructor"""
        if "terminal" in kwargs:
            self.terminal = kwargs["terminal"]

    def displayWarning(self, message, force_new_line=True):
        return self.displayMessage(message, force_new_line, 1)

    def displayMessage(self, message, force_new_line=True, color=2):
        end = ""
        if force_new_line:
            end = "\n"

        sys.stdout.write(
            self.terminal.setaf(color) + message + self.terminal.op() + end
        )

    def displayError(self, message):
        self.terminal.prettyMessage(message, 7, 1)
