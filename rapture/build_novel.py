import base64, json, os, html

L = {}  # panel -> dict(caps=[], lines=[(who,txt)], wide=bool)
def P(k, caps=None, lines=None, wide=False):
    L[k] = dict(caps=caps or [], lines=lines or [], wide=wide)

# PART ONE
P('1.1', caps=["An ordinary Tuesday."], lines=[("KAYLA","Atlantic City tonight, my mother in the morning, and you're all chipping in on gas."),("TESS","We *said*.")], wide=True)
P('1.2'); P('1.3'); P('1.4', wide=True); P('1.5')
P('1.6', caps=["Billions, in the same second, everywhere on earth."], wide=True)
P('1.7', caps=["Every one of them left a body where they stood.","No wound. No cause. Nothing a doctor could find."], wide=True)
P('1.8', wide=True)
P('1.9', caps=["He had come that morning to ask what he'd done wrong."])
P('1.10', lines=[("PARISHIONER","He's not dead. Look at him. He's *not dead*.")])
P('1.11', lines=[("JOHN","If this is a judgment, and he's still standing here, then what does that —")])
P('1.12', caps=["It took him four hours and he didn't stop.","That was the first grave."], wide=True)
P('1.13', caps=["Forty-one units off Route 5. Three weeks from the walk-through."], wide=True)
P('1.14')
P('1.15', caps=["Nobody was going to foreclose on it. Nobody was going to sue him for it.","It hadn't been lost. It had stopped being counted."], wide=True)
P('1.16', caps=["Forty-one of them were still in the pews. Nobody else was coming."], wide=True)
P('1.17', lines=[("RAY","— stupidest animal ever born in Schenectady County."),("JOHN","You've said.")])
P('1.18', caps=["A man visibly doing something is the most magnetic object in a collapsed world."])
P('1.19', caps=["Her mother. Her father. Her brother, who was fifteen.","She was the only one in that house who ever went to church."], wide=True)
P('1.20')
P('1.21', lines=[("RUTHIE","Emma. Who *does* this?")], caps=["She knew exactly what she was looking at."])
P('1.22', wide=True); P('1.23', wide=True)

# PART TWO
P('2.1', caps=["Nobody decided anything. They simply failed to leave."], wide=True)
P('2.2', lines=[("DELIA","Eaten, that's a week. One week, for nineteen of us."),("DELIA","Planted, it's three acres. A year of food for forty.")])
P('2.3', caps=["There wasn't a Bible in that camp and there wouldn't be one for two more years."], lines=[("HAZEL","I'm doing it from memory. If I've got one wrong, somebody tell me.")], wide=True)
P('2.4', caps=["The last two were hers, and she said so. Then and every time after."])
P('2.5'); P('2.6'); P('2.7', wide=True)
P('2.8', lines=[("WARD","None of it's your fault. You know that?"),("WARD","There's nobody keeping score. There never was.")], wide=True)
P('2.9', lines=[("WARD","We're collecting seed. It gets catalogued, it gets planted, it feeds people. This winter.")])
P('2.10')
P('2.11', lines=[("RUTHIE","They stamped it. Look —")])
P('2.12', caps=["Eight days. She said good morning and got a nod.","They had a law that told them exactly what to do, and not one of them could do it."], wide=True)
P('2.13', lines=[("JOHN","She owes something she'll never be able to pay. I'm asking you to let it go anyway.")], caps=["That was not written anywhere on that board."], wide=True)
P('2.14', lines=[("EMMA","Nobody's putting you out."),("RUTHIE","You don't have to.")])
P('2.15', lines=[("WARD","Just walk us in. They'd never bar it to you. You told me that yourself.")])
P('2.16', caps=["East. Away from the ridge, away from the river, away from every part of it.","A day and a half."], wide=True)
P('2.17'); P('2.18', wide=True); P('2.19')
P('2.20', lines=[("(OFF)","What do you think you're doing?"),("EVIE","It's late in the year for it.")], wide=True)
P('2.21', caps=["The only time in her life anybody used her whole name."], wide=True)

