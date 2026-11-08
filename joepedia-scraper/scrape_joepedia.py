#!/usr/bin/env python3
"""Scrape Joepedia (gijoe.fandom.com) into a spreadsheet of G.I. Joe characters.

Every character page on Joepedia carries a faction infobox template
("Joe character infobox", "Cobra character infobox", ...). This script asks the
MediaWiki API for every page that uses one, pulls the wikitext in batches of
50, reads the infobox fields, and writes an .xlsx (and a .csv alongside it).

  python3 scrape_joepedia.py                 # G.I. Joe team only
  python3 scrape_joepedia.py --all           # every faction (Cobra, Dreadnoks, ...)
  python3 scrape_joepedia.py -o joes.xlsx

Needs: pip install requests mwparserfromhell openpyxl
"""
import argparse
import csv
import re
import sys
import time

import mwparserfromhell
import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

API = "https://gijoe.fandom.com/api.php"
WIKI = "https://gijoe.fandom.com/wiki/"
UA = "joepedia-figure-sheet/1.0 (personal research script)"

# Infobox template -> faction label. Discovered from the wiki's Template namespace.
INFOBOXES = {
    "Joe character infobox": "G.I. Joe",
    "Cobra character infobox": "Cobra",
    "Dreadnok character infobox": "Dreadnoks",
    "IRON character infobox": "Iron Grenadiers",
    "OG character infobox": "Oktober Guard",
    "RS character infobox": "Red Shadows",
    "IG character infobox": "Iron Grenadiers",
    "Skar character infobox": "Skar",
    "Character infobox": "Other",
}

# (spreadsheet column, infobox parameter names to try in order)
COLUMNS = [
    ("Code Name", ["name"]),
    ("Role / Specialty", ["specialty", "function", "role"]),
    ("Real Name", ["realname"]),
    ("Rank", ["graderank", "rank"]),
    ("Branch", ["branch"]),
    ("Factions", ["factions"]),
    ("Sub-teams", ["subteams"]),
    ("Birthplace", ["birthplace"]),
    ("Gender", ["gender"]),
    ("First Comic", ["1stcomic"]),
    ("First Cartoon", ["1sttoon"]),
]

session = requests.Session()
session.headers["User-Agent"] = UA


