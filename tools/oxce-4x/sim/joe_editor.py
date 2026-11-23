"""G.I. JOE 4x - JOE LAB's Rules Editor and My Play Style tabs (BUILD-1, 18 Nov 2026).

John 18:26 "record my play style to learn and play like i do in sims", 18:27 "can make it so it can change things in the
game? change anything? add anything?"

RULES EDITOR
  Every rule in the installed mod (user\\mods\\GIJoe4x\\Ruleset), by kind, with search. Pick an entry: its effective
  values (all the files that set it, merged in load order) show as text. Edit and Save: the whole entry goes into YOUR
  override file, zzzz_john_changes.rul, which loads after everything else, so the mod's own files are never touched.
  Duplicate: a copy under a new name, to add a weapon, topic, mission, event... Strings are their own kind.
  Check: starts the game on your changes for 40 seconds and lists the errors it logged.
  Every save is logged in lab\\CHANGES_LOG.txt with your note; the master copy is lab\\john_changes.rul.
  It cannot add mechanics that need engine code, or draw art (a rule can point at any picture the mod already has).

MY PLAY STYLE
  Your own campaigns write user\\playstyle.txt (the game does it, once an hour: research you start, missions and Cobra
  sites you answer - how fast, how many, in what - and the ones you let go). This tab turns that into a profile
  (lab\\profile.txt): your research order, how often you answer each kind of mission, how long you take, your squad
  size. Tick "Simulations play like me" and the Campaign and Checks tabs play by it. Battles stay the game's AI.
"""
import os, re, sys, glob, json, time, shutil, subprocess, statistics, datetime, threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

try:
    import yaml
except ImportError:
    yaml = None

OVERRIDE = 'zzzz_john_changes.rul'
KEYS = ('type', 'name', 'id', 'delete')


def need_yaml(parent=None):
    """PyYAML reads the rule files; it installs itself once if missing (needs the internet that one time)"""
    global yaml
    if yaml: return True
    if not messagebox.askyesno('Joe Lab', 'The Rules Editor needs PyYAML, a small Python add-on. Install it now (one time, needs the internet)?'):
        return False
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'pyyaml'], check=True,
                       creationflags=0x08000000 if sys.platform.startswith('win') else 0)
        import importlib, site
        importlib.invalidate_caches(); sys.path.append(site.getusersitepackages())
        yaml = importlib.import_module('yaml')
        return True
    except Exception as e:
        messagebox.showerror('Joe Lab', f'Could not install PyYAML: {e}')
        return False


_LOADER = None


def L():
    """a safe loader that reads OXCE's !tags as plain values (made once PyYAML is there)"""
    global _LOADER
    if _LOADER is None:
        class _L(yaml.SafeLoader):
            pass

        def _any_tag(loader, suffix, node):
            if isinstance(node, yaml.MappingNode): return loader.construct_mapping(node, deep=True)
            if isinstance(node, yaml.SequenceNode): return loader.construct_sequence(node, deep=True)
            return loader.construct_scalar(node)
        _L.add_multi_constructor('!', _any_tag)
        _LOADER = _L
    return _LOADER


def entry_id(e):
    if not isinstance(e, dict): return None
    for k in KEYS:
        if k in e and isinstance(e[k], (str, int)): return k, str(e[k])
    return None


def merge(a, b):
    out = dict(a)
    for k, v in b.items(): out[k] = v
    return out