# MONTAGE
P('M.1', caps=["He wasn't taken. Everyone around him simply went."])
P('M.2', caps=["He got the power back on. He got food moving.","They weren't fools for loving him. He was good at it."], wide=True)
P('M.3')
P('M.4', lines=[("THE PRESIDENT","If there had been a judgment — would I be standing here?")], wide=True)
P('M.5'); P('M.6')
P('M.7', caps=["For one hour and forty minutes the world was told the President was dead."], wide=True)
P('M.8', lines=[("THE PRESIDENT","I forgive him. I want everyone to hear me say his name, and then forgive him too.")], wide=True)
P('M.9', caps=["Six million acres. He crossed off a river every few months.","He was patient. He thought he had time."], wide=True)

# EDEN
P('3.1', wide=True)
P('3.2', caps=["Forty-one of them. Six children. Four years."], wide=True)
P('3.3')
P('3.4', lines=[("EVIE","You're going to lose the whole row doing that. Who told you to do that?")])
P('3.5')
P('3.6', lines=[("ADAM","I'm saying no. I can't tell you why. I'm saying it anyway."),("DELIA","He's a fair hand with a saw and we can feed one more.")], wide=True)
P('3.7', wide=True)
P('3.8', lines=[("DELIA","At two-thirds ration we're empty in March and not one of us is strong enough to plant in April."),("EVIE","We'll grow more.")], wide=True)
P('3.9', caps=["A family came in with a Bible in a bread bag. One of the ten was wrong.","Nobody changed it."], wide=True)
P('3.10', caps=["February should have read four thousand one hundred pounds.","It read five thousand nine hundred."], wide=True)
P('3.11'); P('3.12', wide=True); P('3.13')

# SIEGE
P('4.1', wide=True); P('4.2', wide=True)
P('4.3', lines=[("WARD","There was no judgment. None of you are guilty of anything."),("WARD","Come out. There's food.")], wide=True)
P('4.4', wide=True); P('4.5', wide=True); P('4.6'); P('4.7'); P('4.8')
P('4.9', caps=["Fourth on the board. Every seventh day for four years.","The argument lasted ten minutes. Hazel won it without saying a word."], wide=True)
P('4.10')
P('4.11', lines=[("(OFF)","Then tell us where you were that morning. That's all. Just say it.")], caps=["Ray would rather have gone out the gate than say it."], wide=True)
P('4.12', lines=[("JOHN","I'll tell you where *I* was.")], wide=True)
P('4.13', lines=[("WARD","She gave you to me. And then I asked her again, and she wouldn't."),("WARD","She went east for a day and a half. I've never been able to account for it.")], wide=True)
P('4.14', wide=True); P('4.15'); P('4.16', wide=True); P('4.17', wide=True)
P('4.18', lines=[("WARD","Who exactly do you think is watching?"),("EMMA","Nobody.")], wide=True)
P('4.19')
P('4.20', lines=[("EMMA","John. I've never —")], wide=True)

# GOLD
P('4.21', wide=True); P('4.22', wide=True)
P('4.23', caps=["Not in front of them.","Beside them."], wide=True)
P('4.24', wide=True); P('4.25'); P('4.26'); P('4.27', wide=True); P('4.28', wide=True)
P('4.29', lines=[("WARD","Wait —")])
P('4.30'); P('4.31', wide=True)
P('4.32', caps=["That morning had been a judgment.","It had also been a selection, and nobody down here could ever tell the difference."], wide=True)
P('4.33', caps=["They had not been left behind.","They had been deployed."], wide=True)

# EPILOGUE
P('5.1', wide=True)
P('5.2', caps=["Nine of them along the south edge. Fruit trees give you nothing for ten years.","You do not plant an orchard for yourself."], wide=True)
P('5.3', caps=["Four dead people built it, and neither of them earned it.","That was always the point."], wide=True)
P('5.4', wide=True)

