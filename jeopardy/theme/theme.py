# -*- coding: utf-8 -*-
"""SCFL JEOPARDY — main theme. Original cue in the game-show idiom.

Sixteen bars at 124bpm: a two-bar brass fanfare, a sixteen-bar-feel A section
over a walking bass, a lift into the relative minor, and a button. Nothing here
is transcribed from anything; the shape is the genre, the tune is ours.
"""
from midiwrite import Track, write

TPQ = 480
Q, H, E, S, W = TPQ, TPQ*2, TPQ//2, TPQ//4, TPQ*4
BPM = 124

N = {}
for o in range(0, 9):
    for i, nm in enumerate(['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']):
        N[f'{nm}{o}'] = 12 * (o + 1) + i
def n(s): return N[s]

def bar(i): return i * W                      # bar index -> tick

# ---- the harmony: one chord per bar, sixteen bars -------------------------
CHORDS = [
 ('C',  [0,4,7,11]), ('C',  [0,4,7,11]),      # 1-2   fanfare
 ('C',  [0,4,7,11]), ('A',  [0,3,7,10]),      # 3-4   A section
 ('D',  [0,3,7,10]), ('G',  [0,4,7,10]),
 ('C',  [0,4,7,11]), ('A',  [0,3,7,10]),
 ('D',  [0,3,7,10]), ('G',  [0,4,7,10]),      # 9-10
 ('F',  [0,4,7,11]), ('F',  [0,3,7,10]),      # 11-12 the lift
 ('C',  [0,4,7,11]), ('A',  [0,3,7,10]),      # 13-14
 ('D',  [0,3,7,10]), ('G',  [0,4,7,10]),      # 15-16 turnaround / button
]
ROOT = {'C':n('C2'), 'A':n('A1'), 'D':n('D2'), 'G':n('G1'), 'F':n('F1')}

lead  = Track('Lead')
comp  = Track('Comp')
bass  = Track('Bass')
drums = Track('Drums')

lead.tempo(0, BPM); lead.timesig(0, 4, 4)
lead.program(0, 0, 62)    # Synth Brass 1
comp.program(0, 1, 11)    # Vibraphone
bass.program(0, 2, 33)    # Electric Bass (finger)

