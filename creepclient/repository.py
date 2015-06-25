"""Repository for packages"""

import json # JSON encoder and decoder
import os # Miscellaneous operating system interfaces
import re # Regular expressions

from operator import attrgetter
from entity.package import Package

class Repository(object):
    """Repository class"""

    remote_url = 'http://quantalideas.com/mcpackages/packages.json'
    version_hash = ''
    version_date = ''

    # Has every package, including every version of each
    packages = []

    # List of all packages, but only the latest version
    unique_packages = []

    def __init__(self, appdir):
        self.localdir = appdir + os.sep + 'packages.json'

    def download_remote_repository(self):
        import urllib2

        try:
            response = urllib2.urlopen(self.remote_url)
        except urllib2.URLError:
            return False

        data = response.read()

        f = open(self.localdir, 'w')
        f.write(data)
        f.close()
        return True

    def load_repository(self):
        # Repository file doesn't exist, fetch it from remote url
        if not os.path.isfile(self.localdir):
            if not self.download_remote_repository():
                print "Package definition file not found or no internet connection."
                return {'packages': {}}
            return json.load(open(self.localdir))
        
        # Check repository file date last modified
        # If it is older than an hour, redownload
        import calendar
        import time
        filetime = os.stat(self.localdir).st_mtime
        if filetime + 3600 < calendar.timegm(time.gmtime()):
            if not self.download_remote_repository():
                print "No internet connection. Using current version of repository. Date: {}".format(filetime)

        return json.load(open(self.localdir))

    def clear_cache(self):
        if os.path.isfile(self.localdir):
            os.remove(self.localdir)

    def populate(self, location=''):
        if not location:
            registry = self.load_repository()
        else:
            # Assuming location is a path to an alternate file
            registry = json.load(open(location))

        if 'repository_version' in registry:
            self.version_hash = registry['repository_version']
        if 'date' in registry:
            self.version_date = registry['date']

        for namekey in registry['packages']:
            for versionkey in registry['packages'][namekey]:
                data = registry['packages'][namekey][versionkey]
                package = Package()
                package.name = data['name']
                package.version = data['version']
                package.description = data['description']
                package.keywords = data['keywords']
                package.require = data['require']
                package.filename = data['filename'] if 'filename' in data else ''
                package.url = data['url'] if 'url' in data else ''
                package.author = data['author']
                package.homepage = data['homepage'] if 'homepage' in data else ''
                package.type = data['type']
                if 'installdir' in data:
                    package.installdir = data['installdir']
                if 'installstrategy' in data:
                    package.installstrategy = data['installstrategy']
                self.packages.append(package)

        self.packages.sort(key=attrgetter('name'))
        self.reduce_to_unique_packages()

    def reduce_to_unique_packages(self):
        """Make a listing of packages with only the latest version for each one"""
        package_dict = {};
        self.unique_packages = []

        # First make a dict of packages index by name
        for package in self.packages:
            if not package.name in package_dict:
                package_dict[package.name] = []
            package_dict[package.name].append(package)

        # Now go through dict and find the latest version of each
        for name in package_dict:
            packages = package_dict[name]
            if len(packages) == 1:
                self.unique_packages.append(packages[0])
            else:
                latest = packages[0]
                for package in packages:
                    if self.compare_versions(package.version, latest.version) > 0:
                        latest = package
                self.unique_packages.append(latest)

        self.unique_packages.sort(key=attrgetter('name'))

    def compare_versions(self, version1, version2):
        return cmp(self.normalize_version(version1), self.normalize_version(version2))

    def normalize_version(self, v):
        return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]

    def count_packages(self):
        return len(self.packages)

    def fetch_package(self, name):
        if name == '':
            return False

        # only select from the latest versions (unique_packages)
        # TODO allow to fetch a package for a specific version
        for package in self.unique_packages:
            if package.name == name:
                return package

        return False

    def fetch_package_byfilename(self, filename):
        for package in self.packages:
            if package.filename == filename or package.get_local_filename() == filename:
                return package

        return False

    def search(self, term):
        results = []
        for package in self.unique_packages:
            if term in package.name.split('/'):
                results.append(package)
                continue
            if term in package.description.split():
                results.append(package)
                continue
            if term in package.keywords:
                results.append(package)
                continue

        results.sort(key=attrgetter('name'))
        return results
