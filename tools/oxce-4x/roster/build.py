"""ROSTER character builder: one run turns every hand layer (characters_*.yaml) into finished records.

  sources  (John's private files, NOT in this repo)  ->  source_extract.json (only the rows the hand layers use)
      Roster_and_Arsenal_Bible.xlsx  Roster, Loadouts
      GI_Joe_XCOM_Catalog.xlsx       Figures, Signature Weapons, Cobra Signature Moves, Joe Recruitment
      CHARACTER_ARTICLES.md          real name, rank line, dossier, quote
  hand layers  characters_<batch>.yaml   only what the sources lack (stat-model inputs, engine route, bonds, voice)
  statmodel.py                         the stats (named = template + rank + 25% secondary + nudge)

Writes (edit the hand layers or the model, never these):
  roster_day1.yaml, roster_<batch>.yaml        records for BUILD (the installer contract in README.md)
  ../mod/Ruleset/gijoe_roster_text.rul         extraStrings only (STR_GJR_*)
  <docs>/ROSTER_Records_<batch>.md             the readable records (project doc)
  <docs>/ROSTER_Review_<batch>.md              one page for John: cards + the FLAGS he must answer
  <docs>/ROSTER_TRACKER.md                     every character: data / figure art / look / sprites

Run:  python3 build.py [--src <dir with the xlsx + articles>] [--docs <out dir>]
Without --src it builds from source_extract.json alone. Owner: ROSTER (claude/status/ROSTER.md)."""
import argparse, glob, json, os, re, sys
import yaml
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import statmodel as SM

K = ['tu', 'stamina', 'health', 'bravery', 'reactions', 'firing', 'throwing', 'strength', 'melee']
KS = SM.K
EV = ['deploy', 'order', 'kill', 'hit', 'down', 'move']
RANKS = {'O-6': 'Colonel', 'O-4': 'Major', 'O-3': 'Captain', 'O-2': 'First Lieutenant', 'E-9': 'Sergeant Major',
         'E-8': 'Master Sergeant', 'E-7': 'Sergeant First Class', 'E-6': 'Staff Sergeant', 'E-5': 'Sergeant', 'E-4': 'Corporal'}
EXTRACT = os.path.join(HERE, 'source_extract.json')

def skey(s): return re.sub(r'[^A-Z0-9]+', '_', s.upper()).strip('_')
def q(s): return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'

# ---------------------------------------------------------------- sources
def rows(wb, sheet):
    r = list(wb[sheet].iter_rows(values_only=True)); h = [str(x).strip() if x else '' for x in r[0]]
    return [dict(zip(h, x)) for x in r[1:] if any(v is not None for v in x)]

def parse_articles(path):
    out, cur = {}, None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(r'^### (.+)$', line)
        if m: cur = out.setdefault(m.group(1).strip(), {'lines': []}); continue
        if line.startswith('## '): cur = None; continue
        if cur is not None: cur['lines'].append(line)
    res = {}
    for name, d in out.items():
        L = [l for l in d['lines'] if l.strip()]
        a = {'header': L[0] if L else ''}
        for l in L[1:]:
            if l.startswith('Real name:'):
                for part in l.split(' | '):
                    k, _, v = part.partition(':'); a[k.strip().lower().replace(' ', '_')] = v.strip()
            elif l.startswith('**Dossier.**'): a['dossier'] = l[len('**Dossier.**'):].strip()
            elif l.startswith('*"') and l.endswith('"*'): a['quote'] = l.strip('*')
        res[name] = a
    return res

