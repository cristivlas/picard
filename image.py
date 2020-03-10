from __future__ import print_function
from layer import Layer
from PIL import Image, ImageChops, ImageColor, ImageEnhance, ImageFilter, ImageOps
#from scipy import ndimage as ndi
#from skimage import filters, morphology
from matplotlib import colors
import colorsys
import numpy as np

bloomKernel = [
    0.003, 0.053, 0.003,
    0.053, 1.124, 0.053,
    0.003, 0.053, 0.003 ]

def mean_to_alpha_threshold(im, level):
    a = np.array(im)
    a = a.T
    w = (np.mean(a,axis=0)>=level)
    np.place(a[3], w, 0)
    return Image.fromarray(a.T)

def normalize(im, usr):
    a = np.array(im)
    a = a.T
    num_colors=1 if len(a.shape)==2 else min(a.shape[2], 3)
    for i in range(num_colors):
        q = usr[i]
        r = [np.min(a[i]), np.max(a[i])]
        a[i] = ((a[i]-r[0])*1.0*(q[1]-q[0])/(r[1]-r[0])+q[0]).astype(np.uint8)
    return Image.fromarray(a.T)

def change_hue(im, color, range=None):
    assert im.mode=='RGBA'
    (r,g,b) = (x/255. for x in ImageColor.getrgb(color))
    (h,s,v) = colorsys.rgb_to_hsv(r,g,b)
    a = np.array(im)
    a = a.reshape(int(a.size/4),4)
    alpha = a[:,3:]
    a = a[:,:3]
    a = colors.rgb_to_hsv(a/255.)
    a = a.T
    if range:
        np.place(a[0], np.logical_and(a[0]<range[1], a[0]>range[0]), h)
        np.place(a[2], np.logical_and(a[0]<range[1], a[0]>range[0]), v)
    else: 
        a[0] = h
        a[2] = v

    # back to RGBA
    a = a.T
    a = colors.hsv_to_rgb(a)*255.5
    a = a.astype(np.uint8)
    a = np.concatenate((a,alpha), axis=1)
    a = a.reshape((im.size[1], im.size[0], 4))
    return Image.fromarray(a)
    

class MeanToAlpha(Layer):
    ___ = Layer.Register('mean-to-alpha', lambda d: MeanToAlpha(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.level=int(Layer.arg(d))

    def apply(self, ctxt, image):
        return mean_to_alpha_threshold(image, self.level)

class Opacity(Layer):
    #___ = Layer.Register('opacity', lambda d: Opacity(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.opacity=min(Layer.arg(d), 100.0)/100.0

    def apply(self, ctxt, image):
        if self.verbose:
            print (' Opacity: ', self.opacity, '%')
        a = np.array(image)
        a = a.T
        a[3] = (a[3] * self.opacity)
        return Image.fromarray(a.T)

class Mask(Layer):
    ___ = Layer.Register('mask', lambda d: Mask(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.color = Layer.arg(d)
        
    def apply(self, ctxt, image):
        image = image.convert('RGBA')
        solid = Image.new('RGBA', image.size, self.color)
        mask = Image.new('RGBA', image.size, None)
        mask.paste(solid, (0,0), image)
        return mask

class Brighten(Layer):
    ___ = Layer.Register('brighten', lambda d: Brighten(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.amount = Layer.arg(d)
        
    def apply(self, ctxt, image):
        return ImageEnhance.Brightness(image).enhance(self.amount)

class Contrast(Layer):
    ___ = Layer.Register('contrast', lambda d: Contrast(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.amount = Layer.arg(d)
        
    def apply(self, ctxt, image):
        return ImageEnhance.Contrast(image).enhance(self.amount)
        return ImageEnhance.Color(image).enhance(self.amount)

class Sharpen(Layer):
    ___ = Layer.Register('sharpen', lambda d: Sharpen(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.amount = Layer.arg(d)
        
    def apply(self, ctxt, image):
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
        self.filter = Layer.arg(d)
        
    def apply(self, ctxt, image):
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
        self.mode = Layer.arg(d)
        
    def apply(self, ctxt, image):
        return Flip.Func[self.mode](image)

class Halo(Layer):
    ___ = Layer.Register('halo', lambda d: Halo(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.color = Layer.arg(d)
        self.radius = self.attr('gauss-blur-radius', 2)
        
    def apply(self, ctxt, image):
        mask = Mask({'mask':self.color, 'ctor':'mask'})
        im = mask.apply(ctxt, image)
        im = im.filter(ImageFilter.GaussianBlur(self.radius))
        im = Image.composite(im, image, ImageChops.invert(im))
        return im.filter(ImageFilter.Kernel((3, 3), bloomKernel, 1, 0))

class Rotate(Layer):
    ___ = Layer.Register('rotate', lambda d: Rotate(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.angle = float(Layer.arg(d))
    def apply(self, ctxt, image):
        return image.rotate(self.angle, expand=True)

class ChangeHue(Layer):
    ___ = Layer.Register('hue', lambda d: ChangeHue(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.color = Layer.arg(d)
        self.range = self.attr('range', [.2, .5])

    def apply(self, ctxt, image):
        return change_hue(image, self.color, self.range)

class NormalizeColor(Layer):
    ___ = Layer.Register('normalize-color', lambda d: NormalizeColor(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.r = Layer.arg(d)

    def apply(self, ctxt, image):
        return normalize(image, self.r)
