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
        return self.terminal.pretty_message(message, 7, 1)

    def text_success(self, message):
        return self.colortext(message, self.terminal.C_GREEN)

    def text_notify(self, message):
        return self.colortext(message, self.terminal.C_YELLOW)

    def text_info(self, message):
        return self.colortext(message, self.terminal.C_BLUE)

    def text_info_alt(self, message):
        return self.colortext(message, self.terminal.C_CYAN)

    def text_info_desc(self, message):
        return self.colortext(message, self.terminal.C_MAGENTA)

    def text_error(self, message):
        return self.colortext(message, self.terminal.C_RED, isbold=True)

    def colortext(self, text, forecolor=None, backcolor=None, isbold=None):
        if forecolor is None and backcolor is None and isbold is None:
            return text

        if isbold:
            boldstart = self.terminal.bold()
            boldend = self.terminal.sgr0()
        else:
            boldstart = ""
            boldend = ""

        return "{bold}{start}{text}{end}{unbold}".format(
            bold=boldstart,
            start=self.colorstart(forecolor, backcolor),
            text=text,
            end=self.colorend(),
            unbold=boldend,
        )

    def colorstart(self, forecolor=None, backcolor=None):
        coloring = ""
        if forecolor is not None:
            coloring = "{}{}".format(coloring, self.terminal.setaf(forecolor))
        if backcolor is not None:
            coloring = "{}{}".format(coloring, self.terminal.setab(backcolor))

        return coloring

    def colorend(self):
        return self.terminal.op()
