from PIL import Image, ImageDraw
import os
W,H=30,46
def P(): return Image.new('RGBA',(W,H),(0,0,0,0))

def sh(c,f): return tuple(max(0,min(255,int(v*f))) for v in c[:3])

def figure(body, trim, skin, head='bare', hair=None, cape=None, bulk=0,
           shoulder=None, visor=None, belt=None):
    im=P(); d=ImageDraw.Draw(im)
    cx=W//2
    bw=5+bulk                                   # half-width of the torso
    if cape:
        # behind the shoulders and flaring out, not a slab over the whole man.
        # Drawn full width it read as a hood - Overlord came out as a red blob.
        d.polygon([(cx-bw,16),(cx+bw,16),(cx+bw+3,38),(cx-bw-3,38)],fill=sh(cape,.72))
        d.polygon([(cx-bw+1,17),(cx+bw-1,17),(cx+bw+1,37),(cx-bw-1,37)],fill=cape)
        d.line([(cx-bw-3,38),(cx+bw+3,38)],fill=sh(cape,.55))
    # legs
    for s in (-1,1):
        d.rectangle([cx+s*2-2 if s<0 else cx+1, 33, cx-1 if s<0 else cx+3, 43],fill=sh(body,.78))
        d.rectangle([cx+s*2-2 if s<0 else cx+1, 43, cx-1 if s<0 else cx+3, 45],fill=(34,32,34))
    # torso
    d.rectangle([cx-bw,17,cx+bw,34],fill=body)
    d.rectangle([cx-bw,17,cx-bw+1,34],fill=sh(body,1.18))
    d.rectangle([cx+bw-1,17,cx+bw,34],fill=sh(body,.76))
    if belt: d.rectangle([cx-bw,30,cx+bw,32],fill=belt)
    d.rectangle([cx-1,18,cx+1,29],fill=trim)     # chest stripe / sigil field
    if shoulder:
        d.rectangle([cx-bw-2,16,cx-bw+1,21],fill=shoulder)
        d.rectangle([cx+bw-1,16,cx+bw+2,21],fill=shoulder)
    # arms
    for s in (-1,1):
        x0=cx+s*(bw+2)-1 if s<0 else cx+bw+1
        d.rectangle([x0,18,x0+1,30],fill=sh(body,.72))
        d.line([(x0,18),(x0,30)],fill=sh(body,.95))
        d.rectangle([x0,30,x0+1,33],fill=sh(skin,.95) if head in ('bare','hair') else sh(body,.7))
    # head
    hx0,hx1,hy0,hy1=cx-3,cx+3,8,16
    if head=='bare' or head=='hair':
        d.rectangle([hx0,hy0,hx1,hy1],fill=skin)
        if hair: d.rectangle([hx0,hy0,hx1,hy0+2],fill=hair)
        d.rectangle([cx-2,hy0+4,cx-1,hy0+5],fill=(40,36,34)); d.rectangle([cx+1,hy0+4,cx+2,hy0+5],fill=(40,36,34))
    elif head=='hood':
        d.rectangle([hx0-1,hy0-1,hx1+1,hy1],fill=body)
        d.rectangle([hx0,hy0+3,hx1,hy0+6],fill=sh(body,.5))
        if visor: d.rectangle([hx0,hy0+4,hx1,hy0+5],fill=visor)
    elif head=='helm':
        d.rectangle([hx0-1,hy0-1,hx1+1,hy1],fill=trim)
        d.rectangle([hx0-1,hy0-1,hx1+1,hy0+1],fill=sh(trim,1.2))
        d.rectangle([hx0,hy0+4,hx1,hy0+6],fill=visor or (40,42,48))
    elif head=='mask':
        d.rectangle([hx0,hy0,hx1,hy1],fill=trim)
        d.rectangle([hx0,hy0+4,hx1,hy0+5],fill=visor or (26,26,28))
    elif head=='chrome':
        d.rectangle([hx0,hy0,hx1,hy1],fill=(196,200,206))
        d.rectangle([hx0,hy0,hx0+1,hy1],fill=(236,238,242))
        d.rectangle([hx1-1,hy0,hx1,hy1],fill=(140,144,150))
    elif head=='crest':
        d.rectangle([hx0,hy0,hx1,hy1],fill=trim)
        d.polygon([(cx,hy0-5),(cx+4,hy0),(cx-4,hy0)],fill=sh(trim,1.3))
        d.rectangle([hx0,hy0+4,hx1,hy0+5],fill=visor or (30,30,32))
    d.rectangle([cx-2,16,cx+2,17],fill=sh(skin,.8) if head in ('bare','hair') else sh(body,.7))
    return im

RED=(176,30,34); CRIM=(150,22,30); BLU=(42,62,132); LBLU=(70,96,172); BLK=(36,36,40)
GRY=(104,108,114); SIL=(186,190,196); WHT=(228,230,232); GRN=(62,104,58); OLI=(104,116,74)
PUR=(96,56,128); ORG=(192,104,36); TAN=(168,142,96); BRN=(104,76,48); GLD=(198,164,66)
SKIN=(206,168,134); SKIN2=(150,110,80); PNK=(206,96,132); CYA=(82,150,170); YEL=(214,186,60)

