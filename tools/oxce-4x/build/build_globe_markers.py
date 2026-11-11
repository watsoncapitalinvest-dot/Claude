#!/usr/bin/env python3
"""Draw the geoscape markers and write them as indexed PNGs on the geoscape palette.

    python3 build/build_globe_markers.py [--palettes <PALETTES.DAT>]

Writes mod/Resources/Globe/marker_NN_<key>.png (one per marker, 72x72, 8-bit)
and a labelled contact sheet next to this script for eyeballing the set.

The index map, the five legal colours and the reason each one was chosen are
documented in mod/Ruleset/gijoe_globe_markers.rul. Read that before changing a
colour here: the constraint is not aesthetic. Globe::drawTarget blinks a marker
by drawing index+1, so a colour is only usable if its NEIGHBOUR in the palette
is also usable, and index 15 is pure black.
"""
import argparse, math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# The five entries this set is allowed to use, with their geoscape-palette
# indices. Copied here so the script needs no X-COM data to run: PALETTES.DAT
# is original game data and this repository is public. Pass --palettes to check
# these against a real one.
PAL_INDEX = {'COBRA': 13, 'GOLD': 144, 'JOE': 245, 'WHITE': 5, 'DIM': 161}

SS, N = 6, 72                      # supersample, final marker size
U  = SS                            # one design unit at supersample
W  = 3*U                           # standard line weight

# Every one of these is an EXACT entry in the geoscape palette (PALETTES.DAT,
# palette 0), so nothing shifts when the engine draws the marker in 8-bit.
COBRA = (252,   0,   0, 255)   # idx  13 (14 is (192,0,0); 15 is BLACK, and
                               #          Globe::drawTarget blinks to index+1)
GOLD  = (176, 148,  68, 255)   # idx 144 - the only true warm gold in the palette
JOE   = (128, 188, 228, 255)   # idx 245
WHITE = (252, 252, 252, 255)   # idx   5
DIM   = (144, 168, 168, 255)   # idx 161
CREAM = (252, 252, 252, 255)   # idx   5

def pad():  return Image.new('RGBA', (N*SS, N*SS), (0,0,0,0))
def fin(im): return im.resize((N, N), Image.LANCZOS)
C = 36*U                            # centre at supersample

# ---- helpers -------------------------------------------------------------
def dash_ellipse(d, box, colour, width=W, dash=14, gap=12, phase=0.0):
    x0,y0,x1,y1 = box; rx,ry = (x1-x0)/2,(y1-y0)/2; cx,cy = x0+rx, y0+ry
    per = math.pi*(3*(rx+ry) - math.sqrt((3*rx+ry)*(rx+3*ry)))
    steps = max(64, int(per/4)); acc, on, prev = phase, True, None
    for i in range(steps+1):
        a = 2*math.pi*i/steps
        p = (cx+rx*math.cos(a), cy+ry*math.sin(a))
        if prev:
            acc += math.dist(prev,p)
            if on: d.line([prev,p], fill=colour, width=width)
            if acc >= (dash if on else gap): on, acc = not on, 0.0
        prev = p

def dash_path(d, pts, colour, width=W, dash=14, gap=12):
    acc, on, prev = 0.0, True, None
    for p in pts:
        if prev:
            n = max(2, int(math.dist(prev,p)/3))
            for i in range(1, n+1):
                q = (prev[0]+(p[0]-prev[0])*i/n, prev[1]+(p[1]-prev[1])*i/n)
                acc += math.dist(prev if i==1 else last, q); last = q
                if on: d.line([(prev if i==1 else lastdraw), q], fill=colour, width=width)
                lastdraw = q
                if acc >= (dash if on else gap): on, acc = not on, 0.0
        prev = p; last = p; lastdraw = p

def pin_body(d, colour, width=W, fill=None):
    """the teardrop every player pin shares"""
    hx, hy, hr = C, 26*U, 14*U
    d.ellipse([hx-hr,hy-hr,hx+hr,hy+hr], outline=colour, width=width, fill=fill)
    d.line([(hx-9*U, hy+11*U), (hx, 60*U), (hx+9*U, hy+11*U)], fill=colour,
           width=width, joint='curve')

