Net generator from Simon Tatham's Portable Puzzle Collection, compiled to WebAssembly for the puzzle prototype's computer hack.
Licence: MIT-style, see LICENCE (copyright Simon Tatham and contributors). The licence must travel with this code.
Source: https://github.com/ghewgill/puzzles (mirror of Simon Tatham's collection), commit 01c3e382d9c7013f0bb4eb9f1ff2d19bb05d4241.
gen.c is ours (STORY): it calls the game's own default_params / decode_params / new_desc and returns the description
(the shuffled tiles, one hex digit per tile: R=1 U=2 L=4 D=8) and aux (the unshuffled solution).
Build (zig from pip: pip install ziglang), from the collection's source folder:
  python3 -m ziglang cc -target wasm32-wasi -Os -s -I. -o net.wasm gen.c net.c misc.c random.c malloc.c tree234.c dsf.c drawing.c -mexec-model=reactor
