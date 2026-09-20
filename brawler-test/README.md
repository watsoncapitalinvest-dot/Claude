# brawler-test/ — OpenBOR engine proof-of-concept

This is a technical test, not the real game yet. It exists to answer one
question: can a real Streets-of-Rage-style engine (OpenBOR, compiled to
WebAssembly) actually run our own custom character content in a browser,
mobile included?

## What's actually here

- The engine and web wrapper come from **OpenBOR-WASM**
  (github.com/minidogenft/OpenBOR-WASM), an unofficial WebAssembly port of
  OpenBOR. Unmodified: `content/OpenBOR.zip` (the engine), `main.js`,
  `mobile.js`, `game.css`, `nipplejs.min.js` (touch joystick), `fflate.min.js`
  (client-side unzip).
- The game content (`content/game-test.zip`) is the **Super Doginals** sample
  game (CC BY 4.0, credit @minidogeart) that ships with that port, with one
  change: the character "Kabo" has been duplicated, hue-shifted from
  orange to red/black, and renamed **SmokeDragons** — a placeholder stand-in
  for the real SCFL "Smoke Dragons" franchise, reusing Kabo's existing
  animation frames (idle, walk, punches, jump, etc.) under a new palette.
  This is a proof that our own content loads and runs — it is **not** real
  SCFL character art. Real art is still pending from the separate
  outsourced-art track (see the "SCFL Championship Brawl — Asset Catalog"
  doc).
- Everything else — the title screen, story intro, menus, other playable
  characters, levels, music — is still 100% the original Super Doginals
  demo. It has not been re-themed for SCFL. That's real remaining work, not
  done here.

## What was verified

- The engine boots and renders correctly in a real browser (confirmed via
  headless Chromium + screenshots).
- The custom `SmokeDragons` model loads cleanly with no errors, alongside
  the existing roster — confirmed directly from the engine's own boot log:
  `Loading 'SmokeDragons' from data/chars/smokedragons/smokedragons.txt`.
- Touch controls (joystick + attack/jump/star/pause buttons) are wired in
  from the OpenBOR-WASM port and should work on a phone.

## What was NOT verified

Automated testing could not click all the way through Super Doginals' own
title/intro sequence to visually confirm the recolored character in actual
gameplay — likely a quirk of scripting synthetic input against a compiled
game engine, not a sign of a real bug (the model loads with zero errors,
which is the part that would fail if something were actually wrong). Try it
yourself in a real browser — press Enter a few times through the intro to
reach the title screen, then Enter again to start; if that doesn't advance,
try 1, 5, or Space, or tap directly on the screen.

## Powered by OpenBOR

This project uses the OpenBOR engine — see `content/` licensing from the
OpenBOR-WASM port for OpenBOR's own license terms.
