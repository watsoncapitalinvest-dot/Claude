import struct, numpy as np
U='/mnt/user-data/uploads/UFO/'
def palette(i=4):
    d=open(U+'GEODATA/PALETTES.DAT','rb').read()
    p=np.frombuffer(d[i*774:i*774+768],np.uint8).reshape(256,3).astype(np.int32)*4
    return np.clip(p,0,255)
def mcd(name):
    d=open(U+'TERRAIN/'+name+'.MCD','rb').read(); return [bytearray(d[i:i+62]) for i in range(0,len(d),62)]
FIELDS={'frames':(0,8),'loft':(8,20)}
def desc(r):
    return dict(fr=list(r[0:8]),loft=list(r[8:20]),ufodoor=r[30],stoplos=r[31],nofloor=r[32],bigwall=r[33],door=r[35],tuwalk=r[39],armor=r[42],die=r[44],flam=r[45],alt=r[46],tlevel=struct.unpack('b',bytes([r[48]]))[0],plevel=r[49],foot=r[52],ttype=r[53],hetype=r[54],hestr=r[55],fuel=r[57],light=r[58],special=r[59])
