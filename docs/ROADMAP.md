# SCFL — what we're building next

Standing list of agreed ideas so they survive between sessions. Ordered by the
fun-per-effort call we made on 2026-08-20.

## In progress

### 2. Player pages — "The Ledger"
Every player who has ever been traded gets a page: every trade he appeared in,
who owned him when, and what the chat said about him at the time. Foundation for
the Curse Watch, the Rivalry Board and the Trade Court — they all get to cite it.
Sources: `trades.json` (256 deals), the chat corpus, `pop-grades.json`.

### 3. The Rivalry Board
One page per pairing: all-time head-to-head, the defining game, the defining
quote, current streak. The magazine pulls a "grudge of the week" off it.
Head-to-head engine built 2026-08-20 from `history.json` — 18 seasons,
2,344 games, 21 franchises resolved by owner id across renames.

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

## House rules this project runs on

- Chat exports never enter the repo. Only distilled, reviewed artifacts.
- Every published quotation is verified verbatim against the corpus first.
- Private-chat commentary stays out of print; the offers themselves are usable.
- Page builders live in `scripts/`, not in a temp directory.
