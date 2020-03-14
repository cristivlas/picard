from __future__ import print_function
import os
import portable
import re
import sys
import urllib
import zipfile
from PIL import Image, ImageFont

DataPath = ''

def join(elems):
    return str('/').join(elems)

def normpath(path):
    return join(os.path.normpath(path).split(os.path.sep))

class CacheFile:
    CurrentWorkDir = normpath(os.path.splitdrive(os.getcwd())[1])
    Root = join((CurrentWorkDir, '.cache'))
    Verbose = sys.modules['__main__'].verbose

    def __init__(self, url):
        parsedUrl = portable.urlparse(url)
        start = 1 if os.path.isabs(parsedUrl.path) else 0
        path = join(parsedUrl.path.split('/')[start:])
        if not os.path.splitext(path)[1]:
            path = self.resolvePath(parsedUrl, path)
        if len(parsedUrl.netloc):
            path = join((CacheImage.Root, parsedUrl.netloc, path))
        else:
            if not os.path.isabs(path):
                url = join((DataPath, path))
            path = join((CacheImage.Root, path))

        path = CacheFile.getValidPathName(path)
        portable.makedirs(os.path.split(path)[0])

        if not os.path.exists(path):
            if not parsedUrl.scheme:
                if not os.path.isabs(url):
                    url = join([CacheFile.CurrentWorkDir, url])
                    if not os.path.exists(url):
                        url += '.zip'
                        path += '.zip'
                url = "file://" + url
            print ('Downloading', url, '...')
            portable.urlretrieve(url, path)
        self.path = path

    @staticmethod
    def getValidPathName(s):
        s = str(s).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.\\\/]', '', s)

    def resolvePath(self, url, path):
        assert False
        return path


class CacheImage(CacheFile):
    Cache = {}
    def __init__(self, url):
        assert url
        self.image = self.Cache.get(url)
        if not self.image:
            try:
                CacheFile.__init__(self, url)
                self.load(url)
            except Exception as e:
                if CacheFile.Verbose:                    
                    portable.rethrow(e, url)
                self.image = e
                print (e)

        assert self.image

    def load(self, url):
        try:
            self.image = Image.open(self.path).convert('RGBA')
            self.Cache[url] = self.image
        except Exception as e:
            self.image = e
            print (e)

    def resolvePath(self, url, path):
        return join((path, 'image.jpg'))

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
                if CacheFile.Verbose:
                    print ('Loading font:', self.path)
                if os.path.splitext(self.path)[1] in ['.zip' ]:
                    zip = zipfile.ZipFile(self.path)
                    match = lambda x: os.path.splitext(x.lower())[1] in ['.ttf', '.otf']
                    fname = next((x for x in zip.namelist() if match(x)), None)
                    self.path = zip.extract(fname, os.path.split(self.path)[0])
                self.font = ImageFont.truetype(self.path, int(size))
                self.Cache[(url, size)] = self.font

    def resolvePath(self, url, path):
        if url.query and url.netloc=='dl.dafont.com':
            return url.query.split('=')[1] + '.zip'
        return join((path, 'font.zip'))
