from enum import Enum
import warnings

class Units(Enum):
    PERCENT = 0
    PIXEL = 1
    INCH = 2
    MILIMETER = 3

class Box:
    Verbose = False
    def __init__(self, box, units = Units.PIXEL):
        if box.__class__==Box:
            self.box = box.box
            self.units = box.units
        elif type(box) in [list, tuple]:
            self.box = list(box)
            self.units = units
            if len(self.box)==2:
                self.box = [0,0] + self.box
        else:
            b = getsize(box)
            self.box = b.box
            self.units = b.units
            if Box.Verbose:
                warnings.warn('Ignored ' + str(units))

    def __repr__(self):
        return (self.box, self.units.name).__repr__()

    def convert(self, size=None, dpi=300):
        assert self.box
        assert isinstance(self.box, list)
        assert len(self.box)==4
        if self.units == Units.PERCENT:
            if len(size)==2:
                size += size
            return Box([int(x*y/100.0) for x,y in zip(self.box, size)])
        elif self.units == Units.PIXEL:
            if size:
                pc = [float('{0:0.2f}'.format(x*100.0/y)) for x,y in zip(self.box, size+size)]
                print 'Consider relative coordinates:', pc, '("units": "PERCENT") instead of', self

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

    def reflect(self, axis, d):
        if axis:
            assert self.units == Units.PERCENT
            if axis=='HORIZONTAL':
                box = [100-self.box[2], self.box[1], 100-self.box[0], self.box[3]]
            else:
                assert axis=='VERTICAL'
                box = [self.box[0], 100-self.box[3], self.box[2], 100-self.box[1]]
            d['box'] = box
            d['units'] = 'PERCENT'

class Size(Enum):
    BRIDGE = Box([2.25, 3.5], Units.INCH)
    POKER = Box([2.5, 3.5], Units.INCH)
    MINI = Box([1.65, 2.5], Units. INCH)
    TAROT = Box([2.75, 4.75], Units.INCH)

Sizes = dict([(x.name, x.value) for x in list(Size)])

def getsize(size):
    if size.__class__ != Box:
        if type(size) in [list, tuple]:
            size = Box(size, Units.INCH)
        else:
            size = Sizes[size]
    return size

