"""G.I. JOE 4x - JOE LAB's GUNS and SOLDIERS tabs (BUILD-1, 23 Nov 2026).

John 23 Nov: "the character and guns apps" - the Rules Editor can change anything, but as rule text. These two are
forms: pick a gun or a man, change the numbers in boxes, Save. Same override file as the Rules Editor
(zzzz_john_changes.rul, loads after everything), same change log, same Undo. "New from this" copies a gun or a unit
under a new name you choose, ready to be edited.

What a form cannot do: draw a new picture (pick any sprite number the mod already has), or add a mechanic.
"""
import os, datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import joe_editor as je

BT = {0: 'none', 1: 'gun', 2: 'ammo', 3: 'melee', 4: 'grenade', 5: 'proximity', 6: 'medikit', 7: 'scanner',
      8: 'mind probe', 9: 'psi amp', 10: 'flare', 11: 'corpse'}
DT = {0: 'none', 1: 'armour-piercing', 2: 'incendiary', 3: 'high explosive', 4: 'laser', 5: 'plasma', 6: 'stun',
      7: 'melee', 8: 'acid', 9: 'smoke'}
GUN_FIELDS = [  # (field, label, kind)
    ('battleType', 'Kind (1 gun, 2 ammo, 3 melee, 4 grenade)', int),
    ('power', 'Damage', int),
    ('damageType', 'Damage type (1 AP, 2 fire, 3 HE, 4 laser, 5 plasma, 6 stun, 7 melee)', int),
    ('accuracySnap', 'Accuracy, snap shot %', int), ('tuSnap', 'Time units, snap shot %', int),
    ('accuracyAimed', 'Accuracy, aimed shot %', int), ('tuAimed', 'Time units, aimed shot %', int),
    ('accuracyAuto', 'Accuracy, auto %', int), ('tuAuto', 'Time units, auto %', int),
    ('accuracyMelee', 'Accuracy, melee %', int), ('tuMelee', 'Time units, melee %', int),
    ('clipSize', 'Rounds in a clip (ammo)', int),
    ('compatibleAmmo', 'Takes this ammo (comma between)', list),
    ('weight', 'Weight', int), ('invWidth', 'Inventory width', int), ('invHeight', 'Inventory height', int),
    ('costBuy', 'Price to buy ($)', int), ('costSell', 'Sells for ($)', int),
    ('twoHanded', 'Two-handed (true / false)', bool),
    ('blastRadius', 'Blast radius (grenades)', int),
    ('bigSprite', 'Inventory picture number', int), ('floorSprite', 'Floor picture number', int),
    ('handSprite', 'Hand picture number', int), ('bulletSprite', 'Bullet picture number', int),
    ('fireSound', 'Fire sound number', int),
]
STATS = ['tu', 'stamina', 'health', 'bravery', 'reactions', 'firing', 'throwing', 'strength', 'melee', 'psiStrength', 'psiSkill']
STAT_LABEL = {'tu': 'Time units', 'stamina': 'Energy', 'health': 'Health', 'bravery': 'Bravery', 'reactions': 'Reactions',
              'firing': 'Firing', 'throwing': 'Throwing', 'strength': 'Strength', 'melee': 'Melee',
              'psiStrength': 'Psi strength', 'psiSkill': 'Psi skill'}


def parse(kind, text):
    text = text.strip()
    if text == '': return None
    if kind is int:
        if ',' in text: return [int(float(t)) for t in text.split(',') if t.strip()]   # a sound list, a sprite list
        return int(float(text))
    if kind is bool: return text.lower() in ('1', 'true', 'yes', 'y')
    if kind is list: return [t.strip() for t in text.split(',') if t.strip()]
    return text


def show(v):
    if v is None: return ''
    if isinstance(v, list): return ', '.join(str(x) for x in v)
    return str(v)


