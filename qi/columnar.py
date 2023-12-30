"""QI columnar module"""

import re


def get_visible_length(text):
    # remove ansi escape sequences (coloring!) before getting the length
    ansi_escape = re.compile(r"(?:\x1b[^m]*m|\x0f)", re.UNICODE)
    # return len(ansi_escape.sub("", text).decode("utf-8"))
    return len(ansi_escape.sub("", text))


class Columnar(object):
    """For displaying rows of data in a columnar format in the terminal

    Columnar(data, headers, fillchars)
      data is a list of lists of each row of data to display
      headers is an optional list of header names
      fillchars is an optional list of padding chars to use for each column

    Example Usage:
      headers = ["name", "phone"]
      data = [["George", "612-555-1234"], ["Mary", "952-555-1010"]]
      columnar = Columnar(data, headers)
      columnar.render()
    """

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

    def __init__(self, data=None, headers=None, fillchars=None):
        """Construct object"""
        self.widths = []
        self.data = data or []
        self.set_headers(headers)
        self.set_fillchars(fillchars)

        self.measure_column_widths()
        self.pos = 0

    def set_headers(self, headers=None):
        self.headers = headers or []
        return self

    def set_fillchars(self, fillchars=None):
        """Set fillchars property"""

        if fillchars is None:
            fillchars = []

        if len(fillchars) == 0:
            # Default to spaces for each column
            fillchars = [" " for _ in range(len(self.headers))]

        self.fillchars = fillchars
        return self

    def render(self, do_print=True):
        """Render the content of this columnar data"""

        if do_print:
            print(self.render_headers())
            for row in self:
                print(row)
            self.pos = 0
            return None

        output = []
        output.append(self.render_headers())
        for row in self:
            output.append(row.render())
        self.pos = 0
        return "{}\n".format("\n".join(output))

    def render_headers(self):
        """Render the headers row"""

        if len(self.headers) == 0:
            return ""

        output = []
        for i in range(len(self.widths)):
            header = self.headers[i]
            filler = (self.widths[i] - get_visible_length(header)) * " "
            output.append(f"{header}{filler}")

        return " ".join(output)

    def get_widths(self):
        return self.widths

    def get_rows(self):
        return self.data

    def get_row(self, offset):
        """Get a hydrated row for a given row offset"""
        return ColumnarRow(self.data[offset], self.widths, self.fillchars)

    def add_row(self, row_data):
        """Add a row to the data"""
        self.data.append(row_data)
        self.measure_column_widths()

    def measure_column_widths(self):
        """Measure the widest entries in each column in the data and the headers"""
        for row in self.data:
            for i, col in enumerate(row):
                self._set_column_width(col, i)
        for i, col in enumerate(self.headers):
            self._set_column_width(col, i)

    def _set_column_width(self, col, i):
        """Set the column width for a given column offset"""
        length = get_visible_length(col)

        try:
            if length > self.widths[i]:
                self.widths[i] = length
        except IndexError:
            self.widths.insert(i, length)

    def __iter__(self):
        """Iterator protocol"""
        return self

    def __next__(self):
        """Iterator protocol for getting next item"""
        if self.pos >= len(self.data):
            raise StopIteration
        row = self.get_row(self.pos)
        self.pos = self.pos + 1
        return row


class ColumnarRow(object):
    """Representation of one row of data"""

    def __init__(self, data=None, widths=None, fillchars=None):
        self.data = data or []
        self.widths = widths or []
        self.fillchars = fillchars or []

    def render(self):
        """Render this row on a line"""
        output = []

        for i in range(len(self.data)):
            value = self.data[i]
            visible_len = get_visible_length(value)

            # Get this column's defined width
            try:
                width = self.widths[i]
            except IndexError:
                width = visible_len

            # Get this column's defined padding char
            try:
                fillchar = self.fillchars[i]
            except IndexError:
                fillchar = " "

            filler = (width - visible_len) * fillchar
            output.append(f"{value}{filler}")

        return " ".join(output)

    def __str__(self):
        return self.render()

    def get(self, offset):
        """Get a specific column's value by column offset"""
        try:
            value = self.data[offset]
        except IndexError:
            return ""

        return value

    def set(self, offset, value):
        """Set a specific column's value by offset"""
        self.data[offset] = value
        return self
