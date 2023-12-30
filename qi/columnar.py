import re


def getVisibleLength(text):
    # remove ansi escape sequences (coloring!) before getting the length
    ansi_escape = re.compile(r"(?:\x1b[^m]*m|\x0f)", re.UNICODE)
    return len(ansi_escape.sub("", text).decode("utf-8"))


class Columnar(object):
    pos = 0
    """The internal cursor"""

    headers = []
    """Headers for data"""

    data = []
    """Data rows"""

    widths = []
    """Widths of data for display"""

    fillchars = []
    """Fillchar for each column"""

    def __init__(self, data=[], headers=[], fillchars=[]):
        """Construct object"""
        self.widths = []
        self.data = data
        self.setHeaders(headers)
        self.setFillchars(fillchars)

        self.measureColumnWidths()

    def setHeaders(self, headers=[]):
        self.headers = headers
        return self

    def setFillchars(self, fillchars=[]):
        if len(fillchars) == 0:
            for i in range(len(self.headers)):
                # Default to spaces for each column
                fillchars.append(" ")
        self.fillchars = fillchars
        return self

    def render(self, do_print=True):
        print(self.renderHeaders())

        if do_print:
            for row in self:
                print(row)
        else:
            output = ""
            for row in self:
                output += row.render()
            return output

    def renderHeaders(self):
        out = ""

        if len(self.headers) == 0:
            return out

        for i in range(len(self.widths)):
            header = self.headers[i]
            filler = (self.widths[i] - getVisibleLength(header)) * " "
            out += header + filler + " "

        return out

    def getWidths(self):
        return self.widths

    def getRows(self):
        return self.data

    def getRow(self, offset):
        row = ColumnarRow(self.data[offset], self.widths, self.fillchars)
        return row

    def addRow(self, rowData):
        self.data.append(rowData)
        self.measureColumnWidths()

    def measureColumnWidths(self):
        """Measure the widest entries in each column in the data and the
        headers"""
        for row in self.data:
            i = 0
            for col in row:
                self._setColumnWidth(col, i)
                i = i + 1
        i = 0
        for col in self.headers:
            self._setColumnWidth(col, i)
            i = i + 1

    def next(self):
        if self.pos >= len(self.data):
            raise StopIteration
        row = ColumnarRow(self.data[self.pos], self.widths, self.fillchars)
        self.pos = self.pos + 1
        return row

    def _setColumnWidth(self, col, i):
        # length = getVisibleLength(col.encode('utf-8'))
        length = getVisibleLength(col)

        try:
            if length > self.widths[i]:
                self.widths[i] = length
        except IndexError:
            self.widths.insert(i, length)

    def __iter__(self):
        """Iterator protocol"""
        return self


class ColumnarRow(object):
    widths = []
    data = []
    fillchars = []

    def __init__(self, data=[], widths=[], fillchars=[]):
        self.data = data
        self.widths = widths
        self.fillchars = fillchars

    def render(self):
        out = ""

        for i in range(len(self.widths)):
            try:
                fillchar = self.fillchars[i]
            except IndexError:
                # Default to space if not set
                fillchar = " "

            data = self.data[i]
            filler = (self.widths[i] - getVisibleLength(data)) * fillchar
            out += data + filler + " "

        return out

    def __str__(self):
        return self.render()

    def get(self, offset):
        try:
            itemValue = self.data[offset]
        except:
            return ""

        return itemValue

    def set(self, offset, value):
        self.data[offset] = value
        return self
