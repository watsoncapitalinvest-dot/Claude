# Joepedia figure sheet

Scrapes [Joepedia](https://gijoe.fandom.com) (the G.I. Joe wiki) through its
MediaWiki API and writes a spreadsheet of every character page that carries a
faction infobox: code name, role/specialty, real name, rank, branch, factions,
sub-teams, first appearances and a link back to the page.

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
