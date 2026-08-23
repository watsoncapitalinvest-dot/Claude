# THE FILM ROOM — Set Design Brief

Self-contained. Everything needed is in this document.

## What this is

A quiz-board game show for a 21-year-old fantasy football league, played in a
web browser on phones and laptops. The host — an older, weary, deadpan
broadcaster in a navy blazer over a loud floral shirt — already exists and is
**finished. Do not redraw him.** What's needed is the **set around him**.

The tone is deliberately not a slick national network. It's a regional
late-night sports broadcast with a budget that ran out in about 1994: heavy
desk, dim studio, a few monitors, one warm key light. Slightly cheap, entirely
sincere. That's the joke, so play it straight.

---

## THE RULES THAT MATTER MOST

**1. No text anywhere.** No letters, no numbers, no words, no filenames, no
captions. Every piece of text in this game — category names, dollar values,
questions, answers, the host's dialogue — is drawn by the software on top of
your art. A tile with "$400" painted on it is unusable, because the software
needs to put a different number there. The single exception is the show logo,
which is listed separately below.

**2. Nothing rendered into the image that describes the image.** No filename,
no label, no watermark, no border frame, no drop shadow onto a background. A
previous batch had each file's own name painted across the bottom of the
artwork; every one of those was unusable.

**3. Exact pixel dimensions.** Listed per asset. Not approximate.

**4. Dark and low contrast.** White and pale-gold text sits on top of all of
this and has to stay readable. If a piece is bright or busy, the text dies.
Keep everything in shadow except where a spec explicitly asks for a highlight.

**5. Alpha means alpha.** Where an asset is specified as transparent, the empty
area must be genuinely transparent — an actual alpha channel, not black pixels
painted in. Where it's specified as opaque, it must be fully opaque.

---

## PALETTE

Match these. They're the colours the software already draws in.

| Role | Hex |
|---|---|
| Deep background | `#070b16` |
| Panel / surface | `#111a2e` |
| Edge / border line | `#22304c` |
| Gold (headings, trim) | `#f2c14e` |
| Money gold (brighter) | `#ffd76b` |
| Correct green | `#5fd48a` |
| Wrong red | `#ff6b5c` |
| Cool accent | `#7cc0ff` |

Warm practical light (desk lamps, monitor glow) should read amber-to-gold. Cool
fill light should read the cool blue. Avoid pure white and avoid saturated
colours outside this set.

---

## THE ASSETS

### 1. `set-backdrop.png` — 1320 × 560 — **opaque**

The studio behind the host. He is composited over the lower-left of this, about
360px tall, so **keep the lower-left third quiet** — no detail that fights a
person standing in front of it.

A dim broadcast set: a wall of dark panelling, two or three inset monitors
glowing faintly with unreadable abstract graphics (charts, a scoreboard shape —
**no legible text or numbers**), a hanging banner or pennant shape, one warm key
light raking in from the right, deep shadow everywhere else. A little haze in
the light beam.

### 2. `set-desk.png` — 1320 × 220 — **transparent above the desk**

The anchor desk, seen straight on, drawn to sit across the bottom of the
backdrop with the host behind it. Heavy laminate or dark wood, a chunky front
panel, a subtle warm highlight along the top edge where the key light catches
it. The area above the desk surface must be transparent so the host shows
through behind it.

### 3. `tile-face.png` — 240 × 160 — **opaque**

One blank board tile. The software draws a dollar amount centred on it, so the
centre must be clear and dark. A slightly domed or bevelled panel, a soft inner
glow, a thin lit edge. Think an illuminated plastic cell in a physical board.
This tile is repeated 16 times across the board, so it must look right tiling
next to itself with a small gap.

### 4. `tile-spent.png` — 240 × 160 — **opaque**

The same tile after it's been used — dark, unlit, recessed, clearly dead. Same
outer silhouette as `tile-face.png` so the board doesn't shift when one changes.

### 5. `cat-plate.png` — 240 × 120 — **opaque**

The plate a category name sits on, above each column. Darker and flatter than a
tile, with a gold hairline along the bottom edge. The software prints the
category name across it in gold, so the centre must stay dark and even.

### 6. `clue-card.png` — 1320 × 900 — **transparent centre**

A frame, not a fill. The border of a card that a clue is displayed inside:
bevelled edge, faint gold trim, soft outer glow, corners with a little weight to
them. **The entire middle must be transparent** — the question and answer
buttons are drawn inside it. Keep the border under about 40px thick so it
doesn't eat the space.

### 7. `final-card.png` — 1320 × 900 — **transparent centre**

Same idea as the clue card, but for the final wager — the dramatic one. Heavier
gold, a deeper glow, maybe a suggestion of a spotlight falling across the top
edge. Same transparent middle, same border thickness.

### 8. `logo-filmroom.png` — 1200 × 400 — **transparent**

**The one asset that may contain text.** The show's title lockup, reading:

> **THE FILM ROOM**

with a smaller line above it reading:

> **SCFL NETWORK**

Broadcast-graphics styling of the era: heavy condensed lettering, a metallic or
gold bevel, a hard drop shadow, maybe a swoosh or an underline bar. Slightly
overwrought is correct. Transparent background.

### 9. `bug.png` — 200 × 200 — **transparent**

The little on-air channel badge that sits in a screen corner. A compact emblem —
a shield, a stylised film reel, a broadcast tower — in gold on dark. **No
lettering.** It sits at about 40px on screen, so it must read at that size: bold
shapes only, no fine detail.

---

## WHAT NOT TO SEND

- Anything with words, letters or numbers on it (except asset 8)
- The host — he's finished
- Frames or borders around a whole image
- Bright, high-key, or heavily saturated art
- Screenshots or contact sheets. **Raw PNG files only.**

## CHECK BEFORE SENDING

For every file:

- [ ] Exact dimensions as listed
- [ ] No text, letters, numbers, filenames or watermarks (except asset 8)
- [ ] Transparent where the spec says transparent, and genuinely so
- [ ] Opaque where the spec says opaque
- [ ] Dark enough that pale text on top would still read
- [ ] Palette matches the table above

Deliver as raw PNG files, named exactly as listed.

---

## PRIORITY

If only some can be made, this order gives the most improvement per asset:

1. `set-backdrop.png` — turns a web page into a studio
2. `tile-face.png` + `tile-spent.png` — turns a grid into a board
3. `logo-filmroom.png`
4. `cat-plate.png`
5. `clue-card.png`, `final-card.png`
6. `set-desk.png`, `bug.png`
