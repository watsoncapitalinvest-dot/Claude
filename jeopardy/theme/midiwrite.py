# -*- coding: utf-8 -*-
"""A dependency-free MIDI writer. Format 1, one track per part."""
import struct

def vlq(n):
    """MIDI variable-length quantity."""
    out = [n & 0x7F]; n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80); n >>= 7
    return bytes(reversed(out))

class Track:
    def __init__(self, name=None):
        self.ev = []            # (abs_tick, order, bytes)
        self._n = 0
        if name:
            b = name.encode(); self.raw(0, b'\xFF\x03' + vlq(len(b)) + b)
    def raw(self, tick, data):
        self.ev.append((tick, self._n, data)); self._n += 1
    def program(self, tick, ch, prog): self.raw(tick, bytes([0xC0 | ch, prog]))
    def tempo(self, tick, bpm):
        us = int(60_000_000 / bpm)
        self.raw(tick, b'\xFF\x51\x03' + us.to_bytes(3, 'big'))
    def timesig(self, tick, n, d):
        import math
        self.raw(tick, b'\xFF\x58\x04' + bytes([n, int(math.log2(d)), 24, 8]))
    def note(self, tick, ch, pitch, vel, dur):
        # note-offs sort before note-ons at the same tick so repeats retrigger
        self.ev.append((tick,        self._n, bytes([0x90 | ch, pitch, vel]))); self._n += 1
        self.ev.append((tick + dur, -1,       bytes([0x80 | ch, pitch, 0])))
    def build(self):
        evs = sorted(self.ev, key=lambda e: (e[0], e[1]))
        out, last = bytearray(), 0
        for tick, _, data in evs:
            out += vlq(tick - last) + data; last = tick
        out += vlq(0) + b'\xFF\x2F\x00'
        return b'MTrk' + struct.pack('>I', len(out)) + bytes(out)

def write(path, tracks, tpq=480):
    head = b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), tpq)
    with open(path, 'wb') as f:
        f.write(head)
        for t in tracks: f.write(t.build())
