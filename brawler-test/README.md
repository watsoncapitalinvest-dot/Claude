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
  game (CC BY 4.0, credit @minidogeart) that ships with that port, with three
  of its playable character slots replaced by real SCFL characters built from
  actual delivered art (see the "SCFL Championship Brawl — Asset Catalog" doc):
  - **SmokeDragons** — full 50-frame set (idle/walk/attack1/attack2/jump/
    land/pain/fall/rise/grab/grabattack/throw) from real Smoke Dragons art.
  - **TheMachines** — full 56-frame set from real The Machines art.
  - **PorkChopExpress** — full 50-frame set + boss extras from real Pork
    Chop Express art.
  Each was cropped from the delivered sheets/files, chroma-keyed to
  transparent GIFs, and wired into a real multi-frame OpenBOR character
  (animation timing/hitboxes borrowed from the sample's own "Kabo" character
  as a structural template, since that data wasn't part of the art
  delivery). All three load cleanly with zero engine errors, confirmed
  directly from the boot log.
- Everything else — the title screen, story intro, menus, remaining 13
  characters, levels, music — is still the original Super Doginals demo,
  not re-themed for SCFL yet.

## What was verified

- The engine boots and renders correctly in a real browser (confirmed via
  headless Chromium + screenshots).
- All three real characters (`SmokeDragons`, `TheMachines`, `PorkChopExpress`)
  load cleanly with no errors, confirmed directly from the engine's own boot
  log.
- `SmokeDragons` (the default P1 character) was confirmed rendering and
  walking in an actual level with its real art and full HUD (name, health
  bar, lives) via automated screenshot.
- Touch controls (joystick + attack/jump/star/pause buttons) are wired in
  from the OpenBOR-WASM port and should work on a phone.

## What was NOT verified

Automated testing could not get a clean screenshot of `TheMachines` or
`PorkChopExpress` specifically in motion (Super Doginals' own menu/pause
flow is finicky to script synthetic input against) — their underlying
character data is confirmed correct via the clean boot log, same standard
as everything else here, but nobody has watched them walk on screen yet. A
real person playing normally shouldn't hit this; if you want to pick a
different character than the default, look for a character-select or P2
join prompt in the pause menu (Enter to open it).

## Known rough edges in this pass

- A few animation frames have minor edge-crop artifacts from the source
  sheets not having perfectly uniform cell widths — cosmetic, not
  functional.
- Hit boxes, attack timing, and movement speed for these three characters
  are borrowed from the sample game's own "Kabo" character as a structural
  template (the art delivery didn't include that data) — they'll feel
  slightly generic rather than tuned to each character.

## Powered by OpenBOR

This project uses the OpenBOR engine — see `content/` licensing from the
OpenBOR-WASM port for OpenBOR's own license terms.
