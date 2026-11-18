"""G.I. JOE 4x - THE BATTLE SIMULATOR APP (BUILD-1, 17 Nov 2026; John 20:06 "a better user friendly ui and maybe some readouts
of whats happening").

A window over the battle simulator. It does what Sim_Battles_4x.bat does - the game plays New Battle missions by itself,
Joes and Cobra both, one game per battle - and shows what is going on while it does:
  - NOW PLAYING: the mission, the battle number, the turn, whose turn it is, Joes / Cobra / civilians still standing,
    how long the battle has run, and the latest picture the game took;
  - WHAT HAPPENED: that battle's events as they come (turns, men going down, popups answered, the end);
  - RESULTS: every battle so far, coloured (WIN green, LOSS amber, CRASH / HANG / STUCK red), with the totals.
Double-click a result to open that battle's folder (pictures, events, log).
Runs on this PC with no internet and no AI. Started by SIM_APP.bat (py -3.13 sim_app.py). Never touches your saves:
it plays in user_sim\\ and writes to sim_battles\\.
"""
import os, sys, time, shutil, subprocess, threading, queue, glob
import tkinter as tk
from tkinter import ttk, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
WIN = sys.platform.startswith('win')
GAME = os.environ.get('SIM_GAME', os.path.join(HERE, 'OpenXcom.exe' if WIN else 'openxcom'))
USER = os.path.join(HERE, 'user')
USER_SIM = os.environ.get('SIM_USER', os.path.join(HERE, 'user_sim'))
OUT = os.path.join(HERE, 'sim_battles')
EXTRA = os.environ.get('SIM_ARGS', '').split()          # the test rig adds its own (-data ...)

INK, PAPER, PANEL, GOLD, RED, GREEN, AMBER, GREY = '#e8e4d8', '#14181c', '#1f262c', '#d8b45a', '#ff5a4a', '#5ec46a', '#e0a030', '#8a9198'
FONT = ('Segoe UI', 10) if WIN else ('DejaVu Sans', 10)
BIG = (FONT[0], 15, 'bold')
MONO = ('Consolas', 9) if WIN else ('DejaVu Sans Mono', 9)


def kind(result):
    r = result.split()[0] if result else ''
    return {'WIN': 'win', 'LOSS': 'loss', 'STOPPED': 'stopped'}.get(r, 'bad')


