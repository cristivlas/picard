from box import Box, Units
from PIL import Image, ImageDraw
from cache import CacheFont, CacheImage
import exceptions
import importlib
import math
import textwrap

class Layer:
    Dict = { }
    Factory = { }
    Units = dict([(x.name, x.value) for x in list(Units)])

    class Register:
        def __init__(self, name, fun):
            Layer.Factory[name]=fun
   
    def __init__(self, d):
        d.setdefault('id', None)
        self.d=d
        unique_id=d['id']
        if unique_id:
            assert unique_id not in Layer.Dict
            Layer.Dict[unique_id] = self
        units = Units[d['units']] if 'units' in d else Units.PIXEL
        try:
            box = d['box']
            self.box = Box(box, units)
        except KeyError:
            self.box = None

    def clone(self, d):
        return self.__class__(d)

    def subst(self, d):
        return d[self] if self in d else self

    @staticmethod
    def resolveModifiers(layers):
        d = dict((x, x) for x in layers)
        for x in layers:
            if isinstance(x, Modifier):
                orig, mod = x.modify()
                d[orig] = mod
        resolved = []
        for x in layers:
            if not isinstance(x, Modifier):
                resolved.append(x.subst(d))
        return resolved

    @staticmethod
    def fromDict(d):
        for k in d:
            t = k.split('.')
            assert len(t) <= 2
            if len(t) > 1:
                importlib.import_module(t[0])
                d[t[1]] = d[k]
                k = t[1]
                return Layer.Factory[k](d)
        raise RuntimeError('Layer not recognized: '+str(d))

    @staticmethod
    def applyGroup(image, layers, dpi, verbose):
        assert dpi is not None
        for x in layers:
            x.dpi = dpi
            x.verbose = verbose
            if verbose:
                print ' Applying:', x
            image = x.apply(image)
        return image

    def applyImage(self, image1, image2):
        assert image2
        image2 = image2.convert('RGBA')
        if image1:
            assert image1.mode=='RGBA'
            if self.box:
                box = self.box.convert(image1.size)
                image2 = image2.resize(box.size(), Image.LANCZOS)
                image1.paste(image2, box.box, image2)
            else:
                image2 = image2.resize(image1.size, Image.LANCZOS)
                image1 = Image.alpha_composite(image1, image2)
            return image1
        return image2
    
class Group(Layer):
    ___ = Layer.Register('group', lambda d: Group(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
        self.group = [Layer.fromDict(x) for x in d['group']]
    def apply(self, image):
        image2 = Layer.applyGroup(None, self.group, self.dpi, self.verbose)
        return self.applyImage(image, image2)
    def subst(self, d):
        group = [x.subst(d) for x in self.group]
        if group==self.group:
            return self
        other = Group({'group':[]})
        other.group = group
        return other

class Modifier(Layer):
    ___ = Layer.Register('modify', lambda d: Modifier(d) )
    def __init__(self, d):
        Layer.__init__(self, d)
        d.setdefault('modify', None)
        self.target = d['modify']

    def apply(self, image):
        assert False

    def modify(self):
        target = Layer.Dict[self.target]
        d = dict(target.d)
        del d['id']
        for k in self.d:
            if k in d:
                d[k] = self.d[k]
        return (target, target.clone(d))

class Crop(Layer):
    GetOrigin = {
        'CENTER': lambda s,b: [(x-y)/2 for x,y in zip(s, b[2:])],
        'NW': lambda s,b: [0,0],
        'NE': lambda s,b: [s[0]-b[2], 0],
        'SW': lambda s,b: [0, s[1]],
        'SE': lambda s,b: [(x-y) for x, y in zip(s, b[2:])],
    }
    ___ = Layer.Register('crop', lambda d: Crop(d) )
    def __init__(self, d):
        Layer.__init__(self, d)
        self.origin = d['crop']
    def apply(self, image):
        box = self.box.convert(image.size).box
        orig = Crop.GetOrigin[self.origin](image.size, box)
        box = [x+o for x,o in zip(box, orig+orig)]
        if self.verbose:
            print '  Crop box:', self.box, box
        return image.crop(box)

class Scale(Layer):
    ___ = Layer.Register('scale', lambda d: Scale(d) )
    def __init__(self, d):
        Layer.__init__(self, d)
        self.factor = float(d['scale'])
    def apply(self, image):
        return image.resize([int(self.factor*x) for x in image.size], Image.LANCZOS)

def drawText(draw, xy, text, fill, font):
    draw.text(xy, text, fill, font)

def centerTextH(size, draw, xy, bbox, text, font, fill=(0,0,0), sp=0, wrap=True, out=None):
    if wrap and out:
        h = bbox[1] or size[1]-xy[1]
        draw.rectangle([xy[0], xy[1], xy[0]+bbox[0]-2, xy[1]+h-1], outline=out, width=3)
    textsz = draw.textsize(text, font, spacing=sp)
    if wrap and (textsz[0] >= bbox[0]):
        average_char_width = math.ceil(1.0 *textsz[0] / len(text))
        max_cols = int(math.floor(bbox[0] / average_char_width)) or 70
        paragraph = textwrap.wrap(text, width=max_cols, expand_tabs=False)
        for line in paragraph:
            xy = centerTextH(size, draw, xy, bbox, line, font, fill, sp=sp, wrap=False, out=out)
        return xy
    coords = [xy[0] + (bbox[0]-textsz[0])/2, xy[1]]
    drawText(draw, coords, text, fill, font)
    if not hasattr(font, 'size'):
        font.size = textsz[1]
    return [xy[0], xy[1]+font.size+sp]

class TextLayer(Layer):
    ___ = Layer.Register('text', lambda d: TextLayer(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
        d.setdefault('outline', None)
        d.setdefault('color', 'black')
        d.setdefault('font', None)
        d.setdefault('font-size', None)
        self.text = d['text']
        self.font = d['font']
        self.fontSize = d['font-size']
        self.outline = d['outline']
        self.color = d['color']
        
    def apply(self, image):
        assert image
        if not self.box:
            self.box = Box([0,0]+list(image.size))
        font = CacheFont(self).font
        box = self.box.convert(image.size)
        xy = box.box[:2]
        bbox = box.size()
        draw = ImageDraw.Draw(image)
        centerTextH(image.size, draw, xy, bbox, self.text, font, self.color, out=self.outline)
        return image

class ImageLayer(Layer):
    ___ = Layer.Register('image', lambda d: ImageLayer(d) )
    def __init__(self, d):
        Layer.__init__(self, d) 
        self.image = CacheImage(d['image']).image
        if self.box:
            box = self.box.convert(self.image.size)
            self.image = self.image.resize(box.size(), Image.LANCZOS)
    def apply(self, image):
        if isinstance(self.image, exceptions.Exception):
            return self.errorImage()
        return self.applyImage(image, self.image)

    def errorImage(self):
        im = Image.new('RGBA', [self.dpi, self.dpi], 'white')
        draw = ImageDraw.Draw(im)
        draw.line([0,0]+list(im.size), fill='red', width=2)
        draw.line([0,im.size[1],im.size[0],0], fill='red', width=2)
        d = {'text':str(self.image), 'color':'black'}
        text = TextLayer(d)
        return text.apply(im)

