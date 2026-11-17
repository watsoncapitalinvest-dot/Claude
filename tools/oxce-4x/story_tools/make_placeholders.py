"""Placeholder art for pictures STORY is still waiting on from the graphics AI (John 17 Nov 01:31: "use placeholders").
Each is the real size, dark, labelled PLACEHOLDER with its file name and what the real picture shows, and keeps the
caption/text area clear the way the real one must. Replace by dropping the real file in art_briefs/returned/ under the
same name. Usage: python3 story_tools/make_placeholders.py   (writes art_briefs/placeholders/...)"""
import os, textwrap
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(ROOT, 'art_briefs', 'placeholders')
def font(n):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, n)
    return ImageFont.load_default()
SETS = {
  'cutscenes_act1': ('bottom', [
    ('cut_drome_c1', "Cobra's Terror Drome half-built: scaffolding, cranes, the round fortress ring with no roof yet."),
    ('cut_close_u1', 'The half-built Drome wrecked after the Joe assault: cranes down, smoke.'),
    ('cut_close_c1', 'An empty Cobra front-company office: shutters down, papers on the floor, nobody left.')]),
  'villain_briefings': ('left', [
    ('brief_silent_night', 'A roadside motel at night, rain-wet lot, one lit upstairs window, a dark figure on the roof.'),
    ('brief_swamp_rat', 'Army fuel trucks stopped on a swamp road, bikers in leather, barges at a dock, a hooded man watching.'),
    ('brief_trade_fair', 'A Scottish castle above a firing range, spectator stands, a big new weapon on display, a man in a steel mask.'),
    ('brief_chain_of_custody', 'Two prison trucks on a highway under an overpass, a black helicopter coming in low.'),
    ('brief_hostile_takeover', 'A glass office tower at dusk, red-uniformed guards in the lobby.'),
    ('brief_second_opinion', 'A white desert clinic at night, a green glow from a basement window.'),
    ('brief_last_relic', 'A museum hall at night, a glass skylight broken open, ropes hanging down.')]),
}
W, H = 1920, 1200
for folder, (clear, items) in SETS.items():
    os.makedirs(os.path.join(OUT, folder), exist_ok=True)
    for name, what in items:
        im = Image.new('RGB', (W, H), (20, 24, 26)); d = ImageDraw.Draw(im)
        # picture area: a hatched panel so nobody mistakes it for art; the clear area stays plain dark
        box = (0, 0, W, H - 240) if clear == 'bottom' else (W // 2, 0, W, H)
        bw, bh = box[2] - box[0], box[3] - box[1]
        panel = Image.new('RGB', (bw, bh), (42, 48, 51)); pd = ImageDraw.Draw(panel)
        for x in range(-bh, bw, 60):
            pd.line([(x, bh), (x + bh, 0)], fill=(52, 59, 62), width=6)
        im.paste(panel, box[:2])
        d.rectangle(box, outline=(232, 185, 35), width=8)
        cx = (box[0] + box[2]) // 2
        lines = ['PLACEHOLDER', name + '.png'] + textwrap.wrap(what, 40 if clear == 'left' else 60)
        y = (box[1] + box[3]) // 2 - 40 * len(lines)
        for i, t in enumerate(lines):
            f = font(96 if i == 0 else 56 if i == 1 else 40)
            w = d.textlength(t, font=f)
            d.text((cx - w / 2, y), t, font=f, fill=(232, 185, 35) if i == 0 else (233, 230, 220))
            y += 120 if i == 0 else 80 if i == 1 else 56
        im.save(os.path.join(OUT, folder, name + '.png'))
    print(folder, len(items))
