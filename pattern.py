from __future__ import print_function
from PIL import Image, ImageColor, ImageDraw
from layer import Layer

def dots(im, box, radius1=2, radius2=5, color='black', grad=False, opacity=100.0):
    assert radius1 < radius2
    box = box.convert(im.size) 
    rgb = ImageColor.getrgb(color)
    draw = ImageDraw.Draw(im)
    count = [int(i/(2*radius2)) for i in box.size()]
    opacity = int(255 * opacity/100.0)
    color = tuple(list(rgb) + [opacity])
    r = radius1
    for x in range(count[0]):
        if grad:
            color = tuple([min(255, int(i + 255.0 * x / count[0])) for i in rgb] + [opacity])
            r = int(radius1 * (count[0]-x)/count[0]) if grad else radius1
        for y in range(count[1]):
            xy = [2*radius2 * i + radius2 - r + j for i,j in zip([x,y], box.xy())]
            draw.ellipse([xy[0]-r, xy[1]-r, xy[0]+r, xy[1]+r], fill=color, outline=color)

class Dots(Layer):
    ___ = Layer.Register('dots', lambda d: Dots(d))
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.color = Layer.arg(d)
        self.r1 = self.attr('radius', 2)
        self.r2 = self.attr('distance', 5) + self.r1
        self.grad = self.attr('grad', True)
        self.opacity=int(255 * min(self.attr('opacity', 100.0), 100.0)/100.0)
        assert self.attr('box')
        self.attr('units')

    def apply(self, ctxt, image):
        dots(image, self.box, self.r1, self.r2, self.color, self.grad, self.opacity)
        return image
