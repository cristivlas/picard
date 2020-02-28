from PIL import Image
from layer import Layer, Group, ImageLayer, TextLayer
from os import path
import box
import cache
import copy
import json

class Card:
    def __init__(self, d, dpi):
        self.dpi = dpi
        d.setdefault('bg', 'white')
        d.setdefault('orientation', 'portrait')
        d.setdefault('recipe', None)
        self.recipe = None
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
            self.recipe = Card(json.load(f), dpi)

    @staticmethod
    def load(data, dpi):
        if type(data) is str:
            d = json.loads(data)
        else:
            d = json.load(data)
        return Card(d, dpi) 

    def blank(self):
        return Image.new('RGBA', self.size.convert(dpi=self.dpi).size(), self.bg)

    def merge(self, which):
        layers = getattr(self.recipe, which, []) + getattr(self, which)
        for x in layers:
            x.resolve()
        return layers

    def front(self):
        return Layer.applyGroup(self.blank(), self.merge('frontLayers'), dpi=self.dpi)
    
    def back(self):
        return Layer.applyGroup(self.blank(), self.merge('backLayers'), dpi=self.dpi)

