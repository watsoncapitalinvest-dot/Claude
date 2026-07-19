# 🏈 Gridiron GM

A mobile **general-manager companion** for your Sleeper fantasy football team. It
deliberately does **not** rebuild what the Sleeper app already does well (live
scores, setting lineups, chat). Instead it adds the three things Sleeper *doesn't*:

| Tab | What it does |
| --- | --- |
| 📰 **News Room** | Auto-writes a weekly newsletter from your league's real matchups — game stories, superlatives, and a lead recap that weaves **actual player stat lines** (yards, TDs, catches) and expectation gaps into narrative around the fantasy results. |
| 🔄 **Trade Analyzer** | Build a trade with any team, see each side's value tally, a fairness verdict, and the net swing — all scored under *your* league's exact settings. |
| 📋 **Draft Assistant** | A best-available board with value tiers and your live roster needs. Detects an in-progress Sleeper draft and removes players as they're picked. |

Everything is powered by Sleeper's **public, read-only API** — no login, no API
key, no password. You just enter your Sleeper **username** and pick a league.

## How the News Room writes articles

The newsletter is generated **on-device** from real data, so it works with no
external AI service and no keys:

1. Pulls the week's matchups and every player's real box-score stats from Sleeper.
2. Scores each performance under your league's own scoring rules.
3. Finds the storylines — top performers, busts (projected vs. delivered), the
   closest game, blowouts, points stranded on the bench.
4. Weaves the real stat lines into varied, readable prose (e.g. *"Josh Allen
   erupted for 31.4 on 27/38, 341 pass yds, 3 pass TD, pacing the roster."*).

Output is deterministic — a given week reads the same each time you open it.

## Running it on your phone

You'll need [Node.js](https://nodejs.org) 18+ and the free **Expo Go** app
([iOS](https://apps.apple.com/app/expo-go/id982107779) /
[Android](https://play.google.com/store/apps/details?id=host.exp.exponent)).

```bash
npm install
npx expo start
```

Then scan the QR code in your terminal with your phone's camera (iOS) or the
Expo Go app (Android). The app opens; enter your Sleeper username and pick a
league.

> **Off-season note:** projections and stats populate once the NFL season is
> underway. In the off-season the News Room reads best from a completed prior
> week — use the week stepper to browse back. If a season's leagues don't exist
> yet, the app automatically falls back to your most recent season.

## Project layout

```
app/                       # expo-router screens
  _layout.tsx              # root stack + providers
  index.tsx                # boot gate → setup or app
  setup.tsx                # username + league picker
  settings.tsx             # switch league / sign out
  (tabs)/
    _layout.tsx            # News / Trade / Draft tab bar
    index.tsx              # 📰 News Room
    trade.tsx              # 🔄 Trade Analyzer
    draft.tsx              # 📋 Draft Assistant
src/
  api/sleeper.ts           # Sleeper API client + on-device player cache
  hooks/                   # useLeague, useValues, useProjections
  lib/
    scoring.ts             # league-aware fantasy scoring
    statline.ts            # raw stats → readable box-score lines
    narrative.ts           # the News Room newsletter engine
  components/              # shared UI primitives
  store/AppContext.tsx     # persisted session (username + league)
  theme.ts                 # design tokens
```

## Notes & caveats

- The stats/projections endpoints (`api.sleeper.com`) are community-known but
  unofficial; the app degrades gracefully (values fall back to Sleeper's
  ADP-style `search_rank`) if they're ever unavailable.
- Player values are projected **full-season** fantasy points under your league's
  scoring — a strong, objective starting point, but they don't know about your
  bye weeks, injuries-of-the-moment, or gut feel. You're still the GM.
- Not affiliated with or endorsed by Sleeper.
