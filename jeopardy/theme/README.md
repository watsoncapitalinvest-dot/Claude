# The SCFL Jeopardy theme

An original game-show cue — brass fanfare, walking bass, vibes on the offbeats,
a lift into the relative minor and a stacked button. 124 bpm, sixteen bars,
about thirty-two seconds.

It is written in the idiom of a television quiz theme but it is not a
transcription of one. The Jeopardy think-music is somebody else's property;
this tune is ours.

| file | what it is |
|---|---|
| `scfl-jeopardy-theme.mid` | the score. Four tracks — brass lead, vibes, bass, drums. Open it in anything and every note is movable. |
| `scfl-jeopardy-theme.wav` | a rendering, so it can be heard without a soundfont |

## Rebuilding it

No dependencies beyond numpy for the render.

    python3 theme.py     # writes the .mid
    python3 verify.py    # parses it back: no hanging notes, sane range, right tempo
    python3 render.py    # writes the .wav

`midiwrite.py` is a small MIDI writer — this sandbox has no MIDI library, and
the format is simple enough to emit directly. `render.py` is a four-voice synth
rather than a General MIDI player: the runner has no soundfont, so the
instruments are hand-rolled to suit the parts. That is why the recording sounds
a little synthetic. The notes are not the weak part; the sounds are. Anyone
opening the `.mid` with real brass and vibes samples starts most of the way
home and does not have to rewrite anything.

## Not wired into the game yet

The game does not play this. Putting it on the title screen means rebuilding it
in Web Audio so it needs no download, which is a separate job.
