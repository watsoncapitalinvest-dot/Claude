#!/usr/bin/env python3
"""Scrape YoJoe.com's 3 3/4" vehicle archive into a spreadsheet with pictures.

YoJoe lists vehicles by year (/vehicles/85/ ...) in sections — Vehicles, Small
Vehicles, Battle Stations, Mail-In ... — with a photo of each toy. Every vehicle
has its own page carrying the full toy name, YoJoe ID, series, driver/pilot and
a release note. This reads every year page plus the convention page, then each
vehicle page, and writes an .xlsx (photo in the first column) and a .csv.

  python3 scrape_yojoe_vehicles.py
  python3 scrape_yojoe_vehicles.py -o vehicles.xlsx --width 250

Needs: pip install requests beautifulsoup4 openpyxl pillow
"""
import argparse
import csv
import io
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

BASE = "https://www.yojoe.com"
UA = "yojoe-vehicle-sheet/1.0 (personal collection list)"
PIC_H = 110  # px height of each picture in the sheet

session = requests.Session()
session.headers["User-Agent"] = UA


def get(url, binary=False):
    for attempt in range(5):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            time.sleep(0.4)  # be polite
            return r.content if binary else r.text
        except requests.RequestException as e:
            if attempt == 4:
                print(f"  gave up on {url}: {e}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)


def absolute(href):
    href = href.strip()
    if href.startswith("http"):
        return href.replace("vehicles//", "vehicles/")
    return BASE + "/" + href.lstrip("/")


def year_label(code):
    if code == "convention":
        return "Convention"
    y = int(code)
    return str(1900 + y if y >= 80 else 2000 + y)


def index_pages():
    html = get(BASE + "/vehicles/")
    codes = sorted(set(re.findall(r'href="[^"]*/vehicles/+(\d{2})/"', html)),
                   key=lambda c: (int(c) < 80, int(c)))
    return codes + ["convention"]


def listing(code):
    """Vehicles on one year page: (url, name, photo path, section)."""
    html = get(f"{BASE}/vehicles/{code}/")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    out, section = [], ""
    # Walk the page in order so each box picks up the section header above it.
    for el in soup.find_all(["div"]):
        style = el.get("style") or ""
        if "top:-10px" in style:
            section = el.get_text(" ", strip=True)
        elif "vehicleBox" in (el.get("class") or []):
            links = [a for a in el.find_all("a", href=True) if "/vehicles/" in a["href"]]
            img = el.find("img")
            name = next((a.get_text(strip=True) for a in links if a.get_text(strip=True)), "")
            if not links:
                continue
            photo = ""
            if img and img.get("src"):
                # /images/resize/w/180/vehicles/85/x/y.jpg -> vehicles/85/x/y.jpg
                photo = re.sub(r"^.*?/images/resize/w/\d+/", "", absolute(img["src"]))
            out.append((absolute(links[0]["href"]), name, photo, section))
    return out


def detail(url):
    html = get(url)
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="titleBoxSection") or soup
    d = {}
    h1 = box.find("h1")
    d["Toy Name"] = h1.get_text(" ", strip=True) if h1 else ""
    p = h1.find_next("p") if h1 else None
    if p:
        sub = p.find(string=True, recursive=False)
        d["Subtitle"] = re.sub(r"\s+", " ", sub or "").strip()
    text = box.get_text("\n", strip=True)
    m = re.search(r"YoJoe ID:\s*\n?\s*([\w-]+)", text)
    d["YoJoe ID"] = m.group(1) if m else ""
    m = re.search(r"Series:\s*\n?\s*([^\n]+)", text)
    d["Series"] = m.group(1).strip() if m else ""
    # The subtitle <p> is never closed, so it swallows the whole block; keep
    # only the innermost paragraphs, once each.
    paras = [q.get_text(" ", strip=True) for q in box.find_all("p") if not q.find("p")]
    paras = [q for q in paras if len(q) > 40 and "YoJoe ID" not in q]
    d["Release Notes"] = re.sub(r"\s+([.,])", r"\1", " ".join(dict.fromkeys(paras)))
    tag = box.find("span", style=re.compile("small-caps"))
    d["Box Tagline"] = tag.get_text(" ", strip=True) if tag else ""
    drivers = [h.get_text(" ", strip=True).split(":", 1)[1].strip()
               for h in soup.find_all("h2") if h.get_text().strip().startswith("Driver/Pilot")]
    d["Driver / Pilot"] = "; ".join(dict.fromkeys(drivers))
    page = soup.get_text(" ", strip=True)
    m = re.search(r"([\d,]+) People Have It", page)
    d["Collectors Have It"] = int(m.group(1).replace(",", "")) if m else ""
    m = re.search(r"([\d,]+) People Want It", page)
    d["Collectors Want It"] = int(m.group(1).replace(",", "")) if m else ""
    return d