class Rules:
    """the installed mod's rules, merged in the game's load order (alphabetical: a later file wins)"""

    def __init__(self, ruleset_dir):
        self.dir = ruleset_dir
        self.kinds = {}      # kind -> {id: entry}
        self.where = {}      # (kind, id) -> [files]
        self.idkey = {}      # (kind, id) -> 'type' / 'name' / 'id'
        self.strings = {}    # key -> text (en-US)
        self.singles = {}    # top-level blocks that are one mapping (cobraNetwork, ...)
        self.errors = []
        # the stock X-COM rules first (the game loads them under every mod): <game>\standard\xcom1, four folders up
        # from user\mods\GIJoe4x\Ruleset, so the M4 Carbine (stock STR_RIFLE) and the rest are here too
        game = os.path.normpath(os.path.join(ruleset_dir, '..', '..', '..', '..'))
        std = os.environ.get('JOE_STANDARD', os.path.join(game, 'standard', 'xcom1'))
        lang = os.path.join(std, 'Language', 'en-US.yml')
        if os.path.exists(lang):
            try:
                d = yaml.load(open(lang, encoding='utf-8', errors='replace'), Loader=L()) or {}
                self.strings.update({str(k): str(v) for k, v in (d.get('en-US') or {}).items()})
            except Exception as e:
                self.errors.append(f'en-US.yml: {str(e).splitlines()[0]}')
        mlang = os.path.join(ruleset_dir, '..', 'Language', 'en-US.yml')   # the mod's own names (M4 Carbine ...)
        if os.path.exists(mlang):
            try:
                d = yaml.load(open(mlang, encoding='utf-8', errors='replace'), Loader=L()) or {}
                self.strings.update({str(k): str(v) for k, v in (d.get('en-US') or {}).items()})
            except Exception as e:
                self.errors.append(f'mod en-US.yml: {str(e).splitlines()[0]}')
        files = (sorted(glob.glob(os.path.join(std, '*.rul'))) if os.path.isdir(std) else []) \
            + sorted(glob.glob(os.path.join(ruleset_dir, '*.rul')), key=lambda p: os.path.basename(p))
        for f in files:
            try:
                doc = yaml.load(open(f, encoding='utf-8', errors='replace'), Loader=L()) or {}
            except Exception as e:
                self.errors.append(f'{os.path.basename(f)}: {str(e).splitlines()[0]}'); continue
            if not isinstance(doc, dict): continue
            for kind, val in doc.items():
                if kind == 'extraStrings' and isinstance(val, list):
                    for blk in val:
                        if isinstance(blk, dict) and blk.get('type') == 'en-US' and isinstance(blk.get('strings'), dict):
                            for k, v in blk['strings'].items(): self.strings[str(k)] = str(v)
                    continue
                if isinstance(val, list):
                    for e in val:
                        ident = entry_id(e)
                        if not ident: continue
                        key, i = ident
                        d = self.kinds.setdefault(kind, {})
                        d[i] = merge(d.get(i, {}), e)
                        self.idkey[(kind, i)] = key
                        self.where.setdefault((kind, i), []).append(os.path.basename(f))
                elif isinstance(val, dict):
                    self.singles[kind] = merge(self.singles.get(kind, {}), val)
                    self.where.setdefault((kind, ''), []).append(os.path.basename(f))


class Changes:
    """your override file: {kind: {id: entry}}, strings, and single blocks"""

    def __init__(self, master):
        self.master = master
        self.lists, self.strings, self.singles = {}, {}, {}
        if os.path.exists(master) and yaml:
            try: doc = yaml.load(open(master, encoding='utf-8'), Loader=L()) or {}
            except Exception: doc = {}
            for kind, val in doc.items():
                if kind == 'extraStrings':
                    for blk in val or []:
                        if blk.get('type') == 'en-US': self.strings.update({str(k): str(v) for k, v in (blk.get('strings') or {}).items()})
                elif isinstance(val, list):
                    for e in val:
                        ident = entry_id(e)
                        if ident: self.lists.setdefault(kind, {})[ident[1]] = e
                elif isinstance(val, dict):
                    self.singles[kind] = val

    def doc(self):
        d = {k: list(v.values()) for k, v in self.lists.items() if v}
        d.update({k: v for k, v in self.singles.items() if v})
        if self.strings:
            d['extraStrings'] = [{'type': 'en-US', 'strings': dict(self.strings)}, {'type': 'en-GB', 'strings': dict(self.strings)}]
        return d

    def write(self, targets):
        text = ('# JOHN\'S CHANGES, made in JOE LAB\'s Rules Editor. Loads after every other rule file, so what is here wins.\n'
                '# The change log with his notes: lab\\CHANGES_LOG.txt. BUILD-1 folds the keepers into the mod.\n'
                + yaml.safe_dump(self.doc(), sort_keys=False, allow_unicode=True, width=140))
        os.makedirs(os.path.dirname(self.master), exist_ok=True)
        open(self.master, 'w', encoding='utf-8').write(text)
        for t in targets:
            if os.path.isdir(os.path.dirname(t)):
                open(t, 'w', encoding='utf-8').write(text)


def diff_lines(old, new, prefix=''):
    out = []
    for k in list(old.keys()) + [k for k in new if k not in old]:
        if old.get(k) != new.get(k):
            out.append(f'{prefix}{k}: {json.dumps(old.get(k))[:80]} -> {json.dumps(new.get(k))[:80]}')
    return out


