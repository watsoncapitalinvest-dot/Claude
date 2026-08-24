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

**Conferences.** Two: **John McClane** (often written Maclean/McClane) and
**Cobra Kai**.

| Conference | Divisions |
|---|---|
| John McClane | Spartan + Spectre Syndicate |
| Cobra Kai | Black and Blue + The Four Horsemen |

This comes from the **bracket**, which is seeded within conference: round one is
four games, two per conference, and the semi-finals are the conference
championships. It matches the chat — in December 2024 the Beaver Eaters called
Jet-I vs Klowns the McClane conference game and Big Blue vs NWO the Cobra Kai
one, and the bracket agrees. Stable across 2023–2025.

**Do not derive conferences from the schedule.** Each division plays one other
division in full (four games per team), and that partner is in the *opposite*
conference — so the schedule gives exactly the wrong answer. This was got wrong
once already.

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

- **`rank` in the standings is FINAL PLACEMENT — where a team finished after the
  playoffs — not the playoff seed and not record order.** `rank == 1` is the
  champion in 18 of 18 seasons, including a 6-8 team (2024) and a 7-7 team
  (2025). The week-17 game between `rank` 1 and 2 is therefore always the title
  game, and 3v4, 5v6, 7v8 are placement games.
  **Playoff seeds cannot be recovered from this data.** Division winners are
  seeded above wild cards, but the division standings and tiebreakers that decide
  who won a division are not stored, so never describe a team as the "#1 seed" or
  as having "won its division" from `rank` alone. What `rank` does support:
  ranks 1-8 are the eight teams that made the bracket, 9-16 the consolation half.
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

## Who is in which chat

There are two league chats and they are not interchangeable. **Mos Eisley** is
the banter chat, where effectively all of the volley traffic lives. The
**league chat** is the low-volume official one: trades, the draft link,
scheduling.

Mike Lagares (**The Jet-I**) left Mos Eisley on 5 June 2022 and has not posted
in it since. The reasons were political and are not the Newsroom's business.
He did **not** leave the league — he is still in it, still drafting, and still
in the league chat, most recently 17 August 2026.

This matters to every chat-derived number:

- His volley total measures **when he stopped**, not how much he talks.
- His pairing splits are inflated by a small denominator, which is the only
  reason he takes two of the top four rows of the one-way-streets figure.
- Never write him up as quiet, checked out, or disengaged from the league on
  the strength of a chat count.

`scripts/build_addendum.py` detects this in `compute()` rather than hardcoding
it: any manager whose Mos Eisley presence ended more than eighteen months ago
while their league-chat presence continues is flagged into `D['absent']` and
carries a dagger through the figures. If somebody else goes quiet the same way,
the addendum picks it up on the next build.

### Open data gap

`~ Dave Sheq` (271 messages) is a second display name for sheq7777 / **The
Beaver Eaters** and is mapped in `MENTNAME` but *not* in the `CHAT` map, so
those messages produce no volleys. It is under one per cent of that
franchise's traffic. Fixing it means changing the `CHAT` map in **both**
`build_rivalries.py` and `build_addendum.py` together — the addendum's claim is
that it shares a code path with the ranking, so they cannot diverge — and then
rebuilding the rivalry board, which may shift scores and ranks slightly.
