"""Package entity"""

import creepclient
import os
import urllib.request
import urllib.error

from creepclient.entity import Entity


class Package(Entity):
    def __init__(self, data={}, **kwargs):
        self.name = ""
        self.version = ""
        self.description = ""
        self.keywords = ""
        self.require = {}
        self.filename = ""
        self.url = ""
        self.author = ""
        self.homepage = ""
        self.type = "mod"
        self.installdir = "mods"
        self.installstrategy = ""

        super(Package, self).__init__(data, **kwargs)

    def download(self, savelocation):
        """Download this package from the specified URL in the package"""

        url = self.get_download_location()

        # Using these specific headers to make the request seem like a browser.
        # The old curseforge is using cloudflare to prevent bots
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
        }
        request = urllib.request.Request(url, headers=headers)
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as e:
            print(
                "No internet connection or unable to download file. Attempted to download '"
                + self.get_download_location()
                + "'"
            )
            return False

        data = response.read()

        f = open(savelocation + os.sep + self.get_local_filename(), "wb")
        f.write(data)
        f.close()

        return True

    def get_download_location(self):
        """Get the download location for this package"""
        if self.url:
            return self.url

        # Backup location in case no url is provided for direct download
        url = "http://quantalideas.com/creep/packages/" + self.filename

        return url

    def get_local_filename(self):
        """Get the local canonical filename made up of entity attributes"""

        if self.installdir != "mods":
            # For non-regular mods use the orig filename
            return self.filename

        _, extension = os.path.splitext(self.filename)

        # Format is 'vendor_name_version.extension'
        return "{}_{}{}".format(
            self.name.replace("/", "_"), self.version.replace(" ", "-"), extension
        )

    def get_minecraft_version(self):
        """Get the minecraft version for this package"""
        return self.require["minecraft"]

    def get_simple_name(self):
        """Get the second name (without the vendor) for a package"""
        return self.name.split("/")[1]

    def __str__(self):
        """Convert this object to a string"""
        return "{0} ({1}) - {2}".format(self.name, self.version, self.description)
