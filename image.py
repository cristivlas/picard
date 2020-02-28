from layer import Layer
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps
import matplotlib
import numpy as np

class MeanToAlpha(Layer):
    ___ = Layer.Register('mean-to-alpha', lambda d: MeanToAlpha(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
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

class Mask(Layer):
    ___ = Layer.Register('mask', lambda d: Mask(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
        self.color = d['mask']
        
    def apply(self, image):
        image = image.convert('RGBA')
        solid = Image.new('RGBA', image.size, self.color)
        mask = Image.new('RGBA', image.size, None)
        mask.paste(solid, (0,0), image)
        return mask

class Sharpen(Layer):
    ___ = Layer.Register('sharpen', lambda d: Sharpen(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
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
    def __init__(self, d):
        Layer.__init__(self, d) 
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
    def __init__(self, d):
        Layer.__init__(self, d) 
        self.mode = d['flip']
        
    def apply(self, image):
        return Flip.Func[self.mode](image)

def gradient(im):
    a = np.array(im)
    s = a.shape
    d = a.shape[2]
    assert d==3 or d==4
    a = a.reshape(a.size/d,d)
    alpha = a[:,3:] # save transparency
    a = a[:,:3]
    a = matplotlib.colors.rgb_to_hsv(a/255.)
    a = a.T
    v = np.ones(s[:2])
    v = np.cumsum(v, axis=0)
    np.place(a[2], np.ones(a[2].shape), v) 
    # back to RGB
    a = a.T
    a = matplotlib.colors.hsv_to_rgb(a)*255.5
    a = a.astype(np.uint8)
    a = np.concatenate((a,alpha), axis=1)
    a = a.reshape((im.size[1], im.size[0], d))
    return Image.fromarray(a)

class Halo(Layer):
    ___ = Layer.Register('halo', lambda d: Halo(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
        self.color = d['halo']
        
    def apply(self, image):
        mask = Mask({'mask':self.color})
        im = gradient(mask.apply(image))
        im = im.filter(ImageFilter.BLUR)
        return Image.composite(im, image, ImageChops.invert(im))

class Rotate(Layer):
    ___ = Layer.Register('rotate', lambda d: Rotate(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
        self.angle = float(d['rotate'])
        
    def apply(self, image):
        return image.rotate(self.angle, expand=True)

