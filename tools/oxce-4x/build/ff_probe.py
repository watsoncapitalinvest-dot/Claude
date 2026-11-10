"""Temporary instrumentation: advance the geoscape N days without touching the UI.

Driving the geoscape with xdotool does not work and the failures all look like a quiet campaign.
A UFO detection popup stops the clock and Return will not clear it, because its default button is
INTERCEPT. Escape opens the options menu, and a second one lands in the mod list - which is where
a ten-minute run finished, stopped three months in, with a log that read exactly like Cobra
having nothing to build. Only a screenshot told the difference.

So the clock is advanced in code, through the same switch timeAdvance() uses, and the popups that
would have stopped it are dropped on the floor rather than shown. Everything the months do -
missions thinking, bases spawning, the economy ticking - runs exactly as it would with a person
holding the key down.

OXCE_CAMP_FF=<days> is how long to run. It happens once, on the first init.

usage: ff_probe.py apply|revert <src dir>
"""
import sys, os

MODE, SRC = sys.argv[1], sys.argv[2]
MARK = '// FFPROBE'
TARGET = os.path.join(SRC, 'Geoscape', 'GeoscapeState.cpp')

ANCHOR = """void GeoscapeState::init()
{
	State::init();
	timeDisplay();
"""

PROBE = ANCHOR + """	{                                                                          // FFPROBE
		static bool ffDone = false;                                            // FFPROBE
		const char* ffEnv = getenv("OXCE_CAMP_FF");                            // FFPROBE
		if (ffEnv && !ffDone)                                                  // FFPROBE
		{                                                                      // FFPROBE
			ffDone = true;                                                     // FFPROBE
			int days = atoi(ffEnv);                                            // FFPROBE
			Log(LOG_INFO) << "[ff] advancing " << days << " days";             // FFPROBE
			// 5-second steps, which is what the slowest speed does, so every  // FFPROBE
			// handler fires the same number of times a real run would.        // FFPROBE
			long steps = (long)days * 24L * 60L * 12L;                         // FFPROBE
			for (long s = 0; s < steps; ++s)                                   // FFPROBE
			{                                                                  // FFPROBE
				TimeTrigger t = _game->getSavedGame()->getTime()->advance();   // FFPROBE
				switch (t)                                                     // FFPROBE
				{                                                              // FFPROBE
				case TIME_1MONTH: time1Month(); FALLTHROUGH;                   // FFPROBE
				case TIME_1DAY:   time1Day();   FALLTHROUGH;                   // FFPROBE
				case TIME_1HOUR:  time1Hour();  FALLTHROUGH;                   // FFPROBE
				case TIME_30MIN:  time30Minutes(); FALLTHROUGH;                // FFPROBE
				case TIME_10MIN:  time10Minutes(); FALLTHROUGH;                // FFPROBE
				case TIME_5SEC:   time5Seconds();                              // FFPROBE
				}                                                              // FFPROBE
				// Whatever wanted to interrupt is thrown away. A run with a   // FFPROBE
				// hand on the controls is a different test and needs one.     // FFPROBE
				for (auto* p : _popups) { delete p; }                          // FFPROBE
				_popups.clear();                                               // FFPROBE
				_pause = false;                                                // FFPROBE
			}                                                                  // FFPROBE
			Log(LOG_INFO) << "[ff] done";                                      // FFPROBE
		}                                                                      // FFPROBE
	}                                                                          // FFPROBE
"""

src = open(TARGET, encoding='utf-8').read()

if MODE == 'apply':
    if MARK in src:
        print('already applied')
        sys.exit(0)
    if src.count(ANCHOR) != 1:
        print('ANCHOR appears %d times - do not guess' % src.count(ANCHOR))
        sys.exit(1)
    open(TARGET, 'w', encoding='utf-8').write(src.replace(ANCHOR, PROBE, 1))
    print('applied')
else:
    out = '\n'.join(l for l in src.split('\n') if MARK not in l)
    open(TARGET, 'w', encoding='utf-8').write(out)
    print('reverted; markers left:', out.count(MARK))
