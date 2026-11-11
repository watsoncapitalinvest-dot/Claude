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

ANCHOR = """	// 1. DROP
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
		// SAY WHICH FAILURE IT IS. Silence here read identically for "nobody is   // CAPPROBE
		// carrying anyone yet" (the exit block ran on turn 1, before pass 3 had   // CAPPROBE
		// ever fired) and "this map has no START_POINT tile". They need different // CAPPROBE
		// fixes and the probe could not tell them apart.                          // CAPPROBE
		int carriers = 0, exits = 0;                                               // CAPPROBE
		for (BattleUnit *c : *_save->getUnits()) if (c->isCarrying()) ++carriers;  // CAPPROBE
		for (int i = 0; i < _save->getMapSizeXYZ(); ++i)                           // CAPPROBE
		{                                                                          // CAPPROBE
			Tile *t = _save->getTile(i);                                           // CAPPROBE
			if (t && t->getMapData(O_FLOOR)                                        // CAPPROBE
				&& t->getMapData(O_FLOOR)->getSpecialType() == START_POINT) ++exits; // CAPPROBE
		}                                                                          // CAPPROBE
		Log(LOG_INFO) << "[cap] exit block: carriers=" << carriers                 // CAPPROBE
			<< " startPointTiles=" << exits;                                       // CAPPROBE
		for (BattleUnit *u : *_save->getUnits())                                   // CAPPROBE
		{                                                                          // CAPPROBE
			if (!u->isCarrying()) continue;                                        // CAPPROBE
			Log(LOG_INFO) << "[cap] carrier " << u->getId()                        // CAPPROBE
				<< " out=" << (u->isOut() ? 1 : 0);                                  // CAPPROBE
		}                                                                          // CAPPROBE
	}                                                                              // CAPPROBE
""" + ANCHOR

A1 = '\t\tconst Position &p = bu->getPosition();\n'
A2 = '\t\t\t\tBattleUnit *cand = t->getUnit();\n'
I1 = '\t\tconst Position &p = bu->getPosition();\n\t\tLog(LOG_INFO) << "[cap] pass3 hostile " << bu->getId() << " at " << p;   // CAPPROBE\n'
A3 = '\t// 3. EXTRACT - LAST, not first.\n'
I3 = '\t// 4. PROBE: walk the carrier to the exit the moment he has someone, in the same  // CAPPROBE\n\t// captureStep, immediately before the extract pass reads the board. Placing him    // CAPPROBE\n\t// on a later turn meant racing the squad, who shot every carrier dead first.       // CAPPROBE\n\tif (getenv("OXCE_CAP_EXIT"))                                                       // CAPPROBE\n\t{                                                                                  // CAPPROBE\n\t\tfor (BattleUnit *u : *_save->getUnits())                                       // CAPPROBE\n\t\t{                                                                              // CAPPROBE\n\t\t\tif (!u->isCarrying() || u->isOut()) continue;                              // CAPPROBE\n\t\t\tfor (int i = 0; i < _save->getMapSizeXYZ(); ++i)                           // CAPPROBE\n\t\t\t{                                                                          // CAPPROBE\n\t\t\t\tTile *t = _save->getTile(i);                                           // CAPPROBE\n\t\t\t\tif (!t || !(t->getMapData(O_FLOOR)                                     // CAPPROBE\n\t\t\t\t\t&& t->getMapData(O_FLOOR)->getSpecialType() == START_POINT)) continue; // CAPPROBE\n\t\t\t\tif (!_save->setUnitPosition(u, t->getPosition(), false)) continue;     // CAPPROBE\n\t\t\t\tu->setPosition(t->getPosition());                                      // CAPPROBE\n\t\t\t\tLog(LOG_INFO) << "[cap] carrier " << u->getId()                        // CAPPROBE\n\t\t\t\t\t<< " placed in the exit area at " << t->getPosition();              // CAPPROBE\n\t\t\t\tbreak;                                                                 // CAPPROBE\n\t\t\t}                                                                          // CAPPROBE\n\t\t\tbreak;                                                                     // CAPPROBE\n\t\t}                                                                              // CAPPROBE\n\t}                                                                                  // CAPPROBE\n\t// 3. EXTRACT - LAST, not first.\n'
I2 = '\t\t\t\tBattleUnit *cand = t->getUnit();\n\t\t\t\tif (cand) Log(LOG_INFO) << "[cap] pass3 saw " << cand->getId()        // CAPPROBE\n\t\t\t\t\t<< " st=" << (int)cand->getStatus()                                 // CAPPROBE\n\t\t\t\t\t<< " of=" << (int)cand->getOriginalFaction()                        // CAPPROBE\n\t\t\t\t\t<< " carried=" << (cand->isBeingCarried() ? 1 : 0);                 // CAPPROBE\n'

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    if src.count(ANCHOR) != 1:
        print('ANCHOR appears %d times - do not guess' % src.count(ANCHOR))
        sys.exit(1)
    src = src.replace(ANCHOR, PROBE, 1)
    # Two more, INSIDE the real pass 3. The outside reproduction of its predicate was wrong
    # (distance2d is a float, so a diagonal neighbour is 1.41 and the only case the probe ever
    # creates got filtered out of its own diagnostic). Nothing to reproduce if we log in place.
    for anchor, ins in ((A1, I1), (A2, I2)):
        if src.count(anchor) != 1:
            print('pass-3 anchor appears %d times - refusing to guess' % src.count(anchor))
            sys.exit(1)
        src = src.replace(anchor, ins, 1)
    if src.count(A3) != 1:
        print('end-of-captureStep anchor appears %d times - refusing to guess' % src.count(A3))
        sys.exit(1)
    src = src.replace(A3, I3, 1)
    open(TARGET, 'w', encoding='utf-8').write(src)
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