# ---- 1. the fanfare -------------------------------------------------------
FANFARE = [
 (0.0,'G4',E),(0.5,'C5',E),(1.0,'E5',E),(1.5,'G5',E),(2.0,'C6',H//Q*Q if False else Q+E),
 (3.5,'B5',E),
 (4.0,'C6',Q),(5.0,'G5',E),(5.5,'E5',E),(6.0,'D5',Q+E),(7.5,'D5',E),
]
for beat, p, d in FANFARE:
    lead.note(int(beat*Q), 0, n(p), 118, d)

# ---- 2. the tune ----------------------------------------------------------
# bars 3-10, then restated a step brighter in 13-16
TUNE = [
 # bar 3
 (8.0,'E5',E),(8.5,'G5',E),(9.0,'A5',Q),(10.0,'G5',E),(10.5,'E5',E),(11.0,'D5',Q),
 # bar 4
 (12.0,'C5',E),(12.5,'E5',E),(13.0,'G5',Q),(14.0,'E5',E),(14.5,'C5',E),(15.0,'A4',Q),
 # bar 5
 (16.0,'D5',E),(16.5,'F5',E),(17.0,'A5',Q),(18.0,'F5',E),(18.5,'D5',E),(19.0,'C5',Q),
 # bar 6
 (20.0,'B4',E),(20.5,'D5',E),(21.0,'F5',Q),(22.0,'F5',E),(22.5,'E5',E),(23.0,'D5',Q),
 # bar 7 — the hook
 (24.0,'C5',Q),(25.0,'E5',Q),(26.0,'G5',Q),(27.0,'C6',Q),
 # bar 8
 (28.0,'B5',E),(28.5,'A5',E),(29.0,'G5',Q),(30.0,'E5',H//Q*Q),
 # bar 9
 (32.0,'D5',E),(32.5,'F5',E),(33.0,'A5',Q),(34.0,'C6',E),(34.5,'A5',E),(35.0,'F5',Q),
 # bar 10
 (36.0,'G5',E),(36.5,'B5',E),(37.0,'D6',H),(39.0,'D6',Q),
]
for beat, p, d in TUNE:
    lead.note(int(beat*Q), 0, n(p), 104, d)

# bars 11-12 the lift, up an octave in feel
LIFT = [
 (40.0,'A5',E),(40.5,'C6',E),(41.0,'E6',Q),(42.0,'C6',E),(42.5,'A5',E),(43.0,'G5',Q),
 (44.0,'F5',E),(44.5,'A5',E),(45.0,'C6',Q),(46.0,'A5',E),(46.5,'F5',E),(47.0,'E5',Q),
]
for beat, p, d in LIFT:
    lead.note(int(beat*Q), 0, n(p), 110, d)

# bars 13-16 restatement and button
END = [
 (48.0,'C5',Q),(49.0,'E5',Q),(50.0,'G5',Q),(51.0,'C6',Q),
 (52.0,'B5',E),(52.5,'A5',E),(53.0,'G5',Q),(54.0,'A5',E),(54.5,'B5',E),(55.0,'C6',Q),
 (56.0,'D6',E),(56.5,'C6',E),(57.0,'B5',Q),(58.0,'A5',E),(58.5,'G5',E),(59.0,'F5',Q),
 (60.0,'E5',E),(60.5,'G5',E),(61.0,'C6',H),
]
for beat, p, d in END:
    lead.note(int(beat*Q), 0, n(p), 112, d)
# the button
for p in ('C4','E4','G4','C5','E5'):
    lead.note(int(63.0*Q), 0, n(p), 120, Q)

# ---- 3. comp, bass, drums -------------------------------------------------
for i, (root, ivs) in enumerate(CHORDS):
    t0, r = bar(i), ROOT[root]
    # vibes: offbeat stabs, skip the fanfare bars
    if i >= 2:
        for beat in (1.5, 3.5):
            for iv in ivs:
                comp.note(t0 + int(beat*Q), 1, r + 24 + iv, 62, E)
    else:
        for iv in ivs:
            comp.note(t0, 1, r + 24 + iv, 78, H)
    # walking bass: root, fifth, octave, approach
    walk = [0, 7, 12, ivs[1]] if i >= 2 else [0, 0, 7, 7]
    for k, iv in enumerate(walk):
        bass.note(t0 + k*Q, 2, r + iv, 96, Q - 20)

for i in range(16):
    t0 = bar(i)
    if i < 2:
        for beat in (0.0, 1.0, 2.0, 3.0):
            drums.note(t0 + int(beat*Q), 9, 49 if beat == 0 else 42, 90, E)
        drums.note(t0, 9, 36, 110, Q)
        continue
    for beat in range(4):                       # ride
        drums.note(t0 + beat*Q, 9, 51, 74, E)
        if beat % 2 == 1: drums.note(t0 + beat*Q + E, 9, 51, 58, E)
    drums.note(t0,        9, 36, 108, Q)        # kick
    drums.note(t0 + 2*Q,  9, 36,  98, Q)
    drums.note(t0 + 1*Q,  9, 38, 100, Q)        # snare on 2 and 4
    drums.note(t0 + 3*Q,  9, 38, 100, Q)
    if i in (9, 15):                            # fills
        for k, p in enumerate((48, 47, 45, 43)):
            drums.note(t0 + 3*Q + k*S, 9, p, 104, S)
drums.note(bar(15) + 3*Q, 9, 49, 118, Q)        # crash on the button

write('scfl-jeopardy-theme.mid', [lead, comp, bass, drums], TPQ)
print('wrote scfl-jeopardy-theme.mid')
