#!/usr/bin/env python3
"""Battle effects (ART, 12 Nov: art_briefs/returned/battle_effects, brief claude/BRIEF_ART_BattleEffects.txt)
into the engine's own effect sets. No new engine systems: each picture goes into the frame the engine
already plays, as an 8-bit stand-in plus its full-colour <file>_rgb.png twin (HiColor draws the twin).

    python3 build/install_battle_effects.py

  X1.PCK (explosions, 4x frames 512 x 256, the art fitted to 256 px tall and centred)
      0-7   explosion_grenade   (stock explosives, hitAnimation 0)
      8-15  explosion_big       (rockets, HE rounds, C-4: hitAnimation 8)
      16-23 explosion_fire      (incendiary: hitAnimation 16)
      24-31 explosion_gas       (smoke grenade: hitAnimation 24)
  SMOKE.PCK (128 x 160)
      0-3   fire_big            (a burning tile; the engine has one fire, not two sizes)
      8-23  smoke_1..smoke_4    (constants extendedSmokeOffset: 1 = four densities of four frames)
      26-35 hit_bullet          (10 frames: the 4 delivered, each held 2-3 frames)
      36-45 hit_laser_blue      (lasers)
      46-55 hit_laser_red       (Cobra pulse weapons)
  HIT.PCK (128 x 160)
      0-3   hit_melee
Not wired yet (need engine work): cursors, path dots, tracers, rockets in flight, muzzle flash.
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_weapon_sprites as mws

ROOT = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.join(ROOT, 'art_briefs', 'returned', 'battle_effects')
OUT = os.path.join(ROOT, 'mod', 'Resources', 'Effects')
RUL = os.path.join(ROOT, 'mod', 'Ruleset', 'gijoe_battle_effects.rul')


def frames(name):
    d = os.path.join(SRC, name)
    return [Image.open(os.path.join(d, f)).convert('RGBA') for f in sorted(os.listdir(d)) if f.endswith('.png')]


def stretch(seq, n):
    return [seq[min(len(seq) - 1, i * len(seq) // n)] for i in range(n)]


def x1_frame(im):
    """128x160 art -> 512x256: scaled to 256 tall about its own centre."""
    s = 256 / 160
    big = im.resize((round(128 * s), 256), Image.LANCZOS)
    out = Image.new('RGBA', (512, 256), (0, 0, 0, 0))
    out.alpha_composite(big, ((512 - big.width) // 2, 0))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    pal, legal, lp = mws.palette_and_legal()
    plan = {'X1.PCK': [], 'SMOKE.PCK': [], 'HIT.PCK': []}
    for base, name in ((0, 'explosion_grenade'), (8, 'explosion_big'), (16, 'explosion_fire'), (24, 'explosion_gas')):
        for i, im in enumerate(stretch(frames(name), 8)):
            plan['X1.PCK'].append((base + i, f'x1_{base + i:02d}', x1_frame(im)))
    for i, im in enumerate(stretch(frames('fire_big'), 4)):
        plan['SMOKE.PCK'].append((i, f'smoke_{i:02d}', im))
    for lvl in range(4):
        for i, im in enumerate(stretch(frames(f'smoke_{lvl + 1}'), 4)):
            n = 8 + lvl * 4 + i
            plan['SMOKE.PCK'].append((n, f'smoke_{n:02d}', im))
    for base, name in ((26, 'hit_bullet'), (36, 'hit_laser_blue'), (46, 'hit_laser_red')):
        for i, im in enumerate(stretch(frames(name), 10)):
            plan['SMOKE.PCK'].append((base + i, f'smoke_{base + i:02d}', im))
    for i, im in enumerate(stretch(frames('hit_melee'), 4)):
        plan['HIT.PCK'].append((i, f'hit_{i:02d}', im))

    lines = ['# Battle effects: ART\'s cartoon explosions, fire, smoke and hits in the engine\'s own effect frames.',
             '# Written by build/install_battle_effects.py - edit the script, not this file.', 'extraSprites:']
    for setname, entries in plan.items():
        w, h = entries[0][2].size
        lines += [f'  - type: {setname}', f'    width: {w}', f'    height: {h}', '    files:']
        for n, stem, im in entries:
            a = np.asarray(im).copy()
            a8 = a.copy(); a8[..., 3] = np.where(a8[..., 3] > 100, 255, 0)
            mws.quantise(Image.fromarray(a8, 'RGBA'), pal, legal, lp).save(os.path.join(OUT, stem + '.png'))
            im.save(os.path.join(OUT, stem + '_rgb.png'))
            lines.append(f'      {n}: Resources/Effects/{stem}.png')
    lines += ['constants:', '  extendedSmokeOffset: 1   # smoke frames 8-23: four densities of four frames']
    # which explosion each weapon plays (X1 frame) and which hit each bullet plays (SMOKE frame)
    hits = {8: ['STR_SMALL_ROCKET', 'STR_LARGE_ROCKET', 'STR_HIGH_EXPLOSIVE', 'STR_HC_HE_AMMO', 'STR_AC_HE_AMMO',
                'STR_ALIEN_GRENADE', 'STR_BLASTER_BOMB'],
            16: ['STR_INCENDIARY_ROCKET', 'STR_HC_I_AMMO', 'STR_AC_I_AMMO'],
            24: ['STR_SMOKE_GRENADE'],
            26: ['STR_PISTOL_CLIP', 'STR_RIFLE_CLIP', 'STR_HC_AP_AMMO', 'STR_AC_AP_AMMO'],
            36: ['STR_LASER_PISTOL', 'STR_LASER_RIFLE', 'STR_HEAVY_LASER'],
            46: ['STR_PLASMA_PISTOL_CLIP', 'STR_PLASMA_RIFLE_CLIP', 'STR_HEAVY_PLASMA_CLIP']}
    lines.append('items:')
    for frame, items in hits.items():
        for it in items:
            lines += [f'  - type: {it}', f'    hitAnimation: {frame}']
    open(RUL, 'w').write('\n'.join(lines) + '\n')
    print({k: len(v) for k, v in plan.items()}, 'frames written')


if __name__ == '__main__':
    main()