ICONS = {}
def icon(key, group, label, note):
    def deco(fn):
        im = pad(); fn(ImageDraw.Draw(im))
        ICONS[key] = dict(img=fin(im), group=group, label=label, note=note)
        return fn
    return deco

# ======================================================= COBRA — STANDING SITES
@icon('cobra_front_company','Cobra sites','FRONT COMPANY','Extensive Enterprises and the like')
def _(d):
    d.rectangle([16*U,16*U,56*U,60*U], outline=COBRA, width=W)
    for r in range(3):
        for c in range(3):
            d.rectangle([23*U+c*10*U, 23*U+r*10*U, 28*U+c*10*U, 28*U+r*10*U],
                        outline=COBRA, width=2*U)
    d.line([(30*U,60*U),(30*U,52*U),(42*U,52*U),(42*U,60*U)], fill=GOLD, width=W)

@icon('cobra_factory','Cobra sites','WEAPONS FACTORY','M.A.R.S. plant, kit tier source')
def _(d):
    d.line([(10*U,58*U),(10*U,40*U),(22*U,28*U),(22*U,40*U),(34*U,28*U),(34*U,40*U),
            (46*U,28*U),(46*U,58*U)], fill=COBRA, width=W, joint='curve')
    d.line([(10*U,58*U),(62*U,58*U)], fill=COBRA, width=W)
    d.rectangle([52*U,16*U,62*U,58*U], outline=GOLD, width=W)
    d.line([(16*U,50*U),(22*U,50*U)], fill=GOLD, width=2*U)
    d.line([(28*U,50*U),(34*U,50*U)], fill=GOLD, width=2*U)
    d.line([(40*U,50*U),(46*U,50*U)], fill=GOLD, width=2*U)

@icon('cobra_camp','Cobra sites','TRAINING CAMP','lifts the garrison rank gate')
def _(d):
    for ox in (-17*U, 13*U):
        d.line([(C+ox, 22*U), (C+ox-15*U, 54*U), (C+ox+15*U, 54*U), (C+ox, 22*U)],
               fill=COBRA, width=W, joint='curve')
        d.line([(C+ox, 26*U), (C+ox, 54*U)], fill=GOLD, width=2*U)
    d.line([(8*U,58*U),(64*U,58*U)], fill=COBRA, width=W)

@icon('cobra_depot','Cobra sites','SUPPLY DEPOT','materiel store, raid target')
def _(d):
    d.rectangle([14*U,20*U,58*U,56*U], outline=COBRA, width=W)
    d.line([(14*U,20*U),(58*U,56*U)], fill=COBRA, width=2*U)
    d.line([(58*U,20*U),(14*U,56*U)], fill=COBRA, width=2*U)
    d.line([(14*U,28*U),(58*U,28*U)], fill=GOLD, width=2*U)

@icon('cobra_lab','Cobra sites','RESEARCH LAB','one bench, one department')
def _(d):
    d.line([(24*U,12*U),(48*U,12*U)], fill=COBRA, width=W)
    d.line([(29*U,12*U),(29*U,30*U),(13*U,56*U),(59*U,56*U),(43*U,30*U),(43*U,12*U)],
           fill=COBRA, width=W, joint='curve')
    d.line([(21*U,45*U),(51*U,45*U)], fill=GOLD, width=W)

@icon('cobra_drome','Cobra sites','TERROR DROME','four benches, regional suppression')
def _(d):
    for rr in (30*U, 19*U): d.ellipse([C-rr,C-rr,C+rr,C+rr], outline=COBRA, width=W)
    for a in (0,90,180,270):
        r = math.radians(a)
        d.line([(C+13*U*math.cos(r), C+13*U*math.sin(r)),
                (C+35*U*math.cos(r), C+35*U*math.sin(r))], fill=COBRA, width=W)
    d.ellipse([C-6*U,C-6*U,C+6*U,C+6*U], fill=GOLD)

@icon('cobra_broadcast','Cobra sites','BROADCAST STATION','erodes regional goodwill')
def _(d):
    d.line([(26*U,58*U),(C,12*U),(46*U,58*U)], fill=COBRA, width=W, joint='curve')
    d.line([(29*U,44*U),(43*U,44*U)], fill=COBRA, width=2*U)
    for rr in (13*U, 21*U):
        d.arc([C-rr, 16*U-rr, C+rr, 16*U+rr], 200, 340, fill=GOLD, width=W)

