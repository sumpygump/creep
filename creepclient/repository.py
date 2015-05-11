"""Repository for packages"""

import json # JSON encoder and decoder
import os # Miscellaneous operating system interfaces

from operator import attrgetter
from entity.package import Package

class Repository(object):
    """Repository class"""

    remote_url = 'http://quantalideas.com/mcpackages/packages.json'
    version_hash = ''
    version_date = ''

    packages = []

    def __init__(self, appdir):
        self.localdir = appdir + os.sep + 'packages.json'

    def download_remote_repository(self):
        import urllib2

        response = urllib2.urlopen(self.remote_url)
        data = response.read()

        f = open(self.localdir, 'w')
        f.write(data)
        f.close()

    def load_repository(self):
        # Repository file doesn't exist, fetch it from remote url
        if not os.path.isfile(self.localdir):
            self.download_remote_repository()
            return json.load(open(self.localdir))
        
        # Check repository file date last modified
        # If it is older than an hour, redownload
        import calendar
        import time
        filetime = os.stat(self.localdir).st_mtime
        if filetime + 3600 < calendar.timegm(time.gmtime()):
            self.download_remote_repository()

        return json.load(open(self.localdir))

    def clear_cache(self):
        os.remove(self.localdir)

    def populate(self, location=''):
        if not location:
            registry = self.load_repository()
        else:
            # Assuming location is a path to an alternate file
            registry = json.load(open(location))

        self.version_hash = registry['repository_version']
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
                package.homepage = data['homepage']
                package.type = data['type']
                if 'installdir' in data:
                    package.installdir = data['installdir']
                self.packages.append(package)

        self.packages.sort(key=attrgetter('name'))

    def count_packages(self):
        return len(self.packages)

    def fetch_package(self, name):
        if name == '':
            return False

        for package in self.packages:
            if package.name == name:
                return package

        return False

    def fetch_package_byfilename(self, filename):
        for package in self.packages:
            if package.filename == filename:
                return package

        return False

    def search(self, term):
        results = []
        for package in self.packages:
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
