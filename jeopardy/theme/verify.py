"""Parse the MIDI back and check it is well-formed and musically sane."""
import struct, collections
d=open('scfl-jeopardy-theme.mid','rb').read()
assert d[:4]==b'MThd', 'bad header'
ln,fmt,ntr,div = struct.unpack('>IHHH', d[4:14])
print(f'format {fmt}, {ntr} tracks, {div} ticks/quarter')
pos=14; tracks=[]
for t in range(ntr):
    assert d[pos:pos+4]==b'MTrk', f'track {t} bad'
    tl=struct.unpack('>I', d[pos+4:pos+8])[0]
    tracks.append(d[pos+8:pos+8+tl]); pos+=8+tl
assert pos==len(d), f'trailing bytes: {len(d)-pos}'
def rvlq(b,i):
    v=0
    while True:
        v=(v<<7)|(b[i]&0x7F); c=b[i]; i+=1
        if not c&0x80: return v,i
tempo=None; allnotes=[]
for ti,tb in enumerate(tracks):
    i=0; tick=0; run=None; on=collections.Counter(); notes=[]
    while i<len(tb):
        dt,i=rvlq(tb,i); tick+=dt
        st=tb[i]
        if st<0x80: st=run
        else: i+=1; run=st if st<0xF0 else None
        if st==0xFF:
            mt=tb[i]; i+=1; l,i=rvlq(tb,i); data=tb[i:i+l]; i+=l
            if mt==0x51: tempo=int.from_bytes(data,'big')
            if mt==0x2F: break
        elif st in (0xF0,0xF7):
            l,i=rvlq(tb,i); i+=l
        elif 0x80<=st<0xF0:
            hi=st&0xF0
            nb=1 if hi in (0xC0,0xD0) else 2
            args=tb[i:i+nb]; i+=nb
            if hi==0x90 and args[1]>0: on[args[0]]+=1; notes.append((tick,args[0],args[1]))
            elif hi==0x80 or (hi==0x90 and args[1]==0): on[args[0]]-=1
    stuck={k:v for k,v in on.items() if v!=0}
    print(f'  track {ti}: {len(notes):3d} notes, last tick {tick:5d}, stuck notes: {stuck or "none"}')
    assert not stuck, f'track {ti} has hanging notes'
    allnotes+=notes
bpm=round(60_000_000/tempo,1) if tempo else None
end=max(t for t,_,_ in allnotes)
print(f'tempo {bpm} bpm  |  {len(allnotes)} notes total  |  length ~{end/div*60/bpm:.1f}s')
lo=min(p for _,p,_ in allnotes); hi=max(p for _,p,_ in allnotes)
print(f'pitch range MIDI {lo}-{hi}')
print('VALID')