class FormTab:
    """shared: the list on the left, a form on the right, Save / New from this / Undo"""
    KIND = None

    def __init__(self, lab, page, paths, title):
        self.lab, self.p = lab, paths
        self.rules = None
        self.cur = None
        self.vars = {}
        bar = ttk.Frame(page); bar.pack(fill='x', pady=(0, 8))
        ttk.Button(bar, text='Load', command=self.load).pack(side='left')
        self.status = ttk.Label(bar, text=f'Press "Load" to list {title}.', foreground='#8a9198'); self.status.pack(side='left', padx=10)
        body = ttk.Frame(page); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=2); body.columnconfigure(1, weight=5); body.rowconfigure(0, weight=1)
        left = ttk.Frame(body); left.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        self.filter = tk.StringVar(value=self.FILTERS[0]); fb = ttk.Combobox(left, textvariable=self.filter, values=self.FILTERS, state='readonly')
        fb.pack(fill='x'); fb.bind('<<ComboboxSelected>>', lambda e: self.fill())
        self.search = tk.StringVar(); self.search.trace_add('write', lambda *a: self.fill())
        ttk.Entry(left, textvariable=self.search).pack(fill='x', pady=4)
        self.lb = tk.Listbox(left, bg='#1f262c', fg='#e8e4d8', selectbackground='#3d4a55', font=lab.MONO, relief='flat', activestyle='none')
        self.lb.pack(fill='both', expand=True); self.lb.bind('<<ListboxSelect>>', lambda e: self.pick())
        right = ttk.Frame(body, style='Panel.TFrame', padding=8); right.grid(row=0, column=1, sticky='nsew')
        self.head = ttk.Label(right, text='', style='Panel.TLabel', font=(lab.MONO[0], 11, 'bold')); self.head.pack(anchor='w')
        self.sub = ttk.Label(right, text='', style='Dim.TLabel'); self.sub.pack(anchor='w', pady=(0, 6))
        canvas = tk.Canvas(right, bg='#2c353d', highlightthickness=0); canvas.pack(fill='both', expand=True, side='top')
        self.form = ttk.Frame(canvas, style='Panel.TFrame'); canvas.create_window((0, 0), window=self.form, anchor='nw')
        self.form.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(int(-e.delta / 120), 'units'))
        nb = ttk.Frame(right, style='Panel.TFrame'); nb.pack(fill='x', pady=(6, 0))
        ttk.Label(nb, text='Note (why):', style='Panel.TLabel').pack(side='left')
        self.note = tk.StringVar(); ttk.Entry(nb, textvariable=self.note, width=40).pack(side='left', padx=6, fill='x', expand=True)
        bb = ttk.Frame(right, style='Panel.TFrame'); bb.pack(fill='x', pady=(6, 0))
        ttk.Button(bb, text='Save', style='Go.TButton', command=self.save).pack(side='right')
        ttk.Button(bb, text='New from this...', command=self.copy).pack(side='right', padx=6)
        ttk.Button(bb, text='Undo my change to this', command=self.undo).pack(side='right')

    # -------------------------------------------------------------------------------------------- data
    def load(self):
        if not je.need_yaml(): return
        if not os.path.isdir(self.p['ruleset']):
            messagebox.showerror('Joe Lab', 'The mod is not unpacked yet. Start the game once with Play_4x.bat.'); return
        self.rules = je.Rules(self.p['ruleset'])
        self.fill()

    def changes(self):
        return je.Changes(self.p['master'])   # read fresh every time, so the Rules Editor and these tabs never overwrite each other

    def entry(self, ident, kind=None):
        kind = kind or self.KIND
        ch = self.changes()
        return je.merge(self.rules.kinds.get(kind, {}).get(ident, {}), ch.lists.get(kind, {}).get(ident, {}))

    def name(self, ident):
        ch = self.changes()
        return ch.strings.get(ident, self.rules.strings.get(ident, ''))

    def fill(self):
        if not self.rules: return
        ch = self.changes()
        s = self.search.get().lower()
        self.lb.delete(0, 'end')
        ids = sorted(set(self.rules.kinds.get(self.KIND, {})) | set(ch.lists.get(self.KIND, {})),
                     key=lambda i: ((self.name(i) or i).lower(), i))
        n = 0
        for i in ids:
            e = self.entry(i)
            if not self.keep(e): continue
            nm = self.name(i)
            if s and s not in i.lower() and s not in nm.lower(): continue
            mark = '* ' if i in ch.lists.get(self.KIND, {}) else '  '
            self.lb.insert('end', f'{mark}{nm or i}   [{i}]'); n += 1
        self.status.configure(text=f'{n} shown. * = changed by you. Save puts it in the game from the next start.')

    def pick(self):
        sel = self.lb.curselection()
        if not sel: return
        self.cur = self.lb.get(sel[0]).rsplit('[', 1)[1].rstrip(']')
        self.draw()

    # -------------------------------------------------------------------------------------------- form
    def clear(self):
        for w in self.form.winfo_children(): w.destroy()
        self.vars = {}

    def row(self, r, label, key, value, width=28):
        ttk.Label(self.form, text=label, style='Panel.TLabel').grid(row=r, column=0, sticky='w', padx=(0, 10), pady=2)
        v = tk.StringVar(value=show(value)); self.vars[key] = v
        ttk.Entry(self.form, textvariable=v, width=width).grid(row=r, column=1, sticky='w', pady=2)

    def collect(self, base):
        out = dict(base)
        for key, (kind, v) in self.read().items():
            try: val = parse(kind, v)
            except ValueError:
                messagebox.showerror('Joe Lab', f'"{v}" is not a number ({key}).'); return None
            self.put(out, key, val)
        return out

    def put(self, out, key, val):
        if val is None: out.pop(key, None)
        else: out[key] = val

    def save(self):
        if not self.cur: messagebox.showinfo('Joe Lab', 'Pick one first.'); return
        old = self.entry(self.cur)
        new = self.collect(old)
        if new is None: return
        ch = self.changes()
        idk = self.rules.idkey.get((self.KIND, self.cur), 'type'); new[idk] = self.cur
        ch.lists.setdefault(self.KIND, {})[self.cur] = new
        nm = self.vars.get('__name')
        if nm is not None and nm.get().strip() and nm.get().strip() != self.name(self.cur):
            ch.strings[self.cur] = nm.get().strip()
            if self.KIND == 'items' and new.get('name') not in (None, self.cur):
                new['name'] = self.cur   # it shows its own name now, not the one it shared through "name:"
                ch.lists[self.KIND][self.cur] = new
        ch.write(self.p['targets'])
        self.log(self.cur, je.diff_lines(old, new) or ['(no difference)'])
        self.status.configure(text=f'Saved {self.name(self.cur) or self.cur}. In the game from the next start.')
        self.fill()

    def copy(self):
        if not self.cur: messagebox.showinfo('Joe Lab', 'Pick one to copy.'); return
        new_id = simpledialog.askstring('Joe Lab', f'Name for the new one (for example STR_MY_NEW_GUN):', parent=self.lab.root)
        if not new_id: return
        new_id = new_id.strip().upper().replace(' ', '_')
        if not new_id.startswith('STR_'): new_id = 'STR_' + new_id
        ch = self.changes()
        if new_id in self.rules.kinds.get(self.KIND, {}) or new_id in ch.lists.get(self.KIND, {}):
            messagebox.showerror('Joe Lab', f'{new_id} already exists.'); return
        e = self.collect(self.entry(self.cur))
        if e is None: return
        idk = self.rules.idkey.get((self.KIND, self.cur), 'type'); e[idk] = new_id
        self.extra_copy(ch, self.cur, new_id, e)
        ch.lists.setdefault(self.KIND, {})[new_id] = e
        ch.strings[new_id] = new_id.replace('STR_', '').replace('_', ' ').title()
        ch.write(self.p['targets'])
        self.log(new_id, [f'NEW, copied from {self.cur}'])
        self.cur = new_id; self.search.set(''); self.fill(); self.draw()
        self.status.configure(text=f'Added {new_id}, a copy. Change its name and numbers, then Save.')

    def extra_copy(self, ch, old, new, entry):
        pass

    def undo(self):
        if not self.cur: return
        ch = self.changes()
        if self.cur not in ch.lists.get(self.KIND, {}) and self.cur not in ch.strings:
            messagebox.showinfo('Joe Lab', 'You have not changed this one.'); return
        if not messagebox.askyesno('Joe Lab', f'Undo your change to {self.cur}? The mod\'s own values come back.'): return
        ch.lists.get(self.KIND, {}).pop(self.cur, None); ch.strings.pop(self.cur, None)
        ch.write(self.p['targets'])
        self.log(self.cur, ['UNDONE'])
        self.fill(); self.draw()

    def log(self, ident, lines):
        note = self.note.get().strip()
        with open(self.p['log'], 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now():%Y-%m-%d %H:%M}  {self.KIND}  {ident}' + (f'  -- {note}' if note else '') + '\n')
            for l in lines: f.write('    ' + l + '\n')
        self.note.set('')


