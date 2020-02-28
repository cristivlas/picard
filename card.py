from PIL import Image
from layer import Layer, Group, ImageLayer, TextLayer
from os import path
import box
import cache
import copy
import json

class Card:
    def __init__(self, d, dpi, cleanup=True):
        self.dpi = dpi
        d.setdefault('bg', 'white')
        d.setdefault('orientation', 'portrait')
        d.setdefault('recipe', None)
        self.frontLayers = [Layer.fromDict(x) for x in d['front']]
        self.backLayers = [Layer.fromDict(x) for x in d['back']]
        self.bg = d['bg']
        self.size = box.getsize(d['size'])
        if d['orientation'] != self.size.orientation():
            self.size.rotate()

        recipe = d['recipe']
        if recipe:
            if not path.isabs(recipe):
                recipe = path.join(cache.DataPath, recipe)
            f = open(recipe, 'r')
            recipe = Card(json.load(f), dpi, cleanup=False)
            self.frontLayers = self.merge(recipe, 'frontLayers')
            self.backLayers = self.merge(recipe, 'backLayers')
        if cleanup:
            Layer.Dict = {}

    def merge(self, recipe, which):
        layers = getattr(recipe, which) + getattr(self, which)
        for x in layers:
            x.resolve()
        return layers

    @staticmethod
    def load(data, dpi):
        if type(data) is str:
            d = json.loads(data)
        else:
            d = json.load(data)
        return Card(d, dpi) 

    def blank(self):
        return Image.new('RGBA', self.size.convert(dpi=self.dpi).size(), self.bg)

    def front(self):
        return Layer.applyGroup(self.blank(), self.frontLayers, dpi=self.dpi)
    
    def back(self):
        return Layer.applyGroup(self.blank(), self.backLayers, dpi=self.dpi)

