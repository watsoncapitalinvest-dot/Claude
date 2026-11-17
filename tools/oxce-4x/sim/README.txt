G.I. JOE 4x - THE UNATTENDED SIMULATOR

1. Put Simulate_4x.bat next to OpenXcom.exe (C:\GI-Joe-Silent-Storm\GIJoe_XCOM_4x).
2. Start the game once with Play_4x.bat first, so the newest updates are unpacked.
3. Double-click Simulate_4x.bat. A small game window opens and closes over and over: that is each run.
4. Leave it. To stop: close its black window, or make an empty file STOP.txt next to it.

What it does: one campaign YEAR after another, nobody at the controls, through 3 player styles (absent / typical /
aggressive) x 3 Cobra head starts (0 / 6 / 12 months). About a minute a year here, so a night is several hundred.
Battles are NOT fought on screen: the style's odds decide them. It records the strategy layer: what Cobra builds and
when, its money and kit tier month by month, sites found and raided, crimes, the Drome, every Geoscape event.

What it keeps, all in sim_runs\:
  runN_<style>_head<H>_report.txt   the year, month by month
  runN_<style>_head<H>_log.txt      the game's log for that run (every [event], [cartel], [network] line)
  problems.txt                      any run that stopped early or wrote an error

It plays in its own folder (user_sim\) and never touches your saves or settings.
When you want it read: zip sim_runs\ (or just tell BUILD where it is) and it gets summarised with build\ff_summary.py.