class GunsTab(FormTab):
    KIND = 'items'
    FILTERS = ['Guns and ammo', 'Guns', 'Ammo', 'Grenades and melee', 'Everything']

    def __init__(self, lab, page, paths):
        super().__init__(lab, page, paths, 'the guns')

    def name(self, ident):
        # an item's name is its own string, or the string its "name:" field points at (the arsenal's vehicle guns)
        own = super().name(ident)
        if own: return own
        n = self.rules.kinds.get(self.KIND, {}).get(ident, {}).get('name')
        return super().name(n) if isinstance(n, str) else ''

    def keep(self, e):
        bt = e.get('battleType', 0)
        f = self.filter.get()
        return {'Guns and ammo': bt in (1, 2), 'Guns': bt == 1, 'Ammo': bt == 2,
                'Grenades and melee': bt in (3, 4, 5), 'Everything': True}[f]

    def draw(self):
        self.clear()
        e = self.entry(self.cur)
        self.head.configure(text=self.name(self.cur) or self.cur)
        files = self.rules.where.get((self.KIND, self.cur), [])
        self.sub.configure(text=f'{self.cur}  -  {BT.get(e.get("battleType", 0), "?")}' + (f'  -  set by {", ".join(files[-3:])}' if files else ''))
        self.row(0, 'Name in the game', '__name', self.name(self.cur), 40)
        r = 1
        for key, label, kind in GUN_FIELDS:
            self.row(r, label, key, e.get(key)); r += 1
        ammo = e.get('compatibleAmmo') or []
        if ammo:
            a = self.entry(ammo[0])
            ttk.Label(self.form, text=f'Its ammo ({ammo[0]}): damage {a.get("power", "?")}, {DT.get(a.get("damageType", 0), "?")}, '
                                      f'{a.get("clipSize", "?")} rounds. Pick the ammo in the list to change it.',
                      style='Dim.TLabel').grid(row=r, column=0, columnspan=2, sticky='w', pady=(8, 0))

    def read(self):
        kinds = {k: t for k, _, t in GUN_FIELDS}
        return {k: (kinds[k], v.get()) for k, v in self.vars.items() if k in kinds}

    def extra_copy(self, ch, old, new, entry):
        # a copied gun keeps firing the same ammo; a copied ammo is offered to nothing until a gun lists it
        pass


