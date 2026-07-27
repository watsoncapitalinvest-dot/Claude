# SCFL Broadcast — Player Sprite Sheet Spec
**Instructions document for the graphics AI. Paste the MASTER STYLE BLOCK into every prompt, then one asset prompt at a time.**

---

## What we're making

Animation frames for a 2.5D football broadcast game. The engine plays the frames
in sequence and **tints the artwork per team**, so the art must be produced in
NEUTRAL COLORS (details below). One consistent athlete character across every
frame — same body, same proportions, same style, like frames of one cartoon.

---

## MASTER STYLE BLOCK — prefix every single prompt with this

> A single stylized cartoon football player, clean bold vector style with dark
> outlines, cel-shaded, crisp silhouette, readable at small size.
> Camera: three-quarter broadcast view, slightly elevated, player facing RIGHT.
> **Jersey: pure flat white (#FFFFFF), completely blank — no number, no name, no
> logo, no stripes.** Helmet shell and pants: flat light gray (#D0D0D0), gray
> facemask, no logos anywhere. Skin tone: medium-brown. Black cleats, white socks.
> **Transparent background. No shadow on the ground. No text, no watermark, no
> props, no other people.** Full body always fully inside the frame with feet on
> a consistent baseline near the bottom edge.

Why the weird colors: the game engine recolors white → team primary and light
gray → team secondary. Any baked-in color breaks 16-team tinting. Any baked-in
number breaks per-player numbering (the engine draws numbers).

---

## Output format

- **PNG with transparency**, one animation per image.
- Each animation is a **horizontal strip**: frames side by side, equal spacing,
  same character scale in every frame, feet baseline aligned across frames.
- Target: each frame roughly square (e.g., a 4-frame strip at 4096×1024 = four
  1024×1024 cells). Exact pixel size matters less than **equal cell widths and
  aligned baselines** — the engine slices strips evenly.
- If the tool can't keep a strip aligned, generate **one frame per image**
  (same master style block every time) and we'll assemble them.

---

## Asset list (one prompt each)

### 1. `run.png` — 8 frames
> …MASTER STYLE BLOCK… Horizontal sprite strip, 8 frames of a smooth full run
> cycle, left-to-right: contact, down, push-off, airborne, contact (other leg),
> down, push-off, airborne. Arms counter-swinging naturally. Identical character
> and scale in every frame, feet baseline aligned.

### 2. `idle.png` — 2 frames
> …MASTER STYLE BLOCK… Horizontal strip, 2 frames: (1) relaxed athletic
> two-point stance at the line, hands on thighs; (2) same stance, subtle breath
> shift. Identical character, aligned baseline.

### 3. `throw.png` — 5 frames
> …MASTER STYLE BLOCK… Horizontal strip, 5 frames of a quarterback throwing
> sequence: (1) two hands on ball at chest, (2) ball cocked back behind ear,
> (3) front shoulder open, ball high, (4) release — arm extended forward, ball
> just leaving hand, (5) follow-through, empty throwing hand across body.

### 4. `catch.png` — 4 frames
> …MASTER STYLE BLOCK… Horizontal strip, 4 frames of a receiver catching:
> (1) running with eyes back over shoulder, (2) both arms extending up,
> (3) hands together catching the ball overhead, (4) ball secured to chest,
> back in stride.

### 5. `dive.png` — 4 frames
> …MASTER STYLE BLOCK… Horizontal strip, 4 frames of a ball-carrier diving
> forward for the endzone: (1) gather step, (2) leaping forward, body angling,
> (3) fully horizontal, ball extended in one outstretched arm, (4) landing
> slide, ball still extended.

### 6. `hit.png` — 3 frames
> …MASTER STYLE BLOCK… Horizontal strip, 3 frames of a runner getting stopped
> at the line: (1) bracing, pads dropped, (2) impact recoil, torso twisted
> back, (3) stumbling backward a step, still on his feet.

### 7. `celebrate.png` — 4 frames
> …MASTER STYLE BLOCK… Horizontal strip, 4 frames of a touchdown celebration:
> (1) both arms shooting up, (2) jump, arms up, (3) ball spike wind-up,
> (4) flex pose. Big cartoon energy, same character.

### 8. `kick.png` — 4 frames
> …MASTER STYLE BLOCK… Horizontal strip, 4 frames of a placekicker: (1) angled
> approach step, (2) plant foot beside the ball spot, kicking leg back,
> (3) leg swinging through contact, (4) follow-through, leg high.

### 9. `lineman.png` — 3 frames
> …MASTER STYLE BLOCK… but a NOTICEABLY BULKIER lineman body type. Horizontal
> strip, 3 frames: (1) three-point stance, hand on ground, (2) firing upward
> out of the stance, (3) upright pass-block posture, arms extended.

### 10. `football.png` — 4 frames
> Same clean vector cartoon style, dark outlines, transparent background.
> Horizontal strip, 4 frames of a brown football rotating through a spiral:
> 0°, 45°, 90°, 135°. Same size and center in each frame. White laces visible.
> No text, no shadow.

---

## Consistency rules (the whole game depends on these)

1. **One character.** Every frame of every strip must look like the same athlete
   — same build, same head size, same line weight. If a generation drifts,
   regenerate rather than accept a different-looking player.
2. **Facing RIGHT always.** The engine mirrors for the other direction.
3. **Feet baseline aligned** across all frames of a strip — this is what makes
   the animation not "bounce." Character scale identical across strips too
   (the lineman may be wider, but same height).
4. **Colors exactly**: white jersey, light-gray helmet/pants, medium-brown skin,
   black cleats. Nothing else colored. No gradients on the tint areas — flat
   fills tint cleanest.
5. **Nothing baked in**: no numbers, no logos, no shadows, no background, no
   motion-blur streaks, no text.

## Delivery

Send the PNGs back in the chat **zipped** (images pasted loose don't come
through — zip them like the logos and covers). Name the files exactly as listed
above. Partial delivery is fine — `run.png`, `throw.png`, and `catch.png` alone
already upgrade most of the broadcast; the rest can follow.

---

# SHEET 2 — delivery update + next assets

**Delivery format change:** the zip requirement is dropped. Deliver everything as
ONE single contact-sheet PNG posted directly in chat (that's how sheet 1 arrived
and the slicer handles it). Layout rules for a contact sheet:

- Thin dark border lines between sections; section label small, top-left of each section.
- Frames left to right with clear gaps — frames never touch each other, the borders, or the label.
- Feet baseline aligned within a section. Checkerboard background is fine (it gets removed).
- Every shape needs a fully CLOSED continuous dark outline — gaps in the line work
  break background removal.

## Sheet 2 asset list (5 sections)

1. `tackle.png` — 4 frames: defender diving tackle (closing in / launching /
   wrapping horizontal / landed, wrap complete). Tackler only, no second player.
2. `backpedal.png` — 3 frames: defensive back backpedaling, knees bent, chest up,
   still FACING RIGHT while moving backward.
3. `spin.png` — 4 frames: ball carrier spin move (run / plant + start rotation /
   mid-spin from behind / out of the spin in stride).
4. `sack.png` — 3 frames: QB sacked (bracing with ball / buckling, ball tucked /
   down on one knee, head down).
5. `ref.png` — 3 frames: referee touchdown signal (arms at sides / rising / both
   straight up). ONLY this section wears different kit: black-and-white striped
   shirt, white pants, black cap. The ref is never team-tinted in the engine.

Character consistency with sheet 1 is mandatory — same athlete, same scale, same
line weight, facing RIGHT, white jersey / light-gray helmet+pants for tinting.