@icon('cobra_hq','Cobra sites','HIDDEN HQ','two benches, garrison bonus')
def _(d):
    p = [(C+28*U*math.cos(math.radians(a)), C+28*U*math.sin(math.radians(a)))
         for a in range(0,360,60)]
    d.polygon(p, outline=COBRA, width=W)
    p2 = [(C+15*U*math.cos(math.radians(a)), C+15*U*math.sin(math.radians(a)))
          for a in range(0,360,60)]
    d.polygon(p2, outline=GOLD, width=2*U)
    d.line([(C-15*U,C),(C+15*U,C)], fill=COBRA, width=2*U)

# ============================================================ COBRA — ACTIVITY
@icon('cobra_flight','Cobra activity','CARGO FLIGHT','materiel in transit between regions')
def _(d):
    d.line([(C,8*U),(C+7*U,22*U),(C+7*U,50*U),(C,60*U),(C-7*U,50*U),(C-7*U,22*U),(C,8*U)],
           fill=COBRA, width=W, joint='curve')
    for sx in (-1,1):
        d.line([(C+sx*7*U,28*U),(C+sx*31*U,40*U),(C+sx*31*U,45*U),(C+sx*7*U,41*U)],
               fill=COBRA, width=W, joint='curve')
        d.line([(C+sx*7*U,52*U),(C+sx*17*U,59*U),(C+sx*7*U,58*U)],
               fill=COBRA, width=W, joint='curve')
    d.rectangle([C-5*U,30*U,C+5*U,42*U], outline=GOLD, width=2*U)

@icon('cobra_craft','Cobra activity','COBRA CRAFT','FANG, Rattler, interceptable')
def _(d):
    d.line([(C,6*U),(C+30*U,56*U),(C,44*U),(C-30*U,56*U),(C,6*U)],
           fill=COBRA, width=W, joint='curve')
    d.line([(C,14*U),(C,40*U)], fill=GOLD, width=W)

@icon('cobra_crash','Cobra activity','CRASH SITE','downed craft, recoverable')
def _(d):
    for a in range(0, 360, 45):
        r = math.radians(a); ln = 32*U if a % 90 == 0 else 24*U
        d.line([(C+9*U*math.cos(r), C+9*U*math.sin(r)),
                (C+ln*math.cos(r), C+ln*math.sin(r))], fill=COBRA, width=W)
    d.ellipse([C-10*U,C-10*U,C+10*U,C+10*U], outline=GOLD, width=W)

@icon('cobra_landed','Cobra activity','LANDED CRAFT','on the ground, assaultable')
def _(d):
    d.line([(C,20*U),(C+20*U,44*U),(C-20*U,44*U),(C,20*U)], fill=COBRA, width=W, joint='curve')
    for sx in (-1,1):
        d.line([(C+sx*30*U, 14*U),(C+sx*30*U, 54*U)], fill=GOLD, width=W)
        d.line([(C+sx*30*U, 14*U),(C+sx*20*U, 14*U)], fill=GOLD, width=W)
        d.line([(C+sx*30*U, 54*U),(C+sx*20*U, 54*U)], fill=GOLD, width=W)
    d.line([(C-22*U,52*U),(C+22*U,52*U)], fill=COBRA, width=2*U)

@icon('cobra_terror','Cobra activity','TERROR ATTACK','civilians on the clock')
def _(d):
    for x0,x1,h in ((11,25,24),(28,42,36),(45,61,28)):
        d.rectangle([x0*U, (58-h)*U, x1*U, 58*U], outline=COBRA, width=W)
    d.line([(8*U,58*U),(64*U,58*U)], fill=COBRA, width=W)
    for a in range(0, 360, 45):
        r = math.radians(a-90)
        d.line([(35*U+7*U*math.cos(r), 18*U+7*U*math.sin(r)),
                (35*U+17*U*math.cos(r), 18*U+17*U*math.sin(r))], fill=GOLD, width=W)

