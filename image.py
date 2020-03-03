from layer import Layer
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps
import matplotlib
import numpy as np

class MeanToAlpha(Layer):
    ___ = Layer.Register('mean-to-alpha', lambda d: MeanToAlpha(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.level=int(d['mean-to-alpha'])
        
    def apply(self, image):
        image = image.convert('RGBA')
        L = self.level
        a = np.array(image)
        if np.mean(a[0,0])<L:
            return image
        a = a.T
        w = (np.mean(a,axis=0)>=L)
        np.place(a[3], w, 0)
        return Image.fromarray(a.T)

class Opacity(Layer):
    ___ = Layer.Register('opacity', lambda d: Opacity(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.opacity=min(d['opacity'], 100.0)/100.0

    def apply(self, image):
        if self.verbose:
            print ' Opacity: ', self.opacity, '%'
        a = np.array(image)
        a = a.T
        a[3] = (a[3] * self.opacity).astype(np.uint8)
        return Image.fromarray(a.T)

class Mask(Layer):
    ___ = Layer.Register('mask', lambda d: Mask(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.color = d['mask']
        
    def apply(self, image):
        image = image.convert('RGBA')
        solid = Image.new('RGBA', image.size, self.color)
        mask = Image.new('RGBA', image.size, None)
        mask.paste(solid, (0,0), image)
        return mask

class Brighten(Layer):
    ___ = Layer.Register('brighten', lambda d: Brighten(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.amount = float(d['brighten'])
        
    def apply(self, image):
        return ImageEnhance.Brightness(image).enhance(self.amount)

class Contrast(Layer):
    ___ = Layer.Register('contrast', lambda d: Contrast(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.amount = float(d['contrast'])
        
    def apply(self, image):
        return ImageEnhance.Contrast(image).enhance(self.amount)
        return ImageEnhance.Color(image).enhance(self.amount)

class Sharpen(Layer):
    ___ = Layer.Register('sharpen', lambda d: Sharpen(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.amount = float(d['sharpen'])
        
    def apply(self, image):
        return ImageEnhance.Sharpness(image).enhance(self.amount)

class Filter(Layer):
    Names = {
        'BLUR': ImageFilter.BLUR,
        'CONTOUR': ImageFilter.CONTOUR,
        'DETAIL': ImageFilter.DETAIL,
        'EDGE_ENHANCE': ImageFilter.EDGE_ENHANCE,
        'EDGE_ENHANCE_MORE': ImageFilter.EDGE_ENHANCE_MORE,
        'FIND_EDGES': ImageFilter.FIND_EDGES,
        'SHARPEN': ImageFilter.SHARPEN,
        'SMOOTH': ImageFilter.SMOOTH,
        'SMOOTH_MORE': ImageFilter.SMOOTH_MORE
    }
    ___ = Layer.Register('filter', lambda d: Filter(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.filter = d['filter']
        
    def apply(self, image):
        return image.filter(Filter.Names[self.filter])

class Flip(Layer):
    Func = {
        'HORIZONTAL': ImageOps.mirror,
        'VERTICAL': ImageOps.flip,
        'H': ImageOps.mirror,
        'V': ImageOps.flip
    }
    ___ = Layer.Register('flip', lambda d: Flip(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.mode = d['flip']
        
    def apply(self, image):
        return Flip.Func[self.mode](image)

class Halo(Layer):
    ___ = Layer.Register('halo', lambda d: Halo(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.color = d['halo']
        self.radius = d.setdefault('gauss-blur-radius', 2)
        
    def apply(self, image):
        mask = Mask({'mask':self.color})
        im = mask.apply(image)
        im = im.filter(ImageFilter.GaussianBlur(self.radius))
        im = Image.composite(im, image, ImageChops.invert(im))
        bloom = [ 0.003, 0.053, 0.003, 0.053, 1.124, 0.053, 0.003, 0.053, 0.003 ]
        return im.filter(ImageFilter.Kernel((3, 3), bloom, 1, 0))

class Rotate(Layer):
    ___ = Layer.Register('rotate', lambda d: Rotate(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.angle = float(d['rotate'])
        
    def apply(self, image):
        return image.rotate(self.angle, expand=True)

class NormalizeColor(Layer):
    ___ = Layer.Register('normalize-color', lambda d: NormalizeColor(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.r = d['normalize-color']

    def apply(self, image):
        a = np.array(image)
        a = a.T
        for i in xrange(3):
            r = [np.min(a[i]), np.max(a[i])]
            q = self.r[i]
            a[i] = ((a[i]-r[0])*1.0*(q[1]-q[0])/(r[1]-r[0])+q[0]).astype(np.uint8)
        return Image.fromarray(a.T)

