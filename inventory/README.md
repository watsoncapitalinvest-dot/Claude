# Bar Count

Beverage inventory counted from shelf photos. Vanilla JS, no dependencies, no build step.
Data lives in your browser's localStorage. Runs as a PWA — add it to your home screen.

## The idea

Counting bottles from a photo fails in one specific, predictable way: **a bottle behind
another bottle is invisible, and no angle or prompt fixes that.** In testing, reading a
cooler shelf by eye gave 4 bottles where there were actually 7 — 43% low. The same
shelf, same method, same error every time.

So this app doesn't ask the model for a total.

1. **Claude reports what it can see.** The prompt is explicit that it must never
   estimate hidden stock. It counts closures — capsules, foils, caps, corks — and
   tells you what it counted, so you can check its work.
2. **Each location carries a depth factor.** How much stock that particular shelf
   hides behind its front row.
3. **Your corrections teach it.** Every time you fix a number, that becomes a
   calibration sample for that location. Correct the Cakebread from 4 to 7 once,
   and every other lane in that cooler adjusts by the same ×1.75.

The model does identification, which it's good at. The shelf's own geometry does
the depth, learned from you. Neither one guesses.

## Using it

**Setup tab, once:**
- Paste an Anthropic API key. It's stored in your browser only — never committed,
  never sent anywhere but `api.anthropic.com`.
- Edit the locations to match your actual room. One location = one shelf or one
  cooler compartment.

**Every count:**
1. Count tab → tap a location
2. Photograph the shelf — straight on, at shelf height. Multiple angles of the same
   shelf are merged into one count, not added together.
3. Tap **Read shelf**
4. Check each line. Tap ✓ or nudge the number with +/−. A corrected line is marked.
5. **Save & mark location counted**

**Totals tab** shows everything by category and exports CSV for Craftable.

## Coverage, not just counts

The Totals tab refuses to show a clean number until every location is counted.
If you've walked 7 of 11 shelves, it says so and names the four you skipped.

This is deliberate. The worst inventory error isn't a miscount — it's a shelf that
silently never got counted and reads as zero.

## Calibration notes

- A fresh location has no factor and passes visible counts through unchanged.
- One correction sets a factor. Three or more and it stops saying "needs more."
- Factors are pooled across all samples for that location, so one odd correction
  doesn't swing it.
- A shelf you count head-on with everything visible stays at ×1.00 forever — the
  math only inflates where you've told it stock hides.
- Adjusted counts never go below what was actually seen.

## Files

| File | |
|---|---|
| `index.html` | shell and views |
| `app.css` | styles, light + dark |
| `app.js` | all logic — storage, API, calibration, export |
| `sw.js` | offline shell cache; never intercepts API calls |
| `manifest.webmanifest` | PWA install |

## Implementation notes

Calls the Messages API directly from the browser with
`anthropic-dangerous-direct-browser-access`, using `claude-opus-5`, adaptive
thinking, and a `json_schema` output format. Raw `fetch` rather than the official
SDK because this repo is a no-build static site with a no-dependencies convention —
if you add a bundler later, swap in `@anthropic-ai/sdk`.

Photos are downscaled to 1568px on the long edge before upload.
