# SCFL — what we're building next

Standing list of agreed ideas so they survive between sessions. Ordered by the
fun-per-effort call we made on 2026-08-20.

## In progress

### 2. Player pages — "The Ledger" — SHIPPED 2026-08-21
In the app under Newsroom → The Record Room. 255 players across 492 trade
assets: searchable list, and a page each with trade count, franchises, the route
he actually took (returns included), and every deal — who sent him, who got him,
who moved with him, what went back. Built by `scripts/build_players.py`, which
canonicalises hand-typed names conservatively and asserts the asset count is
unchanged so a bad merge can't silently swallow a player.
Still to add: what the chat said about him (needs the banter-not-shots rule), and
a valuation column from `dp-values.json`.

### 3. The Rivalry Board — SHIPPED 2026-08-21
In the app under Newsroom → The Record Room. Ranked pairings, everyone's rival,
and a detail page per pairing: series record, playoff record, title-game
meetings, current streak, biggest win, worst loss, closest game, chat focus and
heat. Built by `scripts/build_rivalries.py`; the build asserts the head-to-head
reconciles against the league's stored standings before it will write output.
Still to add: a defining *line* per pairing — but see the rule below.

## Agreed, not started

### 1. The Curse Watch
Live board of every player currently rostered who was acquired from the Wookie,
with health status beside each name. Derives from `trades.json` + roster data;
updates itself weekly. Small, funny, high traffic.

### 4. Awards Night
Annual ceremony in the SportsCenter format with Harry Doyle presenting. Real
categories for this league: Most Trades, Best Draft, the Gumba Award for longest
continuously-held player. Source: `records.json` superlatives, 21 seasons.

### 5. Harry Doyle audio
Ninety-second weekly recap in voice, dropped into the chat. Highest perceived
production value per unit of work.

## Considered and held

- **Season-long pick'em** — likely duplicates the existing Money Lines board.
- **Chat search tool** — genuinely useful, but the corpus can never go on the
  public site (the Pages workflow publishes the whole repo root). Local-only if
  ever built.

## League customs that affect the data

See `docs/LEAGUE-RULES.md`. The big one: **the worst team is renamed every year
and the league votes on the new name**, so franchise names are never stable
identifiers — always resolve identity by owner, and expect a new alias each
August.

## House rules this project runs on

- Chat exports never enter the repo. Only distilled, reviewed artifacts.
- Every published quotation is verified verbatim against the corpus first.
- Private-chat commentary stays out of print; the offers themselves are usable.
- Page builders live in `scripts/`, not in a temp directory.
- **Heat is a metric, not a quote source.** Argument density is a good signal for
  ranking rivalries and it stays. What never ships is the text behind it — angry
  messages between real friends read very differently on a published page than
  they did in the moment. `build_rivalries.py` enforces this: it fails the build
  if any string in the output matches chat text.
- Lines chosen for publication are **banter, not shots** — funny, self-aware, or
  something the speaker would happily repeat. Run them past John before shipping.
