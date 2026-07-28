# Emma's Pool Cleaning

The consumer pool-care app for Emma's own pool: a daily pool log (chemical
doses, chemistry readings, water clarity, weather), trends, a dosage
calculator sized to her pool, reminders, and a built-in offline pool guide.

Single-file vanilla-JS PWA (`index.html`) plus manifest, service worker, and
icons — installable to the home screen, works fully offline after first load.

Her July back history (transcribed from her handwritten pool log) is
pre-loaded on first run; anything she saves afterward takes over.

Data lives in the browser's localStorage on each device — it does not sync
between devices. The Setup tab has CSV/JSON export for backups.

**Updating a deployed copy:** bump the `CACHE` constant at the top of `sw.js`
(`emma-v1` → `emma-v2`, …) whenever any file changes, so installed devices
pick up the new version.

(The business back-office app that previously lived at this path is now in
`/pool-office/`.)
