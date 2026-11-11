"""Temporary instrumentation: does the escalation calendar actually keep units off the map?

A New Battle has no campaign clock, so availableUnit() correctly returns everything and the
battle cannot show the effect. OXCE_CAL_MONTH forces the month by hand instead, so the SAME map
and the SAME deployment can be fought at month 0, month 10 and month 25 and the rosters compared.
Forcing it is the point: a test where the number under test is -1 is not a test.

It also logs every unit the generator actually spawns, because the refusal log alone proves a
decision was taken, not that the man stayed off the map.

usage: cal_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// CALPROBE'
TARGET = os.path.join(SRC, 'Battlescape', 'BattlescapeGenerator.cpp')

ANCHOR = """	const int month = _game->getSavedGame()->getMonthsPassed();
	if (month < 0)"""
PROBE = """	int month = _game->getSavedGame()->getMonthsPassed();                      // CALPROBE
	if (getenv("OXCE_CAL_MONTH")) month = atoi(getenv("OXCE_CAL_MONTH"));      // CALPROBE
	if (month < 0)"""

ANCHOR2 = """			BattleUnit *unit = addAlien(const_cast<Unit*>(rule), dd.alienRank, outside);"""
PROBE2 = """			Log(LOG_INFO) << "[cal] spawned " << rule->getType();                  // CALPROBE
			BattleUnit *unit = addAlien(const_cast<Unit*>(rule), dd.alienRank, outside);"""

def apply(s):
    if MARK in s: sys.exit('probe already applied')
    assert ANCHOR in s, 'month anchor missing'
    s = s.replace(ANCHOR, PROBE, 1)
    assert ANCHOR2 in s, 'spawn anchor missing'
    return s.replace(ANCHOR2, PROBE2, 1)

def revert(s):
    out = [l for l in s.split('\n') if MARK not in l]
    s = '\n'.join(out)
    # put back the line the probe replaced
    s = s.replace("	if (month < 0)", "	const int month = _game->getSavedGame()->getMonthsPassed();\n	if (month < 0)", 1)
    return s

src = open(TARGET).read()
open(TARGET, 'w').write(apply(src) if MODE == 'apply' else revert(src))
print('%sed %s' % (MODE, TARGET))