def extract(src, wanted):
    import openpyxl
    B = openpyxl.load_workbook(glob.glob(os.path.join(src, '**', 'Roster_and_Arsenal_Bible.xlsx'), recursive=True)[0], read_only=True)
    C = openpyxl.load_workbook(glob.glob(os.path.join(src, '**', 'GI_Joe_XCOM_Catalog.xlsx'), recursive=True)[0], read_only=True)
    art = parse_articles(glob.glob(os.path.join(src, '**', 'CHARACTER_ARTICLES.md'), recursive=True)[0])
    R = {r['ID']: r for r in rows(B, 'Roster')}; L = {r['ID']: r for r in rows(B, 'Loadouts')}
    F = rows(C, 'Figures'); SW = {r['Joe']: r for r in rows(C, 'Signature Weapons') if r.get('Joe')}
    CM = {r['Villain or troop']: r for r in rows(C, 'Cobra Signature Moves') if r.get('Villain or troop')}
    REC = {r['Joe']: r for r in rows(C, 'Joe Recruitment') if r.get('Joe')}
    ex = {'_all': [dict(id=r['ID'], name=r['Character'], faction=r['Faction'], arrives=r['Arrives']) for r in R.values()]}
    for sid in sorted(wanted):
        if sid not in R: ex[sid] = {'missing': 'not in the Bible Roster'}; continue
        r = R[sid]; nm = r['Character']; base = re.sub(r'\s*\(.*\)$', '', nm)
        fig = [f for f in F if f.get('Code Name') == base and (f.get('Faction') == r['Faction'] or r['Faction'] == 'G.I. Joe')]
        fig = fig[0] if fig else {}
        e = dict(id=sid, name=nm, faction=r['Faction'], status=r['Status'], arrives=r['Arrives'], toyYear=r['Toy year'],
                 version=r['Version used'], versionWhy=r['Why that version'], specialty=r['Specialty / role'],
                 figure={k: fig.get(k) for k in ('Toy Year', 'Real Name', 'Role / Specialty', 'Rank', 'Branch', 'Sub-team / Note')} if fig else None,
                 loadout={k: L.get(sid, {}).get(k) for k in ('Weapon name shown in game', 'Armory type', 'Type name', 'Mastery track', 'Attachments')},
                 sig=None, cobra=None, recruit=None, article=art.get(nm.upper()))
        if nm in SW: e['sig'] = {k: SW[nm].get(k) for k in ('Signature weapon', 'Signature move (once per mission)', 'Mastery track (unlocks in order)')}
        if nm in CM: e['cobra'] = {k: CM[nm].get(k) for k in ('Signature weapon', 'Trait', 'Signature move (once per mission) or squad ability')}
        if nm in REC: e['recruit'] = {k: REC[nm].get(k) for k in ('Channel', 'How', 'Requirement / reason', 'To stay (else on leave)')}
        ex[sid] = e
    return ex

# ---------------------------------------------------------------- build
def split_named(s):
    """'Coward: withdraws when hurt' -> ('Coward', 'Withdraws when hurt.')"""
    if not s: return None, None
    n, _, t = s.partition(':'); t = t.strip()
    if not t: return None, n.strip()
    t = t[0].upper() + t[1:]
    return n.strip().strip('"'), t if t.endswith('.') else t + '.'

