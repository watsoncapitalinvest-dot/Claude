# core-demo/ — the generic "Core" test build

A fork of `index.html`, for handing to a second, non-SCFL league to try with
their own Sleeper account. Lives in its own folder specifically so it never
touches the production app or its data.

## What's different from the production app

- Every chat-derived or SCFL-hardcoded nav tile is removed from
  `OFFICE_TOOLS` / `OFFICE_SECTIONS` and `NEWSROOM_TOOLS` / `NEWSROOM_SECTIONS`:
  Dossier, Franchise Directory, Record Book, Rivalry Board, The Full Record,
  The Ledger, Ex-Files, Jeopardy, Trade Wars, Ring of Honor, POP's Draft
  Grades, SCFL Politics, SCFL SportsCenter, Storylines, Investigations, the
  Heat Index, and the Weekly Heat Index. None of that data exists for a new
  league, and the underlying JS is untouched — the app just doesn't route to
  it anymore.
- The desk-gate "who's at the desk" picker (three hardcoded SCFL names) is
  replaced with a single "Enter your name" prompt.
- `showArchive()` no longer auto-generates or links SCFL's own Post-Draft/
  Draft Issue special editions.
- "SCFL" branding is stripped from page titles, meta tags, and on-screen
  copy. **The crest artwork and desk photos are still SCFL's actual images**
  — replacing those is a design task, not a code one, and wasn't done here.
- What's kept, unmodified: Sleeper league lookup, live rosters/matchups,
  Power Rankings, Money Lines, the export tools, Create Issue / Weekly
  Stories (the automated newsletter), Trade Court, Waiver Wire Board,
  Owner Interviews, Newsroom Desk, Calendar, Back Issues / Article Archive.
  These already work for any Sleeper league with zero code changes.

## What was NOT verified

Live Sleeper API calls could not be tested from the sandbox this was built
in (the sandbox's egress policy blocks `api.sleeper.app` outright — a sandbox
restriction, not an app bug). What *was* verified: the trimmed nav renders
correctly, no page errors on load, and every kept view (`trade-court`,
`waiver-wire`, `archive`, the Office and Newsroom menus) runs cleanly against
a simulated league with no console errors. Confirm the actual Sleeper lookup
flow end-to-end with a real browser before handing this to a test league.

## Known gaps, if this goes further after one pilot

- `draft-intel.json` (SCFL's own hand-written 2026 scouting notes, hardcoded
  `myTeam: "The Smoke Dragons"`) still feeds parts of the draft-room /
  pick-value display. It fails silently (empty state) when the file is
  missing, same as everything else here — but a league that *wants* that
  feature needs their own version written, not just the file swapped out.
- The desk-scene photo hotspots (`DESK_HOTSPOTS`, `NEWSROOM_HOTSPOTS`) still
  contain a couple of `act` targets pointing at hidden tools (e.g.
  Ring of Honor). They degrade to an empty-state screen rather than a crash,
  but they're dead links cosmetically and should be trimmed for a second
  pilot.
- No rebrand of the visual assets (crest, desk photos, app icon). Fine for
  a functional pilot; not fine to hand to a paying client as "theirs."
