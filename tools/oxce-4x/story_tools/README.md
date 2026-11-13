# STORY tools
Scripts that write STORY's research rulesets. Edit the scripts, not the .rul files, then rebuild:

```
cd tools/oxce-4x/story_tools
for g in 1 2 3 4; do python3 gen_batch$g.py ../mod/Ruleset; done
python3 add_lanes.py ../mod/Ruleset
```

| Script | Writes |
|---|---|
| gen_batch1.py | gijoe_research_spine.rul (interrogation spine), gijoe_story_act1.rul (Act 1 beats) |
| gen_batch2.py | gijoe_research_captured.rul (captured Cobra gear, clue decodes) |
| gen_batch3.py | gijoe_research_joe.rul (G.I. Joe research, Year 1; costFunds) |
| gen_batch4.py | gijoe_research_retire.rul (stock topics hidden; list in retire_list.json) |
| add_lanes.py | adds `lane:` (department head row for the research tree screen) to every topic |
| pacing.py | Year 1 pacing check. `WAGE=0.6 FUND=1.2 python3 pacing.py 1.0 0.4` (wage scale, funding $M/month; args: research money scale, other income $M/month). Economy numbers are estimates. |

Needs Python 3 with PyYAML.
