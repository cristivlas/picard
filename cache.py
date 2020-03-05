import os
import re
import urlparse
import urllib
import zipfile
from PIL import Image, ImageFont

DataPath = ''

class CacheFile:
    Root = os.path.join(os.path.splitdrive(os.getcwd())[1], '.cache')
    def __init__(self, url):
        parsedUrl = urlparse.urlparse(url)
        start = 1 if os.path.isabs(parsedUrl.path) else 0
        path = str(os.path.sep).join(parsedUrl.path.split('/')[start:])
        if not os.path.splitext(path)[1]:
            path = self.resolvePath(parsedUrl, path)
        if len(parsedUrl.netloc):
            path = os.path.join(os.path.join(CacheImage.Root, parsedUrl.netloc), path)
        else:
            if not os.path.isabs(path):
                url = os.path.normpath(os.path.join(DataPath, path))
            path = os.path.join(CacheImage.Root, path)

        path = CacheFile.getValidPathName(path)
        try:
            os.makedirs(os.path.split(path)[0])
        except OSError as e:
            if not 'already exists' in str(e):
                raise e 
        if not os.path.exists(path):
            print 'Downloading', url, '...'
            urllib.urlretrieve(url, path)
        self.path = path

    @staticmethod
    def getValidPathName(s):
        s = str(s).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.\\]', '', s)

class CacheImage(CacheFile):
    Cache = {}
    def __init__(self, url):
        assert url
        try:
            self.image = self.Cache[url]
        except KeyError:
            CacheFile.__init__(self, url)
            self.load(url)

    def load(self, url):
        try:
            self.image = Image.open(self.path).convert('RGBA')
            self.Cache[url] = self.image
        except Exception as e:
            self.image = e
            print e

    def resolvePath(self, url, path):
        return os.path.join(path, 'image.jpg')

class CacheFont(CacheFile):
    Cache = {}
    def __init__(self, url, size, dpi=300):
        if not url or not size:
            self.font = ImageFont.load_default()
        else:
            size *= dpi/300
            try:
                self.font = self.Cache[(url, size)]
            except KeyError:
                CacheFile.__init__(self, url)
                print 'Loading font:', self.path
                if os.path.splitext(self.path)[1] in ['.zip' ]:
                    zip = zipfile.ZipFile(self.path)
                    match = lambda x: os.path.splitext(x.lower())[1] in ['.ttf', '.otf']
                    fname = next((x for x in zip.namelist() if match(x)), None)
                    self.path = zip.extract(fname, os.path.split(self.path)[0])
                self.font = ImageFont.truetype(self.path, size)
                self.Cache[(url, size)] = self.font

    def resolvePath(self, url, path):
        if url.query and url.netloc=='dl.dafont.com':
            return url.query.split('=')[1] + '.zip'
        return os.path.join(path, 'font.zip')
