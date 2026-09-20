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
- The title/intro sequence now shows the real "Streets of Rage x SCFL"
  splash image instead of Super Doginals branding. This is a GIF
  (`data/scenes/splash.gif`), not video — the original intro used WebM/VP9
  video, which doesn't play at all on Safari/iOS, so a video-based
  replacement wouldn't have worked on most phones either. Two separate
  scenes needed replacing: `logo.txt` (the engine's hardcoded first splash,
  originally a QR-code screen) and `intro.txt` (originally two videos with
  Doginals branding, ~41s total) — both now point at the same splash.gif.
- Everything else — the rest of the menus, remaining 13 characters, levels,
  music — is still the original Super Doginals demo, not re-themed for
  SCFL yet.

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

## "Stuck on loading" fix (round 2)

After the splash fix above, loading got reported stuck again. Root cause
found by reading the loader code (`content/main.js`), not by reproducing it
locally — it never hung in local testing:

- The loader does one big `fetch()` of the ~33MB game-data zip, waits for
  the whole thing to download, decompresses it synchronously, then writes
  every file into the in-memory filesystem — and the loading screen was a
  static `"Loading..."` the entire time, with no progress indicator and no
  timeout. On a slow phone connection this step can genuinely take
  30–90+ seconds, and a slow load looks identical to a dead one when
  nothing on screen ever changes.
- Fixed: the loader now streams the download and updates the loading text
  live (`Downloading game data… 42%`, then `Unpacking…`, `Installing
  files… 300/850`, `Starting engine…`), and if no progress happens for
  20+ seconds it appends a "still working" note instead of staying silent.
  This doesn't guarantee the connection is fast enough, but it now tells
  the truth about whether something is happening.
- Also trimmed ~1.4MB of dead weight from the pak: `moon.webm`/`intro.webm`
  (replaced by `splash.gif`, no longer referenced anywhere), the old
  `tip.gif` QR splash, and an unreferenced `menu.ogg` track.
- Not fully ruled out: whether a ~33MB download is simply too much for the
  connection in question. If loading still doesn't finish after this fix,
  that's the next thing to address (would mean cutting real content, e.g.
  music tracks, not just dead files).

## "Stuck on loading" fix (round 3) — the actual freeze

Round 2 added progress text, but it stayed stuck on real devices. The bug:
the progress text updates were real, but most of them could never actually
paint to the screen. `fflate.unzipSync` decompresses ~33MB synchronously on
the main thread, and the file-install loop wrote hundreds of files in one
synchronous pass right after it — both block the browser's rendering
pipeline for their entire duration, so nothing on screen updates until they
finish, no matter how many times the code changes the loading text mid-loop.
On a phone CPU that stretch can take long enough to look (and on iOS
Safari, risk actually becoming) frozen.

Fixed by switching to `fflate.unzip` (the same library's Web Worker-backed
async decompressor, confirmed present in this build) instead of
`unzipSync`, so the heavy decompression runs off the main thread entirely,
and by breaking the file-install loop into batches with an explicit yield
(`requestAnimationFrame`) every 50 files so the browser can repaint between
batches. Verified locally that every intermediate loading state now
actually renders instead of jumping straight from one download percentage
to "Starting engine…".

## "Stuck on loading" — actual root cause (round 4)

None of rounds 1–3 fixed it on the real device, because none of them were
the actual bug. All local testing up to this point served `game.html` with
`brawler-test/` itself as the web server's root directory, which made
`content/...` paths resolve correctly by coincidence. The real deployed
site serves the whole repo, so the live page is actually at
`/Claude/brawler-test/game.html` — one directory level deeper.

`contentPath` was set to `'/content/'`, an **absolute** path from the
domain root, in the very first commit that created this page, and no
subsequent fix touched it. On the real site that resolves to
`https://<domain>/content/...`, which doesn't exist — the real files are at
`/Claude/brawler-test/content/...`. Every asset fetch (`main.js`,
`fflate.min.js`, the engine, the game data) has 404'd on the live site
since the very first deploy. A `<script src>` or `fetch()` 404 doesn't
throw a catchable JS exception and never reaches `window.onerror`, so this
was completely silent — explaining why the error-surfacing added in round 3
never caught anything, and why the screen never changed no matter what else
was fixed.

Confirmed by serving the repo root locally (matching the real site
structure) instead of `brawler-test/` directly: the old code reproduced the
exact freeze, 404s and all; the fix does not.

Fixed by:
- Changing `contentPath` to the relative `'content/'`, so it resolves
  correctly regardless of what directory depth the page is served from.
- Moving all of game.html's logic (previously two inline `<script>` blocks)
  into external files (`content/errors.js`, `content/config.js`), loaded via
  plain `<script src>` tags. This was a second, independent hardening: an
  inline script silently failing to run (a stripped/sanitized `<script>`
  block, a restrictive delivery path) would have looked identical to this
  bug, and moving the entry point to a real external file removes that
  failure mode too regardless of whether it was ever actually in play here.
- Adding an `onerror` handler to the dynamically created `main.js` script
  tag, so a future path or hosting mistake shows an explicit message on
  screen instead of a silent, permanent freeze.

## Powered by OpenBOR

This project uses the OpenBOR engine — see `content/` licensing from the
OpenBOR-WASM port for OpenBOR's own license terms.
