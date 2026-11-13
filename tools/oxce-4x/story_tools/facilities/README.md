# Facility data (STORY)
`facilities_1.yml` (G.I. Joe main-base rooms) and `facilities_2.yml` (outpost and later-act rooms), in BUILD's FACILITY_DATA_FORMAT.
Design and the reasons behind the numbers: claude/FACILITY_STATS_v1.md (project). STORY owns these files; John's copies are in Reference\.

## Which rooms open each department (FACILITY_STATS section 7)
| Department | Room ids |
|---|---|
| COMMAND | STR_JOE_HQ_COMMAND_CENTER, STR_JOE_FIELD_COMMAND |
| INTEL | STR_JOE_COMPUTER_STATION |
| MOTOR_POOL | STR_JOE_MOTOR_POOL_AND_VEHICLE_LIFT, STR_JOE_MOTOR_POOL_BAY, STR_JOE_VEHICLE_BAYS |
| ARMORY | STR_JOE_WEAPONS_LOCKER |
| MEDICAL | STR_JOE_INFIRMARY_COT, STR_JOE_INFIRMARY, STR_JOE_SICKBAY |
| COMMS | STR_JOE_COMMS_CENTER, STR_JOE_COMMS_ROOM |
| AIR_WING | STR_JOE_HANGAR_BAY, STR_JOE_LARGE_HANGAR, STR_JOE_LAUNCH_PAD |
| TRAINING | STR_JOE_TRAINING_AREA, STR_JOE_RECRUITING_OFFICE |
STR_JOE_ARMORY opens no department (storage 30 + STR_ARMORY_ATTACHMENTS).
