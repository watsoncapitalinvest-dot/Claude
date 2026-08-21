# SCFL house rules worth knowing

League customs that shape the data. Written down because they explain why the
records behave the way they do.

## Structure

Sixteen teams, two conferences, two divisions of four in each.

**Divisions (verified against the league app, 2026):**

| Division | Teams |
|---|---|
| The Four Horsemen | Heavy Hitters, Hairy Gumbas, New World Order, Horse Collars (Forty2V) |
| Black and Blue | Wookie Leaks, Beaver Eaters, Big Blue, Pork Chop Express |
| Spartan | Killer Klowns, Master-Jeti, Lil' Chops, The Machines |
| Spectre Syndicate | Still The Cream, Smoke Dragons, Guido Haters, Powers of Pain |

**Conferences.** Derived from the schedule — the division you play four single
games against is your conference partner. For 2025 that pairs *Spectre Syndicate
with Black and Blue*, and *Spartan with The Four Horsemen*. The conference names
in circulation are **Maclean** and **Cobra Kai**; a May 2023 chat listing pairs
them the other way round, which predates the 2023 realignment, so the names are
recorded here but not attached to a pairing.

**Realignments.** Two in the recoverable history: between 2012 and 2014, and
between 2022 and 2023. The 2023 one is when The Four Horsemen were created — the
New World Order announced it in August 2023: *"A New Division is Born! ... Let me
introduce The Four Horsemen."*

## The schedule

Fourteen games (thirteen through 2020), and it decomposes exactly:

- **6 games** against your own division — the other three teams, twice each.
- **4 games** against the other division in your conference — once each.
- **4 games** scattered across the other conference. The split varies year to
  year: 2022 ran 3+1, 2025 ran 2+2. It is fill, not a clean rotation.

Consequences for the data, both of which bit us:

- **Games played is a fact about the schedule, not the rivalry.** Two teams who
  share a division for a decade rack up thirty meetings without either choosing
  it. `build_rivalries.py` counts shared history in *divisional seasons*.
- Divisions are recovered per season by `scripts/build_divisions.py`; sixteen of
  eighteen seasons resolve, and the 2025 result matches the app exactly.

## The playoffs

**Eight qualify: the four division winners, plus two wild cards from each
conference.** Three rounds, including a conference championship.

Two things follow, and both matter for any analysis:

- **`rank` in the standings is the playoff seed, not record order.** In fifteen
  of eighteen seasons a team with an inferior record is seeded inside the top
  eight — division winners get in regardless. In 2024 and 2025 the #1 seed was a
  6-8 and a 7-7 team.
- All sixteen teams keep playing the final three weeks — the bottom half in a
  consolation ladder that decides nothing — and `history.json` flags **every**
  one of those as `playoff`. Counting them turns 24 games a season into playoff
  history when only 12 are between qualifiers. A playoff meeting means both
  teams finished top eight. Format is not constant either: most seasons are a
  knockout, but 2017 had the top eight replay each other.

## The Name Change

**The team that finishes worst is renamed for the following season, and the
league votes on what it gets called.**

Confirmed across five years of chat:

- Decided on record, with points as the tiebreaker. The Machines, Dec 2021, on
  two teams level on record: *"Hitters more points — so if they both lose or
  they both win and finish same record, A-Team getting a name change."*
- It is supposed to sting. The Machines: *"name change has to be embarrassing."*
- It can hit the same franchise twice running — the Gumbas noted the first ever
  *"consecutive name change"* in 2021.
- The 1.01 pick is the consolation: *"getting the #1 pick helps a little."*
- The league votes on the replacement name. New World Order, Aug 2025:
  *"Changed the name to Lamb Chops. Didn't know what the official name change
  was since I never voted."*

### Why this matters for the data

Franchise names are not stable identifiers — by design, at least one changes
every single year. Everything that tracks a franchise across time must resolve
identity by **owner**, never by team name:

- `scripts/build_rivalries.py` groups by owner id, with a merge table for
  managers whose platform id changed. This is why a single franchise can appear
  as THE DICKS, The Wade Garrets and Wookie Leaks and still be one team.
- `scripts/build_players.py` maps roster-export labels onto ledger names in
  `ROSTER_ALIAS`.
- The broadcast pages carry the same idea in `TALIAS`
  (`broadcast-demo.html`, `scfl-sportscenter.html`).

**Every August, expect at least one new alias.** Currently that mapping lives in
two places and both need the update. Worth consolidating into one shared file.

Known aliases, current era:

| Appears as | Franchise |
|---|---|
| Forty2V | Horse Collars |
| New Wod Order | New World Order |
| Lamb Chops, The Porkys, The A-Team, Disciples of Darnold | Lil Chops |
| StillTheCream | Still The Creamiest |
| Master-Jeti, Return of the JET-I, The Belichicks | The Jet-I |
| Gumbas, Hairy Clams | Hairy Gumbas |
| The Dry Dicks | Wookie Leaks |

### Story potential

The Name Change is one of the league's real institutions and the Newsroom has
never covered it: who has been renamed, how often, who has never been, the
consecutive-rename record, and the vote each year. Sits naturally beside
Awards Night.
