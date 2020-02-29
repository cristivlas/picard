from argparse import ArgumentParser
from card import Card
from PIL import Image, ImageOps, ImageDraw
import math
import cache
import pathlib

cuts_size = None
bleed = 1

class Sheet:
    def __init__(self, size, dpi):
        self.paperSize = size
        self.dpi = dpi
        card_size = [ bleed * s for s in cuts_size ]
        self.size = [int (i * dpi) for i in size]
        self.ncards = [int(i / j) for i, j in zip(self.size, card_size)]
        self.ncards.append(self.ncards[0]*self.ncards[1])
        self.cards = []

    def addCard(self, card):
        if len(self.cards) >= self.ncards[2]:
            print 'Sheet full:', self.ncards[2], 'cards'
            return False;
        self.cards.append(card)
        return True

    def render(self, flip=False):
        card_size = [ bleed * s for s in cuts_size ]
        self.image = Image.new('RGB', self.size, 'white')
        size = [int(math.floor(wh*n)) for wh,n in zip(card_size, self.ncards[:2])]
        dim = [s/n for s, n in zip(size, self.ncards)]
        draw = ImageDraw.Draw(self.image)
                
        # draw the cut marks
        def draw_line(xy):
            draw.line(xy, fill='black', width=2)

        x,y = [math.ceil((d - c)/2 + (ss - si)/2) for d, c, ss, si, in zip(dim, cuts_size, self.size, size)]
        count = 0
        for card in self.cards:
            if count % self.ncards[0] == 0:
                draw_line((0, y, self.size[0], y))
            draw_line((x, 0, x, self.size[1]))
            draw_line((x+cuts_size[0], 0, x+cuts_size[0], self.size[1]))
            x += dim[0]
            count += 1
            if count % self.ncards[0] == 0:
                x = math.ceil((dim[0] - cuts_size[0])/2 + (self.size[0]-size[0])/2)
                draw_line((0, y+cuts_size[1], self.size[0], y+cuts_size[1]))
                y += dim[1]
        draw_line((0, y+cuts_size[1], self.size[0], y+cuts_size[1]))
        
        image = Image.new('RGBA', size, 'white')
        dim = [s/n for s, n in zip(image.size, self.ncards)]

        # draw the card images
        x,y = [math.ceil((d - c)/2) for d, c in zip(dim, card_size)]
        count = 0
        for card in self.cards:
            if flip:
                card = ImageOps.mirror(card)
            card = card.resize([int(i) for i in card_size], Image.LANCZOS)
            image.paste(card, [int(x),int(y)], card)
            x += dim[0]
            count += 1
            if count % self.ncards[0] == 0:
                x = math.ceil((dim[0] - card_size[0])/2)
                y += dim[1]
        if flip:
            image = ImageOps.mirror(image)
        self.image.paste(image, [(ss-si)/2 for ss, si in zip(self.size, size)])

def finishSheet(sheets, s):
    if len(s.cards) == 0:
        return None
    sheets.append(s)
    return Sheet(s.paperSize, s.dpi)

def makeSheets(cards, paperSize, dpi):
    sheets = []
    front = Sheet(paperSize, dpi)
    back = Sheet(paperSize, dpi)
    for c in cards:
        image = c.front()
        if not front.addCard(image):
            front = finishSheet(sheets, front)
            back = finishSheet(sheets, back)
            front.addCard(image)
        image = c.back()
        assert back.addCard(image)
    finishSheet(sheets, front)
    finishSheet(sheets, back)

    for i, s in enumerate(sheets):
        s.render(flip=i%2)
    return sheets

def renderCards(cards, fname, paperSize, dpi):
    print 'Rendering', len(cards), 'cards'
    sheets = makeSheets(cards, paperSize, dpi)
    numPages = len(sheets)
    print fname + ':', numPages, 'pages'
    if numPages:
        images = [x.image for x in sheets]
        images[0].save(fname, save_all=True, append_images=images[1:], resolution=dpi)

def parseArgs():
    ap = ArgumentParser(description='Render game cards as PDF pages')
    ap.add_argument('dir', help="input directory of JSON files")
    ap.add_argument('--pdf', help="filename of PDF output")
    ap.add_argument('--bleed', default=1.035, help="scale factor for bleed area")
    ap.add_argument('--dpi', default=300)
    ap.add_argument('--paper', choices=['letter', 'A4'], default='letter')
    return ap.parse_args()

if __name__ == '__main__':
    args = parseArgs()
    cache.DataPath = args.dir
    bleed = float(args.bleed)
    dpi = int(args.dpi)
    paper_size = {
        'letter': [8.5, 11.0],
        'A4': [8.27, 11.69]
    }
    cards = []
    for i in pathlib.Path(args.dir).iterdir():
        if i.suffix == '.json':
            c = Card.load(str(i), dpi)
            cards.append(c)
            card_size = c.size.convert(dpi=dpi).box[2:]
            assert cuts_size is None or cuts_size==card_size
            cuts_size = card_size
    if len(cards):
        fname = args.pdf
        if not fname:
            fname = pathlib.Path(args.dir).name + '.pdf'
        renderCards(cards, fname, paper_size[args.paper], dpi)

