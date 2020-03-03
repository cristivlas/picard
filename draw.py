from layer import Layer
from PIL import Image, ImageDraw
import numpy as np

def makeShape(shape, im):
    shape = shape[1],shape[0],shape[2]
    a = np.array(im)
    d = [i/2 - j for i, j in zip(shape, a.shape)]
    a = np.pad(a, ((0,d[0]),(0,d[1]),(0,0)), 'edge')
    a = np.pad(a, ((0,shape[0]-a.shape[0]),(0,0),(0,0)), 'symmetric')
    a = np.pad(a, ((0,0), (0, shape[1]-a.shape[1]),(0,0)), 'symmetric')
    return Image.fromarray(a)

class Rectangle(Layer):
    ___ = Layer.Register('rectangle', lambda x: Rectangle(x))
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        assert self.box
        self.outline = d['rectangle']
        self.radius = d.setdefault('corner-radius', 0)
        self.width = d.setdefault('line-width', 1)
        self.fillColor = d.setdefault('fill-color', None)

    def apply(self, image):
        box = self.box.convert(image.size)
        r = self.radius or min(box.size())/2
        size = [r,r]
        if self.radius:
            scale = 2 
            im = Image.new('RGBA', [scale * i for i in size])
            bbox = [0,0] + [(2*i+self.width)*scale for i in size]
            ImageDraw.Draw(im).pieslice(bbox, 180, 270, self.fillColor, self.outline, self.width*scale)
            im = im.resize(size, Image.LANCZOS)
        else:
            im = Image.new('RGBA', size)
            bbox = [0,0] + [i+self.width for i in size]
            ImageDraw.Draw(im).rectangle(bbox, self.fillColor, self.outline, self.width)
        im = makeShape(box.size()+[4], im)
        im2 = Image.new('RGBA', image.size)
        im2.paste(im, box.box, im)
        if 'opacity' in self.d:
            from image import Opacity
            im2 = Opacity(self.d, self.verbose).apply(im2)

        return self.applyImage(image, im2, verbose=self.verbose)