SECTIONS = [('p1','Part One','The First Days'),('p2','Part Two','The First Winter'),
            ('m','','Four Years'),('p3','Part Three','Eden'),
            ('p4','Part Four','The Siege'),('gold','',''),('ep','','The Garden')]

mapping = json.load(open('panel_map.json'))
by_sec = {}
for label, fn, s in mapping:
    by_sec.setdefault(s, []).append((label, fn))

def uri(fn):
    b = open(os.path.join('panels_raw', fn),'rb').read()
    return 'data:image/png;base64,' + base64.b64encode(b).decode()

def esc(t):
    t = html.escape(t)
    # *word* -> italic
    out=[]; parts=t.split('*')
    for i,p in enumerate(parts):
        out.append(p if i%2==0 else f'<i>{p}</i>')
    return ''.join(out)

body=[]
for key, over, title in SECTIONS:
    if title:
        body.append(f'<section class="chap"><div class="chapinner">'
                    f'{f"<p class=eyebrow>{over}</p>" if over else ""}'
                    f'<h2>{title}</h2></div></section>')
    gold = ' gold' if key=='gold' else ''
    body.append(f'<div class="strip{gold}">')
    for label, fn in by_sec[key]:
        if not label: continue
        d = L.get(label, dict(caps=[],lines=[],wide=False))
        cls = 'panel wide' if d['wide'] else 'panel'
        inner = [f'<img src="{uri(fn)}" alt="Panel {label}">', '<span class="grain"></span>']
        if d['caps']:
            inner.append('<div class="caps">' + ''.join(f'<p>{esc(c)}</p>' for c in d['caps']) + '</div>')
        if d['lines']:
            inner.append('<div class="says">' + ''.join(
                f'<p class="bal"><span class="tag">{esc(w)}</span> {esc(t)}<i class="tail"></i></p>' for w,t in d['lines']) + '</div>')
        inner.append(f'<span class="num">{label}</span>')
        body.append(f'<figure class="{cls}">' + ''.join(inner) + '</figure>')
    body.append('</div>')