@icon('cobra_convoy','Cobra activity','M.A.R.S. CONVOY','stock on the move, not Cobra-funded')
def _(d):
    d.rectangle([8*U,22*U,33*U,44*U], outline=COBRA, width=W)
    d.line([(36*U,44*U),(36*U,30*U),(48*U,30*U),(56*U,38*U),(56*U,44*U),(36*U,44*U)],
           fill=GOLD, width=W, joint='curve')
    d.line([(33*U,36*U),(36*U,36*U)], fill=GOLD, width=2*U)
    for cx in (16,27,42,52):
        d.ellipse([cx*U-5*U,44*U-4*U,cx*U+5*U,44*U+6*U], outline=COBRA, width=2*U)
    d.line([(14*U,30*U),(27*U,30*U)], fill=GOLD, width=2*U)

# ========================================================================= JOE
@icon('joe_pit','G.I. Joe','THE PIT','main base')
def _(d):
    d.ellipse([C-30*U,C-30*U,C+30*U,C+30*U], outline=JOE, width=W)
    d.ellipse([C-21*U,C-21*U,C+21*U,C+21*U], outline=WHITE, width=2*U)
    p = [(C, C-17*U)]
    for k in range(1,5):
        a = math.radians(-90 + k*144)
        p.append((C+17*U*math.cos(a), C+17*U*math.sin(a)))
    d.polygon(p, outline=GOLD, width=W)

@icon('joe_base','G.I. Joe','FORWARD BASE','secondary installation')
def _(d):
    d.ellipse([C-28*U,C-28*U,C+28*U,C+28*U], outline=JOE, width=W)
    d.line([(C-15*U,C+8*U),(C,C-14*U),(C+15*U,C+8*U)], fill=WHITE, width=W, joint='curve')
    d.line([(C-15*U,C+16*U),(C+15*U,C+16*U)], fill=GOLD, width=W)

@icon('joe_craft','G.I. Joe','CRAFT IN FLIGHT','fallback marker; art replaces this')
def _(d):
    d.line([(C,10*U),(C+21*U,50*U),(C,40*U),(C-21*U,50*U),(C,10*U)],
           fill=JOE, width=W, joint='curve')
    d.line([(C,16*U),(C,36*U)], fill=WHITE, width=2*U)

@icon('joe_lz','G.I. Joe','LANDING ZONE','where a craft can set down')
def _(d):
    for sx in (-1,1):
        for sy in (-1,1):
            d.line([(C+sx*30*U, C+sy*16*U),(C+sx*30*U, C+sy*30*U)], fill=JOE, width=W)
            d.line([(C+sx*16*U, C+sy*30*U),(C+sx*30*U, C+sy*30*U)], fill=JOE, width=W)
    d.line([(C-14*U,C),(C+14*U,C)], fill=GOLD, width=W)
    d.line([(C,C-14*U),(C,C+14*U)], fill=GOLD, width=W)

@icon('joe_extract','G.I. Joe','EXTRACTION POINT','get them out')
def _(d):
    d.ellipse([C-29*U,C-29*U,C+29*U,C+29*U], outline=JOE, width=W)
    for k,oy in enumerate((10*U, -2*U)):
        col = GOLD if k else WHITE
        d.line([(C-14*U, C+oy+8*U),(C, C+oy-6*U),(C+14*U, C+oy+8*U)],
               fill=col, width=W, joint='curve')

# ====================================================== PLAYER PINS AND ROUTES
@icon('pin_confirmed',"Player's own board",'PIN — CONFIRMED','he has been there, or intel is hard')
def _(d):
    pin_body(d, GOLD, W, fill=(216,180,90,70))
    d.ellipse([C-5*U,21*U,C+5*U,31*U], fill=GOLD)

@icon('pin_likely',"Player's own board",'PIN — LIKELY','good intel, unverified')
def _(d):
    dash_ellipse(d, [C-14*U,12*U,C+14*U,40*U], GOLD, W, 15, 11)
    d.line([(C-9*U,37*U),(C,60*U),(C+9*U,37*U)], fill=GOLD, width=W, joint='curve')
    d.ellipse([C-4*U,22*U,C+4*U,30*U], fill=GOLD)

