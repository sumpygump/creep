"""CLI client for creep"""

import cmd # Command interpreter logic. Gives us the base class for the client
import distutils.dir_util # Directory utilities
import inspect # Functions to inspect live objects
import json # JSON encoder and decoder
import os # Miscellaneous operating system interfaces
import shlex # Lexical analysis of user input.
import shutil # High-level file operations
import subprocess # Spawn subprocesses, connect in/out pipes, obtain return codes
import sys # System specific parameters and functions
import tempfile # Temporary file utilities
import zipfile # Zip file utilities

from lib import argparse
from qi.console.client import Client
from operator import attrgetter
from repository import Repository

DEFAULT_TARGET = "1.16.1"

class CreepClient(Client, cmd.Cmd):
    """Creep Mod Package Manager Client"""

    # Version of this client
    VERSION = '0.1.3'

    # Absolute path where this client is installed
    installdir = ''

    # Absolute path to the dotfile for this client
    appdir = ''

    # Absolute path to the minecraft dir
    minecraftdir = ''

    # Version of minecraft to target for mods
    minecraft_target = ''

    # Directory for minecraft profile
    profiledir = ''

    # Whether should install dependencies too
    install_dependencies = True

    def __init__(self, **kwargs):
        """Constructor"""
        cmd.Cmd.__init__(self)
        Client.__init__(self, **kwargs)

        self.updateVersionWithGitDescribe()
        self.update_paths()
        self.load_options()

        self.createRepository()

    def do_version(self, args):
        """Display creep version"""
        print self.colortext("Creep v{}".format(self.VERSION), self.terminal.C_GREEN)
        self.display_target()
        self.display_profile()

    def do_target(self, args):
        """Set the targeted minecraft version
Usage: creep target <minecraft_version>

Examples:
  creep target 1.7.10
     Set the version of minecraft for mods
"""
        if len(args) > 0:
            # TODO: Validate against ~/.minecraft/launcher_profiles.json for valid versions to use
            self.minecraft_target = args

        self.display_target()
        self.repository.set_minecraft_target(self.minecraft_target)
        self.save_options()

    def display_target(self):
        print self.colortext("Targetting minecraft version {}".format(self.minecraft_target), self.terminal.C_GREEN)

    def load_options(self):
        # TODO: More robust user options file handling. It should be its own object to load options
        options_path = self.appdir + os.sep + 'options.json'
        if os.path.isfile(options_path):
            options = json.load(open(options_path))
            self.minecraft_target = options.get('minecraft_target', DEFAULT_TARGET)
            self.profiledir = options.get('profile_dir', self.minecraftdir)
        else:
            self.minecraft_target = DEFAULT_TARGET
            self.profiledir = self.minecraftdir

    def save_options(self):
        options_path = self.appdir + os.sep + 'options.json'
        with open(options_path, 'w') as outfile:
            json.dump({'minecraft_target': self.minecraft_target, 'profile_dir': self.profiledir}, outfile)

    def do_profile(self, args):
        """Set the path to the profile where you want to manage mods
Usage: creep profile <path/to/minecraft/profile>

Examples:
  creep profile ~/.minecraft
    Set the minecraft profile path
"""
        if len(args) > 0:
            new_profile_dir = args.rstrip('/')

            if new_profile_dir == '' or not os.path.isdir(new_profile_dir):
                print self.colortext(
                    "Invalid directory '{}'".format(new_profile_dir),
                    self.terminal.C_RED
                )
            else:
                self.profiledir = new_profile_dir

        self.display_profile()
        self.save_options()

    def display_profile(self):
        print self.colortext("Profile path '{}'".format(self.profiledir), self.terminal.C_GREEN)

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
            installdir = self.profiledir + os.sep + 'mods'
            files = []
            try:
                files = os.listdir(installdir)
            except OSError:
                pass

            if not files:
                print self.colortext("Looking in {}".format(installdir), self.terminal.C_YELLOW)
                print "No mods installed"
                return False

            packages = []
            unknownfiles = []
            for name in files:
                package = self.repository.fetch_package_byfilename(name)
                if not package:
                    unknownfiles.append(name)
                else:
                    packages.append(package)

            packages.sort(key=attrgetter('name'))

            print self.colortext("Installed mods (in {}):".format(installdir), self.terminal.C_YELLOW)
            for package in packages:
                self.print_package(package)
            for name in unknownfiles:
                print self.colortext(name, self.terminal.C_RED)
        else:
            self.display_packages()

    def display_packages(self):
        """Display list of packages available"""
        for package in self.repository.unique_packages:
            self.print_package(package)

    def print_package(self, package):
        message = u'{name}:{version} - {description} [{mcversion}]'.format(
            name=package.name,
            version=self.colortext(package.version, self.terminal.C_YELLOW),
            description=self.colortext(package.description, self.terminal.C_MAGENTA),
            mcversion=self.colortext(package.get_minecraft_version(), self.terminal.C_YELLOW)
        )

        if package.type == 'collection':
            message = message + self.colortext(' [collection]', self.terminal.C_CYAN)

        print message

    def print_package_details(self, package):
        print package.name
        print '--------'
        print "Version: " + package.version
        print "Description: " + package.description
        print "Package Type: " + package.type
        print "Keywords: " + package.keywords
        print "Homepage: " + package.homepage
        print "Dependencies: "
        for key,value in package.require.iteritems():
            print " - " + key + ": " + value

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

    def do_info(self, args):
        """Display details for a specific package (mod)
Usage: creep info <packagename>

Example: creep info slimeknights/tinkers-construct
"""
        if len(args) == 0:
            print self.colortext("Missing argument", self.terminal.C_RED)
            return 1

        package = self.repository.fetch_package(args)
        if not package:
            print self.colortext("Unknown package '{}'".format(args), self.terminal.C_RED)
            return 1

        self.print_package_details(package)

    def do_install(self, args):
        """Install a package (mod). This will install a given mod and its dependencies too

Usage: creep install [options] (<packagename>|-l <filename>)
  -n, --no-dependencies        Do not install dependencies automatically
  -l, --listfile <filename>    Install packages from file; one package per line

<packagename> can be the name of the package in one of the following formats:
  * package
  * vendor/package
  * package:version
  * vendor/package:version

Creep only considers packages that are in the current targeted minecraft version.
  See `creep help target` for details.

Examples: creep install just-enough-items
          creep install mezz/just-enough-items
          creep install just-enough-items:1.12.2-4.9.2.196
          creep install mezz/just-enough-items:1.12.2-4.9.2.196
          creep install -l mymodlist.txt
"""
        args = shlex.split(args)

        if len(args) == 0:
            print self.colortext("Missing argument", self.terminal.C_RED)
            return 1

        parser = argparse.ArgumentParser(add_help=False, prog='creep install')
        parser.add_argument('packages', nargs='*')
        parser.add_argument('-n', '--no-dependencies', action='store_true')
        parser.add_argument('-l', '--listfile', help='Install packages from file')

        (pargs, remaining_args) = parser.parse_known_args(args)

        if pargs.no_dependencies:
            print self.colortext("Performing install and skipping dependencies\n", self.terminal.C_YELLOW)
            self.install_dependencies = False

        if pargs.packages:
            # Handle install individual package
            for packagename in pargs.packages:
                self.install_package(packagename)

        if pargs.listfile:
            # Handle install from listfile
            self.install_from_listfile(pargs.listfile)

    def install_package(self, packagename):
        package = self.repository.fetch_package(packagename)
        if not package:
            print self.colortext("Unknown package '{}'".format(packagename), self.terminal.C_RED)
            return 1

        print self.colortext("Installing package {}".format(package), self.terminal.C_BLUE)

        # Install any required packages
        # Warning: does not handle versions or circular dependencies
        for dependency in package.require:
            if dependency == 'minecraft' or dependency == 'forge':
                continue
            if self.install_dependencies:
                print self.colortext("Installing dependency '{}'".format(dependency), self.terminal.C_CYAN)
                self.install_package(dependency)
            else:
                print self.colortext("Skipping dependency '{}'".format(dependency), self.terminal.C_YELLOW)

        if package.type == 'collection':
            # Collection only has dependencies
            print self.colortext("  Installed collection '{0}'".format(package.name), self.terminal.C_GREEN)
        else:
            cachedir = self.appdir + os.sep + 'cache' + os.sep + package.installdir

            if not os.path.isdir(cachedir):
                os.mkdir(cachedir)

            if not os.path.isfile(cachedir + os.sep + package.get_local_filename()):
                print self.colortext("  Downloading mod '{0}' from {1}".format(package.name, package.get_download_location()), self.terminal.C_YELLOW)
                downloadResult = package.download(cachedir)

                if not downloadResult:
                    print "Download failed."
                    return False

            # Most of the time this is the '~/.minecraft/mods' dir, but some mods have an alternate location for artifacts
            savedir = self.profiledir + os.sep + package.installdir

            if not os.path.isdir(savedir):
                print self.colortext("Creating directory '{0}'".format(savedir))
                os.mkdir(savedir)

            if package.installstrategy:
                self.install_with_strategy(package.installstrategy, package, cachedir, savedir)

            shutil.copyfile(cachedir + os.sep + package.get_local_filename(), savedir + os.sep + package.get_local_filename())

            print self.colortext("  Installed mod '{0}' in '{1}'".format(package.name, savedir + os.sep + package.get_local_filename()), self.terminal.C_GREEN)

    def install_from_listfile(self, listfile):
        print "Reading packages from file '{}'...".format(listfile)

        if not os.path.isfile(listfile):
            print self.colortext("File '{}' not found".format(listfile), self.terminal.C_RED)
            return 1

        # Read file and attempt to parse each line as a package name
        with open(listfile) as fp:
            for line in fp:
                args = line.split()
                self.install_package(args[0])

    def install_with_strategy(self, installstrategy, package, cachedir, savedir):
        print "Installing with strategy: " + installstrategy

        if ';' in installstrategy:
            strategies = installstrategy.split(';')
        else:
            strategies = [installstrategy]

        # set up a temppath where we will work
        tmppath = tempfile.gettempdir() + os.sep + package.name.replace('/', '_')
        if os.path.exists(tmppath):
            shutil.rmtree(tmppath)
        os.mkdir(tmppath)

        for strategy in strategies:
            args = shlex.split(strategy)
            if args[0] == 'unzip':
                print 'Unzipping archive: ' + cachedir + os.sep + package.get_local_filename()
                self.unzip(cachedir + os.sep + package.get_local_filename(), tmppath)
            elif args[0] == 'move':
                print 'Moving files: ' + args[1]
                path = args[1]
                if path[-2:] == '/*':
                    path = path.replace('/*', '')
                    distutils.dir_util.copy_tree(tmppath + os.sep + path, savedir)
                else:
                    shutil.copytree(tmppath + os.sep + path, savedir)

    def do_uninstall(self, args):
        """Uninstall a package (mod)
Usage: creep uninstall <packagename>

Example: creep uninstall thecricket/chisel2
"""
        package = self.repository.fetch_package(args)
        if not package:
            print 'Unknown package {}'.format(args)
            return 1

        savedir = self.profiledir + os.sep + package.installdir

        os.remove(savedir + os.sep + package.get_local_filename())
        print "Removed mod '{0}' from '{1}'".format(package.name, savedir)

    def do_purge(self, args):
        """Purge all installed packages (mods)
Usage: creep purge
"""
        installdir = self.minecraftdir + os.sep + 'mods'
        print "Purging all installed mods in {}...".format(installdir)
        self.delete_path(installdir)
        print "Done."

    def do_refresh(self, args):
        """Force an refresh of the package repository"""

        self.repository.clear_cache()
        self.repository.populate()
        print self.colortext("Repository updated to version {} ({}).".format(self.repository.version_hash, self.repository.version_date), self.terminal.C_GREEN)
        print "Count: {} packages.".format(self.repository.count_packages())

    def delete_path(self, rootdir):
        files = os.listdir(rootdir)
        for f in files:
            if os.path.isdir(rootdir + os.sep + f):
                self.delete_path(rootdir + os.sep + f)
                os.rmdir(rootdir + os.sep + f)
            else:
                print self.colortext('Removing file {}'.format(f), self.terminal.C_RED)
                try:
                    os.remove(rootdir + os.sep + f)
                except OSError:
                    print 'opa'
                    continue

    def createRepository(self):
        self.repository = Repository(self.appdir)
        self.repository.set_minecraft_target(self.minecraft_target)

        # Check if local packages repository exists and load it too
        if os.path.isfile(self.appdir + os.sep + 'local-packages.json'):
            self.repository.populate('', False)
            self.repository.populate(self.appdir + os.sep + 'local-packages.json')
        else:
            self.repository.populate('', True)

    def update_paths(self):
        #self.installdir = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))

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

        return u'{bold}{start}{text}{end}{unbold}'.format(
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

    def unzip(self, source_filename, dest_dir):
        with zipfile.ZipFile(source_filename) as zf:
            zf.extractall(dest_dir)
