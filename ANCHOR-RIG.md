# SCFL SportsCenter — Anchor Rig: 20 Animation Directions

Motion library for the layered-puppet anchor (see SPRITE-SPEC.md sheet 3 /
layered delivery). Every motion is additive — baseline life never stops under
gestures — and every gesture returns with ease-out + 5-10% overshoot.

## Baseline life (always on)
1. Breathing — torso scaleY ±1%, 3.5s sine; shoulders ride along.
2. Idle sway — upper body ±1° rotation, 8s cycle, desynced from breathing.
3. Blinking — 120ms, random 2-6s; 20% double-blink. Eyebrow dip if no eyelid layer.
4. Micro head drift — yaw ±2° to random focus points every 4-7s, 300ms ease-out.
5. Weight shift — 2° torso lean and settle every 15-25s.

## Speech-driven
6. Jaw sync — closed/half/open mouth from audio (word boundaries or amplitude);
   open 60ms, close 110ms.
7. Talk cadence nod — head pitch -1.5° on stressed beats (~every 4-6 jaw cycles).
8. Sentence-end settle — jaw shut, head to center 400ms, one slow blink.
9. Emphasis pop — eyebrows +3px 250ms on numbers/team names.
10. Lean-in — torso 3° toward camera, 600ms, held for the quip line of each game.

## Gestures
11. Finger point — right forearm up, index at camera, 700ms hold, overshoot drop.
    Trigger: direct-address lines.
12. Palms-up shrug — both forearms out, shoulders +3px, head tilt 4°, 600ms.
    Trigger: absurd scores.
13. Paper tap — forearms tap desk twice, 150ms apart. Trigger: game transitions.
14. Dismissive wave — right hand flick, head turns away 5°. Trigger: Dud outros.
15. Count-off — right forearm ticks up in 3 steps synced to stat-line items.

## Signature Harry
16. The drink (4-phase) — reach 400ms → lift + toast (glass 10°, nod) → drink
    (head back 12°, 800ms) → set down + 2° satisfied shake. Glass layer swaps
    desk→hand. Trigger: the two pour points.
17. Tie adjust — left hand to knot, two 3° wiggles. Trigger: after flourish lines.
18. Disgust collapse — head -8°, hand to forehead through the line, then 3-beat
    slow shake. Trigger: Dud of the Week card.
19. Big laugh — head back 15° + 2 bounces, shoulders 6Hz shake, desk slap.
    Trigger: blowout "crime scene" lines.
20. Sign-off salute — slow toast (no drink), 1s nod to camera, ease to neutral
    before the Goodnight wipe. Final line of every episode.