def build(src=None, docs=None):
    layers = sorted(glob.glob(os.path.join(HERE, 'characters_*.yaml')))
    H = {os.path.basename(p)[11:-5]: yaml.safe_load(open(p)) for p in layers}
    wanted = {c.get('source') or 'C_' + c['key'] for b in H.values() for c in b['characters']}
    if src:
        EX = extract(src, wanted); json.dump(EX, open(EXTRACT, 'w'), indent=1, ensure_ascii=False, default=str)
    EX = json.load(open(EXTRACT))
    out, strings, flags = {}, {}, {}
    for batch, B in H.items():
        recs = []
        for c in B['characters']:
            key = c['key']; sid = c.get('source') or 'C_' + key; e = EX.get(sid, {}); fl = flags.setdefault(key, [])
            if 'missing' in e or not e: fl.append(f'SOURCE: {sid} {e.get("missing", "not extracted")}')
            name = c.get('name') or e.get('name', key)
            st = SM.named(c['rank'], c['primary'], c.get('secondary'), c.get('nudge') or {})
            # weapon, trait, move: hand value if given, else the source's
            w = c.get('weapon') or {}
            lo = e.get('loadout') or {}
            weapon = dict(name=w.get('name') or lo.get('Weapon name shown in game'), armory=w.get('armory') or [lo.get('Armory type')],
                          mastery=w.get('mastery', lo.get('Mastery track')), attachments=w.get('attachments', lo.get('Attachments')))
            if w.get('armory') and lo.get('Armory type') and lo['Armory type'] not in w['armory']:
                fl.append(f"WEAPON: hand armory {w['armory']} vs Bible {lo['Armory type']}")
            cob = e.get('cobra') or {}; sig = e.get('sig') or {}
            tn, tt = split_named(cob.get('Trait'))
            mn, mt = split_named(cob.get('Signature move (once per mission) or squad ability') or sig.get('Signature move (once per mission)'))
            T = c.get('trait') or {}; M = c.get('move') or {}
            trait = dict(name=T.get('name') or tn, text=T.get('text') or tt, engine=T.get('engine'), effect=T.get('effect'))
            move = dict(name=M.get('name') or mn, text=M.get('text') or mt, engine=M.get('engine'), effect=M.get('effect'))
            if M.get('name') and mn and skey(M['name']) != skey(mn) and not M.get('decided'): fl.append(f"MOVE NAME: hand '{M['name']}' vs Catalog '{mn}'")
            for what, d in (('trait', trait), ('move', move)):
                if not d['name']: fl.append(f'GAP: no {what}')
            art = e.get('article') or {}
            voice = dict(c.get('voice') or {})
            if 'move' not in voice and art.get('quote'): voice['move'] = art['quote'].strip('"')
            for ev in EV:
                if not voice.get(ev): fl.append(f'GAP: voice line "{ev}"')
            if c.get('window', '').startswith('PROPOSED'): fl.append(f"WINDOW: {c['window']} (Bible: {e.get('arrives')})")
            fig = e.get('figure') or {}
            canon_rank = fig.get('Rank')
            if c.get('rankNote'): fl.append(f"RANK: {c['rank']} used as tier ({c['rankNote']})")
            elif canon_rank and c['rank'] not in canon_rank: fl.append(f"RANK: model {c['rank']} vs Catalog {canon_rank}")
            faction = e.get('faction') or c.get('faction')
            is_joe = faction == 'G.I. Joe'
            # shown rank: the Joes' canon rank; a villain shows his canon rank only (a tier is a model input, not a title)
            shown = RANKS[c['rank']] if is_joe else (re.sub(r'\s*\(.*\)$', '', canon_rank) if canon_rank else None)
            rank_key = ('STR_GJR_RANK_' + skey(shown)) if shown else None
            if shown: strings[rank_key] = shown
            strings[f'STR_GJR_TRAIT_{key}'] = trait['name'] or ''; strings[f'STR_GJR_TRAIT_{key}_DESC'] = trait['text'] or ''
            strings[f'STR_GJR_MOVE_{key}'] = move['name'] or ''; strings[f'STR_GJR_MOVE_{key}_DESC'] = move['text'] or ''
            for ev in EV:
                if voice.get(ev): strings[f'STR_GJR_VOICE_{key}_{ev.upper()}'] = voice[ev]
            for sp in (c['primary'], c.get('secondary')):
                if sp: strings['STR_GJR_SPEC_' + skey(sp)] = sp
            rec = dict(id='C_' + key, name=name)
            if is_joe:
                rec |= dict(soldierType='STR_' + key, rosterStatus=c.get('status'), rank=c['rank'], rankString=rank_key,
                            allowPromotion=False, costBuy=0)
            else:
                rec |= dict(source=sid, faction=faction, unitType=c.get('unit'), rank=c['rank'], rankString=rank_key,
                            window=c.get('window'), neverDies=True)
            rec |= dict(primary='STR_GJR_SPEC_' + skey(c['primary']),
                        secondary=('STR_GJR_SPEC_' + skey(c['secondary'])) if c.get('secondary') else None,
                        stats={k: st[ks] for k, ks in zip(K, KS)} | {'psiStrength': 0, 'psiSkill': 0}, weapon=weapon,
                        trait=dict(name=f'STR_GJR_TRAIT_{key}', desc=f'STR_GJR_TRAIT_{key}_DESC', engine=trait['engine']) | ({'effect': trait['effect']} if trait['effect'] else {}),
                        move=dict(name=f'STR_GJR_MOVE_{key}', desc=f'STR_GJR_MOVE_{key}_DESC', engine=move['engine'], perMission=1) | ({'effect': move['effect']} if move['effect'] else {}),
                        bonds=c.get('bonds') or [], grudges=c.get('grudges') or [],
                        voice={ev: f'STR_GJR_VOICE_{key}_{ev.upper()}' for ev in EV if voice.get(ev)})
            if is_joe:
                rec |= dict(dossier=f'STR_ART_{key}_TEXT (generated in the design repo, not yet wired)', look=c.get('look'))
            else:
                rec |= dict(dossier=f'STR_ART_{skey(e.get("name", key))}_TEXT (design repo, not yet wired)')
            # what the readable docs need (not written to the data files)
            rec['_doc'] = dict(name=name, faction=faction, art=art, e=e, trait=trait, move=move, voice=voice, st=st, c=c)
            recs.append(rec)
        out[batch] = recs
    return out, strings, flags

