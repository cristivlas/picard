from PIL import Image
from layer import Layer, Group, ImageLayer, TextLayer
from os import path
import box
import cache
import copy
import json

class Card:
    Dict = {}
    def __init__(self, d, fname, dpi):
        self.fname = fname
        self.dpi = dpi
        d.setdefault('bg', 'white')
        d.setdefault('orientation', 'portrait')
        d.setdefault('recipe', None)
        self.frontLayers = [Layer.fromDict(x) for x in d['front']]
        self.backLayers = [Layer.fromDict(x) for x in d['back']]
        self.bg = d['bg']

        recipe = d['recipe']
        if recipe:
            if not path.isabs(recipe):
                recipe = path.join(cache.DataPath, recipe)
            recipe = Card.load(recipe, dpi)
            self.frontLayers = self.buildLayersList(recipe, 'frontLayers')
            self.backLayers = self.buildLayersList(recipe, 'backLayers')
            self.size = recipe.size
        else:
            self.size = box.getsize(d['size'])
        if d['orientation'] != self.size.orientation():
            self.size.rotate()

    def buildLayersList(self, recipe, whichLayers):
        if not recipe:
            return getattr(self, whichLayers)
        d = dict((x, x) for x in getattr(recipe, whichLayers))
        for x in getattr(self, whichLayers):
            orig, mod = x.resolve()
            d[orig] = mod
        layers = []
        for x in getattr(recipe, whichLayers) + getattr(self, whichLayers):
            if d.has_key(x):
                layers.append(d[x])
        return layers

    @staticmethod
    def load(fname, dpi):
        if fname in Card.Dict:
            return Card.Dict[fname]
        with open(fname, 'r') as f:
            d = json.load(f)
        card = Card(d, fname, dpi)
        Card.Dict[fname] = card
        return card

    def blank(self):
        return Image.new('RGBA', self.size.convert(dpi=self.dpi).size(), self.bg)

    def front(self, verbose):
        if verbose:
            print 'Front:', self.fname
        return Layer.applyGroup(self.blank(), self.frontLayers, dpi=self.dpi, verbose=verbose)
    
    def back(self, verbose):
        if verbose:
            print 'Back:', self.fname
        return Layer.applyGroup(self.blank(), self.backLayers, dpi=self.dpi, verbose=verbose)

