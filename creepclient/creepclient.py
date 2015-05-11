"""CLI client for creep"""

import cmd # Command interpreter logic. Gives us the base class for the client
import inspect # Functions to inspect live objects
import os # Miscellaneous operating system interfaces
import shutil # High-level file operations
import subprocess # Spawn subprocesses, connect in/out pipes, obtain return codes
import sys # System specific parameters and functions

from qi.console.client import Client
from repository import Repository

class CreepClient(Client, cmd.Cmd):
    """Creep Mod Package Manager Client"""

    # Version of this client
    VERSION = '0.1'

    # Absolute path where this client is installed
    installdir = ''

    # Absolute path to the dotfile for this client
    appdir = ''

    # Absolute path to the minecraft dir
    minecraftdir = ''

    def __init__(self, **kwargs):
        """Constructor"""
        cmd.Cmd.__init__(self)
        Client.__init__(self, **kwargs)

        self.updateVersionWithGitDescribe()
        self.updatePaths()

        self.createRepository()

    def do_version(self, args):
        """Display creep version"""
        print self.colortext("Creep v{}".format(self.VERSION), self.terminal.C_GREEN)

    def do_list(self, args):
        """List packages (mods)
Usage: creep list [installed]

Examples:
  creep list
     List available packages in repository

  creep list installed
     List installed packages
"""
        if args == 'installed':
            installdir = self.minecraftdir + os.sep + 'mods'
            files = os.listdir(installdir)
            if not files:
                print "No mods installed"
                return False

            print self.colortext("Installed mods (in {}):".format(installdir), self.terminal.C_YELLOW)
            for name in files:
                package = self.repository.fetch_package_byfilename(name)
                if not package:
                    print self.colortext(name, self.terminal.C_RED)
                else:
                    self.print_package(package)
        else:
            self.display_packages()

    def display_packages(self):
        """Display list of packages available"""
        for package in self.repository.packages:
            self.print_package(package)

    def print_package(self, package):
        print '{name} {version} - {description}'.format(
            name=package.name,
            version=self.colortext('(' + package.version + ')', self.terminal.C_YELLOW),
            description=self.colortext(package.description, self.terminal.C_MAGENTA)
        )

    def do_search(self, args):
        """Search for a package (mod)
Usage: creep search <packagename>

Example: creep search nei
"""
        if args == '':
            return False

        packages = self.repository.search(args)
        for package in packages:
            self.print_package(package)

    def do_install(self, args):
        """Install a package (mod)
Usage: creep install <packagename>

Example: creep install thecricket/chisel2 
"""
        package = self.repository.fetch_package(args)
        if not package:
            print self.colortext("Unknown package '{}'".format(args), self.terminal.C_RED)
            return 1

        print self.colortext("Installing package {}".format(package), self.terminal.C_BLUE)

        # Install any required packages
        # Warning: does not handle versions or circular dependencies
        for dependency in package.require:
            if dependency == 'minecraft' or dependency == 'forge':
                continue
            print self.colortext("Installing dependency '{}'".format(dependency), self.terminal.C_CYAN)
            self.do_install(dependency)

        cachedir = self.appdir + os.sep + 'cache'
        if not os.path.isfile(cachedir + os.sep + package.filename):
            print self.colortext("Downloading mod '{0}' from {1}".format(package.name, package.get_download_location()), self.terminal.C_YELLOW)
            package.download(cachedir)

        savedir = self.minecraftdir + os.sep + package.installdir 
        shutil.copyfile(cachedir + os.sep + package.filename, savedir + os.sep + package.filename)

        print self.colortext("Installed mod '{0}' in '{1}'".format(package.name, savedir + os.sep + package.filename), self.terminal.C_GREEN)

    def do_uninstall(self, args):
        """Uninstall a package (mod)
Usage: creep uninstall <packagename>

Example: creep uninstall thecricket/chisel2 
"""
        package = self.repository.fetch_package(args)
        if not package:
            print 'Unknown package {}'.format(args)
            return 1

        savedir = self.minecraftdir + os.sep + package.installdir 
        os.remove(savedir + os.sep + package.filename)
        print "Removed mod '{0}' from '{1}'".format(package.name, savedir)

    def do_purge(self, args):
        """Purge all installed packages (mods)
Usage: creep purge
"""
        print "Purging all installed mods in {}...".format(self.minecraftdir + os.sep + 'mods')
        installdir = self.minecraftdir + os.sep + 'mods'
        self.delete_path(installdir)
        print "Done."

    def do_update(self, args):
        """Force an update of the package repository"""

        self.repository.clear_cache()
        self.repository.populate()
        print self.colortext("Repository updated to version {} ({}).".format(self.repository.version_hash, self.repository.version_date), self.terminal.C_GREEN)
        print "Count: {} packages.".format(self.repository.count_packages())

    def delete_path(self, rootdir):
        files = os.listdir(rootdir)
        for f in files:
            if os.path.isdir(rootdir + os.sep + f):
                self.delete_path(rootdir + os.sep + f)
            else:
                print self.colortext('Removing file {}'.format(f), self.terminal.C_RED)
                try:
                    os.remove(rootdir + os.sep + f)
                except OSError:
                    print 'opa'
                    continue

    def createRepository(self):
        self.repository = Repository(self.appdir)
        self.repository.populate()

    def updatePaths(self):
        self.installdir = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

        self.appdir = self.getHomePath('.creep')
        if not os.path.isdir(self.appdir):
            os.mkdir(self.appdir)

        if not os.path.isdir(self.appdir + os.sep + 'cache'):
            os.mkdir(self.appdir + os.sep + 'cache')

        if sys.platform[:3] == 'win':
            self.minecraftdir = self.getHomePath('AppData\\Roaming\\.minecraft')
        elif sys.platform == 'darwin':
            self.minecraftdir = self.getHomePath('Library/Application Support/minecraft')
        elif sys.platform == 'cygwin':
            self.minecraftdir = os.getenv('APPDATA') + os.sep + '.minecraft'
        else:
            self.minecraftdir = self.getHomePath('.minecraft')

        if not os.path.isdir(self.minecraftdir):
            print "Minecraft dir not found ({})".format(self.minecraftdir)
            print "Is Minecraft installed?"
            sys.exit(2)

        if not os.path.isdir(self.minecraftdir + os.sep + 'mods'):
            os.mkdir(self.minecraftdir + os.sep + 'mods')

    def getHomePath(self, path=''):
        """Get the home path for this user from the OS"""
        home = os.getenv('HOME')
        if home == None:
            home = os.getenv('USERPROFILE')

        return home + os.sep + path

    def updateVersionWithGitDescribe(self):
        """Update the version of this client to reflect any local changes in git"""

        appdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

        try:
            self.VERSION = subprocess.check_output(['git', '-C', appdir, 'describe'], stderr=subprocess.STDOUT).strip()
        except OSError:
            pass
        except subprocess.CalledProcessError:
            # Oh well, we tried, just use the VERSION as it was
            pass

    def colortext(self, text, forecolor=None, backcolor=None, isbold=None):

        if forecolor is None and backcolor is None and isbold is None:
            return text

        if isbold:
            boldstart = self.terminal.bold()
            boldend = self.terminal.sgr0()
        else:
            boldstart = ''
            boldend = ''

        return '{bold}{start}{text}{end}{unbold}'.format(
            bold=boldstart,
            start=self.colorstart(forecolor, backcolor),
            text=text,
            end=self.colorend(),
            unbold=boldend
        )

    def colorstart(self, forecolor=None, backcolor=None):
        coloring = ''
        if forecolor is not None:
            coloring += self.terminal.setaf(forecolor)
        if backcolor is not None:
            coloring += self.terminal.setab(backcolor)

        return coloring

    def colorend(self):
        return self.terminal.op()
