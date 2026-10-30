#!/usr/bin/env python3
"""Eighteen seasons of SCFL, joined to the sixteen franchises playing now.

    import history
    h = history.load()
    h.alltime(rid)            # lifetime record, titles, seasons
    h.series(rid_a, rid_b, st) # all-time head-to-head, current season folded in

Three files hold the past and none of them knows about this week.

- `records.json` is League Legacy's all-time table, 2005-2025: one row a
  franchise with its lifetime record, win percentage, playoff appearances and
  titles.
- `rivalries.json` is 107 pairwise rows built by scripts/build_rivalries.py
  from `history.json` -- every meeting between two franchises since 2008, with
  the series record, the playoff meetings, the biggest win, the worst loss and
  the closest game. It stops at 2025.
- the week files in `week-data/` are this season.

So anything quoted as all-time has to be the stored row PLUS what has happened
since August, or the magazine publishes a head-to-head record that is a year
out of date -- which reads exactly like a correct one.

Franchises are keyed by `roster_id`, resolved through the alias table in
`scfl-franchises.json` once at load. Managers rename constantly (THE DICKS ->
Wade Garrets -> Wookie Leaks, Forty2V -> Horsecollars, Heavy Hitters -> Phins
Phag), and a rename that fails to resolve silently drops a team's whole past.
`load()` therefore reports what it could not resolve rather than returning
quietly, and `unresolved` is printed by the issue build.

One caveat the copy inherits rather than fixes: League Legacy keeps THE DICKS
(38-65-1) and Wookie Leaks (51-97) as separate franchises even though the
chair has been the same, and `rivalries.json` agrees with it -- the BIG BLUE
series reads "since 2015" rather than from 2008. Both sources tell the same
story as each other, so a lifetime record quoted here is the league's own
record of that franchise, not of that man.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Renames the stored alias table has not caught up with. Each is the 2026 name
# on the left and the franchise it has always been on the right; they are here
# rather than in the JSON because the JSON is generated and this is the list
# that has to be read when a side disappears from the history.
ALIAS = {
    'nwo': 'newworldorder',          # n.W.o
    'gumbas': 'gumbas',              # the stored table has hairygumbas only
    'phinsphag': 'heavyhitters',     # renamed mid-2026
    'forty2v': 'horsecollars',
    'heavyhitters': 'heavyhitters',
}

norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower())


class History:
    def __init__(self, fr, rec, riv):
        self.fr, self.rec, self.riv = fr, rec, riv
        self.key_of = {}          # roster_id -> franchise key
        self.unresolved = []
        # A league in its first season has no past, and that is not an error.
        # Every accessor already returns None when it cannot resolve a side, so
        # an empty History simply prints no history lines -- which is the true
        # thing to print. load() used to raise FileNotFoundError instead and
        # took the whole issue down with it.
        self.empty = not (self.rec.get('standings') or self.riv.get('rows'))

    def bind(self, table):
        """Tie this season's roster_ids to franchise keys. Call once per build."""
        look = self.fr.get('lookup') or {}
        if self.empty and not look:
            return self                      # nothing to bind to; say nothing
        for r in table:
            k = look.get(norm(r['team'])) or ALIAS.get(norm(r['team']))
            if k:
                self.key_of[r['roster_id']] = k
            else:
                self.unresolved.append(r['team'])
        return self

    def alltime(self, rid, table=None):
        """Lifetime record through 2025, with this season added if `table` is given."""
        k = self.key_of.get(rid)
        if not k:
            return None
        look = self.fr.get('lookup') or {}
        row = next((x for x in (self.rec.get('standings') or [])
                    if (look.get(norm(x['name'])) or ALIAS.get(norm(x['name']))) == k), None)
        if not row:
            return None
        w, l, t = (list(map(int, row['record'].split('-'))) + [0])[:3]
        out = {'w': w, 'l': l, 't': t, 'seasons': row.get('numSeasons'),
               'titles': row.get('titles') or 0, 'playoffs': row.get('playoffs') or 0,
               'through': self.rec['span'].split('-')[-1]}
        if table:
            me = next((x for x in table if x['roster_id'] == rid), None)
            if me:
                out['w'] += me['w']; out['l'] += me['l']; out['t'] += me['t']
                out['through'] = None          # now current
        out['record'] = f"{out['w']}-{out['l']}" + (f"-{out['t']}" if out['t'] else '')
        out['pct'] = (out['w'] + out['t'] / 2) / max(1, out['w'] + out['l'] + out['t'])
        return out

    def series(self, a, b, st):
        """All-time head-to-head between two roster_ids, from a's side.

        `a` and `b` are the standings rows, so this season's meetings come out
        of their trails and are added to the stored series. Returns None when
        the two have never met at all.
        """
        ka, kb = self.key_of.get(a['roster_id']), self.key_of.get(b['roster_id'])
        if not ka or not kb or ka == kb:
            return None
        hand = self.fr.get('handles') or {}
        row = None
        for x in (self.riv.get('rows') or []):
            if {hand.get(x['ka']), hand.get(x['kb'])} == {ka, kb}:
                row = x
                break
        if row:
            w, l = (list(map(int, row['rec'].split('-'))) + [0])[:2]
            flip = hand.get(row['ka']) != ka
            d = row.get('detail') or {}
            out = {'w': l if flip else w, 'l': w if flip else l,
                   'g': row['g'], 'po': row.get('po') or 0, 'div': row.get('div') or 0,
                   'first': (d.get('first')), 'last': d.get('last'),
                   'biggest': d.get('biggest' 'Win') or d.get('biggestWin'),
                   'worst': d.get('worstLoss'), 'closest': d.get('closest'),
                   'streak': d.get('streak'), 'porec': d.get('playoff'),
                   'flip': flip, 'stored_through': 2025}
        else:
            out = {'w': 0, 'l': 0, 'g': 0, 'po': 0, 'div': 0, 'first': None,
                   'last': None, 'biggest': None, 'worst': None, 'closest': None,
                   'streak': None, 'porec': None, 'flip': False,
                   'stored_through': 2025}
        # this season, which no stored file knows about
        now = []
        for lg in a.get('trail') or []:
            if (lg[4] or '').strip() == b['team'].strip():
                now.append(lg)
        for wk, res, me, them, _ in now:
            out['g'] += 1
            out['w' if res == 'W' else 'l' if res == 'L' else 'g'] += 1
            out['last'] = {'y': int(st['season']), 'wk': wk, 'po': False,
                           'r': res, 'for': me, 'against': them}
        out['this_season'] = [(wk, res, me, them) for wk, res, me, them, _ in now]
        # The stored streak is whoever was winning the series when 2025 ended.
        # A meeting since then may have extended or ended it and the stored row
        # cannot say which, so it is only offered when they have not met yet
        # this season -- and it is stated from the stored row's side, so it
        # flips with everything else.
        # Everything stored is written from the stored row's own side. Flip it
        # here, once, so a caller never has to think about orientation: after
        # this, `biggest` is a's biggest win over b, `worst` is a's worst
        # defeat by b, and `closest` reads for/against from a. Leaving the
        # flip to the caller is how a 26-1 series nearly printed the wrong
        # game as the one defeat.
        if out['flip']:
            out['biggest'], out['worst'] = out['worst'], out['biggest']
            for g in ('biggest', 'worst', 'closest'):
                if out[g]:
                    out[g] = dict(out[g], **{'for': out[g]['against'],
                                             'against': out[g]['for'],
                                             'r': {'W': 'L', 'L': 'W'}.get(out[g].get('r'),
                                                                           out[g].get('r'))})
        if out['porec'] and out['flip']:
            out['porec'] = {'w': out['porec'].get('l', 0), 'l': out['porec'].get('w', 0)}
        if out['this_season'] or not out['streak']:
            out['streak'] = None
        elif out['flip']:
            k = out['streak'].get('kind')
            out['streak'] = dict(out['streak'],
                                 kind={'W': 'L', 'L': 'W'}.get(k, k))
        if not out['g']:
            return None
        return out


def load():
    """The past, where there is one.

    All three files are optional. A league playing its first season has no
    records, no rivalries and no alias table, and the honest output for it is
    no history lines at all -- not a stack trace. `h.empty` says which case
    this is, so a caller can skip the whole thread rather than ask eighteen
    questions that all answer None.
    """
    def j(f):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            return {}
        try:
            d = json.load(open(p, encoding='utf-8'))
            return d if isinstance(d, dict) else {}
        except (ValueError, OSError):
            return {}                       # a half-written file is no past
    return History(j('scfl-franchises.json'), j('records.json'), j('rivalries.json'))
