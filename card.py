from PIL import Image
from layer import Layer, Group, ImageLayer, TextLayer
from os import path
import box
import cache
import copy
import json

class Card:
    def __init__(self, d, fname, dpi, cleanup):
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
            recipe = Card.load(recipe, dpi, cleanup=False)
            self.frontLayers = self.merge(recipe, 'frontLayers')
            self.backLayers = self.merge(recipe, 'backLayers')
            self.size = recipe.size
        else:
            self.size = box.getsize(d['size'])
        if d['orientation'] != self.size.orientation():
            self.size.rotate()

        if cleanup:
            Layer.Dict = {}

    def merge(self, recipe, which):
        layers = getattr(recipe, which) + getattr(self, which)
        for x in layers:
            x.resolve()
        return layers

    @staticmethod
    def load(fname, dpi, cleanup=True):
        with open(fname, 'r') as f:
            d = json.load(f)
        return Card(d, fname, dpi, cleanup) 

    def blank(self):
        return Image.new('RGBA', self.size.convert(dpi=self.dpi).size(), self.bg)

    def front(self):
        print 'front:',self.fname
        return Layer.applyGroup(self.blank(), self.frontLayers, dpi=self.dpi)
    
    def back(self):
        print 'back:',self.fname
        return Layer.applyGroup(self.blank(), self.backLayers, dpi=self.dpi)