# ---------------------------------------------------------------- write
def y(v, ind):
    p = '  ' * ind
    if isinstance(v, dict):
        return ''.join(f"\n{p}{k}:" + (' ' + y(x, ind + 1) if not isinstance(x, (dict, list)) or not x else y(x, ind + 1)) for k, x in v.items())
    if isinstance(v, list):
        if not v: return '[]'
        return ''.join(f"\n{p}- " + (y(x, ind + 1).lstrip('\n').lstrip() if isinstance(x, dict) else y(x, ind + 1)) for x in v)
    if v is None: return 'null'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return str(v)
    return q(str(v))

def clean(r): return {k: v for k, v in r.items() if not k.startswith('_')}

def write(out, strings, flags, docs):
    unn = {('STR_GJR_SPEC_' + skey(p)): dict(name=p, start={k: s[ks] for k, ks in zip(K, KS)}, cap={k: c[ks] for k, ks in zip(K, KS)})
           for p in SM.T for s, c in [SM.unnamed(p)]}
    for p in SM.T: strings['STR_GJR_SPEC_' + skey(p)] = p
    for batch, recs in out.items():
        fn = 'roster_day1.yaml' if batch == 'day1' else f'roster_{batch}.yaml'
        with open(os.path.join(HERE, fn), 'w') as f:
            if batch == 'day1':
                f.write('# ROSTER data, Day-1 Joes (generated by build.py from characters_day1.yaml - edit those, not this file).\n'
                        '# Named Joes: stats fixed for the game (John 12 Nov 21:13): minStats = maxStats = statCaps = stats; allowPromotion false; costBuy 0 (not hireable).\n'
                        '# Unnamed Joes by specialty: roll around start, grow to cap (cap = 78% of the specialty template; John 21:16).\n'
                        '# Text keys resolve in mod/Ruleset/gijoe_roster_text.rul.\n')
                f.write('named:' + y([clean(r) for r in recs], 1) + '\nunnamed:' + y(unn, 1) + '\n')
            else:
                f.write(f'# ROSTER data, {batch} (generated by build.py from characters_{batch}.yaml - edit those, not this file).\n'
                        '# Named villains: OXCE unit stats = stats (fixed; the engine adds its own difficulty bonus on top).\n'
                        '# Never die: go down, are captured, or escape. window = campaign months (gijoe_availability.rul is BUILD\'s).\n'
                        '# Text keys resolve in mod/Ruleset/gijoe_roster_text.rul.\n')
                f.write('named:' + y([clean(r) for r in recs], 1) + '\n')
    joe_types = {'STR_' + r['id'][2:] for recs in out.values() for r in recs if 'soldierType' in r}
    with open(os.path.join(HERE, '..', 'mod', 'Ruleset', 'gijoe_roster_text.rul'), 'w') as f:
        f.write('# ROSTER text (generated by tools/oxce-4x/roster/build.py - edit the hand layers, not this file).\n'
                '# Strings only: canon ranks, specialties, signature traits and moves, voice lines. Unit and soldier-type names are BUILD\'s.\n'
                '# Owner: ROSTER (claude/status/ROSTER.md). Data: tools/oxce-4x/roster/roster_*.yaml.\nextraStrings:\n  - type: en-US\n    strings:\n')
        for k in sorted(strings):
            if k in joe_types: continue
            f.write(f'      {k}: {q(strings[k])}\n')
    if docs: write_docs(out, flags, docs); write_tracker(out, docs)
    print('records', {b: len(r) for b, r in out.items()}, 'strings', len(strings), 'flags', sum(len(v) for v in flags.values()))

