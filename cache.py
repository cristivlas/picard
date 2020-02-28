import os
import urlparse
import urllib
import zipfile
from PIL import Image, ImageFont

DataPath = ''

class CacheFile:
    Root = os.path.join(os.getcwd(), '.cache')
    def __init__(self, url):
        parsedUrl = urlparse.urlparse(url)
        start = 1 if os.path.isabs(parsedUrl.path) else 0
        path = str(os.path.sep).join(parsedUrl.path.split('/')[start:])
        if path.endswith(os.path.sep):
            path = self.resolvePath(parsedUrl)
        if len(parsedUrl.netloc):
            path = os.path.join(os.path.join(CacheImage.Root, parsedUrl.netloc), path)
        else:
            if not os.path.isabs(path):
                abspath = os.path.normpath(os.path.join(DataPath, path))
                url = os.path.splitdrive(abspath)[1]
            path = os.path.join(CacheImage.Root, path)
        try:
            os.makedirs(os.path.split(path)[0])
        except OSError as e:
            if not 'already exists' in str(e):
                raise e 
        if not os.path.exists(path):
            print 'Downloading', url, '...'
            urllib.urlretrieve(url, path)
        self.path = path

class CacheImage(CacheFile):
    Cache = {}
    def __init__(self, url):
        try:
            self.image = self.Cache[url]
        except KeyError:
            CacheFile.__init__(self, url)
            self.Cache[url] = self.image = Image.open(self.path)

class CacheFont(CacheFile):
    Cache = {}
    def __init__(self, url, size):
        try:
            self.font = self.Cache[(url, size)]
        except KeyError:
            CacheFile.__init__(self, url)
            print 'Loading font:', self.path
            if os.path.splitext(self.path)[1] in ['.zip' ]:
                zip = zipfile.ZipFile(self.path)
                fname = next((x for x in zip.namelist() if x.lower().endswith('.ttf')), None)
                self.path = zip.extract(fname, os.path.split(self.path)[0])
            self.font = ImageFont.truetype(self.path, size)
            self.Cache[(url, size)] = self.font

    def resolvePath(self, url):
        if url.query and url.netloc=='dl.dafont.com':
            return url.query.split('=')[1] + '.zip'
        return 'font.zip'
