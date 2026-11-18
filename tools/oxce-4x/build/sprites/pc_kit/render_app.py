# RENDER MACHINE - the app. A window over render_cartel.py --watch: start/stop, add models, pick the extra clips,
# watch each model's progress, see the last finished sheet. Run from RENDER_APP.bat (py -3.13 render_app.py).
import os, sys, json, time, shutil, subprocess, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import threading, glob

KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
import render_cartel as M                                      # paths, clip list, model scan - one source of truth

BG, PANEL, FG, DIM, ACC, OK, BAD, WARN = '#16181d', '#20232b', '#e8e6e1', '#8b8f99', '#d8b45a', '#5cb85c', '#d9534f', '#e0a030'
SHEET_FRAMES = 896
WIN = sys.platform.startswith('win')


def open_path(p):
    os.makedirs(p, exist_ok=True) if not os.path.splitext(p)[1] else None
    try:
        if WIN: os.startfile(p)
        elif sys.platform == 'darwin': subprocess.Popen(['open', p])
        else: subprocess.Popen(['xdg-open', p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        messagebox.showerror('Render Machine', 'Could not open %s\n%s' % (p, e))


def count_frames(d):
    n = 0
    for _, _, fs in os.walk(d):
        n += sum(1 for f in fs if f.endswith('_beauty.png'))
    return n


def read_log_tail(n=14):
    p = os.path.join(M.WORK, 'render_log.txt')
    if not os.path.exists(p): return []
    with open(p, errors='replace') as f: lines = f.readlines()
    return [l.rstrip('\n') for l in lines[-n:]]


def current_model():
    """The model being worked on now, from the log: the last '== name start' with no done/FAILED after it."""
    p = os.path.join(M.WORK, 'render_log.txt')
    if not os.path.exists(p): return None
    cur = None
    with open(p, errors='replace') as f:
        for l in f:
            m = re.search(r'== (\S+) start', l)
            if m: cur = m.group(1); continue
            if cur and re.search(r'\b(extras|EXTRAS FAILED|RENDER FAILED|ASSEMBLE FAILED|CHECK FAILED)\b ' + re.escape(cur) + r'\b', l):
                cur = None
    return cur


class App:
    def __init__(self, root):
        self.root = root; self.proc = None; self.preview_img = None; self.preview_name = None
        root.title('Render Machine'); root.configure(bg=BG); root.geometry('1180x780'); root.minsize(980, 640)
        st = ttk.Style(); st.theme_use('clam')
        st.configure('.', background=BG, foreground=FG, fieldbackground=PANEL, font=('Segoe UI', 10))
        st.configure('TFrame', background=BG); st.configure('Panel.TFrame', background=PANEL)
        st.configure('TLabel', background=BG, foreground=FG); st.configure('Dim.TLabel', foreground=DIM)
        st.configure('Panel.TLabel', background=PANEL, foreground=FG)
        st.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=ACC)
        st.configure('H.TLabel', font=('Segoe UI', 11, 'bold'), background=PANEL, foreground=ACC)
        st.configure('TButton', background='#2c3039', foreground=FG, padding=(12, 7), borderwidth=0)
        st.map('TButton', background=[('active', '#3a3f4b'), ('disabled', '#23262d')], foreground=[('disabled', '#5a5e68')])
        st.configure('Go.TButton', background='#2f6b3a'); st.map('Go.TButton', background=[('active', '#3b8448'), ('disabled', '#23262d')])
        st.configure('Stop.TButton', background='#7a2e2b'); st.map('Stop.TButton', background=[('active', '#963733'), ('disabled', '#23262d')])
        st.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=FG, rowheight=26, borderwidth=0)
        st.configure('Treeview.Heading', background='#2c3039', foreground=DIM, relief='flat')
        st.map('Treeview', background=[('selected', '#3a3f4b')])
        st.configure('TCheckbutton', background=PANEL, foreground=FG); st.map('TCheckbutton', background=[('active', PANEL)])
        st.configure('Horizontal.TProgressbar', background=ACC, troughcolor='#2c3039', borderwidth=0)

        # --- header: title, state light, start/stop
        top = ttk.Frame(root, padding=(16, 12)); top.pack(fill='x')
        ttk.Label(top, text='RENDER MACHINE', style='Title.TLabel').pack(side='left')
        self.light = tk.Canvas(top, width=16, height=16, bg=BG, highlightthickness=0); self.light.pack(side='left', padx=(18, 6))
        self.dot = self.light.create_oval(2, 2, 14, 14, fill=DIM, outline='')
        self.state_lbl = ttk.Label(top, text='Stopped', style='Dim.TLabel'); self.state_lbl.pack(side='left')
        self.stop_btn = ttk.Button(top, text='■  Stop', style='Stop.TButton', command=self.stop); self.stop_btn.pack(side='right')
        self.start_btn = ttk.Button(top, text='▶  Start machine', style='Go.TButton', command=self.start); self.start_btn.pack(side='right', padx=8)

        body = ttk.Frame(root, padding=(16, 0, 16, 12)); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(1, weight=1)

        # --- left: models
        left = ttk.Frame(body, style='Panel.TFrame', padding=12); left.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=(0, 12))
        hdr = ttk.Frame(left, style='Panel.TFrame'); hdr.pack(fill='x')
        ttk.Label(hdr, text='Models', style='H.TLabel').pack(side='left')
        ttk.Button(hdr, text='+ Add civilian', command=lambda: self.add(True)).pack(side='right')
        ttk.Button(hdr, text='+ Add armed', command=lambda: self.add(False)).pack(side='right', padx=6)
        cols = ('type', 'status', 'when')
        self.tree = ttk.Treeview(left, columns=cols, show='tree headings', selectmode='browse')
        self.tree.heading('#0', text='Name'); self.tree.column('#0', width=190)
        for c, w, t in (('type', 80, 'Type'), ('status', 200, 'Status'), ('when', 120, 'Finished')):
            self.tree.heading(c, text=t); self.tree.column(c, width=w, anchor='w')
        self.tree.tag_configure('done', foreground=OK); self.tree.tag_configure('fail', foreground=BAD)
        self.tree.tag_configure('busy', foreground=ACC); self.tree.tag_configure('queued', foreground=DIM)
        self.tree.pack(fill='both', expand=True, pady=(10, 8))
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.show_preview(self.selected()))
        self.tree.bind('<Double-1>', lambda e: self.open_result(self.selected()))
        row = ttk.Frame(left, style='Panel.TFrame'); row.pack(fill='x')
        self.cur_lbl = ttk.Label(row, text='', style='Panel.TLabel'); self.cur_lbl.pack(side='left')
        self.bar = ttk.Progressbar(left, mode='determinate', maximum=100); self.bar.pack(fill='x', pady=(6, 8))
        btns = ttk.Frame(left, style='Panel.TFrame'); btns.pack(fill='x')
        ttk.Button(btns, text='Edit look…', command=self.edit_look).pack(side='left')
        ttk.Button(btns, text='Re-render selected', command=self.rerender).pack(side='left', padx=6)
        ttk.Button(btns, text='Armed results', command=lambda: open_path(M.OUT)).pack(side='right')
        ttk.Button(btns, text='Civilian results', command=lambda: open_path(M.OUT_CIV)).pack(side='right', padx=6)

        # --- right top: preview
        pv = ttk.Frame(body, style='Panel.TFrame', padding=12); pv.grid(row=0, column=1, sticky='nsew')
        self.pv_title = ttk.Label(pv, text='Preview', style='H.TLabel'); self.pv_title.pack(anchor='w')
        self.pv = tk.Label(pv, bg='#2a2d35', height=12, text='Pick a finished model', fg=DIM); self.pv.pack(fill='x', pady=(8, 0))

        # --- right bottom: extras checklist
        ex = ttk.Frame(body, style='Panel.TFrame', padding=12); ex.grid(row=1, column=1, sticky='nsew', pady=(12, 0))
        eh = ttk.Frame(ex, style='Panel.TFrame'); eh.pack(fill='x')
        ttk.Label(eh, text='Extra animations', style='H.TLabel').pack(side='left')
        self.ex_lbl = ttk.Label(eh, text='', style='Panel.TLabel'); self.ex_lbl.pack(side='right')
        grid = ttk.Frame(ex, style='Panel.TFrame'); grid.pack(fill='both', expand=True, pady=(8, 4))
        self.ex_vars = {}
        on = set(M.extras_list())
        for i, e in enumerate(M.ALL_EXTRAS):
            v = tk.BooleanVar(value=e in on); self.ex_vars[e] = v
            ttk.Checkbutton(grid, text=e.replace('_', ' '), variable=v, command=self.save_extras).grid(row=i // 3, column=i % 3, sticky='w', padx=(0, 10), pady=1)
        eb = ttk.Frame(ex, style='Panel.TFrame'); eb.pack(fill='x')
        ttk.Button(eb, text='All', command=lambda: self.set_all(True)).pack(side='left')
        ttk.Button(eb, text='None', command=lambda: self.set_all(False)).pack(side='left', padx=6)
        self.update_ex_lbl()

        # --- bottom: log
        lg = ttk.Frame(root, style='Panel.TFrame', padding=(12, 8)); lg.pack(fill='x', padx=16, pady=(0, 14))
        lh = ttk.Frame(lg, style='Panel.TFrame'); lh.pack(fill='x')
        ttk.Label(lh, text='Log', style='H.TLabel').pack(side='left')
        ttk.Button(lh, text='Open full log', command=lambda: open_path(os.path.join(M.WORK, 'render_log.txt'))).pack(side='right')
        self.log = tk.Text(lg, height=8, bg='#121418', fg='#c9c7c1', relief='flat', font=('Consolas', 9), wrap='none')
        self.log.pack(fill='x', pady=(6, 0)); self.log.configure(state='disabled')

        root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.refresh()

    # ---------------- machine control
    def start(self):
        if self.proc and self.proc.poll() is None: return
        os.makedirs(M.WORK, exist_ok=True)
        py = os.environ.get('KIT_PY', sys.executable)
        if py.lower().endswith('pythonw.exe'): py = py[:-len('pythonw.exe')] + 'python.exe'   # the worker wants a console-less python, not pythonw
        kw = {}
        if WIN: kw['creationflags'] = 0x08000000      # CREATE_NO_WINDOW
        else: kw['start_new_session'] = True
        self.out = open(os.path.join(M.WORK, 'machine_console.txt'), 'a')
        self.proc = subprocess.Popen([py, os.path.join(KIT, 'render_cartel.py'), '--watch'], cwd=KIT,
                                     stdout=self.out, stderr=subprocess.STDOUT, **kw)
        self.refresh()

    def stop(self):
        if not (self.proc and self.proc.poll() is None): return
        if WIN: subprocess.call(['taskkill', '/PID', str(self.proc.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            import signal
            try: os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except Exception: self.proc.terminate()
        self.proc.wait(timeout=10); self.proc = None
        cur = current_model()
        if cur: M.log('stopped by the app while working on', cur, '- it starts over from the beginning next time')
        self.refresh()

    def running(self):
        return bool(self.proc and self.proc.poll() is None)

    def on_close(self):
        if self.running() and not messagebox.askyesno('Render Machine', 'The machine is running. Stop it and close?'):
            return
        self.stop(); self.root.destroy()

    # ---------------- models
    def add(self, civ):
        fs = filedialog.askopenfilenames(title='Add %s model(s)' % ('civilian' if civ else 'armed'),
                                         filetypes=[('Blender model', '*.blend')])
        dest = M.CIV if civ else M.CARTEL; os.makedirs(dest, exist_ok=True)
        for f in fs:
            n = os.path.basename(f)
            if os.path.abspath(os.path.dirname(f)) != os.path.abspath(dest):
                shutil.copy2(f, os.path.join(dest, n))
                ink = os.path.splitext(f)[0] + '.ink.txt'
                if os.path.exists(ink): shutil.copy2(ink, dest)
            os.utime(os.path.join(dest, n), None)    # counts as new: the machine renders it
        self.refresh()

    def selected(self):
        s = self.tree.selection(); return s[0] if s else None

    def rerender(self):
        n = self.selected()
        if not n: return
        for d in (M.CARTEL, M.CIV):
            p = os.path.join(d, n + '.blend')
            if os.path.exists(p): os.utime(p, None)
        self.refresh()

    def state(self):
        p = os.path.join(M.WORK, 'machine_state.json')
        try: return json.load(open(p)) if os.path.exists(p) else {}
        except Exception: return {}

    def rows(self):
        st = self.state(); cur = current_model() if self.running() else None; out = []
        for folder, civ in ((M.CARTEL, False), (M.CIV, True)):
            for n in M.models(folder):
                p = os.path.join(folder, n + '.blend'); s = st.get(p.lower())
                fresh = s and s.get('mtime') == os.path.getmtime(p)
                if n == cur: status, tag, when = self.progress_text(n), 'busy', ''
                elif fresh: status, tag, when = ('Done' + ('' if s.get('extras') else ' (no extras)') if s['ok'] else 'FAILED - see log'), ('done' if s['ok'] else 'fail'), s.get('when', '')
                else: status, tag, when = 'Queued', 'queued', ''
                out.append((n, 'civilian' if civ else 'armed', status, when, tag, civ))
        return out

    def progress(self, n):
        ex = os.path.join(M.WORK, 'extras_' + n); fr = os.path.join(M.WORK, 'fr16_' + n)
        if os.path.isdir(ex):
            total = max(1, len([e for e in M.extras_list() if e in M.ALL_EXTRAS]) * 8 * 16)
            return 'extras', min(100, 100 * count_frames(ex) / total)
        if os.path.isdir(fr):
            done = count_frames(fr)
            return ('sheet', 100 * done / SHEET_FRAMES) if done < SHEET_FRAMES else ('assembling', 100)
        return 'starting', 0

    def progress_text(self, n):
        phase, pct = self.progress(n)
        return {'sheet': 'Rendering sheet  %d%%' % pct, 'assembling': 'Assembling sheet', 'extras': 'Extras  %d%%' % pct,
                'starting': 'Starting'}[phase]

    def edit_look(self):
        n = self.selected()
        if not n: messagebox.showinfo('Render Machine', 'Pick a model in the list first.'); return
        if self.running() and current_model() == n:
            messagebox.showinfo('Render Machine', '%s is rendering right now. Edit him when he is done, or Stop the machine.' % n); return
        blend, civ = M.where(n)
        if blend: LookEditor(self, n, blend, civ)

    # ---------------- extras
    def save_extras(self):
        f = os.path.join(KIT, 'extras.txt')
        lines = open(f).read().splitlines() if os.path.exists(f) else []
        seen, out = set(), []
        for l in lines:
            key = l.split('#')[0].strip() or l.lstrip('# ').split(' ')[0].strip()
            if key in self.ex_vars and key not in seen:
                seen.add(key); note = l[l.index('#', l.index(key)):] if '#' in l[l.find(key):] else ''
                body = key.ljust(22) + (' ' + note if note else '')
                out.append(body if self.ex_vars[key].get() else '# ' + body)
            else:
                out.append(l)
        for k, v in self.ex_vars.items():
            if k not in seen: out.append(k if v.get() else '# ' + k)
        open(f, 'w').write('\n'.join(out) + '\n'); self.update_ex_lbl()

    def set_all(self, on):
        for v in self.ex_vars.values(): v.set(on)
        self.save_extras()

    def update_ex_lbl(self):
        n = sum(v.get() for v in self.ex_vars.values())
        self.ex_lbl.configure(text='%d of %d  ·  about %d min a model' % (n, len(self.ex_vars), 14 + round(1.5 * n)))

    # ---------------- preview / results
    def sheet_path(self, n):
        for d in (M.OUT, M.OUT_CIV):
            p = os.path.join(d, n + '_body.png')
            if os.path.exists(p): return p
        return None

    def open_result(self, n):
        p = self.sheet_path(n) if n else None
        if p: open_path(os.path.dirname(p))

    def show_preview(self, n):
        p = self.sheet_path(n) if n else None
        if not p:
            self.pv.configure(image='', text='%s - no sheet yet' % n if n else 'Pick a finished model'); self.preview_name = None; return
        if self.preview_name == (n, os.path.getmtime(p)): return
        try:
            from PIL import Image, ImageTk
            im = Image.open(p).convert('RGBA')
            def cell(i):
                r, c = divmod(i, 16); return im.crop((c * 128, r * 160, c * 128 + 128, r * 160 + 160))
            # facing 5 (towards the camera): stand, mid-walk, aim, down - trimmed to the figures, as big as the panel allows
            picks = [0 + 5 * 8, 384 + 5 * 16 + 4, 128 + 5 * 8, 192 + 5 * 8 + 7]
            cells = [cell(i) for i in picks]
            box = None
            for c in cells:
                bb = c.getbbox()
                if bb: box = bb if not box else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
            box = box or (0, 0, 128, 160)
            box = (max(0, box[0] - 4), max(0, box[1] - 4), min(128, box[2] + 4), min(160, box[3] + 4))
            cw, ch = box[2] - box[0], box[3] - box[1]
            strip = Image.new('RGBA', (cw * len(cells) + 12 * (len(cells) - 1), ch), (42, 45, 53, 255))
            for k, c in enumerate(cells): strip.alpha_composite(c.crop(box), (k * (cw + 12), 0))
            self.root.update_idletasks()
            avail = max(320, self.pv.master.winfo_width() - 32)
            sc = min(avail / strip.width, 230 / strip.height)
            w, h = int(strip.width * sc), int(strip.height * sc)
            self.preview_img = ImageTk.PhotoImage(strip.resize((w, h), Image.NEAREST))
            self.pv.configure(image=self.preview_img, text='', height=h + 8); self.preview_name = (n, os.path.getmtime(p))
            self.pv_title.configure(text='Preview - %s  (stand, walk, aim, down)' % n)
        except Exception as e:
            self.pv.configure(image='', text='Preview failed: %s' % e)

    def refresh_now(self):
        self.preview_name = None

    # ---------------- refresh loop
    def refresh(self):
        run = self.running()
        cur = current_model() if run else None
        self.light.itemconfigure(self.dot, fill=(ACC if cur else OK) if run else DIM)
        self.state_lbl.configure(text=('Working on ' + cur if cur else 'Running - waiting for models') if run else 'Stopped')
        self.start_btn.state(['disabled'] if run else ['!disabled']); self.stop_btn.state(['!disabled'] if run else ['disabled'])
        sel = self.selected(); rows = self.rows(); names = [r[0] for r in rows]
        for iid in self.tree.get_children():
            if iid not in names: self.tree.delete(iid)
        for i, (n, typ, status, when, tag, civ) in enumerate(rows):
            if self.tree.exists(n): self.tree.item(n, values=(typ, status, when), tags=(tag,)); self.tree.move(n, '', i)
            else: self.tree.insert('', i, iid=n, text=n, values=(typ, status, when), tags=(tag,))
        if sel and self.tree.exists(sel): self.tree.selection_set(sel)
        if cur:
            phase, pct = self.progress(cur); self.bar['value'] = pct
            self.cur_lbl.configure(text='%s - %s' % (cur, self.progress_text(cur)))
        else:
            self.bar['value'] = 0
            q = sum(1 for r in rows if r[4] == 'queued'); d = sum(1 for r in rows if r[4] == 'done')
            self.cur_lbl.configure(text='%d done, %d queued%s' % (d, q, '' if run or not q else ' - press Start'))
        done = [r for r in rows if r[4] == 'done']
        if not sel and done: self.show_preview(sorted(done, key=lambda r: r[3])[-1][0])
        self.log.configure(state='normal'); self.log.delete('1.0', 'end'); self.log.insert('end', '\n'.join(read_log_tail()))
        self.log.see('end'); self.log.configure(state='disabled')
        self.root.after(3000, self.refresh)


def worker_python():
    py = os.environ.get('KIT_PY', sys.executable)
    return py[:-len('pythonw.exe')] + 'python.exe' if py.lower().endswith('pythonw.exe') else py


def run_quiet(cmd, log):
    kw = {'creationflags': 0x08000000} if WIN else {}
    with open(log, 'w') as f: return subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=KIT, **kw)


def hexcol(rgb): return '#%02x%02x%02x' % tuple(int(c) for c in rgb)


GEAR_KINDS = [('bandana', 'Bandana', [118, 28, 30]), ('cap', 'Cap', [30, 30, 32]), ('dome', 'Helmet', [70, 76, 50]),
              ('vest', 'Plate vest', [84, 90, 58]), ('sunglasses', 'Sunglasses', [16, 16, 18]), ('chain', 'Gold chain', [214, 170, 52])]
ATTACH_NAMES = [('head', 'Head (hat, helmet)'), ('face', 'Face (mask, goggles)'), ('chest', 'Chest (vest, rig)'),
                ('back', 'Back (pack, sword)'), ('hip_l', 'Left hip'), ('hip_r', 'Right hip'), ('hand_r', 'Right hand'),
                ('hand_l', 'Left hand')]


class LookEditor:
    """Edit look: skins, colours, built-in gear and gear files for one model. Preview renders one picture;
    Apply keeps the old file in _versions and the machine re-renders the model by itself."""

    def __init__(self, app, name, blend, civ):
        self.app, self.name, self.blend, self.civ = app, name, blend, civ
        self.skins, self.colours, self.props_add, self.props_remove = {}, {}, [], []
        self.gear_changed = False; self.img = None; self.face = None
        w = self.w = tk.Toplevel(app.root); w.title('Edit look - ' + name); w.configure(bg=BG); w.geometry('1320x780'); w.minsize(1200, 700)
        w.transient(app.root)
        self.status = ttk.Label(w, text='Reading the model…'); self.status.pack(anchor='w', padx=16, pady=(12, 0))
        self.body = ttk.Frame(w, padding=(16, 8)); self.body.pack(fill='both', expand=True)
        self.busy(True)
        self.bg(lambda: self.read(), self.build)

    # -- plumbing
    def bg(self, work, done):
        def run():
            try: r = work()
            except Exception as e: r = e
            self.w.after(0, lambda: done(r))
        threading.Thread(target=run, daemon=True).start()

    def busy(self, on, text=None):
        if text: self.status.configure(text=text)
        self.w.configure(cursor='watch' if on else '')

    def dress(self, args, tag):
        os.makedirs(M.WORK, exist_ok=True)
        log = os.path.join(M.WORK, 'dress_%s_%s.log' % (self.name, tag))
        c = run_quiet([worker_python(), os.path.join(KIT, 'dress.py'), '--blend', self.blend] + args, log)
        txt = open(log, errors='replace').read()
        if c != 0 or ('DRESS_OK' not in txt and 'DRESS_JSON' not in txt):
            raise RuntimeError('the model editor failed - see %s' % log)
        return txt

    def read(self):
        txt = self.dress(['--list'], 'list')
        line = [l for l in txt.splitlines() if l.startswith('DRESS_JSON ')][0]
        return json.loads(line[len('DRESS_JSON '):])

    # -- the window
    def build(self, info):
        self.busy(False)
        if isinstance(info, Exception): self.status.configure(text=str(info)); return
        self.info = info
        self.status.configure(text='Changes are only made when you press Apply. Preview shows them first.')
        b = self.body; b.columnconfigure(0, weight=0); b.columnconfigure(1, weight=1); b.rowconfigure(0, weight=1)
        left = ttk.Frame(b); left.grid(row=0, column=0, sticky='nsew', padx=(0, 12))
        right = ttk.Frame(b, style='Panel.TFrame', padding=12); right.grid(row=0, column=1, sticky='nsew')

        # skins & colours
        sk = ttk.Frame(left, style='Panel.TFrame', padding=12); sk.pack(fill='x')
        ttk.Label(sk, text='Skins and colours', style='H.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 6))
        ttk.Button(sk, text='Face from photo…', command=self.face_photo).grid(row=0, column=3, columnspan=3, sticky='e', pady=(0, 6))
        self.face_lbl = ttk.Label(sk, text='', style='Panel.TLabel', foreground=ACC)
        self.face_lbl.grid(row=99, column=0, columnspan=6, sticky='w', pady=(6, 0))
        self.mat_lbl = {}
        base = self.name
        for r, m in enumerate([m for m in info['materials'] if m['image']], start=1):
            short = re.sub(r'^civ_[^_]+_[^_]+_', '', m['name']) or m['name']
            short = short.replace('body_', '').replace('Ch', 'Ch')
            ttk.Label(sk, text=short, style='Panel.TLabel', width=16).grid(row=r, column=0, sticky='w')
            lab = ttk.Label(sk, text=self.mat_text(m), style='Panel.TLabel', width=30); lab.grid(row=r, column=1, sticky='w')
            self.mat_lbl[m['name']] = (lab, m)
            ttk.Button(sk, text='New skin…', command=lambda m=m: self.pick_skin(m)).grid(row=r, column=2, padx=2, pady=2)
            ttk.Button(sk, text='Colour…', command=lambda m=m: self.pick_colour(m)).grid(row=r, column=3, padx=2)
            ttk.Button(sk, text='Original', command=lambda m=m: self.clear_colour(m)).grid(row=r, column=4, padx=2)
            ttk.Button(sk, text='Template…', command=lambda m=m: self.save_template(m)).grid(row=r, column=5, padx=2)

        # built-in gear
        g = ttk.Frame(left, style='Panel.TFrame', padding=12); g.pack(fill='x', pady=(12, 0))
        ttk.Label(g, text='Built-in gear', style='H.TLabel').grid(row=0, column=0, columnspan=6, sticky='w', pady=(0, 6))
        now = {x[0]: x[1:] for x in info['gear'] if x and x[0] != 'unknown'}
        self.gear_on, self.gear_col = {}, {}
        for i, (k, label, dflt) in enumerate(GEAR_KINDS):
            v = tk.BooleanVar(value=k in now); self.gear_on[k] = v
            col = list(now[k][0]) if k in now and now[k] else dflt; self.gear_col[k] = col
            r, c = 1 + i // 3, (i % 3) * 2
            ttk.Checkbutton(g, text=label, variable=v, command=self.mark_gear).grid(row=r, column=c, sticky='w', pady=2)
            sw = tk.Button(g, bg=hexcol(col), width=3, relief='flat', command=lambda k=k: self.pick_gear_colour(k))
            sw.grid(row=r, column=c + 1, sticky='w', padx=(2, 14)); self.gear_col[k + '_btn'] = sw
        if any(x and x[0] == 'unknown' for x in info['gear']):
            ttk.Label(g, text='This model has gear from before the editor. Ticking a box replaces all of it.', style='Panel.TLabel',
                      foreground=WARN).grid(row=4, column=0, columnspan=6, sticky='w', pady=(6, 0))

        # gear files
        gf = ttk.Frame(left, style='Panel.TFrame', padding=12); gf.pack(fill='both', expand=True, pady=(12, 0))
        hdr = ttk.Frame(gf, style='Panel.TFrame'); hdr.pack(fill='x')
        ttk.Label(hdr, text='Gear files (.glb .fbx .obj)', style='H.TLabel').pack(side='left')
        ttk.Button(hdr, text='+ Add gear file…', command=self.add_prop).pack(side='right')
        self.props_box = tk.Listbox(gf, height=5, bg='#121418', fg=FG, relief='flat', selectbackground='#3a3f4b')
        self.props_box.pack(fill='both', expand=True, pady=(8, 4))
        ttk.Button(gf, text='Remove selected', command=self.remove_prop).pack(anchor='w')
        self.refresh_props()

        # right: preview + actions
        ttk.Label(right, text='Preview', style='H.TLabel').pack(anchor='w')
        self.pv = tk.Label(right, bg='#2a2d35', fg=DIM, text='Press Preview to see the changes\n(about 20-40 seconds)', height=16)
        self.pv.pack(fill='both', expand=True, pady=(8, 10))
        acts = ttk.Frame(right, style='Panel.TFrame'); acts.pack(fill='x')
        ttk.Button(acts, text='Preview', command=self.preview).pack(side='left')
        ttk.Button(acts, text='Apply', style='Go.TButton', command=self.apply).pack(side='left', padx=6)
        acts2 = ttk.Frame(right, style='Panel.TFrame'); acts2.pack(fill='x', pady=(6, 0))
        ttk.Button(acts2, text='Undo last change', command=self.undo).pack(side='left')
        ttk.Button(acts2, text='Close', command=self.w.destroy).pack(side='right')

    def mat_text(self, m):
        n = m['name']; parts = []
        if n in self.skins: parts.append('new skin: ' + os.path.basename(self.skins[n]))
        else: parts.append(m['image'] or '')
        if n in self.colours: parts.append('colour %s' % (hexcol(self.colours[n]) if self.colours[n] else 'original'))
        elif m['tinted']: parts.append('recoloured')
        return '  ·  '.join(parts)

    def update_mat(self, m):
        self.mat_lbl[m['name']][0].configure(text=self.mat_text(m))

    def pick_skin(self, m):
        f = filedialog.askopenfilename(parent=self.w, title='New skin for ' + m['name'],
                                       filetypes=[('Image', '*.png *.jpg *.jpeg *.tga *.bmp')])
        if not f: return
        self.skins[m['name']] = f
        if m['tinted'] and m['name'] not in self.colours and messagebox.askyesno(
                'Edit look', 'This part is recoloured. Show the new skin in its own colours instead?', parent=self.w):
            self.colours[m['name']] = None
        self.update_mat(m)

    def pick_colour(self, m):
        c = colorchooser.askcolor(parent=self.w, title='Colour for ' + m['name'])
        if c and c[0]: self.colours[m['name']] = [int(x) for x in c[0]]; self.update_mat(m)

    def clear_colour(self, m):
        self.colours[m['name']] = None; self.update_mat(m)

    def save_template(self, m):
        f = filedialog.asksaveasfilename(parent=self.w, title='Save skin template', defaultextension='.png',
                                         initialfile='%s_%s_template.png' % (self.name, re.sub(r'[^A-Za-z0-9]+', '_', m['name'])))
        if not f: return
        self.busy(True, 'Making the template…')
        self.bg(lambda: self.dress(['--template', m['name'], '--out', f], 'template'),
                lambda r: (self.busy(False, str(r) if isinstance(r, Exception) else
                                     'Template saved: %s - give it to the AI with the note: keep every part inside its magenta outlines' % f)))

    def face_photo(self):
        f = filedialog.askopenfilename(parent=self.w, title='A front-on photo of the face',
                                       filetypes=[('Image', '*.png *.jpg *.jpeg *.bmp *.webp')])
        if f: FaceDialog(self, f)

    def set_face(self, face):
        self.face = face
        self.face_lbl.configure(text='Face from %s - press Preview to see it, Apply to keep it' % os.path.basename(face['photo']))

    def mark_gear(self): self.gear_changed = True

    def pick_gear_colour(self, k):
        c = colorchooser.askcolor(parent=self.w, color=hexcol(self.gear_col[k]), title='Colour')
        if c and c[0]:
            self.gear_col[k] = [int(x) for x in c[0]]; self.gear_col[k + '_btn'].configure(bg=hexcol(self.gear_col[k]))
            self.gear_changed = True

    def refresh_props(self):
        self.props_box.delete(0, 'end')
        for p in self.info.get('props', []):
            mark = '  (will be removed)' if p['name'] in self.props_remove else ''
            self.props_box.insert('end', '%s - %s%s' % (p['name'].replace('Prop_', ''), p.get('attach'), mark))
        for p in self.props_add:
            self.props_box.insert('end', '%s - %s  (new)' % (os.path.basename(p['file']), p['attach']))

    def remove_prop(self):
        sel = self.props_box.curselection()
        if not sel: return
        i = sel[0]; have = self.info.get('props', [])
        if i < len(have): self.props_remove.append(have[i]['name'])
        else: self.props_add.pop(i - len(have))
        self.refresh_props()

    def add_prop(self):
        f = filedialog.askopenfilename(parent=self.w, title='Gear file', filetypes=[('3D model', '*.glb *.gltf *.fbx *.obj')])
        if f: PropDialog(self, f)

    def spec(self):
        sp = {'skins': self.skins, 'colours': self.colours, 'props_add': self.props_add, 'props_remove': self.props_remove}
        if self.face: sp['face'] = self.face
        if self.gear_changed:
            sp['gear'] = []
            for k, _, _ in GEAR_KINDS:
                if self.gear_on[k].get():
                    c = self.gear_col[k]; sp['gear'].append([k, c, [int(x * 0.8) for x in c]] if k == 'vest' else [k, c])
        return sp

    def write_spec(self):
        p = os.path.join(M.WORK, 'dress_%s_spec.json' % self.name); json.dump(self.spec(), open(p, 'w'), indent=1); return p

    # -- preview / apply / undo
    def preview(self):
        self.busy(True, 'Preview: applying the changes to a copy and rendering one picture…')
        def work():
            out = os.path.join(M.WORK, 'preview_%s.blend' % self.name)
            self.dress(['--spec', self.write_spec(), '--out', out], 'preview')
            stills, walks = M.unpack()
            stand = M.civ_stills(stills)['stand'] if self.civ else stills['stand']
            fr = os.path.join(M.WORK, 'preview_%s' % self.name); shutil.rmtree(fr, ignore_errors=True)
            c = run_quiet([worker_python(), os.path.join(KIT, 'build', 'sprites', 'render_char.py'), '--blend', out,
                           '--clips', 'stand=%s,walk=%s' % (stand, walks['walk']), '--frames', '1', '--dirs', '2,5,7', '--out', fr],
                          os.path.join(M.WORK, 'preview_%s.log' % self.name))
            if c: raise RuntimeError('preview render failed - see preview_%s.log in render_work' % self.name)
            return fr
        self.bg(work, self.show)

    def show(self, fr):
        self.busy(False)
        if isinstance(fr, Exception): self.status.configure(text=str(fr)); return
        from PIL import Image, ImageTk
        cells = []
        for clip in ('stand', 'walk'):
            for d in (2, 5, 7):
                p = os.path.join(fr, clip, 'd%d_f00_beauty.png' % d)
                if os.path.exists(p): cells.append(Image.open(p).convert('RGBA'))
        box = None
        for c in cells:
            bb = c.getbbox()
            if bb: box = bb if not box else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
        box = box or (0, 0, 512, 640); cw, ch = box[2] - box[0], box[3] - box[1]
        sheet = Image.new('RGBA', (cw * 3, ch * 2), (42, 45, 53, 255))
        for i, c in enumerate(cells): sheet.alpha_composite(c.crop(box), ((i % 3) * cw, (i // 3) * ch))
        self.w.update_idletasks(); W = max(300, self.pv.winfo_width() - 8); H = max(300, self.pv.winfo_height() - 8)
        sc = min(W / sheet.width, H / sheet.height); sheet = sheet.resize((int(sheet.width * sc), int(sheet.height * sc)), Image.LANCZOS)
        self.img = ImageTk.PhotoImage(sheet); self.pv.configure(image=self.img, text='')
        self.status.configure(text='Preview ready (top: standing, bottom: walking; three directions). Apply to keep it.')

    def apply(self):
        if not (self.skins or self.colours or self.props_add or self.props_remove or self.gear_changed or self.face):
            messagebox.showinfo('Edit look', 'Nothing changed yet.', parent=self.w); return
        if self.app.running() and current_model() == self.name:
            messagebox.showinfo('Edit look', 'He started rendering meanwhile - Stop the machine first.', parent=self.w); return
        self.busy(True, 'Applying… (the old version is kept)')
        def work():
            vd = os.path.join(os.path.dirname(self.blend), '_versions'); os.makedirs(vd, exist_ok=True)
            shutil.copy2(self.blend, os.path.join(vd, '%s_%s.blend' % (self.name, time.strftime('%Y%m%d-%H%M%S'))))
            tmp = self.blend + '.new.blend'
            self.dress(['--spec', self.write_spec(), '--out', tmp], 'apply')
            os.replace(tmp, self.blend); return True
        def done(r):
            self.busy(False)
            if isinstance(r, Exception): self.status.configure(text=str(r)); return
            M.log('look edited:', self.name, json.dumps(self.spec())[:300])
            self.skins, self.colours, self.props_add, self.props_remove, self.gear_changed, self.face = {}, {}, [], [], False, None
            self.status.configure(text='Applied. %s is queued and the machine re-renders him by itself (if it is running).' % self.name)
            self.bg(lambda: self.read(), self.reload)
        self.bg(work, done)

    def reload(self, info):
        if isinstance(info, Exception): return
        for c in self.body.winfo_children(): c.destroy()
        self.build(info); self.app.refresh_now()

    def undo(self):
        vd = os.path.join(os.path.dirname(self.blend), '_versions')
        vs = sorted(glob.glob(os.path.join(vd, self.name + '_*.blend')))
        if not vs: messagebox.showinfo('Edit look', 'No earlier version of %s.' % self.name, parent=self.w); return
        if not messagebox.askyesno('Edit look', 'Go back to the version saved %s?' % os.path.basename(vs[-1])[len(self.name) + 1:-6], parent=self.w): return
        shutil.copy2(self.blend, self.blend + '.undone'); shutil.move(vs[-1], self.blend); os.utime(self.blend, None)
        os.remove(self.blend + '.undone')
        M.log('look undone:', self.name, 'back to', os.path.basename(vs[-1]))
        self.status.configure(text='Back to the earlier version - he is queued to re-render.')
        self.bg(lambda: self.read(), self.reload)


class FaceDialog:
    """Six clicks: left eye, right eye, mouth on the photo and the same three on the model's face."""
    LABELS = ['1 left eye', '2 right eye', '3 mouth']

    def __init__(self, ed, photo):
        from PIL import Image, ImageTk
        self.ed, self.photo = ed, photo; self.pp, self.mp = [], []
        w = self.w = tk.Toplevel(ed.w); w.title('Face from photo'); w.configure(bg=PANEL); w.transient(ed.w); w.geometry('1180x800')
        top = ttk.Frame(w, style='Panel.TFrame', padding=(14, 10)); top.pack(fill='x')
        ttk.Label(top, text='Click on BOTH pictures, in order: 1 the eye on the LEFT of the picture, 2 the eye on the RIGHT, '
                  '3 the middle of the mouth.', style='Panel.TLabel').pack(anchor='w')
        ttk.Label(top, text='Use a photo taken straight on, eyes level, nothing covering the face. Right-click clears that picture.',
                  style='Panel.TLabel', foreground=DIM).pack(anchor='w')
        mid = ttk.Frame(w, style='Panel.TFrame', padding=(14, 4)); mid.pack(fill='both', expand=True)
        self.cv_p = tk.Canvas(mid, width=540, height=560, bg='#121418', highlightthickness=0); self.cv_p.pack(side='left', padx=(0, 10))
        self.cv_m = tk.Canvas(mid, width=540, height=560, bg='#121418', highlightthickness=0); self.cv_m.pack(side='left')
        im = Image.open(photo).convert('RGB'); self.ps = min(540 / im.width, 560 / im.height)
        self.pimg = ImageTk.PhotoImage(im.resize((int(im.width * self.ps), int(im.height * self.ps)), Image.LANCZOS))
        self.cv_p.create_image(0, 0, anchor='nw', image=self.pimg)
        self.cv_m.create_text(270, 280, text='Reading the model’s face…', fill=DIM)
        self.cv_p.bind('<Button-1>', lambda e: self.click(e, 'p')); self.cv_m.bind('<Button-1>', lambda e: self.click(e, 'm'))
        self.cv_p.bind('<Button-3>', lambda e: self.clear('p')); self.cv_m.bind('<Button-3>', lambda e: self.clear('m'))
        bot = ttk.Frame(w, style='Panel.TFrame', padding=14); bot.pack(fill='x')
        self.vars = {}
        for i, (k, label, lo, hi, d, res) in enumerate([('strength', 'Strength', 0.3, 1.0, 0.9, 0.05),
                                                       ('cartoon', 'Cartoon look', 0, 3, 2, 1),
                                                       ('match', 'Match body skin tone', 0, 1, 0.6, 0.05)]):
            ttk.Label(bot, text=label, style='Panel.TLabel').grid(row=0, column=i * 2, sticky='e', padx=(0, 4))
            v = tk.DoubleVar(value=d); self.vars[k] = v
            tk.Scale(bot, variable=v, from_=lo, to=hi, resolution=res, orient='horizontal', length=180, bg=PANEL, fg=FG,
                     highlightthickness=0, troughcolor='#2c3039').grid(row=0, column=i * 2 + 1, padx=(0, 16))
        ttk.Button(bot, text='Use this face', style='Go.TButton', command=self.ok).grid(row=0, column=7, padx=(10, 6))
        ttk.Button(bot, text='Cancel', command=w.destroy).grid(row=0, column=8)
        self.msg = ttk.Label(bot, text='', style='Panel.TLabel', foreground=WARN); self.msg.grid(row=1, column=0, columnspan=9, sticky='w', pady=(6, 0))
        self.fv = os.path.join(M.WORK, 'faceview_%s.png' % ed.name)
        ed.bg(lambda: ed.dress(['--faceview', self.fv], 'faceview'), self.show_model)

    def show_model(self, r):
        from PIL import Image, ImageTk
        if isinstance(r, Exception): self.cv_m.delete('all'); self.cv_m.create_text(270, 280, text=str(r), fill=BAD, width=500); return
        self.meta = json.load(open(self.fv + '.json'))
        im = Image.open(self.fv).convert('RGBA'); self.ms = min(540 / im.width, 560 / im.height)
        bg = Image.new('RGBA', im.size, (18, 20, 24, 255)); bg.alpha_composite(im)
        self.mimg = ImageTk.PhotoImage(bg.resize((int(im.width * self.ms), int(im.height * self.ms)), Image.LANCZOS))
        self.cv_m.delete('all'); self.cv_m.create_image(0, 0, anchor='nw', image=self.mimg)

    def click(self, e, which):
        pts, cv = (self.pp, self.cv_p) if which == 'p' else (self.mp, self.cv_m)
        if which == 'm' and not hasattr(self, 'meta'): return
        if len(pts) >= 3: return
        pts.append((e.x, e.y)); n = len(pts)
        cv.create_oval(e.x - 6, e.y - 6, e.x + 6, e.y + 6, outline=ACC, width=2, tags='mark')
        cv.create_text(e.x + 12, e.y - 12, text=self.LABELS[n - 1], fill=ACC, anchor='w', tags='mark', font=('Segoe UI', 10, 'bold'))

    def clear(self, which):
        (self.pp if which == 'p' else self.mp).clear(); (self.cv_p if which == 'p' else self.cv_m).delete('mark')

    def ok(self):
        if len(self.pp) < 3 or len(self.mp) < 3:
            self.msg.configure(text='Three clicks on each picture: left eye, right eye, mouth.'); return
        photo_pts = [[x / self.ps, y / self.ps] for x, y in self.pp]
        m = self.meta; model_pts = [[m['x0'] + (x / self.ms) * m['s'], m['z1'] - (y / self.ms) * m['s']] for x, y in self.mp]
        self.ed.set_face({'photo': self.photo, 'photo_pts': photo_pts, 'model_pts': model_pts,
                          **{k: round(v.get(), 2) for k, v in self.vars.items()}})
        self.w.destroy()


class PropDialog:
    """Where a gear file goes and how it sits: attach point, size, nudges, turns."""

    def __init__(self, ed, f):
        self.ed, self.f = ed, f
        w = self.w = tk.Toplevel(ed.w); w.title('Gear file - ' + os.path.basename(f)); w.configure(bg=PANEL); w.transient(ed.w)
        fr = ttk.Frame(w, style='Panel.TFrame', padding=14); fr.pack(fill='both', expand=True)
        ttk.Label(fr, text=os.path.basename(f), style='H.TLabel').grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        ttk.Label(fr, text='Goes on', style='Panel.TLabel').grid(row=1, column=0, sticky='w')
        self.attach = ttk.Combobox(fr, values=[n for _, n in ATTACH_NAMES], state='readonly', width=24); self.attach.current(0)
        self.attach.grid(row=1, column=1, sticky='w', pady=4)
        self.vars = {}
        rows = [('size', 'Size', 0.3, 3.0, 1.0), ('up', 'Up / down (cm)', -30, 30, 0), ('forward', 'Forward / back (cm)', -30, 30, 0),
                ('side', 'Left / right (cm)', -30, 30, 0), ('turn', 'Turn (deg)', -180, 180, 0), ('tilt', 'Tilt (deg)', -180, 180, 0),
                ('roll', 'Roll (deg)', -180, 180, 0)]
        for i, (k, label, lo, hi, d) in enumerate(rows, start=2):
            ttk.Label(fr, text=label, style='Panel.TLabel').grid(row=i, column=0, sticky='w')
            v = tk.DoubleVar(value=d); self.vars[k] = v
            tk.Scale(fr, variable=v, from_=lo, to=hi, resolution=0.05 if k == 'size' else 1, orient='horizontal', length=260,
                     bg=PANEL, fg=FG, highlightthickness=0, troughcolor='#2c3039').grid(row=i, column=1, sticky='w')
        b = ttk.Frame(fr, style='Panel.TFrame'); b.grid(row=20, column=0, columnspan=2, sticky='e', pady=(10, 0))
        ttk.Button(b, text='Add', style='Go.TButton', command=self.ok).pack(side='left')
        ttk.Button(b, text='Cancel', command=w.destroy).pack(side='left', padx=6)
        ttk.Label(fr, text='Add it, Preview, then adjust: remove it and add again with new numbers.', style='Panel.TLabel',
                  foreground=DIM).grid(row=21, column=0, columnspan=2, sticky='w', pady=(8, 0))

    def ok(self):
        a = ATTACH_NAMES[[n for _, n in ATTACH_NAMES].index(self.attach.get())][0]
        p = {'file': self.f, 'attach': a}
        p.update({k: round(v.get(), 2) for k, v in self.vars.items()})
        self.ed.props_add.append(p); self.ed.refresh_props(); self.w.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