def strings_rank(r):
    c = r['_doc']['c']; e = r['_doc']['e']; canon = ((e.get('figure') or {}).get('Rank'))
    if c.get('rankNote'): return f"no canon rank (model tier {c['rank']})"
    return canon or f"{RANKS[c['rank']]} ({c['rank']})"

def write_docs(out, flags, docs):
    os.makedirs(docs, exist_ok=True)
    for batch, recs in out.items():
        if batch == 'day1': continue
        L = [f'# ROSTER records, {batch}', 'Generated by tools/oxce-4x/roster/build.py. Sources: Bible (Roster, Loadouts), Catalog (Figures, Cobra Signature Moves), character articles; stats from statmodel.py.', '']
        R = [f'# ROSTER review, {batch}: one card each, then the questions', 'Anything not under QUESTIONS goes in as written.', '']
        for r in recs:
            d = r['_doc']; a = d['art'] or {}; e = d['e']; st = d['st']; c = d['c']
            stl = ' / '.join(f'{k} {st[k]}' for k in KS)
            shown = strings_rank(r)
            L += [f"## {d['name']}", f"{d['faction']} - {shown} - {c['primary']}{(' / ' + c['secondary']) if c.get('secondary') else ''}",
                  f"Real name: {a.get('real_name', '?')} | Version: {e.get('version')} | Bible arrives: {e.get('arrives')} | Window: {r.get('window') or '-'}",
                  f"Unit: {r.get('unitType') or r.get('soldierType')}", f'Stats: {stl}',
                  f"Weapon: {r['weapon']['name']} ({', '.join(x for x in r['weapon']['armory'] if x)})",
                  f"Trait - {d['trait']['name']}: {d['trait']['text']} [{d['trait']['engine']}] {d['trait'].get('effect') or ''}",
                  f"Move - {d['move']['name']}: {d['move']['text']} [{d['move']['engine']}] {d['move'].get('effect') or ''}",
                  f"Bonds: {'; '.join(r['bonds']) or '-'} | Grudges: {'; '.join(r['grudges']) or '-'}",
                  'Voice: ' + ' / '.join(f'{k}: "{v}"' for k, v in d['voice'].items()),
                  f"Dossier: {a.get('dossier', '(none)')}", '']
            R += [f"**{d['name']}** - {shown}, {c['primary']}. {stl}. {d['trait']['name']} / {d['move']['name']}. "
                  f"Window {r.get('window') or '-'}.", '']
        R += ['## QUESTIONS (answer only these)', '']
        n = 0
        for r in recs:
            k = r['id'][2:]
            for f_ in flags.get(k, []):
                if f_.startswith(('WINDOW', 'SOURCE', 'GAP', 'MOVE NAME', 'WEAPON')) or (f_.startswith('RANK') and 'vs' in f_):
                    n += 1; R.append(f'{n}. {r["_doc"]["name"]}: {f_}')
        open(os.path.join(docs, f'ROSTER_Records_{batch}.md'), 'w').write('\n'.join(L) + '\n')
        open(os.path.join(docs, f'ROSTER_Review_{batch}.md'), 'w').write('\n'.join(R) + '\n')