# ------------------------------------------------------------------------------------------------------- the tabs
class EditorTab:
    QUICK = [  # (label, block, field, kind of value)
        ("Cobra's job chance a month, per site (%)", 'cobraNetwork', 'crimeChance', int),
        ('Cell strike chance a month (%)', 'cobraNetwork', 'strikeChance', int),
        ("The broadcast's day window [from, to]", 'cobraNetwork', 'broadcastDays', list),
        ("Cobra's first job after the broadcast, days [from, to]", 'cobraNetwork', 'firstJobDays', list),
        ('The factory reopens, day window [from, to]', 'cobraNetwork', 'factoryDays', list),
        ('Police scanner notice (hours)', 'cobraNetwork', 'scannerHours', int),
        ('Front companies at the start', 'cobraNetwork', 'startFronts', int),
        ('Cells at the start', 'cobraNetwork', 'startCells', int),
    ]

    def __init__(self, lab, page, paths):
        self.lab, self.p = lab, paths
        self.rules = None
        self.changes = None
        self.cur = None   # (kind, id)
        bar = ttk.Frame(page); bar.pack(fill='x', pady=(0, 8))
        ttk.Button(bar, text='Load the rules', command=self.load).pack(side='left')
        ttk.Button(bar, text='Check my changes (starts the game 40 s)', command=self.check).pack(side='left', padx=6)
        ttk.Button(bar, text='Open the change log', command=lambda: lab.open_path(self.p['log'])).pack(side='left')
        self.status = ttk.Label(bar, text='Press "Load the rules".', foreground='#8a9198'); self.status.pack(side='left', padx=10)
        body = ttk.Frame(page); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=2); body.columnconfigure(1, weight=5); body.rowconfigure(0, weight=1)
        left = ttk.Frame(body); left.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        self.kind = tk.StringVar()
        self.kindbox = ttk.Combobox(left, textvariable=self.kind, state='readonly', width=30); self.kindbox.pack(fill='x')
        self.kindbox.bind('<<ComboboxSelected>>', lambda e: self.fill())
        self.search = tk.StringVar(); self.search.trace_add('write', lambda *a: self.fill())
        ttk.Entry(left, textvariable=self.search).pack(fill='x', pady=4)
        self.lb = tk.Listbox(left, bg='#1f262c', fg='#e8e4d8', selectbackground='#3d4a55', font=lab.MONO, relief='flat', activestyle='none')
        self.lb.pack(fill='both', expand=True); self.lb.bind('<<ListboxSelect>>', lambda e: self.show())
        right = ttk.Frame(body, style='Panel.TFrame', padding=8); right.grid(row=0, column=1, sticky='nsew')
        self.where = ttk.Label(right, text='', style='Dim.TLabel'); self.where.pack(anchor='w')
        self.text = lab.textbox(right, 22); self.text.configure(wrap='none'); self.text.pack(fill='both', expand=True, pady=4)
        nb = ttk.Frame(right, style='Panel.TFrame'); nb.pack(fill='x')
        ttk.Label(nb, text='Note (why):', style='Panel.TLabel').pack(side='left')
        self.note = tk.StringVar(); ttk.Entry(nb, textvariable=self.note, width=50).pack(side='left', padx=6, fill='x', expand=True)
        bb = ttk.Frame(right, style='Panel.TFrame'); bb.pack(fill='x', pady=(6, 0))
        ttk.Button(bb, text='Save change', style='Go.TButton', command=self.save).pack(side='right')
        ttk.Button(bb, text='Duplicate as new...', command=self.duplicate).pack(side='right', padx=6)
        ttk.Button(bb, text='Undo my change to this', command=self.revert).pack(side='right')

    # ---------------------------------------------------------------------------------------------------- loading
    def load(self):
        if not need_yaml(): return
        if not os.path.isdir(self.p['ruleset']):
            messagebox.showerror('Joe Lab', 'The mod is not unpacked yet. Start the game once with Play_4x.bat.'); return
        self.status.configure(text='Reading every rule file ...'); self.lab.root.update_idletasks()
        self.rules = Rules(self.p['ruleset'])
        self.changes = Changes(self.p['master'])
        kinds = sorted(self.rules.kinds) + ['(strings)', '(quick numbers)'] + sorted('(block) ' + k for k in self.rules.singles)
        self.kindbox.configure(values=kinds)
        self.kind.set('research' if 'research' in self.rules.kinds else kinds[0]); self.fill()
        n = sum(len(v) for v in self.rules.kinds.values())
        mine = sum(len(v) for v in self.changes.lists.values()) + len(self.changes.strings) + len(self.changes.singles)
        self.status.configure(text=f'{n} entries in {len(self.rules.kinds)} kinds, {len(self.rules.strings)} strings. Your changes: {mine}.'
                                   + (f'  {len(self.rules.errors)} file(s) could not be read.' if self.rules.errors else ''))

    def fill(self):
        if not self.rules: return
        k, s = self.kind.get(), self.search.get().lower()
        self.lb.delete(0, 'end')
        if k == '(strings)': ids = sorted(set(self.rules.strings) | set(self.changes.strings))
        elif k == '(quick numbers)': ids = [q[0] for q in self.QUICK]
        elif k.startswith('(block) '): ids = ['(the whole block)']
        else: ids = sorted(set(self.rules.kinds.get(k, {})) | set(self.changes.lists.get(k, {})))
        for i in ids:
            text = self.rules.strings.get(i, '') if k == '(strings)' else ''
            if s and s not in i.lower() and s not in text.lower(): continue
            mark = '* ' if self.mine(k, i) else '  '
            self.lb.insert('end', mark + i)

    def mine(self, k, i):
        if k == '(strings)': return i in self.changes.strings
        if k.startswith('(block) '): return k[8:] in self.changes.singles
        if k == '(quick numbers)': return False
        return i in self.changes.lists.get(k, {})

    def effective(self, k, i):
        if k == '(strings)':
            return {'text': self.changes.strings.get(i, self.rules.strings.get(i, ''))}
        if k.startswith('(block) '):
            b = k[8:]; return merge(self.rules.singles.get(b, {}), self.changes.singles.get(b, {}))
        if k == '(quick numbers)':
            q = next(x for x in self.QUICK if x[0] == i)
            blk = merge(self.rules.singles.get(q[1], {}), self.changes.singles.get(q[1], {}))
            return {q[2]: blk.get(q[2])}
        return merge(self.rules.kinds.get(k, {}).get(i, {}), self.changes.lists.get(k, {}).get(i, {}))

    def show(self):
        sel = self.lb.curselection()
        if not sel: return
        i = self.lb.get(sel[0])[2:]
        k = self.kind.get(); self.cur = (k, i)
        files = self.rules.where.get((k, i), []) if not k.startswith('(') else self.rules.where.get((k[8:], ''), []) if k.startswith('(block) ') else []
        self.where.configure(text=(f'{k}: {i}   set by: ' + ', '.join(files[-4:]) if files else f'{k}: {i}') + ('   [YOUR CHANGE IN FORCE]' if self.mine(k, i) else ''))
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', yaml.safe_dump(self.effective(k, i), sort_keys=False, allow_unicode=True, width=120))

    # ---------------------------------------------------------------------------------------------------- saving
    def parsed(self):
        try:
            v = yaml.load(self.text.get('1.0', 'end'), Loader=L())
        except Exception as e:
            messagebox.showerror('Joe Lab', f'That is not valid rule text:\n{e}'); return None
        if not isinstance(v, dict): messagebox.showerror('Joe Lab', 'An entry is a list of "field: value" lines.'); return None
        return v

    def save(self, new_entry=None, kind=None, ident=None):
        if self.rules: self.changes = Changes(self.p['master'])
        if not self.cur and not new_entry: messagebox.showinfo('Joe Lab', 'Pick an entry first.'); return
        k, i = (kind, ident) if new_entry else self.cur
        v = new_entry if new_entry else self.parsed()
        if v is None: return
        old = self.effective(k, i) if not new_entry else {}
        if k == '(strings)':
            self.changes.strings[i] = str(v.get('text', ''))
        elif k.startswith('(block) '):
            self.changes.singles[k[8:]] = merge(self.changes.singles.get(k[8:], {}), {f: x for f, x in v.items() if self.rules.singles.get(k[8:], {}).get(f) != x})
        elif k == '(quick numbers)':
            q = next(x for x in self.QUICK if x[0] == i)
            self.changes.singles[q[1]] = merge(self.changes.singles.get(q[1], {}), v)
        else:
            idk = self.rules.idkey.get((k, i), 'type')
            v[idk] = v.get(idk, i)
            self.changes.lists.setdefault(k, {})[i] = v
        self.changes.write(self.p['targets'])
        lines = diff_lines(old, v) if not new_entry else [f'NEW, copied from {self.cur[1] if self.cur else "?"}']
        note = self.note.get().strip()
        with open(self.p['log'], 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now():%Y-%m-%d %H:%M}  {k}  {i}' + (f'  -- {note}' if note else '') + '\n')
            for l in lines or ['(no difference)']: f.write('    ' + l + '\n')
        self.note.set('')
        self.status.configure(text=f'Saved: {k} {i}. It is in the game from the next start.')
        self.fill()

    def duplicate(self):
        if not self.cur or self.cur[0].startswith('('): messagebox.showinfo('Joe Lab', 'Pick an entry (a weapon, a topic, a mission ...) to copy.'); return
        k, i = self.cur
        v = self.parsed()
        if v is None: return
        new = simpledialog.askstring('Joe Lab', f'Name for the copy of {i} (for example STR_MY_NEW_GUN):', parent=self.lab.root)
        if not new: return
        new = new.strip()
        if new in self.rules.kinds.get(k, {}) or new in self.changes.lists.get(k, {}):
            messagebox.showerror('Joe Lab', f'{new} already exists in {k}.'); return
        idk = self.rules.idkey.get((k, i), 'type')
        v = dict(v); v[idk] = new
        self.save(new_entry=v, kind=k, ident=new)
        if new not in self.changes.strings and not self.rules.strings.get(new):
            self.changes.strings[new] = new.replace('STR_', '').replace('_', ' ').title(); self.changes.write(self.p['targets'])
        self.status.configure(text=f'Added {new} (a copy of {i}). Give it a name in (strings) and change what you like.')
        self.search.set(new)

    def revert(self):
        if self.rules: self.changes = Changes(self.p['master'])
        if not self.cur: return
        k, i = self.cur
        if not self.mine(k, i): messagebox.showinfo('Joe Lab', 'You have not changed this one.'); return
        if not messagebox.askyesno('Joe Lab', f'Undo your change to {i}? The mod\'s own value comes back.'): return
        if k == '(strings)': self.changes.strings.pop(i, None)
        elif k.startswith('(block) '): self.changes.singles.pop(k[8:], None)
        else: self.changes.lists.get(k, {}).pop(i, None)
        self.changes.write(self.p['targets'])
        with open(self.p['log'], 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now():%Y-%m-%d %H:%M}  {k}  {i}  -- UNDONE\n')
        self.fill(); self.show()

    # ---------------------------------------------------------------------------------------------------- checking
    def check(self):
        if not os.path.exists(self.lab.GAME): messagebox.showerror('Joe Lab', 'Put Joe Lab next to OpenXcom.exe.'); return
        if any(j.is_alive() for j in self.lab.jobs.values()): messagebox.showinfo('Joe Lab', 'A run is going: stop it first.'); return
        self.status.configure(text='Starting the game on your changes (40 seconds) ...')

        def go():
            if not self.lab.prepare_user_sim(lambda *m: None): return
            user = self.lab.USER_SIM
            log = os.path.join(user, 'openxcom.log')
            try: os.remove(log)
            except OSError: pass
            cmd = [self.lab.GAME, '-user', user, '-cfg', user, '-displayWidth', '1280', '-displayHeight', '800', '-fullscreen', 'false'] + self.lab.EXTRA
            p = subprocess.Popen(cmd, cwd=os.path.dirname(self.lab.GAME))
            time.sleep(40)
            if p.poll() is None:
                if self.lab.WIN: subprocess.run(['taskkill', '/T', '/F', '/PID', str(p.pid)], creationflags=0x08000000, capture_output=True)
                else: p.kill()
            lines = open(log, encoding='utf-8', errors='replace').read().splitlines() if os.path.exists(log) else []
            bad = [l for l in lines if '[ERROR]' in l or '[FATAL]' in l]
            bad = [l for l in bad if not re.search(r'audio device|ALSA|Mix_OpenAudio', l)]
            crashed = p.returncode not in (None, 0, 1) and not bad
            msg = ('No errors: the game loaded your changes.' if not bad and not crashed else
                   'The game stopped while loading.' if crashed else
                   f'{len(bad)} error(s):\n\n' + '\n'.join(l.split('\t')[-1][:200] for l in bad[:12]))
            self.lab.root.after(0, lambda: (self.status.configure(text=msg.splitlines()[0]),
                                            messagebox.showinfo('Joe Lab - check', msg)))
        threading.Thread(target=go, daemon=True).start()


