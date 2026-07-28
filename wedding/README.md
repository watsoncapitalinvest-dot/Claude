# Wedding Planning App

A custom wedding-planning app for one couple, planning a wedding in either
Westchester County, NY or West Palm Beach, FL.

## Project phases

1. **Research** ✅ — market research for both regions + full scope of modern wedding
   planning. See `research/`.
2. **Discovery** ⏳ — 20 questions to the couple (`QUESTIONS.md`); answers land in
   `ANSWERS.md` and become the app's founding configuration.
3. **Build** — the app itself, covering everything: budget, timeline/checklist,
   guest list, vendors, venues, events, day-of timeline. Expanded iteratively.

## Research library

| File | Contents |
|---|---|
| `research/westchester-ny.md` | Westchester costs, venues, seasonality, vendors, NY license rules, trends |
| `research/west-palm-beach.md` | Palm Beach County costs, venues, hurricane-season math, FL license rules, destination logistics, trends |
| `research/wedding-planning-scope.md` | Full planning timeline, budget percentages & hidden costs, guest/vendor management, existing-app gap analysis (The Knot, Zola, Joy, etc.), 2025–26 trends |

## Design principles distilled from research

- **The guest is the central data object**: one record flows address → save-the-date →
  invite → RSVP → meal → hotel → table → thank-you note.
- **The timeline is the spine**: tasks auto-dated backward from the wedding date, with
  dependencies (seating chart blocked until RSVP deadline passes).
- **Budget tells the truth**: auto-added tax, service-charge (15–25% on F&B), and
  gratuity lines per vendor; hidden-cost checklist pre-seeded; per-vendor payment
  schedules with due-date reminders.
- **A wedding is multiple events**: welcome party, rehearsal dinner, ceremony,
  reception, after-party, brunch — each with its own guest sublist, timeline, budget.
- **No strings**: no ads, no vendor spam, no paywalled exports — the gaps couples
  actually complain about in existing apps.
