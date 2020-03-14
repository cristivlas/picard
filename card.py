from __future__ import print_function
from PIL import Image
from layer import Layer, Group, ImageLayer, TextLayer
from os import path
import box
import cache
import copy
import json
import portable
import sys

class Card:
    Dict = {}
    Verbose = sys.modules['__main__'].verbose
    def __init__(self, d, fname, dpi, args):
        self.d = d
        self.fname = fname
        self.dpi = dpi
        self.bg = d.setdefault('bg', None)
        self.count = d.get('count', 1)
        d.setdefault('front', [])
        d.setdefault('back', [])
        self.frontLayers = [Layer.fromDict(dict(x, scope=fname)) for x in d['front'] if x] 
        self.backLayers = [Layer.fromDict(dict(x, scope=fname)) for x in d['back'] if x]
        self.recipe = d.get('recipe')
        if self.recipe:
            if not path.isabs(self.recipe):
                self.recipe = path.join(cache.DataPath, self.recipe)
            self.recipe = Card.load(self.recipe, dpi, args)
            self.frontLayers = self.concat('frontLayers', args)
            self.backLayers = self.concat('backLayers', args)
            self.size = self.recipe.size
            if not self.bg:
                self.bg = self.recipe.bg
            assert not d.get('orientation')
        else:
            if not 'size' in d:
                raise RuntimeError(fname + ': either size or recipe must be specified')
            self.size = box.getsize(d['size'])
            self.frontLayers = Layer.resolveModifiers(self, self.frontLayers, self, args)
            self.backLayers = Layer.resolveModifiers(self, self.backLayers, self, args)
            orient = d.get('orientation', 'portrait')
            if orient != self.size.orientation():
                self.size.rotate()

    def concat(self, whichLayers, args):
        layers = getattr(self.recipe, whichLayers, []) + getattr(self, whichLayers)
        return Layer.resolveModifiers(self, layers, self.recipe, args)

    @staticmethod
    def load(fname, dpi, args):
        if fname in Card.Dict:
            return Card.Dict[fname]
        with open(fname, 'r') as f:
            if Card.Verbose:
                print ('Loading:', fname)
            try:
                d = json.load(f)
            except Exception as e:
                portable.rethrow(e, '%s: %s' % (fname, str(e)))

        card = Card(d, fname, dpi, args)
        Card.Dict[fname] = card
        return card

    def toJSON(self):
        d = {k: v for k, v in self.d.items() if v}
        return json.dumps(d, indent=2, separators=(',', ': '))

    def blank(self):
        return Image.new('RGBA', self.size.convert(dpi=self.dpi).size(), self.bg)

    def front(self, args):
        if args.verbose:
            print ('Front:', self.fname)
        im = Layer.applyGroup(self, self.blank(), self.frontLayers, dpi=self.dpi, verbose=args.verbose)
        return self.applyOrientation(im, args)
 
    def back(self, args):
        if args.verbose:
            print ('Back:', self.fname)
        im = Layer.applyGroup(self, self.blank(), self.backLayers, dpi=self.dpi, verbose=args.verbose)
        return self.applyOrientation(im, args)

    def applyOrientation(self, im, args):
        im.rotated = False
        if args.orientation and args.orientation != self.size.orientation():
            im = im.rotate(90, expand=True)
            im.rotated = True
        return im

