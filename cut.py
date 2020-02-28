import numpy as np
import sys
from PIL import Image
from layer import Layer
from os import path

L = 200

def cropbox(im):
    a = np.array(im)
    a = a.T
    f = np.nonzero(np.mean(a,axis=0)<L)
    return [min(f[0]), min(f[1]), max(f[0])+1, max(f[1])+1]

def autocrop(im):
    return im.crop(cropbox(im))

class AutoSplit(Layer):
    ___ = Layer.Register('auto-split', lambda d: AutoSplit(d) )
    def __init__(self, d={}, name='image'):
        self.name = name
        Layer.__init__(self, d)
        d.setdefault('auto-split', 0)
        self.i = d['auto-split']
        self.imgs = {}

    def down(self, im):
        a = np.array(im)
        a = a.T
        f = np.all(np.mean(a,axis=0)>=L, axis=0)
        y = min(np.nonzero(f))
        if len(y):
            y = min(y)
            return [self.cut(im.crop((0, 0, im.size[0], y))),
                    self.cut(im.crop((0, y, im.size[0], im.size[1])))]

    def across(self, im):
        a = np.array(im)
        a = a.T
        f = np.all(np.mean(a,axis=0)>=L, axis=1)
        x = min(np.nonzero(f))
        if len(x):
            x = min(x)
            return [self.cut(im.crop((0, 0, x, im.size[1]))),
                    self.cut(im.crop((x, 0, im.size[0], im.size[1])))]
    @property
    def count(self):
        return len(self.imgs)

    def cut(self, im):
        im = autocrop(im)
        if not self.down(im) and not self.across(im):
            name = path.splitext(self.name)[0] + str(self.count).zfill(3)
            self.imgs[name]=im
        return self.imgs

    def apply(self, image):
        self.cut(image)
        return self.imgs[self.i]


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

    imgs = AutoSplit(name=imageFile).cut(im)
    for k in imgs:
        print k
        imgs[k].show()

