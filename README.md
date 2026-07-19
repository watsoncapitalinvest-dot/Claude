# 🏈 Skirt Chasers — SCFL NewsRoom

A single-file **HTML app** that turns your Sleeper league into its own weekly
magazine. It's a companion to Sleeper — it doesn't rebuild live scores or lineup
setting; it adds the things Sleeper doesn't.

## What it does

**The NewsRoom (the shareable magazine)** — auto-written every week from your
real Sleeper box scores:

- **The Cover** — a real magazine cover (your SCFL logotype, a headline about your managers)
- **Cover Story & Game Stories** — every matchup written up, real stat lines woven into the drama, Thursday-night-to-Monday-night timeline
- **The Column** — the state-of-the-league lead
- **By the Numbers**, **Studs & Duds**, **Start/Sit of Shame**, **Superlatives**
- **Power Rankings** — auto, or upload the commissioner's from Excel
- **The Trade Block** — every completed trade reviewed and graded under your scoring
- **The Water Cooler** — paste your league group chat and it becomes a column (optional AI writer)
- **The Record Book** — import your league's ESPN history (champions, all-time standings, records); the writing then references real rivalries and pedigree

**Private GM tools (owner only)** — a **Trade Analyzer** and **Draft Assistant**
scored under your league's exact settings. These never appear on shared/guest views.

## Sharing

- Share the whole issue, or any single story/ranking/trade, as a clean image
  straight to WhatsApp (the cover image travels with a short link).
- A short **guest link** opens the full issue in anyone's browser — no app, no login.
- **Back Issues** are saved on-device so past editions can be re-read.

## Running it

One file, `index.html`, no build step. Host it anywhere static and open the URL;
on a phone, **Share → Add to Home Screen** to launch it full-screen with the SCFL
NewsRoom icon.

Deployed on **GitHub Pages** (auto-deploys on push via
`.github/workflows/deploy-pages.yml`). First launch: enter your Sleeper username,
pick your league — your choice is remembered.

## Notes

- Powered by Sleeper's **public, read-only API** — no login, no password. The
  stats/projections endpoints are community-known; the app degrades gracefully
  if they're unavailable.
- Off-season / first season: generate a **sample issue from your real league**
  (real teams and managers, made-up scores) to preview it before Week 1.
- The optional AI Water Cooler uses your own Anthropic API key, stored only in
  your browser (never committed or shared).
- Not affiliated with or endorsed by Sleeper or ESPN.
