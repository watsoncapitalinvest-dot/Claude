# SPS Pools & Spas — Back Office

A back-office web app for a pool service company. Runs on a phone in the field
and a computer in the office. Manages customers, service routes, on-site visit
logging (with water-chemistry readings), invoicing, crew, and reporting, plus a
pool-chemistry dosage calculator.

Built as a **static PWA** — plain HTML + CSS + vanilla JavaScript, no framework,
no build step. It installs to the home screen and works fully offline.

## ⚠️ Data caveat (read this)

All data is stored **on the device, in the browser** (`localStorage`). It does
**not** sync between devices or users — the phone and the office computer each
have their own copy. That's fine for a single owner/dispatcher; shared,
real-time crew data is a Phase 2 project (hosted database + accounts).
Use **Settings → Full backup (.json)** regularly to keep a copy of your data.
Clearing the browser's site data erases the app's data.

## Run locally

Any static file server works:

```bash
cd sps
python3 -m http.server 8080
# open http://localhost:8080
```

(Opening `index.html` directly from disk works too, but the service worker /
offline mode needs http(s).)

## Deploy — GitHub Pages

1. Put these files in a repository (repo root or a subfolder — all paths are
   relative): `index.html`, `app.css`, `app.js`, `sw.js`,
   `manifest.webmanifest`, `icon-192.png`, `icon-512.png`,
   `apple-touch-icon-180.png`.
2. Repo **Settings → Pages → Source: Deploy from a branch → `main` / root → Save**.
3. The app is live at `https://<username>.github.io/<repo>/` (add the subfolder
   to the URL if you used one) within about a minute.
4. On a phone, open the URL in Safari → **Share → Add to Home Screen**.

### Updating a deployed app

The service worker caches the app for offline use, so after changing any file
**bump the `CACHE` constant at the top of `sw.js`** (`sps-v1` → `sps-v2`, …)
and push it along with your changes. Every installed device then pulls the new
version on its next online load.

(Optional: a GitHub Actions Pages workflow can auto-deploy on push, but the
branch-deploy method above needs no CI at all.)

## Features

- **Dashboard** — today's stops, revenue MTD, outstanding, overdue-invoice alert
- **Schedule** — daily routes from each customer's weekly / bi-weekly / monthly
  plan, grouped by tech
- **Clients** — searchable CRM with pool specs, access notes, service history
- **Visits** — chemistry readings with in/out-of-range coloring, task checklist,
  chemicals used, notes
- **Invoices** — line items, paid/unpaid, overdue tracking
- **Team** — techs with color-coded routes
- **Reports** — 6-month revenue chart, chemical usage
- **Tools** — ideal-range reference + dosage calculator (chlorine, pH,
  alkalinity, calcium, CYA, salt, with dilution guidance)
- **Settings** — company info, CSV/JSON export, sample data, full reset

Chemistry guidance is general-purpose: always follow product labels and never
mix chemicals.
