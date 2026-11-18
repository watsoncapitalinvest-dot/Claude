"""G.I. JOE 4x - JOE LAB: the offline hub for testing, recording, simulating and design notes (BUILD-1, 18 Nov 2026;
John 02:59 "Combine all the features of the other simulators ... and the character machine into one ui", 03:00 "Make it a
real offline hub for testing recording simulating and making design notes. It's a machine for testing gameplay and balance").

Runs on John's PC with no internet and no AI. Started by JOE_LAB.bat (py -3.13 joe_lab.py), next to OpenXcom.exe.
It never touches his saves or settings: the game plays in user_sim\\, and everything it records goes in lab\\.

TABS
  Checks      the fixes to the first two months, tested: plays 60-day campaigns and grades each one PASS / FAIL / NOT REACHED
              against the list in joe_checks.py (the cartel flight, the tail, the tip, no Cobra before the broadcast ...).
  Campaign    the game plays a whole campaign by itself (OXCE_CAMPAIGNSIM): missions flown, battles fought by the AI on both
              sides, labs kept busy. Live: the day, battles, research, quiet days; the timeline, STALLs in red.
  Battles     New Battle missions one after another (the battle simulator): live turn / who is standing / pictures / results.
  Strategy    years of the world map with no battles shown (OXCE_FASTFORWARD): what Cobra builds and when, by player style.
  Characters  the render machine (render_kit\\render_cartel.py --watch): start / stop, what it is doing, the full app.
  Runs        every run ever made, kept: kind, when, settings, result. Open one: its timeline / events, pictures, log.
  Balance     numbers across all the runs: each mission's win rate, turns, Joes lost; each campaign's stalls and when each
              research topic first came; each strategy run's key Cobra dates.
  Notes       design notes: write one, tie it to a run, tag it (balance / bug / design / art / story). Export all as one text
              file to hand to the desks.
"""
import os, sys, time, json, shutil, subprocess, threading, queue, glob, re, statistics, datetime
import tkinter as tk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import joe_checks
import joe_editor
from tkinter import ttk, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
WIN = sys.platform.startswith('win')
GAME = os.environ.get('SIM_GAME', os.path.join(HERE, 'OpenXcom.exe' if WIN else 'openxcom'))
if WIN and 'SIM_GAME' not in os.environ and os.path.exists(os.path.join(HERE, 'x64', 'OpenXcom.exe')):
    GAME = os.path.join(HERE, 'x64', 'OpenXcom.exe')   # the 64-bit game: no 4 GB memory ceiling
USER = os.path.join(HERE, 'user')
USER_SIM = os.environ.get('SIM_USER', os.path.join(HERE, 'user_sim'))
LAB = os.environ.get('LAB_DIR', os.path.join(HERE, 'lab'))
RUNS = os.path.join(LAB, 'runs')
NOTES = os.path.join(LAB, 'notes')
KIT = os.path.join(HERE, 'render_kit')
WORK = os.path.join(HERE, 'render_work')
EXTRA = os.environ.get('SIM_ARGS', '').split()
if not EXTRA and os.path.basename(os.path.dirname(GAME)) == 'x64':
    EXTRA = ['-data', HERE]
PY = sys.executable

INK, PAPER, PANEL, GOLD, RED, GREEN, AMBER, GREY, BLUE = '#e8e4d8', '#14181c', '#1f262c', '#d8b45a', '#ff5a4a', '#5ec46a', '#e0a030', '#8a9198', '#5aa8ff'
FONT = ('Segoe UI', 10) if WIN else ('DejaVu Sans', 10)
MONO = ('Consolas', 9) if WIN else ('DejaVu Sans Mono', 9)
STYLES = ('defensive', 'normal', 'aggressive')
NOTE_TAGS = ('balance', 'bug', 'design', 'art', 'story', 'other')


# ----------------------------------------------------------------------------------------------------------- helpers
def now_tag():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def read(p, default=''):
    try:
        return open(p, encoding='utf-8', errors='replace').read()
    except OSError:
        return default


