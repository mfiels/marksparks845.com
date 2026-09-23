#!/usr/bin/env python3
"""Build the site: src/ + photos.csv -> public/, minified and fingerprinted.

    pip3 install -r tools/requirements.txt
    python3 tools/build.py
    python3 -m http.server -d public 8000     # preview at http://localhost:8000

GitHub Actions runs this on every push to main and publishes public/.

- Generates gallery.js from photos.csv (caption order = carousel order).
- Minifies every .html, .css, and .js file in src/.
- Appends ?v=<content hash> to every local asset href/src in the pages, and to every photo
  URL in gallery.js, so browsers refetch a file as soon as it changes.
"""

import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

try:
    import minify_html
    import rcssmin
    import rjsmin
    from PIL import Image
except ImportError:
    sys.exit("Missing build dependencies: pip3 install -r tools/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "public"
CSV = ROOT / "photos.csv"
ASSET_DIRS = ["photos", "icons", "fonts"]
ROOT_FILES = ["robots.txt", "contact.vcf"]   # served as-is at the site root


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def versioned(rel):
    return f"{rel}?v={fingerprint(OUT / rel)}"


def gallery_js():
    with CSV.open(newline="") as f:
        rows = list(csv.DictReader(f))
    gallery = []
    for r in rows:
        stem = r["file"]
        full = f"photos/{stem}-2000.webp"
        if not (OUT / full).exists():
            sys.exit(f"photos.csv lists {stem}, but src/{full} is missing")
        with Image.open(OUT / full) as im:
            w, h = im.size
        gallery.append({
            "thumb": versioned(f"photos/{stem}-800.webp"),
            "full": versioned(full),
            "w": w,
            "h": h,
            "caption": r["caption"],
            "town": r["town"],
        })
    return "window.GALLERY=" + json.dumps(gallery, separators=(",", ":")) + ";\n"


def stamp(html):
    """Fingerprint every local href/src that points at a built asset (not other pages)."""
    def repl(m):
        attr, url = m.group(1), m.group(2)
        if not url.endswith(".html") and (OUT / url).is_file():
            return f'{attr}="{versioned(url)}"'
        return m.group(0)
    return re.sub(r'\b(href|src)="([^":#?]+)"', repl, html)


def stamp_css(css):
    """Fingerprint local url(...) references, so the font URL matches the page's preload."""
    def repl(m):
        q, url = m.group(1), m.group(2)
        if (OUT / url).is_file():
            return f"url({q}{versioned(url)}{q})"
        return m.group(0)
    return re.sub(r"""url\((["']?)([^"')?#:]+)\1\)""", repl, css)


def write(rel, text):
    (OUT / rel).write_text(text)
    return (OUT / rel).stat().st_size


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for d in ASSET_DIRS:
        shutil.copytree(SRC / d, OUT / d)
    for name in ROOT_FILES:
        shutil.copyfile(SRC / name, OUT / name)

    sizes = {}
    sizes["gallery.js"] = write("gallery.js", gallery_js())
    for src in sorted(SRC.glob("*.css")):
        sizes[src.name] = write(src.name, stamp_css(rcssmin.cssmin(src.read_text())))
    for src in sorted(SRC.glob("*.js")):
        sizes[src.name] = write(src.name, rjsmin.jsmin(src.read_text()))

    # Assets first, so the pages can fingerprint their final (minified) contents.
    for src in sorted(SRC.glob("*.html")):
        sizes[src.name] = write(src.name, minify_html.minify(
            stamp(src.read_text()), minify_css=True, minify_js=True,
            keep_closing_tags=True, keep_html_and_head_opening_tags=True,
        ))

    for name, size in sizes.items():
        src = SRC / name
        before = f"{src.stat().st_size:>7,} -> " if src.exists() else " " * 11
        print(f"  {name:<12}{before}{size:>7,} bytes")
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"public/ built: {total / 1024:,.0f} KB")


if __name__ == "__main__":
    main()
