"""QI Terminfo module"""


class Terminfo(object):
    """Terminfo class defines the current terminal's capabilities"""

    def __init__(self):
        self.has_terminfo_db = True

        # curses isn't available on all platforms
        try:
            import curses  # pylint: disable=import-outside-toplevel
        except:  # pylint: disable=bare-except
            self.has_terminfo_db = False
            return

        try:
            curses.setupterm()
        except:  # pylint: disable=bare-except
            self.has_terminfo_db = False

    def __getattr__(self, attr):
        def default_method(*args):
            return self.do_capability(attr, *args)

        return default_method

    def has_capability(self, cap_name):
        if not self.has_terminfo_db:
            return False

        import curses  # pylint: disable=import-outside-toplevel

        result = curses.tigetstr(cap_name)
        return result is not None

    def do_capability(self, cap_name, *args):
        if not self.has_terminfo_db:
            return ""

        # TODO: this doesn't handle all caps properly
        # It only accepts 1 or 2 args and they must be ints
        import curses  # pylint: disable=import-outside-toplevel

        cap = curses.tigetstr(cap_name)
        if cap is None:
            return ""

        if len(args) > 0:
            int_args = [int(x) for x in args]
            result = curses.tparm(cap, *int_args)
        else:
            result = curses.tparm(cap)

        return result.decode("utf-8")
