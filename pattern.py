from __future__ import print_function
from PIL import Image, ImageColor, ImageDraw
from layer import Layer

def dots(im, box, radius1=2, radius2=5, color='black', grad=False):
    assert radius1 < radius2
    box = box.convert(im.size) 
    rgb = ImageColor.getrgb(color)
    draw = ImageDraw.Draw(im)
    count = int(min(box.size()) / radius2)
    for x in range(count):
        color = tuple(min(255, int(i + 255 * x / count)) for i in rgb) if grad else rgb
        for y in range(count):
            xy = [2*radius2 * i + radius2 - radius1 + j for i,j in zip([x,y], box.xy())]
            draw.ellipse(xy + [i+2*radius1 for i in xy], fill=color, outline=color)

class Dots(Layer):
    ___ = Layer.Register('dots', lambda d: Dots(d))
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.color = Layer.arg(d)
        self.r1 = self.attr('radius', 2)
        self.r2 = self.attr('distance', 5)
        self.grad = self.attr('grad', True)
        assert self.attr('box')
        self.attr('units')

    def apply(self, ctxt, image):
        dots(image, self.box, self.r1, self.r2, self.color, self.grad)
        return image