def open_path(p):
    if not os.path.exists(p): return
    if WIN: os.startfile(p)
    else: subprocess.Popen(['xdg-open', p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def kind_of(result):
    if result.startswith('CAMPAIGN '):
        return 'win' if result.startswith('CAMPAIGN END') else 'bad'
    w = result.split()[0] if result else ''
    return {'WIN': 'win', 'LOSS': 'loss', 'STOPPED': 'stopped', 'CAMPAIGN': 'win', 'FINISHED': 'win'}.get(w, 'bad')


def new_run_dir(kind, settings):
    d = os.path.join(RUNS, f'{kind}_{now_tag()}')
    os.makedirs(d, exist_ok=True)
    json.dump({'kind': kind, 'started': datetime.datetime.now().isoformat(timespec='seconds'), 'settings': settings},
              open(os.path.join(d, 'run.json'), 'w'), indent=1)
    return d


def finish_run(d, result, errors=0, seconds=0):
    p = os.path.join(d, 'run.json')
    try: meta = json.load(open(p))
    except (OSError, ValueError): meta = {}
    meta.update(result=result, errors=errors, seconds=seconds, finished=datetime.datetime.now().isoformat(timespec='seconds'))
    json.dump(meta, open(p, 'w'), indent=1)


def prepare_user_sim(post):
    """the simulator plays in its own folder: the mod and the options copied in, nothing of John's changed"""
    if os.environ.get('SIM_USER'):
        return True
    if not os.path.isdir(os.path.join(USER, 'mods', 'GIJoe4x')):
        post('error', 'Start the game once with Play_4x.bat first, so the mod is unpacked.')
        return False
    post('status', 'Copying the mod into the simulator\'s own folder ...')
    os.makedirs(USER_SIM, exist_ok=True)
    if WIN:
        subprocess.run(['robocopy', os.path.join(USER, 'mods'), os.path.join(USER_SIM, 'mods'), '/MIR', '/NFL', '/NDL', '/NJH',
                        '/NJS', '/NP'], creationflags=0x08000000)
    else:
        shutil.copytree(os.path.join(USER, 'mods'), os.path.join(USER_SIM, 'mods'), dirs_exist_ok=True)
    if os.path.exists(os.path.join(USER, 'options.cfg')):
        shutil.copyfile(os.path.join(USER, 'options.cfg'), os.path.join(USER_SIM, 'options.cfg'))
    return True


class GameJob(threading.Thread):
    """Runs the game one or more times with a set of variables; talks to the window only through the queue."""

    def __init__(self, q, kind, plan):
        """plan: a list of (settings dict, env dict) - one game run each, each with its own run folder"""
        super().__init__(daemon=True)
        self.q, self.kind, self.plan, self.stop, self.proc, self.dir = q, kind, plan, False, None, None

    def post(self, *m):
        self.q.put((self.kind,) + m)

    def run(self):
        if not prepare_user_sim(self.post):
            self.post('finished'); return
        for settings, env_add in self.plan:
            if self.stop: break
            d = new_run_dir(self.kind, settings)
            self.dir = d
            self.post('started', d, settings)
            env = dict(os.environ, OXCE_BATTLESIM_OUT=d, OXCE_BATTLE_SCALE='4', OXCE_MAP_HIRES='4', **env_add)
            if self.kind == 'strategy':
                env['OXCE_FF_REPORT'] = os.path.join(d, 'report.txt')
            log = os.path.join(USER_SIM, 'openxcom.log')
            try: os.remove(log)
            except OSError: pass
            cmd = [GAME, '-user', USER_SIM, '-cfg', USER_SIM, '-displayWidth', '1280', '-displayHeight', '800', '-fullscreen', 'false',
                   '-debug', 'false'] + EXTRA
            t0 = time.time()
            try:
                self.proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(GAME))
                code = self.proc.wait()
            except OSError as e:
                self.post('error', f'Could not start the game: {e}'); break
            if os.path.exists(log): shutil.copyfile(log, os.path.join(d, 'log.txt'))
            res = read(os.path.join(d, 'result.txt')).strip()
            if self.kind == 'strategy' and not res and os.path.exists(os.path.join(d, 'report.txt')):
                res = 'FINISHED ' + str(settings.get('days', '')) + ' days'
            if self.stop and not res: res = 'STOPPED by you'
            if not res: res = f'CRASH: the game shut down (exit code {code})'
            errs = sum(1 for l in read(os.path.join(d, 'log.txt')).splitlines() if '[ERROR]' in l or '[FATAL]' in l)
            finish_run(d, res, errs, int(time.time() - t0))
            self.post('result', d, res, errs)
            if res.startswith('NO MISSION'):
                self.post('nomore'); break
        self.post('finished')

    def halt(self):
        self.stop = True
        if self.proc and self.proc.poll() is None:
            if WIN: subprocess.run(['taskkill', '/T', '/F', '/PID', str(self.proc.pid)], creationflags=0x08000000, capture_output=True)
            else: self.proc.kill()


def picture(label, path, size):
    try:
        from PIL import Image, ImageTk
        im = Image.open(path); im.thumbnail(size); ph = ImageTk.PhotoImage(im)
    except ImportError:
        ph = tk.PhotoImage(file=path); f = max(1, ph.width() // size[0] + 1); ph = ph.subsample(f, f)
    except Exception:
        return None
    label.configure(image=ph, text='', width=0, height=0)
    label.image = ph
    return ph


# --------------------------------------------------------------------------------------------------------- the window
class Lab:
    def __init__(self, root):
        self.root, self.q = root, queue.Queue()
        self.jobs = {}
        root.title('G.I. Joe 4x - JOE LAB')
        root.configure(bg=PAPER); root.geometry('1280x820'); root.minsize(1040, 680)
        st = ttk.Style(); st.theme_use('clam')
        st.configure('.', background=PAPER, foreground=INK, font=FONT, fieldbackground=PANEL)
        for n, bg in (('TFrame', PAPER), ('Panel.TFrame', PANEL)): st.configure(n, background=bg)
        st.configure('TLabel', background=PAPER, foreground=INK)
        st.configure('Panel.TLabel', background=PANEL, foreground=INK)
        st.configure('Head.TLabel', background=PAPER, foreground=GOLD, font=(FONT[0], 13, 'bold'))
        st.configure('Dim.TLabel', background=PANEL, foreground=GREY)
        st.configure('TButton', background='#2c353d', foreground=INK, padding=(12, 5), borderwidth=0)
        st.map('TButton', background=[('active', '#3a4651'), ('disabled', '#22282e')], foreground=[('disabled', '#5b6268')])
        st.configure('Go.TButton', background='#2e6b38'); st.map('Go.TButton', background=[('active', '#3a8546'), ('disabled', '#22282e')])
        st.configure('Stop.TButton', background='#8a2a22'); st.map('Stop.TButton', background=[('active', '#a8352b'), ('disabled', '#22282e')])
        st.map('TCombobox', fieldbackground=[('readonly', '#2c353d')], foreground=[('readonly', INK)], selectbackground=[('readonly', '#2c353d')],
               selectforeground=[('readonly', INK)])
        st.configure('TSpinbox', fieldbackground='#2c353d', foreground=INK, arrowcolor=INK)
        st.configure('TEntry', fieldbackground='#2c353d', foreground=INK, insertcolor=INK)
        st.configure('TNotebook', background=PAPER, borderwidth=0)
        st.configure('TNotebook.Tab', background='#2c353d', foreground=INK, padding=(16, 6), font=(FONT[0], 10, 'bold'))
        st.map('TNotebook.Tab', background=[('selected', '#3d4a55')], foreground=[('selected', GOLD)])
        st.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=INK, rowheight=22, borderwidth=0)
        st.configure('Treeview.Heading', background='#2c353d', foreground=GOLD, font=(FONT[0], 9, 'bold'))
        hdr = ttk.Frame(root, padding=(14, 10, 14, 4)); hdr.pack(fill='x')
        ttk.Label(hdr, text='JOE LAB', style='Head.TLabel', font=(FONT[0], 16, 'bold')).pack(side='left')
        ttk.Label(hdr, text='   testing, recording, simulating and design notes - on this PC, no internet, no AI', foreground=GREY).pack(side='left')
        ttk.Button(hdr, text='Open lab folder', command=lambda: (os.makedirs(LAB, exist_ok=True), open_path(LAB))).pack(side='right')
        self.nb = ttk.Notebook(root); self.nb.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        # what the Rules Editor and My Play Style tabs use from here
        self.MONO, self.GAME, self.USER_SIM, self.EXTRA, self.WIN = MONO, GAME, USER_SIM, EXTRA, WIN
        self.open_path, self.prepare_user_sim = open_path, prepare_user_sim
        rs = os.path.join('mods', 'GIJoe4x', 'Ruleset')
        self.paths = {'ruleset': os.path.join(USER, rs), 'master': os.path.join(LAB, 'john_changes.rul'),
                      'targets': [os.path.join(USER, rs, joe_editor.OVERRIDE), os.path.join(USER_SIM, rs, joe_editor.OVERRIDE)],
                      'log': os.path.join(LAB, 'CHANGES_LOG.txt'), 'playlog': os.path.join(USER, 'playstyle.txt'),
                      'profile': os.path.join(LAB, 'profile.txt')}
        self.tab_checks(); self.tab_campaign(); self.tab_battles(); self.tab_strategy(); self.tab_characters(); self.tab_runs(); self.tab_balance(); self.tab_notes()
        self.editor = joe_editor.EditorTab(self, self.page('  Rules Editor  '), self.paths)
        self.style = joe_editor.StyleTab(self, self.page('  My Play Style  '), self.paths)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()

    # ------------------------------------------------------------------------------------------------ common pieces
    def page(self, title):
        f = ttk.Frame(self.nb, padding=10); self.nb.add(f, text=title); return f

    def textbox(self, parent, height=12):
        t = tk.Text(parent, bg=PANEL, fg=INK, font=MONO, relief='flat', wrap='word', height=height, insertbackground=INK)
        for tag, col in (('gold', GOLD), ('red', RED), ('green', GREEN), ('grey', GREY), ('amber', AMBER), ('blue', BLUE)):
            t.tag_configure(tag, foreground=col)
        return t

    def gauge_row(self, parent, items):
        g = {}
        row = ttk.Frame(parent, style='Panel.TFrame', padding=10); row.pack(fill='x', pady=(0, 8))
        for i, (key, label, col) in enumerate(items):
            f = ttk.Frame(row, style='Panel.TFrame'); f.grid(row=0, column=i, sticky='w', padx=(0, 30))
            ttk.Label(f, text=label, style='Dim.TLabel', font=(FONT[0], 8)).pack(anchor='w')
            v = ttk.Label(f, text='-', style='Panel.TLabel', foreground=col, font=(FONT[0], 16, 'bold')); v.pack(anchor='w')
            g[key] = v
        return g

    def controls(self, parent, kind, start):
        bar = ttk.Frame(parent); bar.pack(fill='x', pady=(0, 8))
        go = ttk.Button(bar, text='▶  Start', style='Go.TButton', command=start); go.pack(side='right')
        stop = ttk.Button(bar, text='■  Stop', style='Stop.TButton', state='disabled', command=lambda: self.halt(kind)); stop.pack(side='right', padx=6)
        status = ttk.Label(bar, text='Ready.', foreground=GREY); status.pack(side='left')
        return go, stop, status

    def halt(self, kind):
        j = self.jobs.get(kind)
        if j: j.halt()

    def launch(self, kind, plan):
        if not os.path.exists(GAME):
            messagebox.showerror('Joe Lab', 'Put Joe Lab next to OpenXcom.exe.'); return
        if any(j.is_alive() for j in self.jobs.values()):
            messagebox.showinfo('Joe Lab', 'One run at a time: the game plays in one window. Stop the other run first.'); return
        j = GameJob(self.q, kind, plan); self.jobs[kind] = j; j.start()
        w = getattr(self, kind)
        w['go'].configure(state='disabled'); w['stop'].configure(state='normal')
        w['status'].configure(text='Running. You can use the PC; leave the game window alone.')

    def latest_pic(self, w, d, size=(460, 290)):
        pics = sorted(glob.glob(os.path.join(d, '*.png')), key=os.path.getmtime) if d else []
        if not pics: return
        p = pics[-1]; mt = os.path.getmtime(p)
        if (p, mt) == w.get('pic'): return
        if picture(w['piclabel'], p, size): w['pic'] = (p, mt); w['picname'].configure(text=os.path.basename(p)[:-4].replace('_', ' '))

    def status_file(self, d):
        try: return dict(l.split(' ', 1) for l in read(os.path.join(d, 'status.txt')).split('\n') if ' ' in l)
        except ValueError: return {}

    def feed(self, w, d, fname, colour):
        lines = read(os.path.join(d, fname)).splitlines()
        for l in lines[w.get('seen', 0):]:
            w['text'].insert('end', l + '\n', colour(l)); w['text'].see('end')
        w['seen'] = len(lines)

    # ------------------------------------------------------------------------------------------------------ CHECKS
    VCOL = {'PASS': 'green', 'FAIL': 'red', 'NOT REACHED': 'grey', 'LOOK': 'amber'}
    VMARK = {'PASS': 'PASS', 'FAIL': 'FAIL', 'NOT REACHED': '-', 'LOOK': 'look'}

    def tab_checks(self):
        p = self.page('  Checks  ')
        w = self.checks = {'graded': []}            # graded: [(run folder, [(id, question, verdict, evidence)])]
        w['go'], w['stop'], w['status'] = self.controls(p, 'checks', self.start_checks)
        w['status'].configure(text='Each run is a new campaign. The dice differ, so a check one run never reaches, another will.')
        o = ttk.Frame(p); o.pack(fill='x', pady=(0, 8))
        w['days'], w['runs'] = tk.IntVar(value=60), tk.IntVar(value=3)
        for lab, var, lo, hi in (('Days a run', w['days'], 20, 365), ('Runs', w['runs'], 1, 20)):
            ttk.Label(o, text=lab).pack(side='left'); ttk.Spinbox(o, from_=lo, to=hi, width=5, textvariable=var).pack(side='left', padx=(4, 14))
        ttk.Button(o, text='Grade the last runs again', command=self.regrade).pack(side='left', padx=(10, 0))
        ttk.Button(o, text='Save the report', command=self.save_checks).pack(side='left', padx=6)
        body = ttk.Frame(p); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=5); body.columnconfigure(1, weight=3); body.rowconfigure(0, weight=5); body.rowconfigure(1, weight=1)
        t = ttk.Treeview(body, columns=('q', 'all'), show='headings', height=len(joe_checks.CHECKS))
        for v, col in (('PASS', GREEN), ('FAIL', RED), ('NOT REACHED', GREY), ('LOOK', AMBER)): t.tag_configure(v, foreground=col)
        t.grid(row=0, column=0, sticky='nsew', padx=(0, 8)); t.bind('<<TreeviewSelect>>', self.show_check)
        w['tree'] = t
        ev = ttk.Frame(body, style='Panel.TFrame', padding=8); ev.grid(row=0, column=1, sticky='nsew')
        ttk.Label(ev, text='WHAT EACH RUN SHOWED  (click a check)', style='Dim.TLabel').pack(anchor='w')
        w['ev'] = self.textbox(ev, 14); w['ev'].configure(wrap='word'); w['ev'].pack(fill='both', expand=True)
        lf = ttk.Frame(body, style='Panel.TFrame', padding=8); lf.grid(row=1, column=0, sticky='nsew', padx=(0, 8), pady=(8, 0))
        w['day'] = ttk.Label(lf, text='THIS RUN', style='Dim.TLabel'); w['day'].pack(anchor='w')
        w['text'] = self.textbox(lf, 4); w['text'].pack(fill='both', expand=True)
        ef = ttk.Frame(body, style='Panel.TFrame', padding=8); ef.grid(row=1, column=1, sticky='nsew', pady=(8, 0))
        ttk.Label(ef, text='A CAMPAIGN RUN CANNOT SEE THESE: CHECK THEM BY EYE', style='Dim.TLabel').pack(anchor='w')
        ttk.Label(ef, text='\n'.join('  - ' + x for x in joe_checks.BY_EYE), style='Panel.TLabel', justify='left').pack(anchor='w')
        self.fill_checks()

    def fill_checks(self):
        """the grid: one row a check, one column a run, and the overall answer"""
        w = self.checks; t = w['tree']; g = w['graded']
        cols = ['q', 'all'] + [f'r{i}' for i in range(len(g))]
        t.configure(columns=cols)
        t.heading('q', text='Check'); t.column('q', width=420, minwidth=300, anchor='w', stretch=True)
        t.heading('all', text='Overall'); t.column('all', width=90, anchor='w', stretch=False)
        for i, (d, _) in enumerate(g):
            t.heading(f'r{i}', text=f'Run {i + 1}'); t.column(f'r{i}', width=52, anchor='center', stretch=False)
        t.delete(*t.get_children())
        for n, (cid, q, _fn) in enumerate(joe_checks.CHECKS):
            vs = [res[n][2] for _, res in g]
            overall = ('FAIL' if 'FAIL' in vs else 'PASS' if 'PASS' in vs else 'LOOK' if 'LOOK' in vs else 'NOT REACHED') if vs else ''
            t.insert('', 'end', iid=cid, values=[q, self.VMARK.get(overall, '')]
                     + [self.VMARK[v] for v in vs], tags=(overall,) if overall else ())

    def show_check(self, _e=None):
        w = self.checks; sel = w['tree'].selection(); box = w['ev']; box.delete('1.0', 'end')
        if not sel: return
        n = [c[0] for c in joe_checks.CHECKS].index(sel[0])
        box.insert('end', joe_checks.CHECKS[n][1] + '\n\n', 'gold')
        for i, (d, res) in enumerate(w['graded']):
            _, _, v, ev = res[n]
            box.insert('end', f'Run {i + 1}  {v}\n', self.VCOL[v])
            box.insert('end', f'   {ev}\n   ({os.path.basename(d)})\n\n', 'grey')

    def grade_into(self, d):
        res = joe_checks.grade(d)
        open(os.path.join(d, 'checks.txt'), 'w', encoding='utf-8').write(joe_checks.report([d]) + '\n')
        self.checks['graded'].append((d, res)); self.fill_checks()

    def start_checks(self):
        w = self.checks
        try: days, n = int(w['days'].get()), int(w['runs'].get())
        except (tk.TclError, ValueError): messagebox.showerror('Joe Lab', 'Numbers only, please.'); return
        w['graded'] = []; self.fill_checks()
        s = {'days': days, 'turns': 25, 'headstart': 0, 'joes': 'normal', 'cobra': 'normal'}
        env = {'OXCE_CAMPAIGNSIM': str(days), 'OXCE_CAMPAIGNSIM_SCREENS': str(days), 'OXCE_BATTLESIM_TURNS': '25',
               'OXCE_CAMPAIGNSIM_HEADSTART': '0', 'OXCE_BATTLESIM_JOES': 'normal', 'OXCE_BATTLESIM_COBRA': 'normal'}
        env.update(self.style.env()); s['plays_like_john'] = bool(self.style.env())
        self.launch('checks', [(s, env)] * n)

    def regrade(self):
        """grade the campaign runs already kept (the newest few), with the checks as they are now"""
        w = self.checks
        try: n = int(w['runs'].get())
        except (tk.TclError, ValueError): n = 3
        dirs = [m['dir'] for m in self.all_runs() if m.get('kind') in ('checks', 'campaign')][:n]
        if not dirs: messagebox.showinfo('Joe Lab', 'No campaign runs kept yet. Press Start.'); return
        w['graded'] = []
        for d in reversed(dirs): self.grade_into(d)
        w['status'].configure(text=f'Graded the {len(dirs)} newest campaign run(s) again.')

    def save_checks(self):
        g = self.checks['graded']
        if not g: messagebox.showinfo('Joe Lab', 'Nothing graded yet.'); return
        os.makedirs(LAB, exist_ok=True)
        p = os.path.join(LAB, f'CHECKS_{now_tag()}.txt')
        lines = ['JOE LAB CHECKS, ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), '']
        for n, (cid, q, _fn) in enumerate(joe_checks.CHECKS):
            lines.append(q)
            for i, (d, res) in enumerate(g): lines.append(f'   run {i + 1}: {res[n][2]:12} {res[n][3]}')
            lines.append('')
        lines += ['BY EYE (a campaign run cannot see these):'] + ['   ' + x for x in joe_checks.BY_EYE]
        open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        open_path(p)

    # ---------------------------------------------------------------------------------------------------- CAMPAIGN
    def tab_campaign(self):
        p = self.page('  Campaign  ')
        w = self.campaign = {}
        w['go'], w['stop'], w['status'] = self.controls(p, 'campaign', self.start_campaign)
        o = ttk.Frame(p); o.pack(fill='x', pady=(0, 8))
        w['days'], w['turns'], w['head'], w['runs'] = tk.IntVar(value=120), tk.IntVar(value=25), tk.IntVar(value=0), tk.IntVar(value=1)
        w['joes'], w['cobra'] = tk.StringVar(value='normal'), tk.StringVar(value='normal')
        for lab, var, lo, hi in (('Days to play', w['days'], 5, 1500), ('Battle turn limit', w['turns'], 5, 60),
                                 ('Cobra head start', w['head'], 0, 24), ('Runs', w['runs'], 1, 99)):
            ttk.Label(o, text=lab).pack(side='left'); ttk.Spinbox(o, from_=lo, to=hi, width=5, textvariable=var).pack(side='left', padx=(4, 14))
        for lab, var in (('Joes play', w['joes']), ('Cobra plays', w['cobra'])):
            ttk.Label(o, text=lab).pack(side='left')
            ttk.Combobox(o, values=STYLES, textvariable=var, width=10, state='readonly').pack(side='left', padx=(4, 12))
        w['g'] = self.gauge_row(p, (('day', 'DAY', GOLD), ('battles', 'BATTLES', INK), ('researched', 'RESEARCH KNOWN', BLUE),
                                    ('missions', 'MISSIONS OPEN', AMBER), ('sites_found', 'COBRA SITES FOUND', RED),
                                    ('quiet_days', 'DAYS WITH NOTHING NEW', INK)))
        body = ttk.Frame(p); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)
        tlf = ttk.Frame(body, style='Panel.TFrame', padding=8); tlf.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        ttk.Label(tlf, text='TIMELINE  (STALL = 30 days with nothing new: the thing to look for)', style='Dim.TLabel').pack(anchor='w')
        w['text'] = self.textbox(tlf); w['text'].pack(fill='both', expand=True)
        pf = ttk.Frame(body, style='Panel.TFrame', padding=8); pf.grid(row=0, column=1, sticky='nsew')
        ttk.Label(pf, text='LATEST PICTURE', style='Dim.TLabel').pack(anchor='w')
        w['piclabel'] = tk.Label(pf, bg=PANEL, fg=GREY, text='(none yet)', width=50, height=14); w['piclabel'].pack(fill='both', expand=True)
        w['picname'] = ttk.Label(pf, text='', style='Dim.TLabel'); w['picname'].pack(anchor='w')
        ttk.Label(pf, text='How it plays: a new game, the squad flown to every mission and found Cobra site, both sides\n'
                           'of each battle played by the game\'s AI, the labs kept busy (cheapest topic first),\n'
                           'every popup answered. It does not buy, build or manage the base.',
                  style='Dim.TLabel', justify='left').pack(anchor='w', pady=(8, 0))

    def start_campaign(self):
        w = self.campaign
        try: days, turns, head, n = int(w['days'].get()), int(w['turns'].get()), int(w['head'].get()), int(w['runs'].get())
        except (tk.TclError, ValueError): messagebox.showerror('Joe Lab', 'Numbers only, please.'); return
        s = {'days': days, 'turns': turns, 'headstart': head, 'joes': w['joes'].get(), 'cobra': w['cobra'].get()}
        env = {'OXCE_CAMPAIGNSIM': str(days), 'OXCE_BATTLESIM_TURNS': str(turns), 'OXCE_CAMPAIGNSIM_HEADSTART': str(head),
               'OXCE_BATTLESIM_JOES': s['joes'], 'OXCE_BATTLESIM_COBRA': s['cobra']}
        env.update(self.style.env()); s['plays_like_john'] = bool(self.style.env())
        self.launch('campaign', [(s, env)] * n)

    def tl_colour(self, l):
        return ('red' if 'STALL' in l or 'CRASH' in l or 'STUCK' in l or 'HANG' in l else 'green' if 'BATTLE WIN' in l
                else 'amber' if 'BATTLE LOSS' in l else 'gold' if 'MISSION appears' in l or 'COBRA SITE' in l or 'BROADCAST' in l or 'CARTEL FLIGHT' in l
                else 'blue' if 'RESEARCHED' in l else 'grey' if 'RESEARCH starts' in l or 'SENT' in l else '')

    # ----------------------------------------------------------------------------------------------------- BATTLES
    def tab_battles(self):
        p = self.page('  Battles  ')
        w = self.battles = {}
        w['go'], w['stop'], w['status'] = self.controls(p, 'battles', self.start_battles)
        o = ttk.Frame(p); o.pack(fill='x', pady=(0, 8))
        w['first'], w['count'], w['turns'] = tk.IntVar(value=0), tk.IntVar(value=99), tk.IntVar(value=30)
        w['joes'], w['cobra'] = tk.StringVar(value='normal'), tk.StringVar(value='normal')
        for lab, var, lo, hi in (('First mission #', w['first'], 0, 300), ('How many', w['count'], 1, 999), ('Turn limit', w['turns'], 5, 99)):
            ttk.Label(o, text=lab).pack(side='left'); ttk.Spinbox(o, from_=lo, to=hi, width=5, textvariable=var).pack(side='left', padx=(4, 14))
        for lab, var in (('Joes play', w['joes']), ('Cobra plays', w['cobra'])):
            ttk.Label(o, text=lab).pack(side='left')
            ttk.Combobox(o, values=STYLES, textvariable=var, width=10, state='readonly').pack(side='left', padx=(4, 12))
        w['g'] = self.gauge_row(p, (('mission', 'MISSION', GOLD), ('turn', 'TURN', INK), ('side', 'MOVING', INK),
                                    ('joes', 'JOES STANDING', GREEN), ('cobra', 'COBRA STANDING', RED), ('civilians', 'CIVILIANS', INK)))
        body = ttk.Frame(p); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)
        ef = ttk.Frame(body, style='Panel.TFrame', padding=8); ef.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        ttk.Label(ef, text='WHAT HAPPENED (this battle)', style='Dim.TLabel').pack(anchor='w')
        w['text'] = self.textbox(ef); w['text'].pack(fill='both', expand=True)
        pf = ttk.Frame(body, style='Panel.TFrame', padding=8); pf.grid(row=0, column=1, sticky='nsew')
        ttk.Label(pf, text='LATEST PICTURE', style='Dim.TLabel').pack(anchor='w')
        w['piclabel'] = tk.Label(pf, bg=PANEL, fg=GREY, text='(none yet)', width=50, height=14); w['piclabel'].pack(fill='both', expand=True)
        w['picname'] = ttk.Label(pf, text='', style='Dim.TLabel'); w['picname'].pack(anchor='w')

    def start_battles(self):
        w = self.battles
        try: first, count, turns = int(w['first'].get()), int(w['count'].get()), int(w['turns'].get())
        except (tk.TclError, ValueError): messagebox.showerror('Joe Lab', 'Numbers only, please.'); return
        plan = []
        for m in range(first, first + count):
            s = {'mission': m, 'turns': turns, 'joes': w['joes'].get(), 'cobra': w['cobra'].get()}
            plan.append((s, {'OXCE_BATTLESIM': str(m), 'OXCE_BATTLESIM_TURNS': str(turns), 'OXCE_BATTLESIM_JOES': s['joes'],
                             'OXCE_BATTLESIM_COBRA': s['cobra']}))
        self.launch('battles', plan)

    # ---------------------------------------------------------------------------------------------------- STRATEGY
    def tab_strategy(self):
        p = self.page('  Strategy  ')
        w = self.strategy = {}
        w['go'], w['stop'], w['status'] = self.controls(p, 'strategy', self.start_strategy)
        o = ttk.Frame(p); o.pack(fill='x', pady=(0, 8))
        w['days'], w['runs'] = tk.IntVar(value=365), tk.IntVar(value=9)
        ttk.Label(o, text='Days a run').pack(side='left'); ttk.Spinbox(o, from_=30, to=2000, width=6, textvariable=w['days']).pack(side='left', padx=(4, 14))
        ttk.Label(o, text='Runs').pack(side='left'); ttk.Spinbox(o, from_=1, to=999, width=5, textvariable=w['runs']).pack(side='left', padx=(4, 14))
        ttk.Label(o, text='Each run takes the next of: player absent / typical / aggressive  x  Cobra head start 0 / 6 / 12 months',
                  foreground=GREY).pack(side='left')
        ttk.Label(p, text='The world map alone, no battles shown: the style\'s odds decide them. What Cobra builds, when, and how the\n'
                          'money, the leads and the story beats land. A year takes about a minute.', foreground=GREY,
                  justify='left').pack(anchor='w', pady=(0, 8))
        f = ttk.Frame(p, style='Panel.TFrame', padding=8); f.pack(fill='both', expand=True)
        ttk.Label(f, text='LATEST REPORT', style='Dim.TLabel').pack(anchor='w')
        w['text'] = self.textbox(f, 20); w['text'].pack(fill='both', expand=True)

    def start_strategy(self):
        w = self.strategy
        try: days, n = int(w['days'].get()), int(w['runs'].get())
        except (tk.TclError, ValueError): messagebox.showerror('Joe Lab', 'Numbers only, please.'); return
        combos = [(s, h) for s in ('absent', 'typical', 'aggressive') for h in (0, 6, 12)]
        plan = []
        for i in range(n):
            s, h = combos[i % len(combos)]
            plan.append(({'days': days, 'style': s, 'headstart': h},
                         {'OXCE_FASTFORWARD': str(days), 'OXCE_FF_STYLE': s, 'OXCE_FF_HEADSTART': str(h)}))
        self.launch('strategy', plan)

    # -------------------------------------------------------------------------------------------------- CHARACTERS
    def tab_characters(self):
        p = self.page('  Characters  ')
        w = self.chars = {'proc': None}
        bar = ttk.Frame(p); bar.pack(fill='x', pady=(0, 8))
        w['go'] = ttk.Button(bar, text='▶  Start the render machine', style='Go.TButton', command=self.start_machine); w['go'].pack(side='right')
        w['stop'] = ttk.Button(bar, text='■  Stop it', style='Stop.TButton', state='disabled', command=self.stop_machine); w['stop'].pack(side='right', padx=6)
        ttk.Button(bar, text='Open the full render app (Edit Look)', command=self.open_render_app).pack(side='right', padx=6)
        ttk.Button(bar, text='Finished sheets', command=lambda: open_path(os.path.join(HERE, 'Reference', 'sheets'))).pack(side='right', padx=6)
        w['status'] = ttk.Label(bar, text='', foreground=GREY); w['status'].pack(side='left')
        ttk.Label(p, text='The render machine turns a .blend into a game sheet on this PC: drop models in Reference\\cartel (armed) or\n'
                          'Reference\\civ (unarmed). Edit Look (skins, colours, gear, face from a photo) is in the full render app.',
                  foreground=GREY, justify='left').pack(anchor='w', pady=(0, 8))
        body = ttk.Frame(p); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=1); body.rowconfigure(0, weight=1)
        a = ttk.Frame(body, style='Panel.TFrame', padding=8); a.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        ttk.Label(a, text='MACHINE STATUS', style='Dim.TLabel').pack(anchor='w')
        w['st'] = self.textbox(a, 18); w['st'].pack(fill='both', expand=True)
        b = ttk.Frame(body, style='Panel.TFrame', padding=8); b.grid(row=0, column=1, sticky='nsew')
        ttk.Label(b, text='RENDER LOG (latest)', style='Dim.TLabel').pack(anchor='w')
        w['log'] = self.textbox(b, 18); w['log'].pack(fill='both', expand=True)

    def start_machine(self):
        script = os.path.join(KIT, 'render_cartel.py')
        if not os.path.exists(script):
            messagebox.showerror('Joe Lab', 'render_kit\\render_cartel.py is not here: the render machine is not installed.'); return
        flags = 0x08000000 if WIN else 0
        w = self.chars
        w['proc'] = subprocess.Popen([PY, script, '--watch'], cwd=KIT, creationflags=flags,
                                     stdout=open(os.path.join(WORK if os.path.isdir(WORK) else HERE, 'machine_console.txt'), 'a'),
                                     stderr=subprocess.STDOUT)
        w['go'].configure(state='disabled'); w['stop'].configure(state='normal'); w['status'].configure(text='The machine is running.')

    def stop_machine(self):
        w = self.chars
        if w['proc'] and w['proc'].poll() is None:
            if WIN: subprocess.run(['taskkill', '/T', '/F', '/PID', str(w['proc'].pid)], creationflags=0x08000000, capture_output=True)
            else: w['proc'].kill()
        w['go'].configure(state='normal'); w['stop'].configure(state='disabled'); w['status'].configure(text='Stopped.')

    def open_render_app(self):
        bat = os.path.join(KIT, 'RENDER_APP.bat')
        if os.path.exists(bat): open_path(bat)
        else: messagebox.showerror('Joe Lab', 'render_kit\\RENDER_APP.bat is not here.')

    def tick_characters(self):
        w = self.chars
        for box, path, n in ((w['st'], os.path.join(WORK, 'MACHINE_STATUS.txt'), 60), (w['log'], os.path.join(WORK, 'render_log.txt'), 40)):
            txt = '\n'.join(read(path, '(nothing yet)').splitlines()[-n:])
            if txt != getattr(box, 'last', None):
                box.last = txt; box.delete('1.0', 'end')
                for l in txt.splitlines():
                    box.insert('end', l + '\n', 'red' if 'FAIL' in l else 'green' if ' OK' in l or 'done' in l else '')
                box.see('end')
        if w['proc'] and w['proc'].poll() is not None:
            w['proc'] = None; w['go'].configure(state='normal'); w['stop'].configure(state='disabled'); w['status'].configure(text='The machine stopped.')

    # -------------------------------------------------------------------------------------------------------- RUNS
    def all_runs(self):
        out = []
        for d in sorted(glob.glob(os.path.join(RUNS, '*')), reverse=True):
            try: meta = json.load(open(os.path.join(d, 'run.json')))
            except (OSError, ValueError): continue
            meta['dir'] = d
            out.append(meta)
        return out

    def tab_runs(self):
        p = self.page('  Runs  ')
        w = self.runs = {}
        bar = ttk.Frame(p); bar.pack(fill='x', pady=(0, 8))
        ttk.Label(bar, text='Every run is kept, with its pictures, timeline, events and log. Double-click to open its folder.',
                  foreground=GREY).pack(side='left')
        ttk.Button(bar, text='Refresh', command=self.load_runs).pack(side='right')
        ttk.Button(bar, text='Write a note about this run', command=self.note_for_run).pack(side='right', padx=6)
        body = ttk.Frame(p); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)
        t = ttk.Treeview(body, columns=('k', 'w', 's', 'r'), show='headings')
        for c, wd, h in (('k', 80, 'Kind'), ('w', 140, 'When'), ('s', 260, 'Settings'), ('r', 380, 'Result')):
            t.heading(c, text=h); t.column(c, width=wd, anchor='w')
        for k, col in (('win', GREEN), ('loss', AMBER), ('bad', RED), ('stopped', GREY)): t.tag_configure(k, foreground=col)
        t.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        t.bind('<<TreeviewSelect>>', self.show_run); t.bind('<Double-1>', lambda e: open_path(self.sel_run() or ''))
        w['tree'], w['dirs'] = t, {}
        f = ttk.Frame(body, style='Panel.TFrame', padding=8); f.grid(row=0, column=1, sticky='nsew')
        w['text'] = self.textbox(f, 20); w['text'].pack(fill='both', expand=True)
        self.load_runs()

    def load_runs(self):
        w = self.runs; t = w['tree']
        t.delete(*t.get_children()); w['dirs'].clear()
        for m in self.all_runs():
            s = ', '.join(f'{k} {v}' for k, v in (m.get('settings') or {}).items())
            res = m.get('result', '(running or stopped early)') + (f'  ({m["errors"]} log errors)' if m.get('errors') else '')
            iid = t.insert('', 'end', values=(m.get('kind', '?'), m.get('started', '').replace('T', ' '), s, res),
                           tags=(kind_of(m.get('result', '')),))
            w['dirs'][iid] = m['dir']

    def sel_run(self):
        sel = self.runs['tree'].selection()
        return self.runs['dirs'].get(sel[0]) if sel else None

    def show_run(self, _e=None):
        d = self.sel_run(); box = self.runs['text']; box.delete('1.0', 'end')
        if not d: return
        for f in ('checks.txt', 'result.txt', 'timeline.txt', 'battles.txt', 'events.txt', 'report.txt'):
            txt = read(os.path.join(d, f))
            if txt:
                box.insert('end', f'--- {f} ---\n', 'gold')
                for l in txt.splitlines()[:400]: box.insert('end', l + '\n', self.tl_colour(l))
        pics = glob.glob(os.path.join(d, '*.png'))
        box.insert('end', f'\n{len(pics)} pictures in the folder (double-click the run to open it)\n', 'grey')

    # ----------------------------------------------------------------------------------------------------- BALANCE
    def tab_balance(self):
        p = self.page('  Balance  ')
        bar = ttk.Frame(p); bar.pack(fill='x', pady=(0, 8))
        ttk.Label(bar, text='Numbers across every run kept in lab\\runs. Battles fought inside campaigns count too.', foreground=GREY).pack(side='left')
        ttk.Button(bar, text='Work it out', command=self.compute_balance).pack(side='right')
        ttk.Button(bar, text='Save as a text file', command=self.save_balance).pack(side='right', padx=6)
        self.balance = self.textbox(p, 30); self.balance.pack(fill='both', expand=True)

    def battle_lines(self):
        """every battle result: a battles run's result, and each line of a campaign's battles.txt"""
        lines = []
        for m in self.all_runs():
            if m.get('kind') == 'battles' and m.get('result'): lines.append(m['result'])
            if m.get('kind') in ('campaign', 'checks'): lines += [l for l in read(os.path.join(m['dir'], 'battles.txt')).splitlines() if l.strip()]
        return lines

    def compute_balance(self):
        b = self.balance; b.delete('1.0', 'end')
        per = {}
        for l in self.battle_lines():
            parts = l.split()
            if len(parts) < 2 or parts[0] not in ('WIN', 'LOSS'): continue
            m = parts[1]
            turns = int(re.search(r' turns (\d+)', l).group(1)) if re.search(r' turns (\d+)', l) else None
            lost = sum(int(x) for x in re.findall(r'STR_XCOM_OPERATIVES_(?:KILLED|MISSING_IN_ACTION) (\d+)', l))
            kills = sum(int(x) for x in re.findall(r'STR_ALIENS_KILLED (\d+)', l))
            r = per.setdefault(m, {'n': 0, 'win': 0, 'turns': [], 'lost': [], 'kills': []})
            r['n'] += 1; r['win'] += parts[0] == 'WIN'
            if turns is not None: r['turns'].append(turns)
            r['lost'].append(lost); r['kills'].append(kills)
        b.insert('end', 'BATTLES, by mission\n', 'gold')
        b.insert('end', f'{"mission":44} {"played":>6} {"won":>6} {"turns":>7} {"Joes lost":>10} {"Cobra down":>11}\n', 'grey')
        for m, r in sorted(per.items(), key=lambda kv: kv[1]['win'] / kv[1]['n']):
            wr = 100 * r['win'] // r['n']
            col = 'red' if wr < 50 else 'amber' if wr < 80 else 'green'
            med = lambda xs: f'{statistics.median(xs):.0f}' if xs else '-'
            b.insert('end', f'{m.replace("STR_", "")[:44]:44} {r["n"]:>6} {str(wr) + "%":>6} {med(r["turns"]):>7} {med(r["lost"]):>10} {med(r["kills"]):>11}\n', col)
        if not per: b.insert('end', '(no battles yet)\n', 'grey')
        # campaigns
        camps = [m for m in self.all_runs() if m.get('kind') in ('campaign', 'checks')]
        b.insert('end', f'\nCAMPAIGNS ({len(camps)})\n', 'gold')
        first = {}
        for m in camps:
            tl = read(os.path.join(m['dir'], 'timeline.txt')).splitlines()
            stalls = [l for l in tl if 'STALL' in l]
            b.insert('end', f'{m.get("started", "")}  {m.get("result", "(unfinished)")}  - {len(stalls)} stall(s)\n', 'red' if stalls else '')
            for l in stalls: b.insert('end', '    ' + l + '\n', 'red')
            seen = set()
            for l in tl:
                mm = re.match(r'day (\d+) .*?(RESEARCHED|MISSION appears:|COBRA SITE found:) (.+)$', l)
                if mm:
                    key = mm.group(2).split(':')[0] + ' ' + mm.group(3).strip()
                    if key not in seen:
                        seen.add(key); first.setdefault(key, []).append(int(mm.group(1)))
        if first:
            b.insert('end', '\nWHEN THINGS FIRST HAPPEN (day, median over the campaigns; how many campaigns saw it)\n', 'gold')
            for k, days in sorted(first.items(), key=lambda kv: statistics.median(kv[1])):
                b.insert('end', f'  day {statistics.median(days):>5.0f}   {k[:90]}   ({len(days)}/{len(camps)})\n',
                         'blue' if k.startswith('RESEARCHED') else 'gold' if k.startswith('MISSION') else 'red')
        # strategy runs
        strat = [m for m in self.all_runs() if m.get('kind') == 'strategy']
        b.insert('end', f'\nSTRATEGY RUNS ({len(strat)})\n', 'gold')
        for m in strat[:30]:
            rep = read(os.path.join(m['dir'], 'report.txt'))
            drome = re.search(r'\n(\S+ \(m\d+\))\s+SITE\s+STR_COBRA_TERROR_DROME', rep)
            close = re.search(r'\n(\S+ \(m\d+\)).*(ACT1_CLOSE|Act 1 close)', rep)
            s = m.get('settings') or {}
            b.insert('end', f'  {s.get("style", "?"):10} head start {s.get("headstart", "?"):>2}:  Drome '
                            f'{drome.group(1) if drome else "never"}   Act 1 close {close.group(1) if close else "-"}\n')

    def save_balance(self):
        os.makedirs(LAB, exist_ok=True)
        p = os.path.join(LAB, f'BALANCE_{now_tag()}.txt')
        open(p, 'w', encoding='utf-8').write(self.balance.get('1.0', 'end'))
        open_path(p)

    # ------------------------------------------------------------------------------------------------------- NOTES
    def tab_notes(self):
        p = self.page('  Notes  ')
        w = self.notes = {'page': p}
        body = ttk.Frame(p); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=1); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)
        left = ttk.Frame(body); left.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        t = ttk.Treeview(left, columns=('d', 't', 'g'), show='headings')
        for c, wd, h in (('d', 120, 'When'), ('t', 220, 'Title'), ('g', 70, 'Tag')):
            t.heading(c, text=h); t.column(c, width=wd, anchor='w')
        t.pack(fill='both', expand=True); t.bind('<<TreeviewSelect>>', self.open_note)
        lb = ttk.Frame(left); lb.pack(fill='x', pady=(6, 0))
        ttk.Button(lb, text='New note', command=self.new_note).pack(side='left')
        ttk.Button(lb, text='Export all for the desks', command=self.export_notes).pack(side='right')
        w['tree'], w['files'] = t, {}
        right = ttk.Frame(body, style='Panel.TFrame', padding=8); right.grid(row=0, column=1, sticky='nsew')
        top = ttk.Frame(right, style='Panel.TFrame'); top.pack(fill='x')
        ttk.Label(top, text='Title', style='Panel.TLabel').pack(side='left')
        w['title'] = tk.StringVar(); ttk.Entry(top, textvariable=w['title'], width=40).pack(side='left', padx=(4, 12))
        ttk.Label(top, text='Tag', style='Panel.TLabel').pack(side='left')
        w['tag'] = tk.StringVar(value='balance')
        ttk.Combobox(top, values=NOTE_TAGS, textvariable=w['tag'], width=10, state='readonly').pack(side='left', padx=4)
        w['run'] = tk.StringVar(value='')
        ttk.Label(right, textvariable=w['run'], style='Dim.TLabel').pack(anchor='w', pady=(4, 0))
        w['text'] = self.textbox(right, 22); w['text'].configure(wrap='word'); w['text'].pack(fill='both', expand=True, pady=(6, 6))
        ttk.Button(right, text='Save note', style='Go.TButton', command=self.save_note).pack(anchor='e')
        w['current'] = None
        self.load_notes()

    def load_notes(self):
        w = self.notes; t = w['tree']; t.delete(*t.get_children()); w['files'].clear()
        for f in sorted(glob.glob(os.path.join(NOTES, '*.txt')), reverse=True):
            head = read(f).splitlines()
            meta = dict(l.split(': ', 1) for l in head[:4] if ': ' in l)
            iid = t.insert('', 'end', values=(meta.get('When', ''), meta.get('Title', os.path.basename(f)), meta.get('Tag', '')))
            w['files'][iid] = f

    def new_note(self, run=''):
        w = self.notes
        w['current'] = None; w['title'].set(''); w['tag'].set('balance'); w['text'].delete('1.0', 'end')
        w['run'].set(f'About run: {run}' if run else '')
        self.nb.select(self.notes['page'])

    def note_for_run(self):
        d = self.sel_run()
        if not d: messagebox.showinfo('Joe Lab', 'Pick a run first.'); return
        self.new_note(os.path.basename(d))

    def open_note(self, _e=None):
        w = self.notes; sel = w['tree'].selection()
        if not sel: return
        f = w['files'][sel[0]]; lines = read(f).splitlines()
        meta = dict(l.split(': ', 1) for l in lines[:4] if ': ' in l)
        w['current'] = f; w['title'].set(meta.get('Title', '')); w['tag'].set(meta.get('Tag', 'other'))
        w['run'].set(f'About run: {meta["Run"]}' if meta.get('Run') else '')
        body = lines[5:] if len(lines) > 4 else lines
        w['text'].delete('1.0', 'end'); w['text'].insert('1.0', '\n'.join(body))

    def save_note(self):
        w = self.notes
        title = w['title'].get().strip() or 'Untitled'
        os.makedirs(NOTES, exist_ok=True)
        f = w['current'] or os.path.join(NOTES, f'{now_tag()}_{re.sub(r"[^A-Za-z0-9]+", "_", title)[:40]}.txt')
        run = w['run'].get().replace('About run: ', '')
        when = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        open(f, 'w', encoding='utf-8').write(f'Title: {title}\nTag: {w["tag"].get()}\nWhen: {when}\nRun: {run}\n\n'
                                             + w['text'].get('1.0', 'end').rstrip() + '\n')
        w['current'] = f; self.load_notes()

    def export_notes(self):
        os.makedirs(LAB, exist_ok=True)
        out = os.path.join(LAB, f'DESIGN_NOTES_{now_tag()}.txt')
        parts = ['DESIGN NOTES FROM JOE LAB (John\'s own notes from testing), exported ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), '']
        for f in sorted(glob.glob(os.path.join(NOTES, '*.txt'))):
            parts += ['=' * 100, read(f).rstrip(), '']
        open(out, 'w', encoding='utf-8').write('\n'.join(parts) + '\n')
        open_path(out)

    # ------------------------------------------------------------------------------------------------- the clock
    def tick(self):
        try:
            while True:
                msg = self.q.get_nowait()
                kind, what = msg[0], msg[1]
                w = getattr(self, kind)
                if what == 'status': w['status'].configure(text=msg[2])
                elif what == 'error': messagebox.showerror('Joe Lab', msg[2])
                elif what == 'started':
                    w['dir'], w['seen'], w['pic'] = msg[2], 0, None
                    w['text'].delete('1.0', 'end')
                    w['status'].configure(text=f'Running: {", ".join(f"{k} {v}" for k, v in msg[3].items())}')
                    if 'piclabel' in w: w['piclabel'].configure(image='', text='(none yet)'); w['piclabel'].image = None
                elif what == 'result':
                    w['text'].insert('end', f'RESULT: {msg[3]}' + (f'   ({msg[4]} errors in the log)' if msg[4] else '') + '\n',
                                     'green' if kind_of(msg[3]) != 'bad' else 'red'); w['text'].see('end')
                    self.load_runs()
                    if kind == 'checks': self.grade_into(msg[2])
                elif what == 'nomore': w['status'].configure(text='Every mission played.')
                elif what == 'finished':
                    w['go'].configure(state='normal'); w['stop'].configure(state='disabled')
                    w['status'].configure(text='Stopped. Every run is kept in the Runs tab.')
        except queue.Empty:
            pass
        # live readouts
        c = self.campaign
        if c.get('dir') and self.jobs.get('campaign') and self.jobs['campaign'].is_alive():
            s = self.status_file(c['dir'])
            for k, lab in c['g'].items():
                v = s.get(k, '-')
                lab.configure(text=v if k != 'quiet_days' else v, foreground=RED if k == 'quiet_days' and v.isdigit() and int(v) >= 20 else lab.cget('foreground'))
            self.feed(c, c['dir'], 'timeline.txt', self.tl_colour); self.latest_pic(c, c['dir'])
        ck = self.checks
        if ck.get('dir') and self.jobs.get('checks') and self.jobs['checks'].is_alive():
            s = self.status_file(ck['dir'])
            ck['day'].configure(text=f'THIS RUN   day {s.get("day", "-")}   battles {s.get("battles", "-")}   run {len(ck["graded"]) + 1}')
            self.feed(ck, ck['dir'], 'timeline.txt', self.tl_colour)
        bt = self.battles
        if bt.get('dir') and self.jobs.get('battles') and self.jobs['battles'].is_alive():
            s = self.status_file(bt['dir'])
            bt['g']['mission'].configure(text=s.get('mission', '-').replace('STR_', '').replace('_', ' ').title()[:24])
            for k in ('turn', 'side'): bt['g'][k].configure(text=s.get(k, '-'))
            for k in ('joes', 'cobra', 'civilians'):
                a = s.get(k, '').split(); bt['g'][k].configure(text=f'{a[0]} / {a[1]}' if len(a) == 2 else '-')
            self.feed(bt, bt['dir'], 'events.txt', lambda l: 'gold' if ' turn ' in l else 'red' if ' down: ' in l else 'grey' if 'OK on' in l else '')
            self.latest_pic(bt, bt['dir'])
        sg = self.strategy
        if sg.get('dir'):
            rep = read(os.path.join(sg['dir'], 'report.txt'))
            if rep and rep != sg.get('last'):
                sg['last'] = rep; sg['text'].delete('1.0', 'end'); sg['text'].insert('end', rep)
        self.tick_characters()
        self.root.after(1000, self.tick)

    def close(self):
        if any(j.is_alive() for j in self.jobs.values()):
            if not messagebox.askyesno('Joe Lab', 'A run is going. Stop it and close?'): return
            for j in self.jobs.values(): j.halt()
        if self.chars.get('proc') and self.chars['proc'].poll() is None:
            if messagebox.askyesno('Joe Lab', 'The render machine is running. Stop it too?'): self.stop_machine()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    Lab(root)
    root.mainloop()
