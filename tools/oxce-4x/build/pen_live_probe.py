"""Temporary instrumentation: has a shot ever actually gone through a wall?

Everything about penetration has been verified except the thing it does. The matrix loads from
the ruleset, the 627 material tags reach MapData, the code compiles - and no shot has ever been
watched passing through anything. "It is in the build and it runs" was the exact state wall
penetration was in this morning while being completely inert, so that evidence is worth nothing
on its own.

Three log points, because silence has to be readable:

  TERRAIN  every hit on terrain, with whether the gate let it through to penetrate() and why
           not when it did not - so "no penetration lines" can be told apart from "no shots".
  PEN      every penetrate() call: the material, the power in, the power out.
  ONWARD   every penetrateOnward(): whether the re-trace found anything behind the wall, which
           is the half that actually delivers damage and the half most likely to be silently
           wrong.

usage: pen_live_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// LIVEPROBE'
TARGET = os.path.join(SRC, 'Battlescape', 'TileEngine.cpp')

GATE_ANCHOR = """			if (stoodUp && rangeAtack && terrainMeleeTilePart == 0)
			{
				int through = penetrate(power, hitMaterial, type);
"""

GATE_PROBE = """			if (getenv("OXCE_PEN_LIVE"))                                           // LIVEPROBE
			{                                                                      // LIVEPROBE
				Log(LOG_INFO) << "[pen] TERRAIN mat=" << hitMaterial               // LIVEPROBE
					<< " power=" << power << " stoodUp=" << stoodUp                // LIVEPROBE
					<< " ranged=" << rangeAtack << " melee=" << terrainMeleeTilePart;// LIVEPROBE
			}                                                                      // LIVEPROBE
			// The measurement the gate question needs. OXCE_PEN_BROKEN=1 lets a shot that     // LIVEPROBE
			// DESTROYED the tile carry on as well, which is the one-line alternative to the   // LIVEPROBE
			// current rule, so both can be measured from the same build instead of argued.    // LIVEPROBE
			if (getenv("OXCE_PEN_BROKEN") && !stoodUp && rangeAtack                            // LIVEPROBE
				&& terrainMeleeTilePart == 0)                                                  // LIVEPROBE
			{                                                                                  // LIVEPROBE
				int t2 = penetrate(power, hitMaterial, type);                                  // LIVEPROBE
				if (t2 > 0) penetrateOnward(attack, center, t2, type);                         // LIVEPROBE
			}                                                                                  // LIVEPROBE
""" + GATE_ANCHOR

PEN_ANCHOR = """	int left = power - cost;
	if (left <= 0)
	{
		return 0;
	}
	return (int)(left * _penPass[material]);
"""

PEN_PROBE = """	int left = power - cost;
	if (getenv("OXCE_PEN_LIVE"))                                                   // LIVEPROBE
	{                                                                              // LIVEPROBE
		Log(LOG_INFO) << "[pen] PEN mat=" << material << " power=" << power         // LIVEPROBE
			<< " cost=" << cost << " -> "                                          // LIVEPROBE
			<< (left <= 0 ? 0 : (int)(left * _penPass[material]));                 // LIVEPROBE
	}                                                                              // LIVEPROBE
	if (left <= 0)
	{
		return 0;
	}
	return (int)(left * _penPass[material]);
"""

ONWARD_ANCHOR = """	VoxelType next = calculateLineVoxel(start, far, false, &trajectory, attack.attacker);
	if (next != V_EMPTY && !trajectory.empty())
	{
		hit(attack, trajectory.back(), power, type);
	}
"""

ONWARD_PROBE = """	VoxelType next = calculateLineVoxel(start, far, false, &trajectory, attack.attacker);
	if (getenv("OXCE_PEN_LIVE"))                                                   // LIVEPROBE
	{                                                                              // LIVEPROBE
		Log(LOG_INFO) << "[pen] ONWARD depth=" << _penetrationDepth                // LIVEPROBE
			<< " power=" << power << " found=" << (int)next                        // LIVEPROBE
			<< " traj=" << trajectory.size();                                      // LIVEPROBE
	}                                                                              // LIVEPROBE
	if (next != V_EMPTY && !trajectory.empty())
	{
		hit(attack, trajectory.back(), power, type);
	}
"""

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    for name, anchor in (('gate', GATE_ANCHOR), ('pen', PEN_ANCHOR), ('onward', ONWARD_ANCHOR)):
        if src.count(anchor) != 1:
            print('ANCHOR %s appears %d times - do not guess' % (name, src.count(anchor)))
            sys.exit(1)
    src = src.replace(GATE_ANCHOR, GATE_PROBE, 1)
    src = src.replace(PEN_ANCHOR, PEN_PROBE, 1)
    src = src.replace(ONWARD_ANCHOR, ONWARD_PROBE, 1)
    open(TARGET, 'w', encoding='utf-8').write(src)
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