@icon('pin_rumour',"Player's own board",'PIN — RUMOUR','a lead, nothing more')
def _(d):
    dash_ellipse(d, [C-14*U,12*U,C+14*U,40*U], DIM, W, 5, 10)
    dash_path(d, [(C-9*U,37*U),(C,60*U)], DIM, W, 6, 7)
    dash_path(d, [(C,60*U),(C+9*U,37*U)], DIM, W, 6, 7)

@icon('pin_note',"Player's own board",'NOTE','a pin with something written on it')
def _(d):
    pin_body(d, GOLD, W)
    d.rectangle([C-7*U,19*U,C+7*U,33*U], outline=GOLD, width=2*U)
    for yy in (23,27,31): d.line([(C-4*U,yy*U),(C+4*U,yy*U)], fill=CREAM, width=2*U)

@icon('pin_unknown',"Player's own board",'UNKNOWN','something is here, he does not know what')
def _(d):
    dash_ellipse(d, [C-26*U,C-26*U,C+26*U,C+26*U], DIM, W, 13, 11)
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34*U)
    except Exception: f = None
    if f: d.text((C, C-2*U), '?', font=f, fill=GOLD, anchor='mm')

@icon('route_start',"Player's own board",'ROUTE START','where a suspected run begins')
def _(d):
    d.line([(20*U,60*U),(20*U,12*U)], fill=GOLD, width=W)
    d.line([(20*U,14*U),(54*U,22*U),(20*U,32*U)], fill=GOLD, width=W, joint='curve')
    d.ellipse([14*U,54*U,26*U,66*U], fill=GOLD)

@icon('route_waypoint',"Player's own board",'WAYPOINT','a bend in a drawn route')
def _(d):
    d.polygon([(C,C-18*U),(C+18*U,C),(C,C+18*U),(C-18*U,C)], outline=GOLD, width=W)
    d.ellipse([C-5*U,C-5*U,C+5*U,C+5*U], fill=GOLD)
    dash_path(d, [(10*U,C),(C-18*U,C)], DIM, 2*U, 6, 6)
    dash_path(d, [(C+18*U,C),(62*U,C)], DIM, 2*U, 6, 6)

@icon('area_interest',"Player's own board",'AREA OF INTEREST','a region he wants watched')
def _(d):
    dash_ellipse(d, [C-30*U,C-22*U,C+30*U,C+22*U], GOLD, W, 16, 12)
    dash_ellipse(d, [C-16*U,C-11*U,C+16*U,C+11*U], DIM, 2*U, 8, 9)
    d.ellipse([C-4*U,C-4*U,C+4*U,C+4*U], fill=GOLD)


# ---------------------------------------------------------------- the output
ORDER = ['cobra_front_company','cobra_factory','cobra_camp','cobra_depot','cobra_lab',
         'cobra_drome','cobra_broadcast','cobra_hq',
         'cobra_flight','cobra_craft','cobra_crash','cobra_landed','cobra_terror','cobra_convoy',
         'joe_pit','joe_base','joe_craft','joe_lz','joe_extract',
         'pin_confirmed','pin_likely','pin_rumour','pin_note','pin_unknown',
         'route_start','route_waypoint','area_interest']
