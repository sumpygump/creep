
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
        self.installdir = 'mods'

        super(Package, self).__init__(data, **kwargs)

    def download(self, savelocation):
        import urllib2

        url = self.get_download_location()

        response = urllib2.urlopen(url)
        data = response.read()

        f = open(savelocation + os.sep + self.filename, 'w')
        f.write(data)
        f.close()

    def get_download_location(self):
        if self.url:
            return self.url

        url = 'http://quantalideas.com/creep/packages/' + self.filename

        return url

    def __str__(self):
        return "{0} ({1}) - {2}".format(
            self.name,
            self.version,
            self.description
        )
