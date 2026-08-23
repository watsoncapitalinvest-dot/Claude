# -*- coding: utf-8 -*-
"""Render the MIDI to a WAV with a small built-in synth, so the theme can be
heard without a soundfont. Not a General MIDI player — four hand-rolled voices
that suit the parts: brass lead, vibes, bass, drum kit."""
import struct, wave, numpy as np

SR = 44100
d = open('scfl-jeopardy-theme.mid','rb').read()
_, fmt, ntr, div = struct.unpack('>IHHH', d[4:14])
pos = 14; tracks = []
for _ in range(ntr):
    tl = struct.unpack('>I', d[pos+4:pos+8])[0]
    tracks.append(d[pos+8:pos+8+tl]); pos += 8+tl

def rvlq(b, i):
    v = 0
    while True:
        v = (v<<7)|(b[i]&0x7F); c = b[i]; i += 1
        if not c & 0x80: return v, i

tempo = 500000; events = []
for tb in tracks:
    i = tick = 0; run = None; live = {}
    while i < len(tb):
        dt, i = rvlq(tb, i); tick += dt
        st = tb[i]
        if st < 0x80: st = run
        else:
            i += 1; run = st if st < 0xF0 else None
        if st == 0xFF:
            mt = tb[i]; i += 1; l, i = rvlq(tb, i); dat = tb[i:i+l]; i += l
            if mt == 0x51: tempo = int.from_bytes(dat, 'big')
            if mt == 0x2F: break
        elif st in (0xF0, 0xF7):
            l, i = rvlq(tb, i); i += l
        else:
            hi, ch = st & 0xF0, st & 0x0F
            nb = 1 if hi in (0xC0, 0xD0) else 2
            a = tb[i:i+nb]; i += nb
            if hi == 0x90 and a[1] > 0: live[(ch, a[0])] = (tick, a[1])
            elif hi in (0x80, 0x90):
                k = (ch, a[0])
                if k in live:
                    t0, v = live.pop(k); events.append((ch, a[0], v, t0, tick - t0))

spt = tempo / 1e6 / div                      # seconds per tick
total = max(t0+dur for _,_,_,t0,dur in events) * spt + 1.1
buf = np.zeros(int(total*SR), dtype=np.float64)

def env(nsm, a, d_, s, r):
    e = np.ones(nsm)
    ai, di, ri = int(a*SR), int(d_*SR), int(r*SR)
    ai = min(ai, nsm); e[:ai] = np.linspace(0, 1, ai, endpoint=False) if ai else e[:ai]
    if di and ai < nsm:
        k = min(di, nsm-ai); e[ai:ai+k] = np.linspace(1, s, k, endpoint=False)
        e[ai+k:] = s
    if ri:
        k = min(ri, nsm); e[nsm-k:] *= np.linspace(1, 0, k)
    return e

def place(sig, t0):
    i = int(t0*SR); j = min(len(buf), i+len(sig))
    buf[i:j] += sig[:j-i]

rng = np.random.default_rng(7)
def freq(p): return 440.0 * 2**((p-69)/12)

for ch, pitch, vel, t0tick, durtick in events:
    t0 = t0tick*spt; dur = max(durtick*spt, 0.05); v = vel/127
    if ch == 9:
        L = {36:0.30, 38:0.22, 42:0.07, 51:0.16, 49:1.30}.get(pitch, 0.30)
        nsm = int(L*SR); t = np.arange(nsm)/SR
        if pitch == 36:                                   # kick
            f = 118*np.exp(-t*26) + 44
            sig = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*11)
        elif pitch == 38:                                 # snare
            sig = (rng.normal(0, 1, nsm)*0.75 + np.sin(2*np.pi*196*t)*0.5) * np.exp(-t*22)
        elif pitch in (42, 51):                           # hat / ride
            nz = rng.normal(0, 1, nsm)
            nz = np.convolve(nz, [1, -0.92], 'same')
            sig = nz * np.exp(-t*(38 if pitch == 42 else 15))
            if pitch == 51: sig += np.sin(2*np.pi*2100*t)*0.10*np.exp(-t*13)
        elif pitch == 49:                                 # crash
            nz = np.convolve(rng.normal(0, 1, nsm), [1, -0.85], 'same')
            sig = nz*np.exp(-t*3.0)
        else:                                             # toms
            f = freq(pitch)*0.55*np.exp(-t*7) + freq(pitch)*0.45
            sig = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*10)
        place(sig*v*0.42, t0); continue

    f = freq(pitch)
    if ch == 0:                                           # brass lead
        L = dur + 0.16; nsm = int(L*SR); t = np.arange(nsm)/SR
        sig = np.zeros(nsm)
        for det, amp in ((1.0, 1.0), (1.004, 0.65), (0.996, 0.65)):
            ph = 2*np.pi*f*det*t
            sig += amp*(2*(ph/(2*np.pi) % 1.0) - 1.0)     # saw
        sig /= 2.3
        sig += 0.22*np.sin(2*np.pi*f*t)
        sig *= env(nsm, 0.018, 0.10, 0.80, 0.14)
        sig = np.convolve(sig, np.ones(9)/9, 'same')      # soften the top
        place(sig*v*0.30, t0)
    elif ch == 1:                                         # vibes
        L = dur + 1.1; nsm = int(L*SR); t = np.arange(nsm)/SR
        trem = 1 + 0.16*np.sin(2*np.pi*5.2*t)
        sig = (np.sin(2*np.pi*f*t) + 0.34*np.sin(2*np.pi*4*f*t)
               + 0.12*np.sin(2*np.pi*9*f*t))
        sig *= np.exp(-t*3.1)*trem
        place(sig*v*0.20, t0)
    else:                                                 # bass
        L = dur + 0.10; nsm = int(L*SR); t = np.arange(nsm)/SR
        ph = (f*t) % 1.0
        sig = 2*np.abs(2*ph - 1) - 1                      # triangle
        sig += 0.30*(2*ph - 1)                            # a little saw
        sig *= env(nsm, 0.010, 0.07, 0.72, 0.09)
        place(sig*v*0.42, t0)

buf = np.tanh(buf*0.85)
buf /= max(1e-9, np.abs(buf).max()); buf *= 0.92
pcm = (buf*32767).astype('<i2')
with wave.open('scfl-jeopardy-theme.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'wrote scfl-jeopardy-theme.wav  {len(pcm)/SR:.1f}s  {len(pcm)*2/1e6:.1f} MB')
