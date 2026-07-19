# 🏈 Gridiron GM

A single-file **HTML app** that acts as a general-manager companion for your
Sleeper fantasy football team. It deliberately does **not** rebuild what the
Sleeper app already does well (live scores, setting lineups, chat). It adds the
three things Sleeper *doesn't*:

| Tab | What it does |
| --- | --- |
| 📰 **News Room** | Auto-writes a weekly newsletter from your league's real matchups — game stories, superlatives, and a lead recap that weaves **actual player stat lines** (yards, TDs, catches) and projection-vs-reality gaps into narrative around the fantasy results. |
| 🔄 **Trade Analyzer** | Build a trade with any team, see each side's value tally, a fairness verdict, and the net swing — scored under *your* league's exact settings. |
| 📋 **Draft Assistant** | A best-available board with value tiers and your live roster needs. Detects an in-progress Sleeper draft and removes players as they're picked. |

Powered entirely by Sleeper's **public, read-only API** — no login, no API key,
no password. You just enter your Sleeper **username** and pick a league.

## Running it

It's one file, `index.html`, with no build step and no dependencies.

**Option A — just open it.** Double-click `index.html` (or open it in any
browser). Done.

**Option B — put it on your phone's home screen (recommended).** Host the file
anywhere static and open the URL on your phone, then **Share → Add to Home
Screen**. It launches full-screen like a native app. Easy free hosts:

- **GitHub Pages:** in your repo settings → Pages → deploy this branch; your app
  is at `https://<you>.github.io/<repo>/`.
- **Local network:** `python3 -m http.server 8080` in this folder, then open
  `http://<your-computer-ip>:8080` on your phone (same Wi-Fi).

First launch: type your Sleeper username, tap **Find my leagues**, pick a league.
Your choice is remembered (in the browser's local storage) so it opens straight
to the News Room next time.

## How the News Room writes articles

The newsletter is generated **in your browser** from real data — no external AI
service, no keys, no cost:

1. Pulls the week's matchups and every player's real box-score stats from Sleeper.
2. Scores each performance under your league's own scoring rules.
3. Finds the storylines — top performers, busts (projected vs. delivered), the
   closest game, blowouts, points stranded on the bench.
4. Weaves the real stat lines into varied, readable prose, e.g.:

   > **Alice Aces leaves no doubt against Bob**
   > Alice Aces dismantled Bob 93.1–26.2. Josh Allen detonated for 33.8 on 27/38,
   > 341 pass yds, 3 pass TD, 22 rush yds, 1 TD, pacing the roster. … The dagger
   > was CeeDee Lamb, a quiet letdown — projected 22.5, delivered just 5.8.

Output is deterministic — a given week reads the same each time you open it.

## Notes & caveats

- **Off-season:** projections and stats populate once the NFL season is underway.
  In the off-season the News Room reads best from a completed prior week — use the
  week arrows to browse back. If a season's leagues don't exist yet, the app
  automatically falls back to your most recent season.
- The stats/projections endpoints (`api.sleeper.com`) are community-known but
  unofficial; the app degrades gracefully — player values fall back to Sleeper's
  ADP-style ranking, and articles fall back to fantasy scores — if they're ever
  unavailable or blocked by the browser (CORS).
- The ~5 MB NFL player dictionary is cached in your browser (IndexedDB) for a day
  so it isn't re-downloaded every visit.
- Player values are projected **full-season** fantasy points under your league's
  scoring — a strong, objective starting point, but they don't know your bye
  weeks, injuries-of-the-moment, or gut feel. You're still the GM.
- Not affiliated with or endorsed by Sleeper.

## Structure

Everything lives in **`index.html`** — inline CSS and one `<script>` organized
into clear sections: the Sleeper API client, league-aware scoring, the stat-line
formatter, the News Room narrative engine, season-long player values, and the
view/render layer (setup, News Room, Trade, Draft, settings).

> A React Native / Expo version of this app was built earlier in development and
> remains in the git history (commit `7548149`) if a native build is ever wanted.
