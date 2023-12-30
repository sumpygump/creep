"""QI Console Terminal module"""

import os
import sys

from .terminfo import Terminfo


def is_a_tty(stream):
    return hasattr(stream, "isatty") and stream.isatty()


class Terminal:
    """Console terminal

    Provides functions to output text to a terminal. Provides mechanism for
    doing different colors and other terminal functions. Will bypass terminal
    output codes if detecting that current output is not to a TTY"""

    # Output colors
    C_BLACK = 0  # whatever basic terminal color is set at?
    C_RED = 1
    C_GREEN = 2
    C_YELLOW = 3
    C_BLUE = 4
    C_MAGENTA = 5
    C_CYAN = 6
    C_WHITE = 7

    # Offset for things that extend to terminal width terminal.getColumns(),
    # to keep things from being too familiar with right edge
    TERMINAL_WIDTH_OFFSET = 2

    def __init__(self, **options):
        if "terminfo" in options:
            self.terminfo = options["terminfo"]
        else:
            self.terminfo = Terminfo()

        # Set whether output is a tty
        self._isatty = is_a_tty(sys.stdout)

        # Set the columns and lines
        self.columns, self.lines = self._get_size()

    def isatty(self):
        return self._isatty

    def __getattr__(self, attr):
        """Magic method to call into terminfo capability"""

        def default_method(*args):
            if not self.isatty():
                return ""
            return self.terminfo.do_capability(attr, *args)

        return default_method

    def printterm(self, text):
        if self.isatty():
            # print(text, end="")
            sys.stdout.write(text)

    def clear(self):
        self.printterm(self.terminfo.clear())
        return self

    def locate(self, row, col):
        self.printterm(self.terminfo.cup(row, col))
        return self

    def bold_type(self):
        self.printterm(self.terminfo.bold())
        return self

    def set_fg_color(self, num):
        self.printterm(self.terminfo.setaf(num))
        return self

    def set_bg_color(self, num):
        self.printterm(self.terminfo.setab(num))
        return self

    def get_columns(self):
        self.columns, self.lines = self._get_size()
        return self.columns

    def get_lines(self):
        self.columns, self.lines = self._get_size()
        return self.lines

    def pretty_message(self, text, fg=7, bg=4, max_width=None, vertical_padding=True):
        """Print a pretty message to the terminal"""

        if max_width is None:
            max_width = self.columns

        length = len(text) + 4

        start = self.setaf(fg) + self.setab(bg)
        end = self.op() + "\n"
        newline = end + start

        if length > max_width or "\n" in text:
            length = max_width
            text = self.wordwrap(text, max_width - 4)
            lines = text.split("\n")
            text = ""
            for line in lines:
                line = "  " + line.strip()
                text = text + line.ljust(max_width) + newline
        else:
            text = "  " + text + "  " + newline

        if vertical_padding is True:
            padding = " " * length
        else:
            padding = ""
            end = end.strip()
            newline = end + start

        out = start + padding + newline + text + padding + end

        print(out)

        return self

    def wordwrap(self, string, width=80, ind1=0, ind2=0, prefix=""):
        """Word wrapping function.

        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string (goes before any indentation)
        ind1: number of characters to indent the first line
        ind2: number of characters to indent the rest of the lines
        """

        string = prefix + ind1 * " " + string
        newstring = ""
        while len(string) > width:
            # Find position of nearest whitespace char to the left of "width"
            marker = width - 1
            while not string[marker].isspace():
                marker = marker - 1

            # Remove line from original string and add it to the new string
            newline = string[0:marker] + "\n"
            newstring = newstring + newline
            string = prefix + ind2 * " " + string[marker + 1 :]

        return newstring + string

    def wordwrap_fill(self, string, width=80, indent=0):
        """Word wrapping function that uses all of the available space for the
        last column

        string: the string to wrap
        width: the column number to wrap at
        indent: number of characters to indent the second line on
        """

        if width < 35:
            # If we don't have that much room for the description column, we'll
            # skip the fancy wrapping
            return string

        newstring = ""
        while len(string) > width:
            # Find position of nearest whitespace char to the left of "width"
            marker = width - 1
            while not string[marker].isspace():
                marker = marker - 1
                if marker < 0:
                    # Couldn't find any spaces so we'll skip the wrapping on
                    # this one
                    return string

            # Remove line from original string and add it to the new string
            newline = string[0:marker] + "\n"
            if newstring != "":
                newstring += indent * " "
            newstring += newline
            string = string[marker + 1 :]

        if newstring != "":
            newstring += indent * " "

        return newstring + string

    def _get_size(self):
        """Attempt to get the size of the current terminal

        Returns a tuple of rows,columns"""

        def ioctl_gwinsz(fd):
            try:
                # pylint: disable=import-outside-toplevel
                import fcntl
                import termios
                import struct

                cr = struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, "1234"))
            except:  # pylint: disable=bare-except
                return None
            return cr

        cr = ioctl_gwinsz(0) or ioctl_gwinsz(1) or ioctl_gwinsz(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_gwinsz(fd)
                os.close(fd)
            except:  # pylint: disable=bare-except
                pass

        if not cr:
            cr = (os.getenv("COLUMNS", "80"), os.getenv("LINES", "25"))

        return int(cr[1]), int(cr[0])
