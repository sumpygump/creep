class Terminfo(object):
    hasTerminfoDb = True

    def __init__(self):
        # curses isn't available on all platforms
        try: import curses
        except:
            self.hasTerminfoDb = False
            return

        try: curses.setupterm()
        except:
            self.hasTerminfoDb = False
            return

    def __getattr__(self, attr):
        def default_method(*args):
            return self.doCapability(attr, *args)
        return default_method

    def hasCapability(self, capName):
        if not self.hasTerminfoDb:
            return False

        import curses
        result = curses.tigetstr(capName)
        return result != None

    def doCapability(self, capName, *args):
        if not self.hasTerminfoDb:
            return ''

        # TODO: this doesn't handle all caps properly
        # It only accepts 1 or 2 args and they must be ints
        import curses
        cap = curses.tigetstr(capName)

        if cap == None:
            return ''

        # Sorry I don't know python well enough yet
        if len(args) > 1:
            result = curses.tparm(cap, int(args[0]), int(args[1]))
        if len(args) == 1:
            result = curses.tparm(cap, int(args[0]))
        else:
            result = curses.tparm(cap)
        return result