def api(**params):
    params.setdefault("format", "json")
    params.setdefault("formatversion", "2")
    for attempt in range(5):
        try:
            r = session.get(API, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == 4:
                raise
            wait = 2 ** attempt
            print(f"  retry in {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)


def pages_using(template):
    """All article-namespace pages that transclude Template:<template>."""
    out, cont = [], {}
    while True:
        d = api(action="query", list="embeddedin", eititle=f"Template:{template}",
                einamespace=0, eilimit=500, **cont)
        out += [p["title"] for p in d["query"]["embeddedin"]]
        if "continue" not in d:
            return out
        cont = d["continue"]


def wikitexts(titles):
    """Yield (title, wikitext) for titles, 50 per request."""
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        d = api(action="query", prop="revisions", rvprop="content", rvslots="main",
                titles="|".join(batch))
        for p in d["query"]["pages"]:
            if "revisions" in p:
                yield p["title"], p["revisions"][0]["slots"]["main"]["content"]
        time.sleep(0.5)  # be polite to Fandom


def clean(value):
    """Wikitext -> plain text: keep link labels, drop refs/templates/markup."""
    code = mwparserfromhell.parse(value)
    for tag in code.filter_tags(recursive=False):
        if str(tag.tag).lower() == "ref":
            try:
                code.remove(tag)
            except ValueError:
                pass
    text = code.strip_code(normalize=True, collapse=True, keep_template_params=False)
    text = re.sub(r"<[^>]+>", " ", text)                 # stray html
    lines = [l.strip(" *#;:").strip() for l in text.splitlines()]
    text = "; ".join(l for l in lines if l)              # bullet lists -> "a; b"
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*;\s*(;\s*)*", "; ", text)
    return text.strip(" ;")


def read_infobox(wikitext, templates):
    code = mwparserfromhell.parse(wikitext)
    for t in code.filter_templates():
        name = str(t.name).strip().replace("_", " ")
        name = name[0].upper() + name[1:] if name else name
        if name in templates:
            params = {str(p.name).strip().lower(): str(p.value) for p in t.params}
            return name, params
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true",
                    help="include every faction, not just the G.I. Joe team")
    ap.add_argument("-o", "--output", default="joepedia_figures.xlsx")
    args = ap.parse_args()

    wanted = INFOBOXES if args.all else {"Joe character infobox": "G.I. Joe"}

    titles = {}
    for tmpl, faction in wanted.items():
        found = pages_using(tmpl)
        print(f"{tmpl}: {len(found)} pages")
        for t in found:
            titles.setdefault(t, faction)

    rows, skipped = [], []
    for n, (title, text) in enumerate(wikitexts(sorted(titles)), 1):
        tmpl, params = read_infobox(text, wanted)
        if params is None:
            skipped.append(title)
            continue
        row = {"Infobox Faction": wanted[tmpl]}
        for col, keys in COLUMNS:
            row[col] = next((clean(params[k]) for k in keys if clean(params.get(k, ""))), "")
        if not row["Code Name"]:
            row["Code Name"] = re.sub(r"\s*\(.*\)$", "", title)
        # The "(RAH)", "(IDW)", "(Movie)" suffix says which version of the character this is.
        m = re.search(r"\(([^)]*)\)$", title)
        row["Version"] = m.group(1) if m else ""
        row["Page"] = title
        row["URL"] = WIKI + title.replace(" ", "_")
        rows.append(row)
        if n % 50 == 0:
            print(f"  parsed {n}/{len(titles)}")

    # Many IDW/movie pages leave the specialty blank. Borrow it from another
    # version of the same code name (RAH first) in its own column, so it is clear
    # the wiki did not list it on that page.
    by_name = {}
    for r in rows:
        if r["Role / Specialty"]:
            by_name.setdefault(r["Code Name"].lower(), []).append(r)
    for r in rows:
        r["Role (other version)"] = ""
        if not r["Role / Specialty"]:
            donors = sorted(by_name.get(r["Code Name"].lower(), []),
                            key=lambda d: (d["Version"] != "RAH", d["Version"]))
            if donors:
                d = donors[0]
                r["Role (other version)"] = f'{d["Role / Specialty"]} [{d["Version"] or "main"}]'

    rows.sort(key=lambda r: (r["Infobox Faction"], r["Code Name"].lower(), r["Version"]))
    header = ["Code Name", "Role / Specialty", "Role (other version)", "Real Name",
              "Infobox Faction", "Version",
              "Rank", "Branch", "Factions", "Sub-teams", "Birthplace", "Gender",
              "First Comic", "First Cartoon", "Page", "URL"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Figures"
    ws.append(header)
    for r in rows:
        ws.append([r.get(h, "") for h in header])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F4F2F")
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    for i, h in enumerate(header, 1):
        width = max([len(h)] + [len(str(r.get(h, ""))) for r in rows])
        ws.column_dimensions[get_column_letter(i)].width = min(max(width + 2, 10), 60)
    for row in ws.iter_rows(min_row=2, min_col=len(header), max_col=len(header)):
        row[0].hyperlink = row[0].value
        row[0].style = "Hyperlink"
    wb.save(args.output)

    csv_path = re.sub(r"\.xlsx$", "", args.output) + ".csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"\n{len(rows)} figures -> {args.output} and {csv_path}")
    with_role = sum(1 for r in rows if r["Role / Specialty"])
    borrowed = sum(1 for r in rows if r["Role (other version)"])
    print(f"{with_role} have a role/specialty listed; {len(rows) - with_role} are blank on the wiki"
          f" ({borrowed} of those filled from another version of the same character)")
    if skipped:
        print(f"{len(skipped)} pages had no readable infobox: {', '.join(skipped[:10])}"
              + (" ..." if len(skipped) > 10 else ""))


if __name__ == "__main__":
    main()
