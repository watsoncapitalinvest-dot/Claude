#!/usr/bin/env python3
"""Temporary instrumentation: does Cobra actually carry a downed Joe off the map?

Full capture needs three things to line up in one battle - a Joe unconscious, a Cobra trooper
beside him, and that trooper reaching a map edge while still holding him. A New Battle produces
none of them on demand, and waiting for all three to happen by chance is not a test, it is a
hope. Every other feature on this desk that shipped doing nothing shipped because the thing
under test was never true during the run.

So the probe forces the preconditions and lets the REAL captureStep decide what follows. It does
not set _carryingId itself and it does not call captureStep: a wrong captureStep still fails.

  NOTE setUnitPosition's third argument is testOnly and DEFAULTS TO FALSE. Passing true there
  only asks whether the move is legal and moves nobody, which would have made this probe report
  a clean "moved hostile beside victim" while the board never changed.

    OXCE_CAP_STUN=1   at the first hostile turn end, knock one player unit unconscious and move
                      a live hostile next to him. Pickup then has to happen on its own.
    OXCE_CAP_EXIT=1   put whoever is carrying someone into the exit area, so the extract pass
                      has something to find. Set it on a LATER turn than the stun, or the pickup
                      pass has not run yet and there is nobody carrying anything.

usage: cap_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// CAPPROBE'
TARGET = os.path.join(SRC, 'Battlescape', 'BattlescapeGame.cpp')

ANCHOR = """	// 1. EXTRACT
"""

PROBE = """	// Forced preconditions. Deliberately BEFORE the three passes, so the passes below are the
	// real ones and the probe only arranges the board they read.
	if (getenv("OXCE_CAP_STUN"))                                                   // CAPPROBE
	{                                                                              // CAPPROBE
		BattleUnit *victim = nullptr;                                              // CAPPROBE
		for (BattleUnit *u : *_save->getUnits())                                   // CAPPROBE
		{                                                                          // CAPPROBE
			if (u->getOriginalFaction() == FACTION_PLAYER && !u->isOut() && u->getTile()) // CAPPROBE
			{                                                                      // CAPPROBE
				victim = u; break;                                                 // CAPPROBE
			}                                                                      // CAPPROBE
		}                                                                          // CAPPROBE
		if (victim)                                                                // CAPPROBE
		{                                                                          // CAPPROBE
			victim->knockOut(this);                                                // CAPPROBE
			victim->instaFalling();                                                // CAPPROBE
			Log(LOG_INFO) << "[cap] stunned " << victim->getId()                   // CAPPROBE
				<< " status=" << (int)victim->getStatus();                         // CAPPROBE
			for (BattleUnit *h : *_save->getUnits())                               // CAPPROBE
			{                                                                      // CAPPROBE
				if (h->getFaction() != FACTION_HOSTILE || h->isOut()) continue;    // CAPPROBE
				// TRY EVERY NEIGHBOUR, AT THE VICTIM'S OWN Z. The first version tried    // CAPPROBE
				// one tile and ignored the refusal, so the trooper stayed thirty tiles   // CAPPROBE
				// away on another floor while the log said he was beside the body - and // CAPPROBE
				// captureStep got the blame for finding nothing.                        // CAPPROBE
				bool moved = false;                                                    // CAPPROBE
				Position vp = victim->getPosition();                                   // CAPPROBE
				for (int dx = -1; dx <= 1 && !moved; ++dx)                             // CAPPROBE
				{                                                                      // CAPPROBE
					for (int dy = -1; dy <= 1 && !moved; ++dy)                          // CAPPROBE
					{                                                                   // CAPPROBE
						if (!dx && !dy) continue;                                       // CAPPROBE
						Position next = vp + Position(dx, dy, 0);                       // CAPPROBE
						if (!_save->getTile(next)) continue;                            // CAPPROBE
						if (_save->setUnitPosition(h, next, false))                     // CAPPROBE
						{                                                               // CAPPROBE
							h->setPosition(next);                                        // CAPPROBE
							moved = true;                                                // CAPPROBE
						}                                                               // CAPPROBE
					}                                                                   // CAPPROBE
				}                                                                      // CAPPROBE
				Log(LOG_INFO) << "[cap] hostile " << h->getId()                        // CAPPROBE
					<< " move=" << (moved ? "ok" : "REFUSED ALL 8")                     // CAPPROBE
					<< " hpos=" << h->getPosition()                                     // CAPPROBE
					<< " vpos=" << vp                                                   // CAPPROBE
					<< " vTile=" << (victim->getTile() ? 1 : 0)                         // CAPPROBE
					<< " tileUnit=" << (victim->getTile() && victim->getTile()->getUnit()  // CAPPROBE
						? victim->getTile()->getUnit()->getId() : -1);                   // CAPPROBE
				break;                                                             // CAPPROBE
			}                                                                      // CAPPROBE
		}                                                                          // CAPPROBE
		else                                                                       // CAPPROBE
		{                                                                          // CAPPROBE
			Log(LOG_INFO) << "[cap] nobody left to stun";                          // CAPPROBE
		}                                                                          // CAPPROBE
	}                                                                              // CAPPROBE
	if (getenv("OXCE_CAP_EXIT"))                                                   // CAPPROBE
	{                                                                              // CAPPROBE
		for (BattleUnit *u : *_save->getUnits())                                   // CAPPROBE
		{                                                                          // CAPPROBE
			if (!u->isCarrying() || u->isOut()) continue;                          // CAPPROBE
			// find a real exit tile rather than assuming the map edge is one      // CAPPROBE
			for (int i = 0; i < _save->getMapSizeXYZ(); ++i)                       // CAPPROBE
			{                                                                      // CAPPROBE
				Tile *t = _save->getTile(i);                                       // CAPPROBE
				if (!t || !(t->getMapData(O_FLOOR)                                 // CAPPROBE
					&& t->getMapData(O_FLOOR)->getSpecialType() == START_POINT))   // CAPPROBE
					continue;                                                      // CAPPROBE
				_save->setUnitPosition(u, t->getPosition(), false);                 // CAPPROBE
				u->setPosition(t->getPosition());                                  // CAPPROBE
				Log(LOG_INFO) << "[cap] carrier " << u->getId()                    // CAPPROBE
					<< " placed in the exit area";                                 // CAPPROBE
				break;                                                             // CAPPROBE
			}                                                                      // CAPPROBE
			break;                                                                 // CAPPROBE
		}                                                                          // CAPPROBE
	}                                                                              // CAPPROBE
""" + ANCHOR

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    if src.count(ANCHOR) != 1:
        print('ANCHOR appears %d times - do not guess' % src.count(ANCHOR))
        sys.exit(1)
    src = src.replace(ANCHOR, PROBE, 1)
    open(TARGET, 'w', encoding='utf-8').write(src)
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
