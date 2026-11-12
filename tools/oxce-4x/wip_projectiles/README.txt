PARKED: projectiles work in progress (12 Nov 2026). NOT part of the game yet.

The ruleset and sprites here were in mod/ but need engine support (bulletDirectional, bigger
projectile frames) that is not in oxce_4x.patch and not in any build. Loaded by today's exe
they would be wrong, so they were moved out of mod/ until the engine side ships.

engine_tree_diff_projectiles.patch is a full `git diff` of the working OXCE tree the projectile
work was done in. That tree is NOT the same as oxce_4x.patch (it lacks some Camera / Map /
TileEngine changes the committed patch has). Use it only to lift the projectile changes
(Projectile.cpp/.h, RuleItem, the projectile sprite sizing) onto the real patch.

To ship: port those engine changes onto oxce_4x.patch, build, check a battle, then move
mod/Ruleset/gijoe_projectiles.rul and mod/Resources/Projectiles back under mod/.
