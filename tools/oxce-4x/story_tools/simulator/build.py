"""Builds Cobra_Economy_Simulator.html: template.html with sim.js inlined (one file, runs offline in a browser)."""
import os
H = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(H, 'template.html')).read(); s = open(os.path.join(H, 'sim.js')).read()
open(os.path.join(H, 'Cobra_Economy_Simulator.html'), 'w').write(t.replace('/*__SIM__*/', s))
print('built Cobra_Economy_Simulator.html')