def write_tracker(out, docs):
    EX = json.load(open(EXTRACT)); T = yaml.safe_load(open(os.path.join(HERE, 'tracker.yaml')))
    have = {r['id'][2:]: b for b, recs in out.items() for r in recs}
    src_of = {r.get('source'): r['id'][2:] for recs in out.values() for r in recs if r.get('source')}
    fig = {k: 'approved' for k in T['figure']['A']} | {k: 'comic' for k in T['figure']['C'] if k not in T['figure']['A']}
    L = ['# ROSTER tracker: every character in the Bible', 'Generated by tools/oxce-4x/roster/build.py from the Bible roster + tracker.yaml. '
         'data = ROSTER record done (batch); figure = equipment-screen figure; look = 3D look shipped (owner); sprites = game sheet.', '',
         '| Character | Faction | Arrives | data | figure | look | sprites |', '|---|---|---|---|---|---|---|']
    done = {'data': 0, 'figure': 0, 'look': 0, 'sprites': 0}
    for a in EX.get('_all', []):
        keys = [k for s_, k in src_of.items() if s_ == a['id']] or [a['id'][2:]]
        cells = []
        for col in ('data', 'figure', 'look', 'sprites'):
            v = [have.get(k) if col == 'data' else fig.get(k) if col == 'figure' else T['look'].get(k) if col == 'look' else ('yes' if k in T['sprites'] else None) for k in keys]
            v = [x for x in v if x]; cells.append(', '.join(sorted(set(v))) if v else '-'); done[col] += bool(v)
        L.append(f"| {a['name']} | {a['faction']} | {a['arrives']} | " + ' | '.join(cells) + ' |')
    n = len(EX.get('_all', []))
    L[2] = f'Totals of {n}: ' + ', '.join(f'{k} {v}' for k, v in done.items()) + '.'
    open(os.path.join(docs, 'ROSTER_TRACKER.md'), 'w').write('\n'.join(L) + '\n')


# ---------------------------------------------------------------- draft a new hand layer from the sources
SPEC_WORDS = [  # first match wins: catalog role / Bible specialty / armory type -> stat-model specialty
    ('Martial Arts', ('ninja', 'martial', 'W_SWORD', 'W_BOW', 'W_NUNCHAKU', 'boxing', 'staff', 'blade')),
    ('Pilot', ('pilot', 'aviat', 'glider')),
    ('Recon & Sniper', ('sniper', 'marksman', 'recon', 'W_SNIPER', 'tracker', 'poacher', 'hunt')),
    ('Demolitions & Engineering', ('demolition', 'explosive', 'sabot', 'W_CHARGE', 'engineer', 'toxic')),
    ('Covert Ops & Intel', ('intelligence', 'espionage', 'spy', 'disguise', 'infiltrat', 'assassin', 'interrogat', 'hypno')),
    ('Medic', ('medic', 'doctor', 'surgeon')),
    ('Comms & Tech', ('scien', 'computer', 'electronic', 'technic', 'mind')),
    ('Armor & Vehicles', ('driver', 'tank', 'vehicle', 'motor')),
    ('Naval & Divers', ('swamp', 'naval', 'diver', 'water', 'sea', 'croc')),
    ('Arctic & Mountain', ('arctic', 'snow', 'mountain')),
    ('Heavy Weapons', ('W_FLAMER', 'W_ROCKET', 'W_MISSILE', 'W_LMG', 'W_HMG', 'W_HEAVY_MELEE', 'heavy', 'anti-armor', 'weapons')),
    ('Command', ('leader', 'command', 'emperor', 'tactician', 'warlord', 'boss', 'dictator')),
]
def guess_spec(text):
    t = text.lower()
    for sp, words in SPEC_WORDS:
        if any(w.lower() in t for w in words): return sp
    return 'Infantry'

