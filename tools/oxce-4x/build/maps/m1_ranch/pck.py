#!/usr/bin/env python3
"""Read X-COM's PCK sprite packs (UFO format) into index arrays.

Each frame starts with one byte: the number of fully transparent rows to skip.
Then a byte stream: 0xFE n skips n transparent pixels, 0xFF ends the frame, and
any other byte is a pixel's palette index. The TAB file holds each frame's start
offset in the PCK as a little-endian 16-bit word.
"""
import struct
import numpy as np


def read_pck(pck_path, tab_path, w, h):
    data = open(pck_path, 'rb').read()
    tab = open(tab_path, 'rb').read()
    offs = [struct.unpack_from('<H', tab, i)[0] for i in range(0, len(tab) - 1, 2)]
    frames = []
    for n, o in enumerate(offs):
        end = offs[n + 1] if n + 1 < len(offs) else len(data)
        img = np.zeros((h, w), np.uint8)
        i = o
        pos = data[i] * w
        i += 1
        while i < end:
            b = data[i]
            if b == 0xFF:
                break
            if b == 0xFE:
                pos += data[i + 1]
                i += 2
                continue
            if pos < w * h:
                img[pos // w, pos % w] = b
            pos += 1
            i += 1
        frames.append(img)
    return frames
