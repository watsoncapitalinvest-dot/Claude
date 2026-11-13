"""render one terrain set's kit: python3 run_set.py <module> <outdir>   (ONLY=name1,name2 to limit)"""
import sys, os, importlib, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib
mod = importlib.import_module(sys.argv[-2]); OUT = sys.argv[-1]; os.makedirs(OUT, exist_ok=True)
only = os.environ.get('ONLY')
for i, (name, ink, fn) in enumerate(mod.KIT):
    if only and name not in only.split(','): continue
    random.seed(i); p = kitlib.Part(name, ink); fn(p)
    kitlib.render(p, os.path.join(OUT, '%02d_%s' % (i, name)))
    print('rendered', i, name, flush=True)