class SoldiersTab(FormTab):
    KIND = 'units'
    FILTERS = ['Cobra and other units', 'Joe soldier types']

    def __init__(self, lab, page, paths):
        super().__init__(lab, page, paths, 'the units')

    def fill(self):
        self.KIND = 'soldiers' if self.filter.get() == 'Joe soldier types' else 'units'
        super().fill()

    def keep(self, e):
        return True

    def draw(self):
        self.clear()
        e = self.entry(self.cur)
        self.head.configure(text=self.name(self.cur) or self.cur)
        files = self.rules.where.get((self.KIND, self.cur), [])
        self.sub.configure(text=self.cur + (f'  -  set by {", ".join(files[-3:])}' if files else ''))
        self.row(0, 'Name in the game', '__name', self.name(self.cur), 40)
        self.row(1, 'Armour', 'armor', e.get('armor'), 40)
        r = 2
        if self.KIND == 'soldiers':
            lo, hi = e.get('minStats', {}) or {}, e.get('maxStats', {}) or {}
            ttk.Label(self.form, text='Stat                       lowest  -  highest when hired', style='Dim.TLabel').grid(row=r, column=0, columnspan=2, sticky='w'); r += 1
            for s in STATS:
                ttk.Label(self.form, text=STAT_LABEL[s], style='Panel.TLabel').grid(row=r, column=0, sticky='w', pady=2)
                f = ttk.Frame(self.form, style='Panel.TFrame'); f.grid(row=r, column=1, sticky='w')
                for tag, src in (('min', lo), ('max', hi)):
                    v = tk.StringVar(value=show(src.get(s))); self.vars[f'{tag}:{s}'] = v
                    ttk.Entry(f, textvariable=v, width=8).pack(side='left', padx=(0, 6))
                r += 1
        else:
            st = e.get('stats', {}) or {}
            for s in STATS:
                self.row(r, STAT_LABEL[s], f'stat:{s}', st.get(s), 8); r += 1
            for key, label in (('standHeight', 'Height standing'), ('kneelHeight', 'Height kneeling'), ('value', 'Score for killing him'),
                               ('aggression', 'Aggression (0-2)'), ('intelligence', 'Intelligence'), ('deathSound', 'Death sound number')):
                self.row(r, label, key, e.get(key), 8); r += 1

    def read(self):
        return {k: (int if k != 'armor' else str, v.get()) for k, v in self.vars.items() if k != '__name'}

    def put(self, out, key, val):
        if ':' in key:
            tag, s = key.split(':', 1)
            blk = {'min': 'minStats', 'max': 'maxStats', 'stat': 'stats'}[tag]
            d = dict(out.get(blk) or {})
            if val is None: d.pop(s, None)
            else: d[s] = val
            out[blk] = d
        else:
            super().put(out, key, val)
