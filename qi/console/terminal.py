import sys

def is_a_tty(stream):
    return hasattr(stream, 'isatty') and stream.isatty()

class Terminal(object):
    terminfo = None
    columns = 80
    lines = 25
    isatty = True
    isCygwin = False

    # output colors
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

    def __init__(self, options = {}):
        if 'terminfo' in options:
            self.terminfo = options['terminfo']
        else:
            from .terminfo import Terminfo
            self.terminfo = Terminfo()

        # Set whether output is a tty
        self.isatty = is_a_tty(sys.stdout)

        # Set the columns and lines
        (self.columns, self.lines) = self._getSize()

    def isatty(self):
        return self.isatty

    def printterm(self, text):
        if self.isatty:
            sys.stdout.write(text)

    def clear(self):
        self.printterm(self.terminfo.clear())
        return self

    def locate(self, row, col):
        self.printterm(self.terminfo.cup(row, col))
        return self

    def boldType(self):
        self.printterm(self.terminfo.bold())
        return self

    def setFgColor(self, num):
        self.printterm(self.terminfo.setaf(num))
        return self

    def setBgColor(self, num):
        self.printterm(self.terminfo.setab(num))
        return self

    def prompt(self, text):
        return raw_input(text)

    def getColumns(self):
        (self.columns, self.lines) = self._getSize()
        return self.columns

    def getLines(self):
        (self.columns, self.lines) = self._getSize()
        return self.lines

    def centerText(self, text):
        # TODO: implement
        return text

    def prettyMessage(self, text, fg=7, bg=4, size_=None, verticalPadding=True):

        if None == size_:
            size_ = self.columns

        length = len(text) + 4

        start = self.setaf(fg) + self.setab(bg)
        end = self.op() + "\n"
        newline = end + start

        if length > size_ or "\n" in text:
            length = size_
            text = self.wordwrap(text, size_-4)
            lines = text.split("\n")
            text = ''
            for line in lines:
                line = "  " + line.strip()
                text = text + line.ljust(size_) + newline
        else:
            text = '  ' + text + '  ' + newline

        if verticalPadding == True:
            padding = ' ' * length
        else:
            padding = ''
            end = end.strip()
            newline = end + start

        out = start \
            + padding + newline \
            + text \
            + padding \
            + end

        print(out)

        return self

    def makeBox(self, y, x, w, h):
        # TODO: implement
        return ''

    def startAltCharsetMode(self):
        self.printterm(chr(27) + chr(40) + chr(48))

    def endAltCharsetMode(self):
        self.printterm(chr(27) + chr(40) + chr(66))

    def __getattr__(self, attr):
        def default_method(*args):
            if not self.isatty:
                return ''
            return self.terminfo.doCapability(attr, *args)
        return default_method

    def wordwrap(self, string, width=80, ind1=0, ind2=0, prefix=''):
        """ word wrapping function.
            string: the string to wrap
            width: the column number to wrap at
            prefix: prefix each line with this string (goes before any indentation)
            ind1: number of characters to indent the first line
            ind2: number of characters to indent the rest of the lines
        """
        string = prefix + ind1 * " " + string
        newstring = ""
        while len(string) > width:
            # find position of nearest whitespace char to the left of "width"
            marker = width - 1
            while not string[marker].isspace():
                marker = marker - 1

            # remove line from original string and add it to the new string
            newline = string[0:marker] + "\n"
            newstring = newstring + newline
            string = prefix + ind2 * " " + string[marker + 1:]

        return newstring + string

    def wordwrapDescription(self, string, width=80, indent=0):
        """ word wrapping function that uses all of the available space
            for the last column
            string: the string to wrap
            width: the column number to wrap at
            indent: number of characters to indent the second line on
        """

        if width < 35:
            # if we don't have that much room for the description column, we'll
            # skip the fancy wrapping
            return string

        newstring = ""
        while len(string) > width:
            # find position of nearest whitespace char to the left of "width"
            marker = width - 1
            while not string[marker].isspace():
                marker = marker - 1
                if marker < 0:
                    # couldn't find any spaces so we'll skip the wrapping on
                    # this one
                    return string

            # remove line from original string and add it to the new string
            newline = string[0:marker] + '\n'
            if newstring != '':
                newstring += indent * ' '
            newstring += newline
            string = string[marker + 1:]

        if newstring != '':
            newstring += indent * ' '

        return newstring + string

    def _getSize(self):
        def ioctl_GWINSZ(fd):
            try:
                import fcntl, termios, struct, os
                cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            except:
                return None
            return cr
        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
        if not cr:
            try:
                cr = (env['LINES'], env['COLUMNS'])
            except:
                cr = (25, 80)
        return int(cr[1]), int(cr[0])

