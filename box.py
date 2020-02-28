from enum import Enum
import warnings

class Units(Enum):
    PERCENT = 0
    PIXEL = 1
    INCH = 2
    MILIMETER = 3

class Box:
    def __init__(self, box, units = Units.PIXEL):
        if box.__class__==Box:
            self.box = box.box
            self.units = box.units
        elif type(box)==list:
            self.box = box
            self.units = units
            if len(self.box)==2:
                self.box = [0,0] + self.box
        else:
            b = getsize(box)
            self.box = b.box
            self.units = b.units
            #warnings.warn('Ignored ' + str(units))

    def __repr__(self):
        return (self.box, self.units.name).__repr__()

    def convert(self, other=None, dpi=300):
        assert self.box
        assert type(self.box) is list
        assert len(self.box)==4
        if self.units == Units.PERCENT:
            if len(other)==2:
                other += other
            return Box([int(x*y/100.0) for x,y in zip(self.box, other)])
        elif self.units == Units.PIXEL:
            return self
        elif self.units == Units.INCH:
            return Box([int(x*dpi) for x in self.box])
        elif self.units == Units.MILIMETER:
            return Box([int(x*0.0393701*dpi) for x in self.box])
        assert False

    def size(self):
        return [self.box[2]-self.box[0], self.box[3]-self.box[1]]

    def orientation(self):
        s = self.size()
        return 'portrait' if s[0] <= s[1] else 'landscape'

    def rotate(self):
        assert self.box[0] == 0 and self.box[1] == 0
        self.box = [0, 0, self.box[3], self.box[2]]

class Size(Enum):
    BRIDGE = Box([2.25, 3.5], Units.INCH)
    POKER = Box([2.5, 3.5], Units.INCH)
    MINI = Box([1.65, 2.5], Units. INCH)
    TAROT = Box([2.75, 4.75], Units.INCH)

Sizes = dict([(x.name, x.value) for x in list(Size)])

def getsize(size):
    if size.__class__ != Box:
        if type(size) is list:
            size = Box(size, Units.INCH)
        else:
            size = Sizes[size]
    return size

