from box import Box, Units
from PIL import Image, ImageDraw
from cache import CacheFont, CacheImage
from os import path
import exceptions
import importlib
import inspect
import math
import textwrap

class Layer:
    Dict = {}
    Factory = {}
    Units = dict([(x.name, x.value) for x in list(Units)])

    class Register:
        def __init__(self, name, fun):
            fullname = inspect.getmodule(fun).__name__ + '.' + name
            Layer.Factory[fullname]=fun
            print 'Registered:', fullname

    @staticmethod
    def id(scope, id):
        return id if (id is None or ':' in id) else (path.splitext(scope)[0] + ':' + id)

    def __init__(self, d, verbose):
        self.d=d
        self.used=set()
        self.__toDict()
        self.verbose=verbose
        self.fill = self.attr('fill', False)
        units = Units[d.get('units', 'PIXEL')]
        box = d.get('box', None)
        self.box = Box(box, units) if box else None

    def __del__(self):
        for k in self.d:
            if k in self.specialAttrs():
                continue
            if not k in self.used:
                print self, ' Unexpected attribute:', str(k)

    def unique_id(self):
        scope = self.d.get('scope')
        return Layer.id(scope, self.attr('id'))

    def __toDict(self):
        unique_id = self.unique_id()
        if unique_id:
            assert unique_id not in Layer.Dict, unique_id
            Layer.Dict[unique_id] = self

    def clone(self, d):
        return self.__class__(d)

    def specialAttrs(self):
        return ['ctor', 'id', 'scope'] + [self.d['ctor']]

    def subst(self, d):
        return d.get(self, self)
        
    @staticmethod
    def resolveModifiers(ctxt, layers, recipe, args):
        d = dict((x, x) for x in layers)
        for x in layers:
            if isinstance(x, Modifier):
                orig, mod = x.modify(recipe, args)
                assert mod is not orig
                d[orig] = mod
                mod.d['id'] = orig.d['id']
                mod.d['scope'] = ctxt.fname
                mod.__toDict()
        resolved = []
        for x in layers:
            if not isinstance(x, Modifier):
                resolved.append(x.subst(d))
        return resolved

    def errorImage(self, ctxt, err):
        im = Image.new('RGBA', [self.dpi, self.dpi], 'white')
        draw = ImageDraw.Draw(im)
        draw.line([0,0]+list(im.size), fill='red', width=2)
        draw.line([0,im.size[1],im.size[0],0], fill='red', width=2)
        text = TextLayer(dict(ctor='text', text=str(err), color='black'))
        text.dpi = self.dpi
        return text.apply(ctxt, im)

    @staticmethod
    def fromDict(d):
        for k in d:
            t = k.split('.')
            assert len(t) <= 2
            if len(t) > 1:
                importlib.import_module(t[0])
                d['ctor'] = k
                return Layer.Factory[k](d)
        raise RuntimeError('Constructor not found: ' + str(d))

    @staticmethod
    def arg(d, replace=None):
        k = d['ctor']
        if replace is not None:
            d[k] = replace
        return d[k]

    @staticmethod
    def applyGroup(ctxt, image, layers, dpi, verbose):
        assert dpi is not None
        for x in layers:
            x.dpi = dpi
            x.verbose = verbose
            if verbose:
                print ' Applying:', x
            image = x.apply(ctxt, image)
        return image

    @staticmethod
    def applyImage(image1, image2, box=None, fill=True, verbose=False):
        assert image2
        assert image2.mode == 'RGBA'
        if image1:
            assert image1.mode=='RGBA'
            box = box.convert(image1.size) if box else Box(image1.size)
            if fill:
                image2 = image2.resize(box.size(), Image.LANCZOS)
            else:
                image2 = scaleToFit(image2, box.size(), verbose)
            image1.paste(image2, box.box, image2)
            return image1
        return image2

    def attr(self, a, default=None, domain=None):
        val = self.d.get(a, default)
        if domain and (val < domain[0] or val > domain[1]):
            raise ValueError(val, domain)
        self.used.add(a)
        return val
    
    def __change(self, d, k1, k2, args):
        if args.verbose:
            print ' Modify:', k1, d.get(k1), '<--', self.d[k2]
        d[k1] = self.attr(k2)

    def modify(self, target, args):
        if not isinstance(target, Layer):
            assert str(target.__class__) == 'card.Card'
            target = Layer.Dict[Layer.id(target.fname, self.target)]
            self.target = target
        d = dict(target.d)
        c = d['ctor']

        for k in self.d:
            if k in self.specialAttrs():
                continue
            if not k in d:
                if k==c.split('.')[1]:
                    self.__change(d, c, k, args)
                    continue
            self.__change(d, k, k, args)
        assert d != target.d, d['id']
        del d['id']
        return (target, target.clone(d))

