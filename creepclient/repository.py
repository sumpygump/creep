"""Repository for packages"""

import json # JSON encoder and decoder
import os # Miscellaneous operating system interfaces

from entity.package import Package

class Repository(object):
    """Repository class"""

    packages = []

    def __init__(self, **kwargs):
        pass

    def readRegistry(self, location):
        registry = json.load(open(location + os.sep + 'registry.json'))

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

        from operator import attrgetter

        self.packages.sort(key=attrgetter('name'))

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
