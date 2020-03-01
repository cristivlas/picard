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
            self.frontLayers = self.concat(recipe, 'frontLayers')
            self.backLayers = self.concat(recipe, 'backLayers')
            self.size = recipe.size
        else:
            self.size = box.getsize(d['size'])
        if d['orientation'] != self.size.orientation():
            self.size.rotate()

    def concat(self, recipe, whichLayers):
        return Layer.resolveModifiers(
            getattr(recipe, whichLayers, []) + getattr(self, whichLayers))

    @staticmethod
    def load(fname, dpi):
        if fname in Card.Dict:
            return Card.Dict[fname]
        with open(fname, 'r') as f:
            print 'Loading:', fname
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

