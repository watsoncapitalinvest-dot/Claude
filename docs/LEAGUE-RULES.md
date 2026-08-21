# SCFL house rules worth knowing

League customs that shape the data. Written down because they explain why the
records behave the way they do.

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
