# Joepedia figure sheet

Scrapes [Joepedia](https://gijoe.fandom.com) (the G.I. Joe wiki) through its
MediaWiki API and writes a spreadsheet of every character page that carries a
faction infobox: code name, role/specialty, real name, rank, branch, factions,
sub-teams, first appearances and a link back to the page — with the page's
infobox picture embedded in the first column of the sheet.

```
pip install requests mwparserfromhell openpyxl
python3 scrape_joepedia.py                                  # G.I. Joe team -> joepedia_figures.xlsx
python3 scrape_joepedia.py --all -o joepedia_all_factions.xlsx   # Joes, Cobra, Dreadnoks, Oktober Guard...
```

Each run also writes a `.csv` next to the `.xlsx`.

- **Version** is the page's suffix — `(RAH)`, `(IDW)`, `(Movie)`, `(Resolute)` —
  so the same code name appears once per version the wiki has a page for.
- **Role / Specialty** is exactly what the page's infobox says. Where that is
  blank (common on IDW and movie pages), **Role (other version)** borrows the
  specialty from another version of the same code name, preferring RAH, and
  says which one it came from.

**Pictures.** Each figure's infobox image is downloaded (250px wide) to
`<output>_images/` and embedded in the **Picture** column. The folder is not
committed — the pictures already live inside the `.xlsx`. 313 of 359 Joes have
one; the rest have no picture on their page. Downloads come from
`static.wikia.nocookie.net`, so that host must be reachable as well as
`gijoe.fandom.com`.

## YoJoe vehicle sheet

`scrape_yojoe_vehicles.py` reads [YoJoe.com](https://www.yojoe.com/vehicles/)'s
3 3/4" vehicle archive — every year page, 1982 to 2017 — then each vehicle's
own page, and writes `yojoe_vehicles.xlsx` with the toy photo embedded in the
first column: name, year, YoJoe's section (Vehicles, Battle Stations, Mail-In,
Convention Exclusives...), subtitle, driver/pilot, series, box tagline, release
notes, how many YoJoe collectors have/want it, and the YoJoe ID.

```
python3 scrape_yojoe_vehicles.py
```

The convention page is read too, but every vehicle on it is already filed under
its year. Years YoJoe does not split into sections leave Category blank.
Needs `www.yojoe.com` reachable.