class StyleTab:
    def __init__(self, lab, page, paths):
        self.lab, self.p = lab, paths
        bar = ttk.Frame(page); bar.pack(fill='x', pady=(0, 8))
        ttk.Button(bar, text='Learn from my games', style='Go.TButton', command=self.learn).pack(side='left')
        self.use = tk.BooleanVar(value=os.path.exists(paths['profile']))
        ttk.Checkbutton(bar, text='Simulations play like me (Campaign and Checks tabs)', variable=self.use).pack(side='left', padx=12)
        ttk.Button(bar, text='Open my raw log', command=lambda: lab.open_path(self.p['playlog'])).pack(side='right')
        ttk.Label(page, text='Every campaign you play yourself writes user\\playstyle.txt: the research you start, the missions you answer\n'
                             '(how fast, how many Joes, which craft) and the ones you let go. "Learn" turns it into a profile the\n'
                             'simulator plays by: your research order, your answer rate for each kind of mission, your reaction\n'
                             'time and squad size. Battles are still fought by the game\'s AI.',
                  foreground='#8a9198', justify='left').pack(anchor='w', pady=(0, 8))
        f = ttk.Frame(page, style='Panel.TFrame', padding=8); f.pack(fill='both', expand=True)
        self.text = lab.textbox(f, 24); self.text.pack(fill='both', expand=True)
        if os.path.exists(paths['profile']): self.text.insert('1.0', open(paths['profile'], encoding='utf-8').read())

    def env(self):
        return {'OXCE_SIM_PROFILE': self.p['profile']} if self.use.get() and os.path.exists(self.p['profile']) else {}

    def learn(self):
        lines = open(self.p['playlog'], encoding='utf-8', errors='replace').read().splitlines() if os.path.exists(self.p['playlog']) else []
        if not lines:
            messagebox.showinfo('Joe Lab', 'No games recorded yet. Play a campaign with the new game (Play_4x.bat); it records itself.'); return
        order, seen = [], set()
        ans, ign, delay, squad, sessions, crafts = {}, {}, [], [], 0, {}
        for l in lines:
            m = re.match(r'day (\d+) (\w+) ?(.*)$', l)
            if not m: continue
            what, rest = m.group(2), m.group(3)
            if what == 'SESSION': sessions += 1
            elif what == 'RESEARCH':
                t = rest.split()[0]
                if t not in seen: seen.add(t); order.append(t)
            elif what == 'ANSWER':
                mm = re.match(r'(\S+) after (\d+)h squad (\d+) vehicles (\d+) craft (\S+)', rest)
                if mm:
                    ans[mm.group(1)] = ans.get(mm.group(1), 0) + 1
                    delay.append(int(mm.group(2))); squad.append(int(mm.group(3)))
                    crafts[mm.group(5)] = crafts.get(mm.group(5), 0) + 1
            elif what == 'IGNORED':
                k = rest.split()[0]; ign[k] = ign.get(k, 0) + 1
        out = [f'# YOUR PLAY STYLE, learnt {datetime.datetime.now():%Y-%m-%d %H:%M} from {sessions} session(s), {len(lines)} lines',
               f'# research topics in your order: {len(order)}; missions answered: {sum(ans.values())}; let go: {sum(ign.values())}']
        if delay: out.append(f'delay {int(statistics.median(delay))}')
        if squad: out.append(f'squad {int(statistics.median(squad))}')
        for k in sorted(set(ans) | set(ign)):
            n = ans.get(k, 0) + ign.get(k, 0)
            out.append(f'answer {k} {100 * ans.get(k, 0) // n}    # {ans.get(k, 0)} of {n}')
        out += [f'research {t}' for t in order]
        if crafts: out.append('# crafts you send: ' + ', '.join(f'{c} x{n}' for c, n in sorted(crafts.items(), key=lambda x: -x[1])))
        os.makedirs(os.path.dirname(self.p['profile']), exist_ok=True)
        open(self.p['profile'], 'w', encoding='utf-8').write('\n'.join(out) + '\n')
        self.text.delete('1.0', 'end'); self.text.insert('1.0', '\n'.join(out) + '\n')
        self.use.set(True)
