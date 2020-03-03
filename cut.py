import numpy as np
import sys
from PIL import Image
from layer import Layer
from os import path

def cropbox(im, threshold):
    a = np.array(im)
    a = a.T
    f = np.nonzero(np.mean(a,axis=0)<threshold)
    return [min(f[0]), min(f[1]), max(f[0])+1, max(f[1])+1]

def autocrop(im, threshold):
    return im.crop(cropbox(im, threshold))

class AutoCrop(Layer):
    ___ = Layer.Register('auto-crop', lambda d: AutoCrop(d) )
    def __init__(self, d={}, name='image', verbose=False):
        self.name = name
        Layer.__init__(self, d, verbose)
        self.i = Layer.arg(d)
        self.threshold = d.setdefault('threshold', 200)
        self.imgs = {}
        self.mod = None

    def clone(self, d):
        obj = Layer.clone(self, d)
        obj.imgs = self.imgs
        return obj

    def down(self, im, threshold):
        a = np.array(im)
        a = a.T
        f = np.all(np.mean(a,axis=0)>=threshold, axis=0)
        y = min(np.nonzero(f))
        if len(y):
            y = min(y)
            return [self.cut(im.crop((0, 0, im.size[0], y)), threshold),
                    self.cut(im.crop((0, y, im.size[0], im.size[1])), threshold)]

    def across(self, im, threshold):
        a = np.array(im)
        a = a.T
        f = np.all(np.mean(a,axis=0)>=threshold, axis=1)
        x = min(np.nonzero(f))
        if len(x):
            x = min(x)
            return [self.cut(im.crop((0, 0, x, im.size[1])), threshold),
                    self.cut(im.crop((x, 0, im.size[0], im.size[1])), threshold)]
    @property
    def count(self):
        return len(self.imgs)

    def cut(self, im, threshold):
        im = autocrop(im, threshold)
        if not self.down(im, threshold) and not self.across(im, threshold):
            name = path.splitext(self.name)[0] + str(self.count).zfill(3)
            self.imgs[name]=im
        return self.imgs

    def apply(self, image):
        if self.mod:
            self.mod.verbose = self.verbose
            return self.mod.apply(image)
        if len(self.imgs)==0:
            self.cut(image, self.threshold)
            if self.verbose:
                print '  Cropped:', len(self.imgs), 'images'
        if self.verbose:
            print ' Indexing:', self.i, '/', len(self.imgs)
        try:
            return self.imgs[self.i]
        except KeyError as e:
            print e
            return self.errorImage(e)

class Crop(Layer):
    GetOrigin = {
        'CENTER': lambda s,b: [(x-y)/2 for x,y in zip(s, b[2:])],
        'NW': lambda s,b: [0,0],
        'NE': lambda s,b: [s[0]-b[2], 0],
        'SW': lambda s,b: [0, s[1]],
        'SE': lambda s,b: [(x-y) for x, y in zip(s, b[2:])],
    }
    ___ = Layer.Register('crop', lambda d: Crop(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.origin = Layer.arg(d)
    def apply(self, image):
        box = self.box.convert(image.size).box
        orig = Crop.GetOrigin[self.origin](image.size, box)
        box = [x+o for x,o in zip(box, orig+orig)]
        if self.verbose:
            print '  Cropbox:', self.box, box, 'alignment=' + self.origin
        return image.crop(box)

if __name__ == '__main__':
    if (len(sys.argv) != 2):
        print("\nUsage: python {} input_file\n".format(sys.argv[0]))
        sys.exit(1)
    imageFile = sys.argv[1]

    im = Image.open(imageFile)
    if im.mode[:3] != 'RGB':
        im = im.convert('RGB')
    elif im.mode == 'RGBA':
        im2 = Image.new('RGB', im.size, (255, 255, 255))
        im2.paste(im, (0,0), im)
        im = im2

    imgs = AutoCrop(name=imageFile).cut(im, 150)
    for k in imgs:
        print k
        imgs[k].show()