def draft(src, batch, arrives, factions):
    path = os.path.join(HERE, f'characters_{batch}.yaml')
    if os.path.exists(path): sys.exit(f'{path} exists - edit it instead')
    import openpyxl
    B = openpyxl.load_workbook(glob.glob(os.path.join(src, '**', 'Roster_and_Arsenal_Bible.xlsx'), recursive=True)[0], read_only=True)
    C = openpyxl.load_workbook(glob.glob(os.path.join(src, '**', 'GI_Joe_XCOM_Catalog.xlsx'), recursive=True)[0], read_only=True)
    L = {r['ID']: r for r in rows(B, 'Loadouts')}; F = rows(C, 'Figures')
    done = {c.get('source') or 'C_' + c['key'] for p in glob.glob(os.path.join(HERE, 'characters_*.yaml')) for c in yaml.safe_load(open(p))['characters']}
    out = []
    for r in rows(B, 'Roster'):
        if r['Arrives'] != arrives or (factions and r['Faction'] not in factions) or r['ID'] in done: continue
        base = re.sub(r'\s*\(.*\)$', '', r['Character'])
        fig = next((f for f in F if f.get('Code Name') == base), {})
        lo = L.get(r['ID'], {})
        role = ' '.join(str(x) for x in (fig.get('Role / Specialty'), r.get('Specialty / role'), lo.get('Armory type')) if x)
        spec = r['Specialty / role'] if r['Specialty / role'] in SM.T else guess_spec(role)
        m = re.search(r'\(([EO]-\d)\)', str(fig.get('Rank') or ''))
        joe = r['Faction'] == 'G.I. Joe'
        c = dict(key=r['ID'][2:], source=r['ID'])
        if m and m.group(1) in SM.RANK: c['rank'] = m.group(1)
        elif joe: c['rank'] = 'E-5'; c['rankNote'] = 'DRAFT: no canon rank found - check the file card'
        else:
            lead = any(w in role.lower() for w in ('leader', 'command', 'emperor', 'warlord', 'boss'))
            c['rank'] = 'O-3' if lead else 'E-6'; c['rankNote'] = 'no canon rank; ' + ('lieutenant tier' if lead else 'specialist tier')
        c |= dict(primary=spec, secondary=None, nudge={}, draftRole=role)
        if joe: c['status'] = r['Arrives']
        else: c |= dict(unit=f'STR_{r["ID"][2:]}_UNIT', window=f'PROPOSED ? ({r["Arrives"]})')
        c |= dict(trait=dict(engine='script', effect=None), move=dict(engine='request' if joe else 'ai-fork', effect=None),
                  bonds=[], grudges=[], voice={})
        out.append(c)
    yaml.safe_dump({'batch': batch, 'characters': out}, open(path, 'w'), sort_keys=False, allow_unicode=True, width=200)
    print(f'drafted {len(out)} -> {path}: check primary/rank/nudge, write effect numbers, bonds, grudges and 5 voice lines; delete draftRole')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--src'); ap.add_argument('--docs')
    ap.add_argument('--draft', help='new batch name: draft characters_<batch>.yaml from the sources (needs --src, --arrives)')
    ap.add_argument('--arrives', help="the Bible's Arrives value, e.g. 'Batch 2: Acts 3 and 4'")
    ap.add_argument('--faction', action='append', help='limit the draft to these factions (repeatable)')
    a = ap.parse_args()
    if a.draft: draft(a.src, a.draft, a.arrives, a.faction); sys.exit(0)
    o, s, f = build(a.src, a.docs); write(o, s, f, a.docs)
    for k, v in f.items():
        for x in v: print(f'  {k}: {x}')
