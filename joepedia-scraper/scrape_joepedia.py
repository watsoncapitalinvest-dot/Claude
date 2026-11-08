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

import io
import os

import mwparserfromhell
from PIL import Image as PILImage
from openpyxl.drawing.image import Image as XLImage
import requests
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
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


def image_file(raw):
    """Infobox image value -> 'File:Name.jpg', or '' if none.

    Usually '[[File:Flint (RAH) 01.jpg|255px]]', sometimes a bare filename."""
    raw = raw.strip()
    m = re.search(r"\[\[\s*(?:File|Image)\s*:\s*([^|\]]+)", raw, re.I)
    name = m.group(1) if m else raw.split("|")[0]
    name = name.strip()
    if not name or "{{" in name or not re.search(r"\.(jpe?g|png|gif|webp|svg)$", name, re.I):
        return ""
    return "File:" + name[0].upper() + name[1:].replace("_", " ")


def image_urls(files, thumb=250):
    """{'File:x.jpg': (full_url, thumb_url)} via the API, 50 at a time."""
    out, files = {}, sorted(set(f for f in files if f))
    for i in range(0, len(files), 50):
        d = api(action="query", prop="imageinfo", iiprop="url", iiurlwidth=thumb,
                titles="|".join(files[i:i + 50]))
        names = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for p in d["query"]["pages"]:
            info = (p.get("imageinfo") or [None])[0]
            if info:
                out[names.get(p["title"], p["title"])] = (info["url"], info.get("thumburl", info["url"]))
        time.sleep(0.5)
    return out


def download_images(rows, folder):
    """Save each row's thumbnail to folder/, return {page: local path}."""
    os.makedirs(folder, exist_ok=True)
    saved = {}
    for n, r in enumerate(rows, 1):
        if not r["Thumbnail URL"]:
            continue
        safe = re.sub(r'[\\/:*?"<>|]+', "_", r["Page"])
        path = os.path.join(folder, safe + ".jpg")
        if not os.path.exists(path):
            try:
                resp = session.get(r["Thumbnail URL"], timeout=30)
                resp.raise_for_status()
                img = PILImage.open(io.BytesIO(resp.content))
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGBA")
                    bg = PILImage.new("RGB", img.size, "white")
                    bg.paste(img, mask=img.split()[-1])
                    img = bg
                img.convert("RGB").save(path, "JPEG", quality=88)
                time.sleep(0.2)
            except Exception as e:  # one bad image should not sink the sheet
                print(f"  image failed for {r['Page']}: {e}", file=sys.stderr)
                continue
        saved[r["Page"]] = path
        if n % 50 == 0:
            print(f"  images {n}/{len(rows)}")
    return saved


PIC_H = 120  # px height of each picture in the sheet


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true",
                    help="include every faction, not just the G.I. Joe team")
    ap.add_argument("-o", "--output", default="joepedia_figures.xlsx")
    ap.add_argument("--images", default=None,
                    help="folder to save pictures in (default: <output name>_images)")
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
        row["_file"] = image_file(params.get("image", ""))
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

    print("looking up image URLs...")
    urls = image_urls([r["_file"] for r in rows])
    for r in rows:
        full, small = urls.get(r["_file"], ("", ""))
        r["Image URL"], r["Thumbnail URL"] = full, small

    rows.sort(key=lambda r: (r["Infobox Faction"], r["Code Name"].lower(), r["Version"]))
    img_dir = args.images or re.sub(r"\.xlsx$", "", args.output) + "_images"
    print(f"downloading pictures to {img_dir}/ ...")
    local = download_images(rows, img_dir)
    for r in rows:
        r["Image File"] = local.get(r["Page"], "")

    header = ["Picture", "Code Name", "Role / Specialty", "Role (other version)", "Real Name",
              "Infobox Faction", "Version",
              "Rank", "Branch", "Factions", "Sub-teams", "Birthplace", "Gender",
              "First Comic", "First Cartoon", "Page", "Image File", "Image URL", "Thumbnail URL", "URL"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Figures"
    ws.append(header)
    for r in rows:
        ws.append([r.get(h, "") for h in header])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F4F2F")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "C2"
    ws.column_dimensions["A"].width = 18
    for i, r in enumerate(rows, start=2):
        if not r["Image File"]:
            continue
        pic = XLImage(r["Image File"])
        scale = PIC_H / pic.height
        if pic.width * scale > 125:          # keep wide images inside the column
            scale = 125 / pic.width
        pic.width, pic.height = int(pic.width * scale), int(pic.height * scale)
        ws.add_image(pic, f"A{i}")
        ws.row_dimensions[i].height = PIC_H * 0.75 + 4   # points, not pixels
    ws.auto_filter.ref = ws.dimensions
    for i, h in enumerate(header, 1):
        if h == "Picture":
            continue
        width = max([len(h)] + [len(str(r.get(h, ""))) for r in rows])
        ws.column_dimensions[get_column_letter(i)].width = min(max(width + 2, 10), 60)
    for col in ("Image URL", "Thumbnail URL", "URL"):
        ci = header.index(col) + 1
        ws.column_dimensions[get_column_letter(ci)].width = 40
        for row in ws.iter_rows(min_row=2, min_col=ci, max_col=ci):
            if row[0].value:
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
    with_img = sum(1 for r in rows if r["Image File"])
    print(f"{with_img} have an image; {len(rows) - with_img} have no picture in their infobox")
    if skipped:
        print(f"{len(skipped)} pages had no readable infobox: {', '.join(skipped[:10])}"
              + (" ..." if len(skipped) > 10 else ""))


if __name__ == "__main__":
    main()
