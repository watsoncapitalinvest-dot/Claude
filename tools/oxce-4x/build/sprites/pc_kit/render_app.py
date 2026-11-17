# RENDER MACHINE - the app. A window over render_cartel.py --watch: start/stop, add models, pick the extra clips,
# watch each model's progress, see the last finished sheet. Run from RENDER_APP.bat (py -3.13 render_app.py).
import os, sys, json, time, shutil, subprocess, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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
        ttk.Button(btns, text='Re-render selected', command=self.rerender).pack(side='left')
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


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
