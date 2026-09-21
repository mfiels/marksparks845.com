#!/usr/bin/env python3
"""Build the M⚡S favicon artwork as SVG from Inter's actual glyph outlines.

    pip3 install fonttools brotli
    python3 tools/make_mark.py        # then: node tools/render_images.js

Spacing is computed from each glyph's ink bounds, not its advance width, so the gaps on
either side of the bolt are identical and the whole mark is centered on the tile.
Writes tools/icons/icon.svg (rounded tile) and tools/icons/apple-touch-icon.svg (square;
iOS rounds the corners itself).
"""

from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

TOOLS = Path(__file__).resolve().parent
FONT = TOOLS / "inter-latin.woff2"
OUT = TOOLS / "icons"

SIZE = 512
INK, CREAM, AMBER = "#141414", "#f6f5f1", "#d0801c"
WEIGHT = 780
ROW_WIDTH = 0.74 * SIZE          # M + gap + bolt + gap + S, as a share of the tile
GAP = 0.15                       # ink gap either side of the bolt, as a share of cap height
BOLT_HEIGHT = 0.86               # bolt height as a share of cap height
BOLT = "M10 0 L0 17 H7 L5 30 L17 11 H9.5 Z"   # 17 x 30 units, the site's bolt
BOLT_W, BOLT_H = 17, 30


def glyph(font, name):
    gs = font.getGlyphSet()
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    return gs[name], bp.bounds  # (xMin, yMin, xMax, yMax) in font units


def path_for(g, scale, dx, dy):
    """SVG path for glyph g, scaled and translated, with the y axis flipped."""
    pen = SVGPathPen(None)
    g.draw(TransformPen(pen, (scale, 0, 0, -scale, dx, dy)))
    return pen.getCommands()


def main():
    font = instantiateVariableFont(TTFont(FONT), {"wght": WEIGHT})
    gM, bM = glyph(font, "M")
    gS, bS = glyph(font, "S")
    cap_top, cap_bot = max(bM[3], bS[3]), min(bM[1], bS[1])
    cap = cap_top - cap_bot                           # font units, including S overshoot

    # Solve for the scale that makes the row exactly ROW_WIDTH wide.
    wM, wS = bM[2] - bM[0], bS[2] - bS[0]
    bolt_h_u = BOLT_HEIGHT * cap
    bolt_w_u = bolt_h_u * BOLT_W / BOLT_H
    gap_u = GAP * cap
    row_u = wM + gap_u + bolt_w_u + gap_u + wS
    s = ROW_WIDTH / row_u

    x0 = (SIZE - row_u * s) / 2
    y_base = (SIZE + cap * s) / 2 + cap_bot * s       # baseline so caps sit centered
    parts = [
        f'<path fill="{CREAM}" d="{path_for(gM, s, x0 - bM[0] * s, y_base)}"/>',
    ]
    bx = x0 + (wM + gap_u) * s
    bh = bolt_h_u * s
    by = (SIZE - bh) / 2
    parts.append(
        f'<path fill="{AMBER}" transform="translate({bx:.3f} {by:.3f}) scale({bh / BOLT_H:.5f})" d="{BOLT}"/>'
    )
    sx = bx + (bolt_w_u + gap_u) * s
    parts.append(f'<path fill="{CREAM}" d="{path_for(gS, s, sx - bS[0] * s, y_base)}"/>')
    body = "\n  ".join(parts)

    for name, radius in (("icon.svg", 112), ("apple-touch-icon.svg", 0)):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
            f'viewBox="0 0 {SIZE} {SIZE}">\n'
            f'  <rect width="{SIZE}" height="{SIZE}" rx="{radius}" fill="{INK}"/>\n  {body}\n</svg>\n'
        )
        (OUT / name).write_text(svg)
    print(f"wrote {OUT/'icon.svg'} and {OUT/'apple-touch-icon.svg'}")


if __name__ == "__main__":
    main()
