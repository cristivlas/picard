from PIL import Image
from layer import Layer, Group, ImageLayer, TextLayer
from os import path
import box
import cache
import copy
import json

class Card:
    Dict = {}
    def __init__(self, d, fname, dpi, args):
        self.d = d
        self.fname = fname
        self.dpi = dpi
        self.bg = d.setdefault('bg', None)
        self.count = d.get('count', 1)
        d.setdefault('back', [])
        self.frontLayers = [Layer.fromDict(dict(x, scope=fname)) for x in d['front'] if x] 
        self.backLayers = [Layer.fromDict(dict(x, scope=fname)) for x in d['back'] if x]
        recipe = d.setdefault('recipe', None)
        if recipe:
            if not path.isabs(recipe):
                recipe = path.join(cache.DataPath, recipe)
            recipe = Card.load(recipe, dpi, args)
            self.frontLayers = self.concat(recipe, 'frontLayers', args)
            self.backLayers = self.concat(recipe, 'backLayers', args)
            self.size = recipe.size
            if not self.bg:
                self.bg = recipe.bg
            assert not d.get('orientation')
        else:
            self.size = box.getsize(d['size'])
            self.frontLayers = Layer.resolveModifiers(self, self.frontLayers, self, args)
            self.backLayers = Layer.resolveModifiers(self, self.backLayers, self, args)
            orient = d.get('orientation', 'portrait')
            if orient != self.size.orientation():
                self.size.rotate()

    def concat(self, recipe, whichLayers, args):
        layers = getattr(recipe, whichLayers, []) + getattr(self, whichLayers)
        return Layer.resolveModifiers(self, layers, recipe, args)

    @staticmethod
    def load(fname, dpi, args):
        if fname in Card.Dict:
            return Card.Dict[fname]
        with open(fname, 'r') as f:
            print 'Loading:', fname
            d = json.load(f)
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
            print 'Front:', self.fname
        im = Layer.applyGroup(self, self.blank(), self.frontLayers, dpi=self.dpi, verbose=args.verbose)
        return self.applyOrientation(im, args)
 
    def back(self, args):
        if args.verbose:
            print 'Back:', self.fname
        im = Layer.applyGroup(self, self.blank(), self.backLayers, dpi=self.dpi, verbose=args.verbose)
        return self.applyOrientation(im, args)

    def applyOrientation(self, im, args):
        im.rotated = False
        if args.orientation and args.orientation != self.size.orientation():
            im = im.rotate(90, expand=True)
            im.rotated = True
        return im

