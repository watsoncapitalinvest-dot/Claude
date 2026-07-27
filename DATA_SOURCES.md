# SCFL Executive Office — Data Source Priority

When two sources disagree, the higher one wins. Priorities are by **domain** —
a source that's authoritative for trades isn't necessarily right for values.

## Golden rule
**Commissioner-confirmed facts beat everything.** Anything a league officer
states directly (playoff appearances, champions, franchise lineage, rule
changes) is the top authority and is **never** overridden by a computed or
scraped number. (This is the Wookie-Leaks playoff lesson: don't compute what
can be confirmed.)

## Trades — who traded what
1. **Obvibase ledger** (the Team A / Team B exports) — the commissioner's full,
   itemized record, 2016–present. **Primary.**
2. **Official league chat (WhatsApp)** — fills detail/context and any gap the
   export misses; used for narrative, not to override the ledger.
3. **Sleeper transactions API** — cross-check for the current Sleeper era only
   (2021+). Reliable as a system-of-record but narrower than Obvibase, so it
   backs up the ledger rather than replacing it.

## Player & pick values ($ board)
1. **Real SCFL trades** (Obvibase) — the calibration anchor: what things
   actually cost in *this* league.
2. **DynastyProcess market** + our adjustments (non-PPR shade, elite "boom"
   stretch, 1.01 = $100 scale) — the coherent baseline for 650+ players.
3. **Positional-rank grid** — last-resort floor for anyone the market doesn't
   cover, so aging-but-startable vets never fall to zero.

## Current season — rosters, scores, standings, live lineups
1. **Sleeper API** — sole source of truth for anything happening now.

## Draft results — who picked whom
1. **Powers of Pain draft posts / `drafts.json`** — the league's own authoritative record.
2. **Sleeper draft API** — for Sleeper-era classes and pick-to-player resolution.

## Historical records — champions, standings, all-time (pre-2021)
1. **Commissioner-confirmed / Record Book.**
2. **ESPN / League Legacy import** — the pre-Sleeper archive (no trade API, so
   pre-2021 trades aren't gradable).

## Narrative — personas, tendencies, storylines
1. **Official chat dossier** — who's who, how they operate, running arcs.

---
*Reliability note:* the Obvibase export carries occasional spelling typos and
surname-only entries; these are corrected in the parse (`trades.json`) so names
resolve to real values. Team defenses and any genuinely ambiguous entry are
left untouched rather than guessed.