class Group(Layer):
    ___ = Layer.Register('group', lambda d: Group(d) )
    def __init__(self, d, verbose=False, group=None):
        Layer.__init__(self, d, verbose)
        self.attr('box')
        self.attr('units')
        self.newImage = self.attr('new-image', False)
        self.group = group if group else [Layer.fromDict(dict(x, scope=d['scope'])) for x in Layer.arg(d) if x]

    def apply(self, ctxt, image):
        image1 = Image.new('RGBA', image.size) if self.newImage else None
        image2 = Layer.applyGroup(ctxt, image1, self.group, self.dpi, self.verbose)
        return Layer.applyImage(image, image2, self.box, self.fill, self.verbose)

    def subst(self, d):
        group = [x.subst(d) for x in self.group]
        if group==self.group:
            return self
        g = dict(self.d)
        Layer.arg(g, [])
        return Group(g, group=group)

class Modifier(Layer):
    ___ = Layer.Register('modify', lambda d: Modifier(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.target = Layer.arg(d)

    def apply(self, ctxt, image):
        assert False

class Copy(Layer):
    ___ = Layer.Register('copy', lambda d: Copy(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose)
        self.ref_id = Layer.arg(d)

    def specialAttrs(self):
        return Layer.specialAttrs(self) + ['reflect']

    def ref(self, ctxt):
        try:
            return Layer.Dict[Layer.id(ctxt.fname, self.ref_id)]
        except KeyError:
            scope = self.d.get('scope')
            assert scope
            return Layer.Dict[Layer.id(scope, self.ref_id)]

    def apply(self, ctxt, image):
        ref = self.ref(ctxt)
        for k in self.d:
            if k not in Layer.specialAttrs(self):
                reflect = self.attr('reflect')
                if reflect:
                    ref.box.reflect(reflect, self.d)
                (ref, ref) = self.modify(ref, self)
                break
        ref.dpi = self.dpi
        return ref.apply(ctxt, image)
  
def scaleToFit(image, size, verbose):
    w, h = (float(x) for x in image.size)
    aspect =  w / h
    keep='height'
    if size[1] * aspect <= size[0]:
        scale = size[1] / h
    elif size[0] / aspect <= size[1]:
        scale = size[0] / w
        keep ='width'
    else:
        assert False
    if verbose:
        print ' scale-to-fit: keeping same %s, scale=%3.2f' % (keep, scale)
    image = image.resize([int(scale * x) for x in image.size], Image.LANCZOS)
    image2 = Image.new('RGBA', size, None)
    image2.paste(image, [(x-y)/2 for x,y in zip(size, image.size)], image)
    return image2

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
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        self.attr('box')
        self.attr('units')
        self.outline = self.attr('outline', None)
        self.color = self.attr('color', 'black')
        self.font = self.attr('font', None)
        self.fontSize = self.attr('font-size', None)
        self.text = Layer.arg(d)
        
    def apply(self, ctxt, image):
        assert image
        if not self.box:
            self.box = Box([0,0, 100, 100], Units.PERCENT)
        font = CacheFont(self.font, self.fontSize, self.dpi).font
        box = self.box.convert(image.size)
        xy = box.box[:2]
        bbox = box.size()
        draw = ImageDraw.Draw(image)
        centerTextH(image.size, draw, xy, bbox, self.text, font, self.color, out=self.outline)
        return image

class ImageLayer(Layer):
    ___ = Layer.Register('image', lambda d: ImageLayer(d) )
    def __init__(self, d, verbose=False):
        Layer.__init__(self, d, verbose) 
        box = self.attr('box', None)
        self.image = CacheImage(Layer.arg(d)).image

    def apply(self, ctxt, image):
        if isinstance(self.image, exceptions.Exception):
            return self.errorImage(ctxt, self.image)
        return self.applyImage(image, self.image, self.box, self.fill, self.verbose)