class Runner(threading.Thread):
    """Plays the missions one game at a time. Talks to the window only through the queue."""

    def __init__(self, q, first, only, turns, joes='normal', cobra='normal'):
        super().__init__(daemon=True)
        self.q, self.first, self.only, self.turns, self.joes, self.cobra = q, first, only, turns, joes, cobra
        self.stop = False
        self.proc = None
        self.dir = None

    def post(self, *msg):
        self.q.put(msg)

    def prepare(self):
        if not os.path.isdir(os.path.join(USER, 'mods', 'GIJoe4x')) and not os.environ.get('SIM_USER'):
            self.post('error', 'Start the game once with Play_4x.bat first, so the mod is unpacked.')
            return False
        if not os.environ.get('SIM_USER'):
            self.post('status', 'Copying the mod into the simulator\'s own folder ...')
            os.makedirs(USER_SIM, exist_ok=True)
            if WIN:
                subprocess.run(['robocopy', os.path.join(USER, 'mods'), os.path.join(USER_SIM, 'mods'), '/MIR', '/NFL', '/NDL',
                                '/NJH', '/NJS', '/NP'], creationflags=0x08000000)
            else:
                shutil.copytree(os.path.join(USER, 'mods'), os.path.join(USER_SIM, 'mods'), dirs_exist_ok=True)
            if os.path.exists(os.path.join(USER, 'options.cfg')):
                shutil.copyfile(os.path.join(USER, 'options.cfg'), os.path.join(USER_SIM, 'options.cfg'))
        os.makedirs(OUT, exist_ok=True)
        return True

    def run(self):
        if not self.prepare():
            self.post('finished'); return
        runs = sorted(glob.glob(os.path.join(OUT, 'r*_m*')))
        run = 1 + max([int(os.path.basename(r)[1:].split('_')[0]) for r in runs if os.path.basename(r)[1:].split('_')[0].isdigit()] or [0])
        m = self.first
        while not self.stop:
            d = os.path.join(OUT, f'r{run}_m{m}')
            shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
            self.dir = d
            self.post('battle', run, m, d)
            env = dict(os.environ, OXCE_BATTLESIM=str(m), OXCE_BATTLESIM_OUT=d, OXCE_BATTLESIM_TURNS=str(self.turns),
                       OXCE_BATTLESIM_JOES=self.joes, OXCE_BATTLESIM_COBRA=self.cobra,
                       OXCE_BATTLE_SCALE='4', OXCE_MAP_HIRES='4')
            log = os.path.join(USER_SIM, 'openxcom.log')
            if os.path.exists(log):
                try: os.remove(log)
                except OSError: pass
            cmd = [GAME, '-user', USER_SIM, '-cfg', USER_SIM, '-displayWidth', '1280', '-displayHeight', '800',
                   '-fullscreen', 'false', '-debug', 'false'] + EXTRA
            t0 = time.time()
            try:
                self.proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(GAME))
                code = self.proc.wait()
            except OSError as e:
                self.post('error', f'Could not start the game: {e}'); break
            if os.path.exists(log): shutil.copyfile(log, os.path.join(d, 'log.txt'))
            res = ''
            if os.path.exists(os.path.join(d, 'result.txt')):
                res = open(os.path.join(d, 'result.txt'), encoding='utf-8', errors='replace').read().strip()
            if self.stop and not res:
                res = 'STOPPED by you'
            if not res:
                res = f'CRASH mission {m}: the game shut down (exit code {code})'
            if res.startswith('NO MISSION'):
                shutil.rmtree(d, ignore_errors=True)
                if m == 0 or self.only:
                    self.post('error', 'New Battle has no mission with that number.'); break
                self.post('status', 'Every mission played. Starting again from the first.')
                m = 0; continue
            errs = 0
            if os.path.exists(os.path.join(d, 'log.txt')):
                errs = sum(1 for l in open(os.path.join(d, 'log.txt'), encoding='utf-8', errors='replace') if '[ERROR]' in l or '[FATAL]' in l)
            line = f'r{run} m{m}: {res}  [Joes {self.joes}, Cobra {self.cobra}]' + (f'  ({errs} errors in the log)' if errs else '')
            with open(os.path.join(OUT, 'results.txt'), 'a', encoding='utf-8') as f: f.write(line + '\n')
            if (kind(res) == 'bad' or errs) and kind(res) != 'stopped':
                with open(os.path.join(OUT, 'problems.txt'), 'a', encoding='utf-8') as f: f.write(line + '\n')
            self.post('result', run, m, res + f'  [Joes {self.joes}, Cobra {self.cobra}]', errs, int(time.time() - t0), d)
            run += 1
            if self.only: break
            m += 1
        self.post('finished')

    def halt(self):
        self.stop = True
        if self.proc and self.proc.poll() is None:
            if WIN: subprocess.run(['taskkill', '/T', '/F', '/PID', str(self.proc.pid)], creationflags=0x08000000, capture_output=True)
            else: self.proc.kill()


