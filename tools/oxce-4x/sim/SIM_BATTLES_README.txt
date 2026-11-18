THE BATTLE SIMULATOR - Sim_Battles_4x.bat (BUILD-1, 17 Nov 2026)

WHAT IT DOES
The computer plays every New Battle mission by itself, one after another, and starts over when it has done them all.
It plays the Joes too, using the same AI that plays Cobra. Each battle runs in a separate copy of the game, so if the
game crashes you lose one battle and the next one starts. Your saves and settings are never touched: it plays in
user_sim\.

HOW TO USE IT
1. Put Sim_Battles_4x.bat next to OpenXcom.exe (C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x).
2. Start the game once with Play_4x.bat, so this build's mod is unpacked.
3. Double-click Sim_Battles_4x.bat. A game window opens and plays. Leave the window alone. A battle takes about
   5 to 25 minutes.
4. To stop: close the black window, or make an empty file called STOP.txt next to the .bat. It stops after the
   battle in hand.

WHAT YOU GET (sim_battles\)
  results.txt     one line a battle:
                    WIN / LOSS            the battle ended normally (turns, score, Cobra killed, Joes lost ...)
                    CRASH                 the game shut down mid-battle
                    HANG                  the game stopped answering for 3 minutes
                    STUCK ... screen      a screen came up that it could not get past (OK pressed 3 times)
                    STUCK ... turn        one side's turn ran 10 minutes
                    NO RESULT             back at the menu without a debrief
  problems.txt    only the battles that went wrong, plus any battle whose log has errors
  r<run>_m<mission>\   that battle's pictures (briefing, turns 1-3 then every 5th, debrief, any stuck screen),
                  events.txt (what happened when) and log.txt (the game's own log)
Give me sim_battles\ (zip it) when we're back.

WHAT IT CAN'T TELL YOU
It finds things that break. It can't tell you whether a mission is fun or fair. Cobra's AI playing the Joes is not
a player: it doesn't search for clues, doesn't use stealth on purpose, and plays every mission the same way.
After 30 turns the Joes pull out and the run says so.
