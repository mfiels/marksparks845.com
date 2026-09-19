#!/usr/bin/env python3
"""Turn original photos into web images in src/. Runs locally; needs the originals.

    pip3 install pillow pillow-heif      # pillow-heif only needed for iPhone .heic
    python3 tools/process_photos.py

For every original in photos-src/:
  - applies EXIF orientation, then strips all metadata (GPS included)
  - writes src/photos/<name>-800.webp (carousel/grid) and <name>-2000.webp (lightbox)
  - adds a row for it at the top of photos.csv if it's new

A source named about.* becomes src/photos/about-1200.webp instead of a carousel photo.

Also sizes the icon masters in tools/icons/ (from render_images.js) into src/icons/.

photos.csv controls captions and order. To drop a photo, delete it from photos-src/ and
src/photos/, then delete its row.
"""

import csv
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is required: pip3 install pillow")

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC = True
except ImportError:
    HEIC = False

ROOT = Path(__file__).resolve().parent.parent
ORIGINALS = ROOT / "photos-src"
PHOTOS = ROOT / "src" / "photos"
ICONS = ROOT / "src" / "icons"
MASTERS = ROOT / "tools" / "icons"
CSV = ROOT / "photos.csv"

SIZES = {"800": 800, "2000": 2000}
ABOUT = "about"
QUALITY = 80
EXTS = {".jpg", ".jpeg", ".png", ".webp"} | ({".heic", ".heif"} if HEIC else set())
FIELDS = ["file", "caption", "town", "category"]
# (master in tools/icons, output in src/icons, size)
ICON_SIZES = [
    ("icon-512.png", "favicon-32.png", 32),
    ("icon-512.png", "icon-192.png", 192),
    ("apple-touch-icon-512.png", "apple-touch-icon.png", 180),
]


def stale(src, dst):
    return not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime


def load_clean(path):
    """Open, rotate upright, and return a copy with no metadata attached."""
    with Image.open(path) as im:
        icc = im.info.get("icc_profile")  # color profile only, no location data
        upright = ImageOps.exif_transpose(im).convert("RGB")
        # Copy pixels into a fresh image so no EXIF/XMP/GPS can ride along in .info
        clean = Image.new("RGB", upright.size)
        clean.paste(upright)
    return clean, icc


def save_webp(im, icc, long_edge, dst):
    out = im.copy()
    out.thumbnail((long_edge, long_edge), Image.LANCZOS)
    out.save(dst, "WEBP", quality=QUALITY, method=6, icc_profile=icc)


def process(src):
    """Write every size for one original, skipping ones already up to date."""
    stem = src.stem.lower().replace(" ", "-")
    targets = {1200: PHOTOS / f"{stem}-1200.webp"} if stem == ABOUT else {
        size: PHOTOS / f"{stem}-{key}.webp" for key, size in SIZES.items()
    }
    im = icc = None
    for size, dst in targets.items():
        if stale(src, dst):
            if im is None:
                im, icc = load_clean(src)
            save_webp(im, icc, size, dst)
    return stem


def make_icons():
    for master, out, size in ICON_SIZES:
        src, dst = MASTERS / master, ICONS / out
        if not src.exists():
            print(f"! tools/icons/{master} missing; run node tools/render_images.js")
            continue
        if stale(src, dst):
            with Image.open(src) as im:
                im.resize((size, size), Image.LANCZOS).save(dst, optimize=True)


def main():
    if not HEIC and ORIGINALS.exists() and any(
        p.suffix.lower() in {".heic", ".heif"} for p in ORIGINALS.iterdir()
    ):
        print("! .heic files found but pillow-heif isn't installed; skipping them")

    PHOTOS.mkdir(parents=True, exist_ok=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    ORIGINALS.mkdir(exist_ok=True)

    rows = []
    if CSV.exists():
        with CSV.open(newline="") as f:
            rows = list(csv.DictReader(f))
    known = {r["file"] for r in rows}

    new_rows = []
    for src in sorted(ORIGINALS.iterdir()):
        if src.suffix.lower() not in EXTS:
            continue
        stem = process(src)
        if stem != ABOUT and stem not in known:
            new_rows.append({"file": stem, "caption": "", "town": "", "category": ""})
            print(f"+ {stem}  (add a caption in photos.csv)")

    with CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(new_rows + rows)

    make_icons()
    print("photos processed; run python3 tools/build.py to rebuild the site")


if __name__ == "__main__":
    main()