CSS = """
*{box-sizing:border-box}
:root{--ink:#e8e6e1;--dim:#8b8f8a;--gold:#d9ae58;--ground:#08090a;--edge:#20242a;
 --paper:#f4f1e9;--paperink:#101214}
body{margin:0;background:var(--ground);color:var(--ink);
 font-family:'Archivo Narrow',Arial Narrow,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 140px}
header{padding:16vh 20px 12vh;text-align:center}
header .eyebrow{font-family:'IBM Plex Mono',monospace;font-size:.68rem;letter-spacing:.3em;
 text-transform:uppercase;color:var(--dim);margin:0 0 1.6rem}
header h1{font-family:'Fraunces',Georgia,serif;font-weight:700;font-size:clamp(3.4rem,16vw,8rem);
 line-height:.9;letter-spacing:-.02em;margin:0 0 1.4rem}
header p{font-family:'IBM Plex Mono',monospace;font-size:.72rem;letter-spacing:.18em;
 text-transform:uppercase;color:var(--dim);margin:0}
.chap{padding:10vh 0 5vh;text-align:center}
.chapinner{display:inline-block;border-top:1px solid var(--edge);border-bottom:1px solid var(--edge);padding:1.6rem 3rem}
.chap .eyebrow{font-family:'IBM Plex Mono',monospace;font-size:.62rem;letter-spacing:.3em;
 text-transform:uppercase;color:var(--dim);margin:0 0 .5rem}
.chap h2{font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:clamp(1.5rem,5vw,2.4rem);margin:0;letter-spacing:.02em}

.strip{display:grid;grid-template-columns:repeat(2,1fr);gap:22px}
.panel{position:relative;margin:0;overflow:hidden;background:#000;border:1px solid var(--edge);
 aspect-ratio:16/9;display:flex}
.panel.wide{grid-column:1 / -1;aspect-ratio:2.4/1}
.panel img{width:100%;height:100%;object-fit:cover;display:block;filter:contrast(1.08) saturate(.9) brightness(.94)}
.grain{position:absolute;inset:0;pointer-events:none;opacity:.42;mix-blend-mode:overlay;
 background-image:radial-gradient(circle at 1px 1px, rgba(255,255,255,.35) .5px, transparent .6px);
 background-size:3px 3px}
.num{position:absolute;right:8px;bottom:6px;font-family:'IBM Plex Mono',monospace;font-size:.58rem;
 letter-spacing:.1em;color:rgba(255,255,255,.3)}

/* CAPTIONS — a slab that sits on the frame edge, not floating in the corner */
.caps{position:absolute;left:0;top:0;max-width:min(62%,30rem);display:flex;flex-direction:column}
.caps p{margin:0;background:var(--paper);color:var(--paperink);
 font-family:'IBM Plex Mono',monospace;font-size:.86rem;line-height:1.5;
 padding:.7rem .95rem;letter-spacing:0;
 box-shadow:3px 3px 0 rgba(0,0,0,.55);border-bottom:1px solid rgba(0,0,0,.18)}
.caps p:last-child{border-bottom:none}
.caps i{font-style:italic}

/* BALLOONS — real tails, speaker inline, set at readable size */
.says{position:absolute;right:16px;bottom:22px;max-width:min(60%,26rem);
 display:flex;flex-direction:column;align-items:flex-end;gap:14px}
.bal{position:relative;margin:0;background:#fdfcf9;color:#0b0d0e;
 border-radius:1.6em/2.2em;padding:.62rem 1rem .66rem;
 font-size:.92rem;line-height:1.24;text-transform:uppercase;letter-spacing:.015em;
 box-shadow:0 2px 0 rgba(0,0,0,.55)}
.bal .tag{font-family:'IBM Plex Mono',monospace;font-size:.62rem;letter-spacing:.14em;
 color:#8d9297;text-transform:uppercase}
.bal i.tail{position:absolute;bottom:-11px;right:26px;width:0;height:0;
 border-left:9px solid transparent;border-right:13px solid transparent;
 border-top:14px solid #fdfcf9;filter:drop-shadow(0 2px 0 rgba(0,0,0,.4))}
.bal b{font-weight:700}
.bal i:not(.tail){font-style:italic;font-weight:700}

/* GOLD FINALE */
.gold .caps p{background:#17130c;color:var(--gold);border-bottom-color:rgba(217,174,88,.22);
 border-left:3px solid var(--gold);box-shadow:3px 3px 0 rgba(0,0,0,.6)}
.gold .panel{border-color:#3a3020}
.gold .bal{background:#f6ecd6}
.gold .bal i.tail{border-top-color:#f6ecd6}

footer{text-align:center;padding:14vh 20px 8vh;border-top:1px solid var(--edge);margin-top:10vh}
footer p{font-family:'IBM Plex Mono',monospace;font-size:.66rem;letter-spacing:.2em;
 text-transform:uppercase;color:var(--dim);margin:.4rem 0}
@media(max-width:720px){
 .strip{grid-template-columns:1fr;gap:16px}
 .panel,.panel.wide{aspect-ratio:16/9}
 .caps{max-width:76%}.caps p{font-size:.74rem;padding:.55rem .75rem}
 .says{max-width:74%;right:10px;bottom:16px}.bal{font-size:.8rem}
}
"""

out = f"""<title>Divinity: The Board</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Narrow:wght@400;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>{CSS}</style>
<header>
<p class="eyebrow">Storyboard · lettered</p>
<h1>Divinity</h1>
<p>103 panels</p>
</header>
<div class="wrap">
{''.join(body)}
</div>
<footer>
<p>End</p>
<p style="color:#5d6165">Panels are placeholder resolution — swap in full-size art and nothing else changes</p>
</footer>
"""
open('graphic-novel.html','w').write(out)
print('written', round(len(out)/1024/1024,2), 'MB')