def save_photo(photo_path, dest, width):
    data = get(f"{BASE}/images/resize/w/{width}/{photo_path}", binary=True)
    if not data:
        return False
    try:
        img = PILImage.open(io.BytesIO(data))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            bg = PILImage.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1])
            img = bg
        img.convert("RGB").save(dest, "JPEG", quality=88)
        return True
    except Exception as e:
        print(f"  bad image {photo_path}: {e}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-o", "--output", default="yojoe_vehicles.xlsx")
    ap.add_argument("--width", type=int, default=250, help="picture width to download")
    ap.add_argument("--images", default=None, help="picture folder (default <output>_images)")
    args = ap.parse_args()
    img_dir = args.images or re.sub(r"\.xlsx$", "", args.output) + "_images"
    os.makedirs(img_dir, exist_ok=True)

    rows, seen = [], set()
    for code in index_pages():
        items = listing(code)
        print(f"{year_label(code)}: {len(items)} vehicles")
        for url, name, photo, section in items:
            if url in seen:
                continue
            seen.add(url)
            row = {"Name": name, "Year": year_label(code), "Category": section,
                   "URL": url, "_photo": photo}
            row.update(detail(url))
            slug = re.sub(r"[^a-z0-9]+", "-", url.split("/vehicles/")[1].lower()).strip("-")
            dest = os.path.join(img_dir, slug + ".jpg")
            if photo and (os.path.exists(dest) or save_photo(photo, dest, args.width)):
                row["Image File"] = dest
                row["Image URL"] = f"{BASE}/images/resize/w/{args.width}/{photo}"
            else:
                row["Image File"] = row["Image URL"] = ""
            rows.append(row)

    header = ["Picture", "Name", "Year", "Category", "Subtitle", "Driver / Pilot",
              "Series", "Box Tagline", "Release Notes", "Collectors Have It",
              "Collectors Want It", "YoJoe ID", "Image File", "Image URL", "URL"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Vehicles"
    ws.append(header)
    for r in rows:
        ws.append([r.get(h, "") for h in header])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2F4F2F")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical="center", wrap_text=True)
    widths = {"Picture": 26, "Name": 26, "Year": 11, "Category": 18, "Subtitle": 32,
              "Driver / Pilot": 26, "Series": 18, "Box Tagline": 34, "Release Notes": 60,
              "Collectors Have It": 11, "Collectors Want It": 11, "YoJoe ID": 28,
              "Image File": 30, "Image URL": 40, "URL": 40}
    for i, h in enumerate(header, 1):
        ws.column_dimensions[get_column_letter(i)].width = widths[h]
    for i, r in enumerate(rows, start=2):
        ws.row_dimensions[i].height = PIC_H * 0.75 + 6
        if not r["Image File"]:
            continue
        pic = XLImage(r["Image File"])
        scale = min(PIC_H / pic.height, 180 / pic.width)  # fit inside the cell
        pic.width, pic.height = int(pic.width * scale), int(pic.height * scale)
        ws.add_image(pic, f"A{i}")
    for col in ("Image URL", "URL"):
        ci = header.index(col) + 1
        for row in ws.iter_rows(min_row=2, min_col=ci, max_col=ci):
            if row[0].value:
                row[0].hyperlink = row[0].value
                row[0].style = "Hyperlink"
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(args.output)

    csv_path = re.sub(r"\.xlsx$", "", args.output) + ".csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header[1:], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    with_img = sum(1 for r in rows if r["Image File"])
    print(f"\n{len(rows)} vehicles -> {args.output} and {csv_path}; {with_img} with a picture")


if __name__ == "__main__":
    main()