class App:
    def __init__(self, root):
        self.root, self.q, self.runner, self.dir = root, queue.Queue(), None, None
        self.events_seen, self.pic_path, self.pic_mtime, self.photo = 0, None, 0, None
        self.counts = {'win': 0, 'loss': 0, 'bad': 0, 'stopped': 0}
        root.title('G.I. Joe 4x - Battle Simulator')
        root.configure(bg=PAPER); root.geometry('1180x780'); root.minsize(980, 640)
        st = ttk.Style(); st.theme_use('clam')
        st.configure('.', background=PAPER, foreground=INK, font=FONT, fieldbackground=PANEL)
        st.configure('TFrame', background=PAPER); st.configure('Panel.TFrame', background=PANEL)
        st.configure('TLabel', background=PAPER, foreground=INK)
        st.configure('Panel.TLabel', background=PANEL, foreground=INK)
        st.configure('Head.TLabel', background=PAPER, foreground=GOLD, font=(FONT[0], 11, 'bold'))
        st.configure('Big.TLabel', background=PANEL, foreground=GOLD, font=BIG)
        st.configure('Dim.TLabel', background=PANEL, foreground=GREY)
        st.configure('TButton', background='#2c353d', foreground=INK, padding=(14, 6), borderwidth=0)
        st.map('TButton', background=[('active', '#3a4651'), ('disabled', '#22282e')], foreground=[('disabled', '#5b6268')])
        st.configure('Go.TButton', background='#2e6b38'); st.map('Go.TButton', background=[('active', '#3a8546'), ('disabled', '#22282e')])
        st.configure('Stop.TButton', background='#8a2a22'); st.map('Stop.TButton', background=[('active', '#a8352b'), ('disabled', '#22282e')])
        st.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=INK, rowheight=22, borderwidth=0)
        st.configure('Treeview.Heading', background='#2c353d', foreground=GOLD, font=(FONT[0], 9, 'bold'))
        st.configure('Horizontal.TProgressbar', background=RED, troughcolor='#2c353d', borderwidth=0)

        # --- top bar: controls ---
        top = ttk.Frame(root, padding=(14, 12, 14, 6)); top.pack(fill='x')
        ttk.Label(top, text='BATTLE SIMULATOR', style='Head.TLabel', font=(FONT[0], 14, 'bold')).pack(side='left')
        self.btn_go = ttk.Button(top, text='▶  Start', style='Go.TButton', command=self.start); self.btn_go.pack(side='right')
        self.btn_stop = ttk.Button(top, text='■  Stop', style='Stop.TButton', command=self.stop, state='disabled')
        self.btn_stop.pack(side='right', padx=6)
        ttk.Button(top, text='Open results folder', command=lambda: self.open(OUT)).pack(side='right', padx=6)
        opts = ttk.Frame(root, padding=(14, 0, 14, 8)); opts.pack(fill='x')
        ttk.Label(opts, text='Start at mission #').pack(side='left')
        self.first = tk.IntVar(value=0)
        ttk.Spinbox(opts, from_=0, to=200, width=5, textvariable=self.first).pack(side='left', padx=(4, 16))
        self.only = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text='only that one', variable=self.only).pack(side='left', padx=(0, 16))
        ttk.Label(opts, text='Joes pull out after turn').pack(side='left')
        self.turns = tk.IntVar(value=30)
        ttk.Spinbox(opts, from_=5, to=99, width=5, textvariable=self.turns).pack(side='left', padx=(4, 16))
        styles = ('defensive', 'normal', 'aggressive')
        ttk.Label(opts, text='Joes play').pack(side='left')
        self.joes = tk.StringVar(value='normal')
        ttk.Combobox(opts, values=styles, textvariable=self.joes, width=10, state='readonly').pack(side='left', padx=(4, 12))
        ttk.Label(opts, text='Cobra plays').pack(side='left')
        self.cobra = tk.StringVar(value='normal')
        ttk.Combobox(opts, values=styles, textvariable=self.cobra, width=10, state='readonly').pack(side='left', padx=4)
        self.status = ttk.Label(opts, text='Ready. Press Start: the game window opens and plays by itself.', foreground=GREY)
        self.status.pack(side='right')

        body = ttk.Frame(root, padding=(14, 0, 14, 14)); body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(1, weight=1)

        # --- NOW PLAYING ---
        now = ttk.Frame(body, style='Panel.TFrame', padding=14); now.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=(0, 10))
        ttk.Label(now, text='NOW PLAYING', style='Dim.TLabel').grid(row=0, column=0, sticky='w')
        self.l_mission = ttk.Label(now, text='-', style='Big.TLabel'); self.l_mission.grid(row=1, column=0, columnspan=4, sticky='w')
        self.l_sub = ttk.Label(now, text='', style='Dim.TLabel'); self.l_sub.grid(row=2, column=0, columnspan=4, sticky='w', pady=(0, 10))
        self.gauges = {}
        for i, (key, label, col) in enumerate((('turn', 'TURN', GOLD), ('side', 'MOVING', INK), ('joes', 'JOES STANDING', GREEN),
                                                ('cobra', 'COBRA STANDING', RED), ('civilians', 'CIVILIANS', INK), ('time', 'BATTLE TIME', INK))):
            f = ttk.Frame(now, style='Panel.TFrame'); f.grid(row=3 + i // 3, column=i % 3, sticky='w', padx=(0, 26), pady=4)
            ttk.Label(f, text=label, style='Dim.TLabel', font=(FONT[0], 8)).pack(anchor='w')
            v = ttk.Label(f, text='-', style='Panel.TLabel', foreground=col, font=(FONT[0], 16, 'bold')); v.pack(anchor='w')
            self.gauges[key] = v
        self.bar = ttk.Progressbar(now, maximum=30, length=360); self.bar.grid(row=5, column=0, columnspan=3, sticky='w', pady=(10, 0))
        ttk.Label(now, text='turns used of the limit', style='Dim.TLabel', font=(FONT[0], 8)).grid(row=6, column=0, columnspan=3, sticky='w')

        # --- latest picture ---
        pic = ttk.Frame(body, style='Panel.TFrame', padding=10); pic.grid(row=0, column=1, sticky='nsew', pady=(0, 10))
        ttk.Label(pic, text='LATEST PICTURE', style='Dim.TLabel').pack(anchor='w')
        self.l_pic = tk.Label(pic, bg=PANEL, fg=GREY, text='(none yet)', width=52, height=14); self.l_pic.pack(fill='both', expand=True)
        self.l_picname = ttk.Label(pic, text='', style='Dim.TLabel'); self.l_picname.pack(anchor='w')

        # --- events + results ---
        ev = ttk.Frame(body, style='Panel.TFrame', padding=10); ev.grid(row=1, column=0, sticky='nsew', padx=(0, 10))
        ttk.Label(ev, text='WHAT HAPPENED (this battle)', style='Dim.TLabel').pack(anchor='w')
        self.t_ev = tk.Text(ev, bg=PANEL, fg=INK, font=MONO, relief='flat', wrap='word', height=12, insertbackground=INK)
        self.t_ev.pack(fill='both', expand=True)
        for tag, col in (('turn', GOLD), ('down', RED), ('ok', GREY), ('end', GREEN)): self.t_ev.tag_configure(tag, foreground=col)
        res = ttk.Frame(body, style='Panel.TFrame', padding=10); res.grid(row=1, column=1, sticky='nsew')
        self.l_tot = ttk.Label(res, text='RESULTS', style='Dim.TLabel'); self.l_tot.pack(anchor='w')
        self.tree = ttk.Treeview(res, columns=('m', 'r', 't', 's'), show='headings', height=12)
        for c, w, h in (('m', 170, 'Mission'), ('r', 70, 'Result'), ('t', 50, 'Turns'), ('s', 130, 'Joes / Cobra')):
            self.tree.heading(c, text=h); self.tree.column(c, width=w, anchor='w')
        self.tree.pack(fill='both', expand=True)
        for k, col in (('win', GREEN), ('loss', AMBER), ('bad', RED), ('stopped', GREY)): self.tree.tag_configure(k, foreground=col)
        self.tree.bind('<Double-1>', self.open_result)
        self.paths = {}
        self.load_old()
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.tick()

    # --- helpers ---
    def open(self, path):
        if not os.path.exists(path): return
        if WIN: os.startfile(path)
        else: subprocess.Popen(['xdg-open', path])

    def open_result(self, _e):
        sel = self.tree.selection()
        if sel and sel[0] in self.paths: self.open(self.paths[sel[0]])

    def add_result(self, run, m, res, d, turns=''):
        k = kind(res)
        word = res.split()[0] if res else '?'
        name = res.split()[1] if len(res.split()) > 1 else f'mission {m}'
        if word in ('CRASH', 'STOPPED', 'HANG', 'STUCK') and not name.startswith('STR_'): name = f'mission {m}'
        if not turns and ' turns ' in res:
            try: turns = res.split(' turns ')[1].split()[0]
            except IndexError: pass
        style = ''
        if '[Joes ' in res:
            try: j, c = res.split('[Joes ')[1].rstrip(']').split(', Cobra '); style = f'{j[:3]} / {c[:3]}'
            except ValueError: pass
        iid = self.tree.insert('', 0, values=(name.replace('STR_', '').replace('_', ' ').title(), word, turns, style), tags=(k,))
        self.paths[iid] = d
        self.counts[k] += 1
        self.l_tot.configure(text=f'RESULTS   {self.counts["win"]} won   {self.counts["loss"]} lost   '
                                  f'{self.counts["bad"]} went wrong   (double-click one to open it)')

    def load_old(self):
        p = os.path.join(OUT, 'results.txt')
        if not os.path.exists(p): return
        for line in open(p, encoding='utf-8', errors='replace'):
            if ': ' not in line: continue
            head, res = line.strip().split(': ', 1)
            try: run, m = head[1:].split(' m')
            except ValueError: continue
            self.add_result(run, m, res, os.path.join(OUT, f'r{run}_m{m}'))

    def start(self):
        try: first, turns = int(self.first.get()), int(self.turns.get())
        except (tk.TclError, ValueError): messagebox.showerror('Simulator', 'The mission number and turn limit must be numbers.'); return
        if not os.path.exists(GAME): messagebox.showerror('Simulator', 'Put this next to OpenXcom.exe.'); return
        self.bar.configure(maximum=turns)
        self.runner = Runner(self.q, first, self.only.get(), turns, self.joes.get(), self.cobra.get()); self.runner.start()
        self.btn_go.configure(state='disabled'); self.btn_stop.configure(state='normal')
        self.status.configure(text='Running. You can use the PC; leave the game window alone.')

    def stop(self):
        if self.runner:
            self.status.configure(text='Stopping ...'); self.runner.halt()

    def close(self):
        if self.runner and self.runner.is_alive():
            if not messagebox.askyesno('Simulator', 'A battle is running. Stop it and close?'): return
            self.runner.halt()
        self.root.destroy()

    # --- the live readout ---
    def read_status(self):
        p = os.path.join(self.dir, 'status.txt') if self.dir else None
        if not p or not os.path.exists(p): return
        try: lines = dict(l.split(' ', 1) for l in open(p, encoding='utf-8').read().split('\n') if ' ' in l)
        except OSError: return
        g = self.gauges
        g['turn'].configure(text=lines.get('turn', '-'))
        g['side'].configure(text=lines.get('side', '-'))
        for k in ('joes', 'cobra', 'civilians'):
            a = lines.get(k, '').split()
            g[k].configure(text=f'{a[0]} / {a[1]}' if len(a) == 2 else '-')
        try:
            s = int(lines.get('seconds', '0')); g['time'].configure(text=f'{s // 60}:{s % 60:02d}')
            self.bar['value'] = int(lines.get('turn', '0'))
        except ValueError: pass
        if lines.get('mission', '').startswith('STR_'):
            self.l_mission.configure(text=lines['mission'].replace('STR_', '').replace('_', ' ').title())

    def read_events(self):
        p = os.path.join(self.dir, 'events.txt') if self.dir else None
        if not p or not os.path.exists(p): return
        try: lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
        except OSError: return
        for l in lines[self.events_seen:]:
            body = l.split(' ', 1)[1] if ' ' in l else l
            tag = ('turn' if body.startswith('turn ') else 'down' if ' down: ' in body else
                   'end' if body.startswith(('area secure', 'done', 'mission ')) else 'ok' if body.startswith(('OK on', 'screenshot', 'equipment')) else '')
            if body.startswith('mission STR_'):
                self.l_mission.configure(text=body[8:].replace('STR_', '').replace('_', ' ').title())
            self.t_ev.insert('end', l + '\n', tag); self.t_ev.see('end')
        self.events_seen = len(lines)

    def read_picture(self):
        if not self.dir: return
        pics = sorted(glob.glob(os.path.join(self.dir, '*.png')), key=os.path.getmtime)
        if not pics: return
        p = pics[-1]; mt = os.path.getmtime(p)
        if p == self.pic_path and mt == self.pic_mtime: return
        try:
            try:
                from PIL import Image, ImageTk
                im = Image.open(p); im.thumbnail((440, 280)); self.photo = ImageTk.PhotoImage(im)
            except ImportError:
                ph = tk.PhotoImage(file=p); f = max(1, ph.width() // 440 + 1); self.photo = ph.subsample(f, f)
        except Exception:
            return   # still being written: next tick
        self.pic_path, self.pic_mtime = p, mt
        self.l_pic.configure(image=self.photo, text='', width=0, height=0)
        self.l_picname.configure(text=os.path.basename(p)[:-4].replace('_', ' '))

    def tick(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg[0] == 'status': self.status.configure(text=msg[1])
                elif msg[0] == 'error': messagebox.showerror('Simulator', msg[1])
                elif msg[0] == 'battle':
                    _, run, m, d = msg
                    self.dir, self.events_seen, self.pic_path = d, 0, None
                    self.t_ev.delete('1.0', 'end')
                    self.l_mission.configure(text=f'Mission {m}')
                    self.l_sub.configure(text=f'battle {run}  ·  New Battle mission #{m}  ·  {d}')
                    for g in self.gauges.values(): g.configure(text='-')
                    self.photo = None; self.l_pic.configure(image='', text='(none yet)'); self.l_picname.configure(text='')
                    self.bar['value'] = 0
                elif msg[0] == 'result':
                    _, run, m, res, errs, secs, d = msg
                    self.read_events()
                    self.add_result(run, m, res, d)
                    self.t_ev.insert('end', f'RESULT: {res}' + (f'   ({errs} errors in the log)' if errs else '') + '\n',
                                     'end' if kind(res) != 'bad' else 'down')
                    self.t_ev.see('end')
                elif msg[0] == 'finished':
                    self.btn_go.configure(state='normal'); self.btn_stop.configure(state='disabled')
                    self.status.configure(text='Stopped. Everything is in sim_battles\\.')
        except queue.Empty:
            pass
        self.read_status(); self.read_events(); self.read_picture()
        self.root.after(1000, self.tick)


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
