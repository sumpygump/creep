"""Package entity"""

import creepclient
import os

from creepclient.entity import Entity

class Package(Entity):

    def __init__(self, data = {}, **kwargs):
        self.name = ''
        self.version = ''
        self.description = ''
        self.keywords = ''
        self.require = {}
        self.filename = ''
        self.url = ''
        self.author = ''
        self.homepage = ''
        self.type = 'mod'
        self.installdir = 'mods'

        super(Package, self).__init__(data, **kwargs)

    def download(self, savelocation):
        """Download this package from the specified URL in the package"""
        import urllib2

        url = self.get_download_location()

        response = urllib2.urlopen(url)
        data = response.read()

        f = open(savelocation + os.sep + self.filename, 'w')
        f.write(data)
        f.close()

    def get_download_location(self):
        """Get the download location for this package"""
        if self.url:
            return self.url

        # Backup location in case no url is provided for direct download
        url = 'http://quantalideas.com/creep/packages/' + self.filename

        return url

    def __str__(self):
        """Convert this object to a string"""
        return "{0} ({1}) - {2}".format(
            self.name,
            self.version,
            self.description
        )
