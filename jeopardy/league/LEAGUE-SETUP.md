# The league log

By default SCFL Jeopardy keeps every game on the device that played it. Connect
it to a Google Sheet and every copy posts its finished games to that one sheet,
so the league has a single record book you can sort, pivot and argue about.

Takes about five minutes, once, by one person.

## 1. Make the sheet

1. Go to <https://sheets.new> and name it something like **SCFL Jeopardy — log**.
2. **Extensions → Apps Script**.
3. Delete whatever is in `Code.gs` and paste in the contents of `Code.gs`
   from this folder.
4. If you want to stop strangers writing to it, put a word in the
   `WRITE_KEY` line near the top:

   ```js
   const WRITE_KEY = 'skirtchasers';
   ```

   Leave it empty and anyone with the URL can post. Reading is always open.
5. Save.

## 2. Publish it

1. **Deploy → New deployment**.
2. Gear icon → **Web app**.
3. Set **Execute as: Me** and **Who has access: Anyone**.
   It must be *Anyone*, not *Anyone with a Google account* — phones in the
   group chat will not be signed in.
4. **Deploy**, approve the permission prompt, and copy the **Web app URL**.
   It ends in `/exec`.

## 3. Point the game at it

In the game: **SCOREBOARD → LEAGUE → paste the URL** (and the write key, if you
set one) → **SAVE & TEST**. It will tell you how many games are on the sheet,
and say so plainly if the sheet refuses a write because the key is wrong.

Each person does this once on their phone. Or send me the URL and I will bake it
into the page, so everyone who opens the link is connected with nothing to paste.

## What lands in the sheet

One row per finished game, same columns as the in-game CSV export:

| column | |
|---|---|
| `date`, `time` | when it was played, on the player's clock |
| `club`, `owner` | which of the sixteen, and the ESPN handle |
| `round1`, `round2` | what each board made |
| `final_wager`, `final_result` | what was risked, and `right` / `wrong` / `not played` |
| `total` | the number that counts |
| `right`, `asked`, `accuracy` | 24, 33, 0.727 |
| `seconds` | how long the game took |
| `r1_right`, `r1_asked`, `r2_right`, `r2_asked` | per round |
| `best_category`, `worst_category` | their best and worst column that game |
| `categories` | every column: `R1 THE CELLAR 2/4 -400 \| R2 THE DRAFT 3/4 +1200` |
| `id` | `club-timestamp`, the dedup key |
| `received` | when the sheet got it |

## Things worth knowing

- **A game is never lost.** If the sheet is unreachable when someone finishes,
  the game is kept on their device and goes up with the next one, or when they
  next open the scoreboard. Nothing is dropped and nothing needs retrying by hand.
- **The same game never lands twice.** Rows are keyed on `club-timestamp`, so a
  retry, a re-send, or a re-paste adds nothing.
- **It only works on a real web address.** The published artifact preview runs
  under a strict content policy that blocks requests to outside hosts, so there
  the game stays on-device. Use the GitHub Pages copy for the live log.
- **Nothing here is private.** Anyone with the URL can read the log. Do not put
  anything in the sheet you would not paste in the group chat.
- **You can still work by copy-paste.** STATS → COPY LOG AS CSV and PASTE
  SOMEONE'S LOG both still work, connected or not.

## Changing the script later

Apps Script serves the deployment, not the file. After editing `Code.gs` you
must **Deploy → Manage deployments → edit → New version → Deploy**, or the URL
keeps running the old code.
