from __future__ import print_function
from layer import Layer
from PIL import Image, ImageDraw
import numpy as np

def makeShape(shape, im):
    shape = shape[1],shape[0],shape[2]
    a = np.array(im)
    d = [int(i/2 - j) for i, j in zip(shape, a.shape)]
    a = np.pad(a, ((0,d[0]+1),(0,d[1]+1),(0,0)), 'edge')
    a = np.pad(a, ((0,shape[0]-a.shape[0]),(0,0),(0,0)), 'symmetric')
    a = np.pad(a, ((0,0), (0, shape[1]-a.shape[1]),(0,0)), 'symmetric')
    return Image.fromarray(a)

class Rectangle(Layer):
    ___ = Layer.Register('rectangle', lambda x: Rectangle(x))
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        assert self.attr('box')
        self.attr('units')
        self.outline = Layer.arg(d)
        self.radius = self.attr('corner-radius', 0)
        self.width = self.attr('line-width', 1)
        self.fillColor = self.attr('fill-color', None)
        assert self.radius==0 or self.width < self.radius

    def apply(self, ctxt, image):
        box = self.box.convert(image.size)
        r = self.radius or int(min(box.size())/2)
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
        opacity = self.attr('opacity')
        if opacity:
            from image import Opacity
            im2 = Opacity({'opacity': opacity, 'ctor': 'opacity'}, self.verbose).apply(ctxt, im2)
        return self.applyImage(image, im2, verbose=self.verbose)