# (key, label, kwargs, confidence)  confidence: 1 sure, 0 roughly
C=[
 ('cobra_commander','Cobra Commander',dict(body=BLU,trim=SIL,skin=SKIN,head='hood',visor=SIL,belt=BLK),1),
 ('major_bludd','Major Bludd',dict(body=BRN,trim=TAN,skin=SKIN,head='helm',visor=BLK,shoulder=GRY,bulk=1),1),
 ('destro','Destro',dict(body=BLK,trim=RED,skin=SKIN,head='chrome',belt=RED,shoulder=BLK),1),
 ('baroness','The Baroness',dict(body=BLK,trim=BLK,skin=SKIN,head='hair',hair=BLK,belt=GRY),1),
 ('tomax','Tomax',dict(body=CRIM,trim=WHT,skin=SKIN,head='bare',hair=(60,44,34),belt=BLK),1),
 ('xamot','Xamot',dict(body=CRIM,trim=WHT,skin=SKIN,head='bare',hair=(60,44,34),belt=BLK),1),
 ('storm_shadow','Storm Shadow',dict(body=WHT,trim=WHT,skin=SKIN,head='mask',visor=(60,60,64)),1),
 ('zartan','Zartan',dict(body=(118,110,96),trim=PUR,skin=(176,168,150),head='hood',visor=(60,56,70)),1),
 ('firefly','Firefly',dict(body=GRY,trim=(72,76,80),skin=SKIN,head='mask',visor=(40,42,46)),1),
 ('wild_weasel','Wild Weasel',dict(body=RED,trim=(60,60,64),skin=SKIN,head='helm',visor=(60,70,90)),1),
 ('scrap_iron','Scrap-Iron',dict(body=(84,86,90),trim=(54,56,60),skin=SKIN,head='mask',visor=(150,150,60)),1),
 ('copperhead','Copperhead',dict(body=ORG,trim=BRN,skin=SKIN,head='hair',hair=(50,40,32),belt=BRN),1),
 ('buzzer','Buzzer',dict(body=(62,84,140),trim=(200,190,120),skin=SKIN,head='hair',hair=YEL),1),
 ('ripper','Ripper',dict(body=(74,96,148),trim=ORG,skin=SKIN,head='hair',hair=(60,46,34)),1),
 ('torch','Torch',dict(body=(150,120,80),trim=ORG,skin=SKIN,head='hair',hair=(70,52,38),bulk=1),1),
 ('dr_mindbender','Dr. Mindbender',dict(body=(140,96,70),trim=PUR,skin=SKIN,head='bare',hair=(50,40,36),cape=RED),1),
 ('serpentor','Serpentor',dict(body=GRN,trim=GLD,skin=SKIN2,head='crest',visor=(40,40,36),cape=(88,40,40)),1),
 ('big_boa','Big Boa',dict(body=RED,trim=BLK,skin=SKIN,head='mask',visor=(60,60,64),bulk=2),1),
 ('croc_master','Croc Master',dict(body=(70,96,62),trim=BLK,skin=SKIN,head='bare',hair=(44,38,32),bulk=1),1),
 ('crystal_ball','Crystal Ball',dict(body=PUR,trim=WHT,skin=SKIN,head='bare',hair=WHT,cape=(70,40,96)),0),
 ('raptor','Raptor',dict(body=TAN,trim=BRN,skin=SKIN,head='crest',visor=(60,48,36)),1),
 ('zarana','Zarana',dict(body=(110,96,118),trim=PNK,skin=SKIN,head='hair',hair=ORG),1),
 ('zandar','Zandar',dict(body=(104,96,112),trim=PUR,skin=SKIN,head='mask',visor=(60,56,66)),1),
 ('monkeywrench','Monkeywrench',dict(body=(150,122,86),trim=(70,66,62),skin=SKIN,head='hair',hair=(56,44,34)),0),
 ('thrasher','Thrasher',dict(body=(70,92,140),trim=ORG,skin=SKIN,head='helm',visor=(50,52,58)),0),
 ('zanzibar','Zanzibar',dict(body=(132,110,74),trim=RED,skin=SKIN,head='hair',hair=(60,46,34)),0),
 ('road_pig','Road Pig',dict(body=(120,104,88),trim=(80,70,60),skin=SKIN,head='mask',visor=(40,40,42),bulk=3),1),
 ('gnawgahyde','Gnawgahyde',dict(body=TAN,trim=BRN,skin=SKIN,head='hair',hair=(180,164,120)),0),
 ('overkill','Overkill',dict(body=(120,126,136),trim=(70,110,150),skin=SIL,head='helm',visor=RED,bulk=1),1),
 ('voltar','Voltar',dict(body=(74,100,64),trim=GLD,skin=SKIN,head='helm',visor=(40,40,36)),0),
 ('darklon','Darklon',dict(body=(96,100,110),trim=SIL,skin=SKIN,head='helm',visor=(150,60,60),shoulder=SIL,bulk=1),0),
 ('metal_head','Metal-Head',dict(body=(96,100,106),trim=SIL,skin=SKIN,head='helm',visor=(90,170,170)),0),
 ('overlord','Overlord',dict(body=BLK,trim=RED,skin=SKIN,head='helm',visor=RED,shoulder=RED,bulk=1),0),
 ('headman','Headman',dict(body=(80,70,96),trim=WHT,skin=SKIN2,head='bare',hair=BLK),0),
 ('gristle','Gristle',dict(body=(96,88,74),trim=(60,56,50),skin=SKIN,head='bare',hair=(44,38,32),bulk=1),0),
 ('slice','Slice',dict(body=(60,74,130),trim=SIL,skin=SKIN,head='mask',visor=SIL),0),
 ('dice','Dice',dict(body=(132,44,46),trim=BLK,skin=SKIN,head='mask',visor=(40,38,40)),0),
 ('vypra','Vypra',dict(body=BLK,trim=RED,skin=SKIN,head='hair',hair=BLK,belt=RED),0),
 ('cesspool','Cesspool',dict(body=(86,110,66),trim=YEL,skin=SKIN,head='bare',hair=(60,54,44)),0),
 ('the_interrogator','The Interrogator',dict(body=(90,94,100),trim=(60,62,68),skin=SKIN,head='helm',visor=(90,160,180)),0),
]
E=[
 ('crimson_guard','Crimson Guard',dict(body=CRIM,trim=WHT,skin=SKIN,head='helm',visor=WHT),1),
 ('crimson_guard_commander','CG Commander',dict(body=CRIM,trim=GLD,skin=SKIN,head='helm',visor=WHT,shoulder=GLD),1),
 ('crimson_guard_immortal','CG Immortal',dict(body=CRIM,trim=SIL,skin=SKIN,head='helm',visor=SIL,bulk=1),1),
 ('bat','B.A.T.',dict(body=(118,122,128),trim=(170,80,40),skin=SIL,head='helm',visor=RED,bulk=1),1),
 ('iron_grenadier','Iron Grenadier',dict(body=BLK,trim=GLD,skin=SKIN,head='helm',visor=GLD,shoulder=GLD),1),
 ('annihilator','Annihilator',dict(body=BLK,trim=GLD,skin=SKIN,head='helm',visor=(120,160,80),bulk=1),0),
 ('targat','T.A.R.G.A.T.',dict(body=SIL,trim=(120,124,130),skin=SIL,head='helm',visor=(80,120,160),bulk=2),0),
 ('night_creeper','Night Creeper',dict(body=(40,44,52),trim=(60,64,74),skin=SKIN,head='mask',visor=(70,80,96)),1),
 ('night_creeper_leader','Night Creeper Leader',dict(body=(44,48,58),trim=GLD,skin=SKIN,head='mask',visor=GLD),0),
 ('red_ninja','Red Ninja',dict(body=(140,36,38),trim=BLK,skin=SKIN,head='mask',visor=(40,36,38)),1),
 ('ninja_viper','Ninja-Viper',dict(body=(52,56,64),trim=RED,skin=SKIN,head='mask',visor=RED),0),
 ('alley_viper','Alley Viper',dict(body=ORG,trim=(56,78,140),skin=SKIN,head='helm',visor=(70,90,150),shoulder=(56,78,140),bulk=1),1),
 ('headhunter','Headhunter Stormtrooper',dict(body=(70,74,82),trim=(150,60,60),skin=SKIN,head='helm',visor=(150,60,60)),0),
]
Y=[
 ('cobra_recruit','Cobra Recruit',dict(body=(96,92,88),trim=(70,68,66),skin=SKIN,head='bare',hair=(60,50,42)),1),
 ('cobra_soldier','Cobra Soldier',dict(body=LBLU,trim=BLK,skin=SKIN,head='mask',visor=(40,42,50)),1),
 ('cobra_officer','Cobra Officer',dict(body=LBLU,trim=RED,skin=SKIN,head='mask',visor=(40,42,50),belt=RED),1),
 ('viper_pilot','Viper Pilot',dict(body=(58,80,150),trim=SIL,skin=SKIN,head='helm',visor=(90,120,170)),1),
 ('stinger_driver','Stinger Driver',dict(body=(70,86,120),trim=TAN,skin=SKIN,head='helm',visor=(60,64,70)),1),
]

D='/mnt/user-data/outputs/cobra'
ALL=[('villain',C),('elite',E),('year1',Y)]
n=0
for grp,lst in ALL:
    for key,label,kw,conf in lst:
        figure(**kw).save(os.path.join(D,'c_%s.png'%key)); n+=1
print('drew',n,'figures')
import json
json.dump([[g,k,l,c] for g,lst in ALL for k,l,_,c in lst], open('/tmp/cobra_index.json','w'))
