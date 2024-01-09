"""CLI client for creep"""

import argparse
import cmd
import inspect
import json
import os
import shlex
import shutil
import subprocess
import sys
from sys import platform as sys_platform
import tempfile
import textwrap
import zipfile

from qi.console.client import Client
from operator import attrgetter
from .repository import Repository
from .config import DEFAULT_TARGET


class CreepClient(Client, cmd.Cmd):
    """Creep Mod Package Manager Client"""

    # Version of this client
    version = "1.1"

    # Absolute path to the dotfile for this client
    appdir = ""

    # Absolute path to the minecraft dir
    minecraftdir = ""

    # Directory for minecraft profile
    profiledir = ""

    # Version of minecraft to target for mods
    minecraft_target = ""

    # Whether should install dependencies too
    install_dependencies = True

    def __init__(self, appdir=None, **kwargs):
        """Constructor"""

        cmd.Cmd.__init__(self)
        Client.__init__(self, **kwargs)

        self.update_version_with_git_describe()
        self.update_paths(appdir=appdir)
        self.load_options()

        self.create_repository()

    def __getattr__(self, name):
        """Special method called when attempting to check for an attr of this class"""

        if name.startswith("help_"):
            # Special logic to dedent the auto 'help text' provided in the do_*
            # methods' docstrings, which have indentation since it is
            # normalized in the source code, but I don't want the indentation
            # in the help output.
            command = name.replace("help_", "")
            doc = getattr(self, "do_" + command).__doc__
            if doc:
                # Return a lambda because cmd's do_help will call this return
                # value as a function.  I put the 8 spaces in front of the
                # docstring so dedent knows that is the indentation level I
                # want to dedent from.
                return lambda: print(
                    textwrap.dedent("{}{}".format(" " * 8, doc.rstrip()))
                )

        # Sorry this attribute doesn't exist
        raise AttributeError()

    def do_version(self, args):  # pylint: disable=unused-argument
        """Display creep version"""
        print(self.text_success(f"Creep v{self.version}"))
        self.display_target()
        self.display_profile()
        return 0

    def load_options(self):
        """Load user creep config options from disk"""

        options_path = os.path.join(self.appdir, "options.json")
        if os.path.isfile(options_path):
            with open(options_path, "r", encoding="utf-8") as fd:
                options = json.load(fd)
        else:
            options = {}

        self.minecraft_target = options.get("minecraft_target", DEFAULT_TARGET)
        self.profiledir = options.get("profile_dir", self.minecraftdir)

    def save_options(self):
        """Save user creep config options to disk"""
        options_path = os.path.join(self.appdir, "options.json")
        with open(options_path, "w", encoding="utf-8") as outfile:
            json.dump(
                {
                    "minecraft_target": self.minecraft_target,
                    "profile_dir": self.profiledir,
                },
                outfile,
                indent=4,
            )

    def do_target(self, args):
        """View or set the targeted minecraft version
        Usage: creep target [minecraft_version]

        Examples:
          creep target
             Show the current target minecraft version

          creep target 1.16.5
             Set the target minecraft version for mods"""

        if len(args) > 0:
            # TODO: Validate against ~/.minecraft/launcher_profiles.json for
            # valid versions to use
            self.minecraft_target = args
            self.repository.set_minecraft_target(self.minecraft_target)
            self.save_options()

        self.display_target()
        return 0

    def display_target(self):
        print(
            self.text_success(f"Targetting minecraft version {self.minecraft_target}")
        )

    def do_profile(self, args):
        """View or set the path to the profile where creep is managing mods
        Usage: creep profile [path/to/minecraft/profile]

        Examples:
          creep profile
            View the current profile path

          creep profile ~/.minecraft
            Set the minecraft profile path"""
        if len(args) > 0:
            new_profile_dir = args.rstrip("/")

            if new_profile_dir == "" or not os.path.isdir(new_profile_dir):
                print(self.text_error(f"Invalid directory '{new_profile_dir}'"))
            else:
                self.profiledir = new_profile_dir
                self.save_options()

        self.display_profile()
        return 0

    def display_profile(self):
        print(self.text_success(f"Profile path '{self.profiledir}'"))

    def do_list(self, args):
        """List packages (mods)
        Usage: creep list [installed]
          -s, --short   Short list (don't display descriptions)

        Examples:
          creep list
             List available packages in repository

          creep list installed
             List installed packages"""
        args = shlex.split(args)

        parser = argparse.ArgumentParser(add_help=False, prog="creep list")
        parser.add_argument("installed", nargs="?")
        parser.add_argument("-s", "--short", action="store_true")
        pargs, _ = parser.parse_known_args(args)

        if pargs.installed == "installed":
            installdir = os.path.join(self.profiledir, "mods")
            self.get_packages_in_dir(
                installdir, display_list=True, short_form=pargs.short
            )
        else:
            self.display_packages(short_form=pargs.short)

        return 0

    def get_packages_in_dir(
        self, dir_name, display_list=False, include_unknowns=True, short_form=False
    ):
        """Get the packages in a given directory"""

        ignore = [".DS_Store"]
        files = []
        try:
            files = os.listdir(dir_name)
        except OSError:
            pass

        library = {}
        packages = []
        unknownfiles = []

        if not files:
            if display_list:
                print(self.text_notify(f"Looking in {dir_name}"))
                print("No mods installed")
            return library

        for name in files:
            if name in ignore:
                continue
            package = self.repository.fetch_package_byfilename(name)
            if not package:
                library[name] = None
                unknownfiles.append(name)
            else:
                library[name] = package
                packages.append(package)

        packages.sort(key=attrgetter("name"))

        if display_list:
            if not short_form:
                print(self.text_notify(f"Installed mods (in {dir_name}):"))
            for package in packages:
                self.print_package(package, short_form=short_form)
            if include_unknowns:
                for name in unknownfiles:
                    print(self.text_error(name))

        return library

    def display_packages(self, short_form=False):
        """Display list of packages available"""
        for package in self.repository.unique_packages:
            self.print_package(package, short_form=short_form)

    def print_package(self, package, short_form=False):
        """Print information about single package"""

        if short_form:
            message = "{name}:{version}".format(
                name=package.name,
                version=self.text_notify(package.version),
            )
        else:
            message = "{name}:{version} - {description} [{mcversion}]".format(
                name=package.name,
                version=self.text_notify(package.version),
                description=self.text_info_desc(package.description),
                mcversion=self.text_notify(package.get_minecraft_version()),
            )

        if package.type == "collection":
            message = "{} {}".format(message, self.text_info_alt("[collection]"))

        try:
            print(message)
        except (BrokenPipeError, IOError):
            # Handles quitting before finishing the listing
            # E.g. `creep list | head`
            sys.stderr.close()

    def print_package_details(self, package):
        print(package.name)
        print("--------")
        print("Version: " + package.version)
        print("Description: " + package.description)
        print("Package Type: " + package.type)
        print("Keywords: " + package.keywords)
        print("Homepage: " + package.homepage)
        print("Local filename: " + package.get_local_filename())
        print("Dependencies: ")
        for key, value in package.require.items():
            print(" - " + key + ": " + value)

    def do_search(self, args):
        """Search for a package (mod) in the package registry

        Usage: creep search <packagename>

        Examples: creep search jade
                  creep search optifine
                  creep search tools
                  creep search blake"""

        if len(args) == 0:
            print(self.text_error("Missing argument"))
            return 1

        packages = self.repository.search(args)
        for package in packages:
            self.print_package(package)

        return 0

    def do_info(self, args):
        """Display details for a specific package (mod)
        Usage: creep info <packagename>

        Example: creep info slimeknights/tinkers-construct"""
        if len(args) == 0:
            print(self.text_error("Missing argument"))
            return 1

        package = self.repository.fetch_package(args)
        if not package:
            print(self.text_error(f"Unknown package '{args}'"))
            return 1

        self.print_package_details(package)

        return 0

    def do_install(self, args):
        """Install a package (mod). This will install a given mod and its dependencies

        Usage: creep install [options] (<packagename>|-l <filename>)
          -n, --no-dependencies        Do not install dependencies automatically
          -l, --listfile <filename>    Install packages from file; one package per line

        <packagename> can be the name of the package in one of the following formats:
          * package
          * vendor/package
          * package:version
          * vendor/package:version

        Creep only considers packages in the current targeted minecraft version.
          See `creep help target` for details.

        Examples: creep install just-enough-items
                  creep install mezz/just-enough-items
                  creep install just-enough-items:1.12.2-4.9.2.196
                  creep install mezz/just-enough-items:1.12.2-4.9.2.196
                  creep install -l mymodlist.txt"""

        args = shlex.split(args)

        if len(args) == 0:
            print(self.text_error("Missing argument"))
            return 1

        parser = argparse.ArgumentParser(add_help=False, prog="creep install")
        parser.add_argument("packages", nargs="*")
        parser.add_argument("-n", "--no-dependencies", action="store_true")
        parser.add_argument("-l", "--listfile", help="Install packages from file")

        (pargs, _) = parser.parse_known_args(args)

        if pargs.no_dependencies:
            print(self.text_notify("Performing install and skipping dependencies\n"))
            self.install_dependencies = False

        if pargs.packages:
            # Handle install individual package
            for packagename in pargs.packages:
                self.install_package(packagename)

        if pargs.listfile:
            # Handle install from listfile
            self.install_from_listfile(pargs.listfile)

        return 0

    def install_package(self, packagename):
        """Install a package by name"""

        package = self.repository.fetch_package(packagename)
        if not package:
            print(self.text_error(f"Unknown package '{packagename}'"))
            return False

        # Detect if a collection type and no deps mode
        if package.type == "collection" and not self.install_dependencies:
            print(
                self.text_error(
                    "Cannot install collection without dependencies. "
                    "Try again without flag -n / --no-dependencies."
                )
            )
            return False

        print(self.text_info(f"Installing package '{package}'"))

        # Install any required packages
        # Warning: does not handle versions or circular dependencies
        for dependency in package.require:
            if dependency in ("minecraft", "forge"):
                continue
            if self.install_dependencies:
                print(self.text_info_alt(f"Installing dependency '{dependency}'"))
                self.install_package(dependency)
            else:
                print(self.text_notify(f"Skipping dependency '{dependency}'"))

        if package.type == "collection":
            # Collection only has dependencies
            print(self.text_success(f"Installed collection '{package.name}'"))
        else:
            cachedir = os.path.join(self.appdir, "cache", package.installdir)

            if not os.path.isdir(cachedir):
                os.mkdir(cachedir)

            if not os.path.isfile(os.path.join(cachedir, package.get_local_filename())):
                print(
                    self.text_notify(
                        "  Downloading mod '{0}' from {1}".format(
                            package.name, package.get_download_location()
                        ),
                    )
                )
                download_result = package.download(cachedir)

                if not download_result:
                    print(self.text_error("Download failed."))
                    return False

            # Most of the time this is the '~/.minecraft/mods' dir, but some
            # mods have an alternate location for artifacts
            savedir = os.path.join(self.profiledir, package.installdir)

            if not os.path.isdir(savedir):
                print(self.text_notify(f"Creating directory '{savedir}'"))
                os.makedirs(savedir, exist_ok=True)

            if package.installstrategy:
                self.install_with_strategy(
                    package.installstrategy, package, cachedir, savedir
                )

            shutil.copyfile(
                os.path.join(cachedir, package.get_local_filename()),
                os.path.join(savedir, package.get_local_filename()),
            )

            print(
                self.text_success(
                    "  Installed mod '{}' in '{}'".format(
                        package.name,
                        os.path.join(savedir, package.get_local_filename()),
                    ),
                )
            )

    def install_from_listfile(self, listfile):
        print("Reading packages from file '{}'...".format(listfile))

        if not os.path.isfile(listfile):
            print(self.text_error(f"File '{listfile}' not found."))
            return 1

        # Read file and attempt to parse each line as a package name
        with open(listfile, encoding="utf-8") as fp:
            for line in fp:
                args = line.split()
                self.install_package(args[0])

    def install_with_strategy(self, installstrategy, package, cachedir, savedir):
        """Install a mod with a set of strategy directives

        Intended use case for this is a mod that is a zip file of mods and the
        jar files are in a subdirectory in the zip archive.

        Example strategy: `unzip; move 'mods/*'`
          This tells creep to unzip the archive and then move all the mods from
          the 'mods' directory into the target save location"""

        if not installstrategy:
            return None

        print("Installing with strategy: " + installstrategy)

        if ";" in installstrategy:
            strategies = installstrategy.split(";")
        else:
            strategies = [installstrategy]

        # Set up a temppath where we will work
        tmppath = os.path.join(tempfile.gettempdir(), package.name.replace("/", "_"))
        if os.path.exists(tmppath):
            shutil.rmtree(tmppath)
        os.mkdir(tmppath)

        for strategy in strategies:
            args = shlex.split(strategy)
            if args[0] == "unzip":
                # 'unzip' will unzip the given package's local filename into temp dir
                filename = os.path.join(cachedir, package.get_local_filename())
                print(f"Unzipping archive: {filename}")
                self.unzip(filename, tmppath)
            elif args[0] == "move":
                # 'move <arg>' will move files from the temp dir into the save dir
                path = args[1]
                print(f"Moving files: {path}")
                if path[-2:] == "/*":
                    path = path.replace("/*", "")
                shutil.copytree(
                    os.path.join(tmppath, path), savedir, dirs_exist_ok=True
                )

        # Clean up
        shutil.rmtree(tmppath)
        return True

    def do_uninstall(self, args):
        """Uninstall a package (mod)
        Usage: creep uninstall <packagename>

        Example: creep uninstall thecricket/chisel2"""

        if len(args) == 0:
            print(self.text_error("Missing argument"))
            return 1

        package = self.repository.fetch_package(args)
        if not package:
            print(self.text_error(f"Unknown package {args}"))
            return 1

        savedir = os.path.join(self.profiledir, package.installdir)

        os.remove(os.path.join(savedir, package.get_local_filename()))
        print("Removed mod '{0}' from '{1}'".format(package.name, savedir))

        return 0

    def do_stash(self, args):
        """Stash list of installed mods to a saved directory that can be restored later.

        Usage: creep stash <subcommand> <stash-name>
               creep stash list

        Subcommands:
         - save <stash-name> : Saves the currently installed mods into a stash
                with given name and empties the install directory.
         - info <stash-name> : Show the mod files present in a given stash.
         - restore <stash-name> : Installs the mods from the given stash into
                the install directory and removes the stash.
         - apply <stash-name> : Installs the mods from the given stash into the
                install directory but keep the stash in tact.
         - list : List the currently available stashes.

        Examples: creep stash save my-world
                  creep stash info my-world
                  creep stash restore my-world
                  creep stash apply my-world
                  creep stash list

        Use command `creep list installed` to see the list of currently installed mods
        """
        args = shlex.split(args)

        if len(args) == 0:
            print(self.text_error("Stash: Missing argument <subcommand>"))
            self.do_help("stash")
            return 1

        parser = argparse.ArgumentParser(add_help=False, prog="creep stash")
        parser.add_argument("subcommand")
        parser.add_argument("stash_name", nargs="?")

        (pargs, _) = parser.parse_known_args(args)

        if pargs.subcommand == "list":
            return self.list_stashes()

        if pargs.subcommand not in ["save", "restore", "info", "pop", "apply"]:
            print(self.text_error(f"Stash: Invalid subcommand {pargs.subcommand}"))
            return 1

        # The remaining subcommands require a stash name arg
        if not pargs.stash_name:
            print(self.text_error("Stash: Missing argument <stash_name>"))
            return 1

        if pargs.subcommand == "save":
            return self.save_stash(pargs.stash_name)

        if pargs.subcommand == "info":
            return self.stash_info(pargs.stash_name)

        if pargs.subcommand in ("restore", "pop"):
            return self.restore_stash(pargs.stash_name)

        if pargs.subcommand == "apply":
            return self.restore_stash(pargs.stash_name, copy_mode=True)

    def list_stashes(self):
        stashes = self.get_stashes()
        if not stashes:
            print(self.text_notify("Looking in {}".format(self.get_stashes_dir())))
            print("No stashes")
            return 2

        for dir_name in stashes:
            print(dir_name)

        return 0

    def get_stashes_dir(self):
        return os.path.join(self.profiledir, "stashes")

    def get_stashes(self):
        stashes = []
        try:
            stashes = os.listdir(self.get_stashes_dir())
        except OSError:
            pass

        return sorted(stashes)

    def save_stash(self, stash_name):
        stashes_dir = self.get_stashes_dir()
        if not os.path.isdir(stashes_dir):
            os.mkdir(stashes_dir)

        stash_dir = os.path.join(stashes_dir, stash_name)

        if os.path.exists(stash_dir):
            print(self.text_error(f"Stash with name {stash_name} already exists."))
            return 1
        else:
            os.mkdir(stash_dir)

        # Collect everything from the mods dir and put it in the stash dir
        installdir = os.path.join(self.profiledir, "mods")
        packages = self.get_packages_in_dir(installdir)

        print("Will stash the following files into stash {}:".format(stash_name))
        files = sorted(packages.keys())

        for file in files:
            print(file)
            from_ = os.path.join(installdir, file)
            to_ = os.path.join(stash_dir, file)
            shutil.move(from_, to_)

        return 0

    def stash_info(self, stash_name):
        stashes_dir = self.get_stashes_dir()
        stash_dir = os.path.join(stashes_dir, stash_name)

        if not os.path.isdir(stash_dir):
            print(self.text_error(f"No stash with name {stash_name}"))
            return 1

        self.get_packages_in_dir(stash_dir, display_list=True, include_unknowns=True)

        return 0

    def restore_stash(self, stash_name, copy_mode=False):
        stashes_dir = self.get_stashes_dir()
        stash_dir = os.path.join(stashes_dir, stash_name)

        if not os.path.isdir(stash_dir):
            print(self.text_error(f"No stash with name {stash_name}"))
            return 1

        # Collect everything from the stash dir and put it in the mods install dir
        installdir = os.path.join(self.profiledir, "mods")
        packages = self.get_packages_in_dir(stash_dir)

        files = sorted(packages.keys())

        verb = "Applying" if copy_mode else "Moving"
        print("{} files from stash {} to install dir.".format(verb, stash_dir))
        for file in files:
            print(file)
            from_ = os.path.join(stash_dir, file)
            to_ = os.path.join(installdir, file)
            if copy_mode:
                shutil.copy(from_, to_)
            else:
                shutil.move(from_, to_)

        if not copy_mode:
            # Delete the stash dir
            print("Deleting stash dir {}".format(stash_name))
            shutil.rmtree(stash_dir)

        return 0

    def do_purge(self, args):  # pylint: disable=unused-argument
        """Purge all installed packages (mods). Deletes all files from the mods
        directory.

        Usage: creep purge

        Use command `creep list installed` to see the list of currently installed mods
        """
        installdir = os.path.join(self.profiledir, "mods")
        print("Purging all installed mods in {}...".format(installdir))
        self.delete_path(installdir)
        print("Done.")

        return 0

    def do_refresh(self, args):  # pylint: disable=unused-argument
        """Force an refresh of the package repository"""

        self.repository.clear_cache()
        self.repository.populate()
        print(
            self.text_success(
                "Repository updated to version {} ({}).".format(
                    self.repository.version_hash, self.repository.version_date
                ),
            )
        )
        print("Count: {} packages.".format(self.repository.count_packages()))

        return 0

    def delete_path(self, rootdir):
        files = os.listdir(rootdir)
        for f in files:
            if os.path.isdir(os.path.join(rootdir, f)):
                self.delete_path(os.path.join(rootdir, f))
                os.rmdir(os.path.join(rootdir, f))
            else:
                print(self.text_error(f"Removing file {f}"))
                try:
                    os.remove(os.path.join(rootdir, f))
                except OSError:
                    print("opa")
                    continue

    def create_repository(self):
        self.repository = Repository(self.appdir)
        self.repository.set_minecraft_target(self.minecraft_target)

        # Check if local packages repository exists and load it too
        local_packages_filename = os.path.join(self.appdir, "local-packages.json")
        if os.path.isfile(local_packages_filename):
            self.repository.populate(should_post_process=False)
            self.repository.populate(local_packages_filename)
        else:
            self.repository.populate(should_post_process=True)

    def update_paths(self, appdir=None):
        """Set configured paths utilized by creep client"""

        # Creep app dir
        if appdir is None:
            self.appdir = self.get_home_path(".creep")
        else:
            self.appdir = appdir
        if not os.path.isdir(self.appdir):
            os.mkdir(self.appdir)

        if not os.path.isdir(os.path.join(self.appdir, "cache")):
            os.mkdir(os.path.join(self.appdir, "cache"))

        # Discover the minecraft dir
        if sys_platform[:3] == "win":
            self.minecraftdir = self.get_home_path(
                os.path.join("AppData", "Roaming", ".minecraft")
            )
        elif sys_platform == "darwin":
            self.minecraftdir = self.get_home_path(
                os.path.join("Library", "Application Support", "minecraft")
            )
        elif sys_platform == "cygwin":
            self.minecraftdir = os.path.join(os.getenv("APPDATA"), ".minecraft")
        else:
            self.minecraftdir = self.get_home_path(".minecraft")

        # Ensure minecraft dir is found
        if not os.path.isdir(self.minecraftdir):
            print("Minecraft dir not found ({})".format(self.minecraftdir))
            print("Is Minecraft installed?")
            sys.exit(2)

        # Ensure the mods dir is created
        if not os.path.isdir(os.path.join(self.minecraftdir, "mods")):
            os.mkdir(os.path.join(self.minecraftdir, "mods"))

    def get_home_path(self, path=""):
        """Get the home path for this user from the OS"""
        home = os.getenv("HOME")
        if home is None:
            home = os.getenv("USERPROFILE")

        return os.path.join(home, path)

    def update_version_with_git_describe(self):
        """Update the version of this client to reflect any local changes in git"""

        appdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))
        )

        try:
            self.version = (
                subprocess.check_output(
                    ["git", "-C", appdir, "describe"], stderr=subprocess.STDOUT
                )
                .strip()
                .decode("utf-8")
            )
        except OSError:
            pass
        except subprocess.CalledProcessError:
            # Oh well, we tried, just use the version as it was
            pass

    def unzip(self, source_filename, dest_dir):
        with zipfile.ZipFile(source_filename) as zf:
            zf.extractall(dest_dir)