FIRST = 9                       # GlobeMarkers maxSharedFrames; vanilla owns 0-8

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--palettes', default=None,
                    help='optional GEODATA/PALETTES.DAT, to verify the five indices')
    ap.add_argument('--out', default=os.path.join(ROOT, 'mod', 'Resources', 'Globe'))
    a = ap.parse_args()

    BASE = {PAL_INDEX['COBRA']: COBRA[:3], PAL_INDEX['GOLD']: GOLD[:3],
            PAL_INDEX['JOE']:   JOE[:3],   PAL_INDEX['WHITE']: WHITE[:3],
            PAL_INDEX['DIM']:   DIM[:3]}

    if a.palettes:
        raw = open(a.palettes, 'rb').read()
        real = [(min(255, raw[i*3]*4), min(255, raw[i*3+1]*4), min(255, raw[i*3+2]*4))
                for i in range(256)]
        bad = [(i, real[i], c) for i, c in BASE.items() if real[i] != c]
        if bad:
            sys.exit('these are not the colours at those indices in %s: %s'
                     % (a.palettes, bad))
        blink = [(i, real[i+1]) for i in BASE if sum(real[i+1]) < 40]
        if blink:
            sys.exit('drawTarget blinks to index+1 and these land on near-black: %s' % blink)
        print('checked against %s: all five indices exact, all five blink safely' % a.palettes)

    assert set(ORDER) == set(ICONS), set(ORDER) ^ set(ICONS)

    def snap(c):
        best, bd = 13, 1e18
        for i, p in BASE.items():
            rm = (p[0]+c[0])/2
            d = ((2+rm/256)*(p[0]-c[0])**2 + 4*(p[1]-c[1])**2
                 + (2+(255-rm)/256)*(p[2]-c[2])**2)
            if d < bd: bd, best = d, i
        return best

    os.makedirs(a.out, exist_ok=True)
    # Only the five used entries are written into the PNG palette. The engine
    # draws these by index against its own geoscape palette, so the embedded
    # one is just so the file previews correctly outside the game.
    flat = [0]*768
    for i, c in BASE.items(): flat[i*3:i*3+3] = list(c)
    cache = {}
    for n, k in enumerate(ORDER):
        im = ICONS[k]['img']; w, h = im.size; sp = im.load()
        out = Image.new('P', (w, h), 0); op = out.load()
        for y in range(h):
            for x in range(w):
                r, g, b, al = sp[x, y]
                if al < 128: continue                  # index 0 is the colour key
                # un-premultiply against black, or every edge pixel reads as dark
                c = (min(255, r*255//al), min(255, g*255//al), min(255, b*255//al))
                if c not in cache: cache[c] = snap(c)
                op[x, y] = cache[c]
        out.putpalette(flat)
        out.save(os.path.join(a.out, 'marker_%02d_%s.png' % (FIRST+n, k)),
                 transparency=0, optimize=False)
    print('wrote %d markers to %s, frames %d-%d'
          % (len(ORDER), a.out, FIRST, FIRST+len(ORDER)-1))
    contact_sheet(os.path.join(HERE, 'globe_markers_sheet.png'))

def contact_sheet(path):
    try:
        F = '/usr/share/fonts/truetype/dejavu/'
        ft = ImageFont.truetype(F+'DejaVuSerif-Bold.ttf', 34)
        fg = ImageFont.truetype(F+'DejaVuSans-Bold.ttf', 19)
        fl = ImageFont.truetype(F+'DejaVuSans-Bold.ttf', 15)
        fn = ImageFont.truetype(F+'DejaVuSans.ttf', 13)
    except Exception:
        print('no DejaVu fonts here, skipping the contact sheet'); return
    from collections import OrderedDict
    groups = OrderedDict()
    for k in ORDER: groups.setdefault(ICONS[k]['group'], []).append(k)
    COL, CW, ROWH, PADT = 3, 416, 136, 120
    rows = sum(math.ceil(len(v)/COL) for v in groups.values())
    sheet = Image.new('RGB', (COL*CW+60, PADT + rows*ROWH + len(groups)*64 + 60), (23,24,28))
    d = ImageDraw.Draw(sheet)
    d.text((30,34), 'G.I. JOE - GEOSCAPE MARKERS', font=ft, fill=(255,253,251))
    d.text((30,78), 'indexed on the geoscape palette; frame numbers are GlobeMarkers indices',
           font=fn, fill=(150,160,172))
    y = PADT
    for gname, keys in groups.items():
        d.line([(30,y),(COL*CW+30,y)], fill=(70,74,82), width=2)
        d.text((30,y+14), gname.upper(), font=fg, fill=(176,148,68))
        y += 54
        for i, k in enumerate(keys):
            v = ICONS[k]
            cx, cy = 30 + (i % COL)*CW, y + (i // COL)*ROWH
            sheet.paste(v['img'], (cx+14, cy+16), v['img'])
            d.text((cx+104, cy+28), v['label'], font=fl, fill=(255,253,251))
            d.text((cx+104, cy+50), v['note'],  font=fn, fill=(150,160,172))
            d.text((cx+104, cy+70), '%d  %s' % (FIRST+ORDER.index(k), k),
                   font=fn, fill=(96,102,112))
        y += math.ceil(len(keys)/COL)*ROWH + 10
    sheet.save(path); print('contact sheet ->', path)

if __name__ == '__main__':
    main()
