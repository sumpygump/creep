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
        self.installstrategy = ''

        super(Package, self).__init__(data, **kwargs)

    def download(self, savelocation):
        """Download this package from the specified URL in the package"""
        import urllib2

        url = self.get_download_location()

        request = urllib2.Request(url, headers={'User-Agent' : "Creep Browser 0.1"}) 
        try:
            response = urllib2.urlopen(request)
        except urllib2.URLError:
            print "No internet connection. Cannot download file '" + self.get_download_location() + "'"
            return False

        data = response.read()

        f = open(savelocation + os.sep + self.get_local_filename(), 'w')
        f.write(data)
        f.close()

        return True

    def get_download_location(self):
        """Get the download location for this package"""
        if self.url:
            return self.url

        # Backup location in case no url is provided for direct download
        url = 'http://quantalideas.com/creep/packages/' + self.filename

        return url

    def get_local_filename(self):
        """Get the local canonical filename made up of entity attributes"""
        if self.installdir != 'mods':
            # For non-regular mods use the orig filename
            return self.filename

        filename, extension = os.path.splitext(self.filename)

        # vendor_name_version.extension
        return self.name.replace('/', '_') + '_' + self.version.replace(' ', '-') + extension

    def get_simple_name(self):
        """Get the second name (without the vendor) for a package"""
        return self.name.split('/')[1]

    def __str__(self):
        """Convert this object to a string"""
        return "{0} ({1}) - {2}".format(
            self.name,
            self.version,
            self.description
        )
