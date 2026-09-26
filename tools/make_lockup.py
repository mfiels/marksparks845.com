#!/usr/bin/env python3
"""Build the hero lockup (M⚡S mark, name, amber rule, trades line) as one inline SVG.

    pip3 install fonttools brotli uharfbuzz
    python3 tools/make_lockup.py      # rewrites the <svg class="lockup-art"> in src/index.html

The text is drawn from Inter's glyph outlines, kerned the way browsers set it, so the
lockup paints in its final form on the first frame: no web font to wait for, nothing to
measure in the page. Every row spans the name's ink exactly. Vertical spacing follows the CSS
boxes the rows used as live text: line-height 1, gaps in em of the name size.
"""

import io
import re
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from make_mark import BOLT, BOLT_H, BOLT_HEIGHT, BOLT_W, GAP
from make_mark import WEIGHT as MARK_WEIGHT

TOOLS = Path(__file__).resolve().parent
FONT = TOOLS / "inter-latin.woff2"
PAGE = TOOLS.parent / "src" / "index.html"

NAME, NAME_WEIGHT, NAME_TRACKING = "MARK SPARKS LLC", 650, 0.18
TRADES, TRADES_WEIGHT, TRADES_TRACKING = "ELECTRICAL · SMART HOME · CARPENTRY", 500, 0.2
ACCENT_CHARS = "·"
MARK_GAP, NAME_GAP, RULE_GAP = 0.62, 0.44, 0.44   # ems of the name size, as in the CSS
RULE_HEIGHT = 0.1
UNIT = 100        # SVG units per em of the name size
DIGITS = 1


def load():
    tt = TTFont(FONT)
    tt.flavor = None                                   # harfbuzz reads TTF, not WOFF2
    buf = io.BytesIO()
    tt.save(buf)
    font = hb.Font(hb.Face(buf.getvalue()))
    upm = tt["head"].unitsPerEm
    # Baseline within a line-height: 1 box: half-leading (negative for Inter) plus ascent.
    asc, desc = tt["hhea"].ascent, -tt["hhea"].descent
    baseline = ((upm - asc - desc) / 2 + asc) / upm
    return font, upm, baseline


def outline(font, gid, scale, dx, dy):
    """SVG path and ink bounds for a glyph, scaled, translated, and flipped to y-down."""
    pen = SVGPathPen(None, ntos=lambda v: f"{round(v, DIGITS):g}")
    bounds = BoundsPen(None)
    t = (scale, 0, 0, -scale, dx, dy)
    font.draw_glyph_with_pen(gid, TransformPen(pen, t))
    font.draw_glyph_with_pen(gid, TransformPen(bounds, t))
    return pen.getCommands(), bounds.bounds


def shape(font, upm, text, weight, tracking):
    """Glyph ids, pen x positions (font units), and source characters, as a browser sets it."""
    font.set_variations({"wght": weight})
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    x, glyphs = 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        glyphs.append((info.codepoint, x + pos.x_offset, text[info.cluster]))
        x += pos.x_advance + tracking * upm            # CSS letter-spacing follows every glyph
    return glyphs


def ink_span(font, glyphs):
    lo, hi = float("inf"), float("-inf")
    for gid, x, _ in glyphs:
        _, b = outline(font, gid, 1, x, 0)
        if b:
            lo, hi = min(lo, b[0]), max(hi, b[2])
    return lo, hi


class Row:
    """One line of text: shared glyph shapes go in <defs>, placed with <use>."""

    def __init__(self, font, upm, key, text, weight, tracking):
        self.font, self.key = font, key
        self.weight, self.glyphs = weight, shape(font, upm, text, weight, tracking)
        self.left, self.right = ink_span(font, self.glyphs)

    def render(self, scale, x0, baseline, defs):
        """Draw with the ink's left edge at x0; returns <use> elements."""
        self.font.set_variations({"wght": self.weight})
        uses = []
        for gid, x, ch in self.glyphs:
            ref = f"{self.key}{gid}"
            if ref not in defs:
                d, b = outline(self.font, gid, scale, 0, 0)
                if not b:
                    continue                           # space
                defs[ref] = d
            cls = ' class="accent"' if ch in ACCENT_CHARS else ""
            px = x0 + (x - self.left) * scale
            uses.append(f'<use href="#{ref}" x="{px:.{DIGITS}f}" y="{baseline:.{DIGITS}f}"{cls}/>')
        return uses


def mark(font, width):
    """The M⚡S row, `width` wide, top at y=0; returns (svg elements, height)."""
    font.set_variations({"wght": MARK_WEIGHT})
    gM, gS = font.get_nominal_glyph(ord("M")), font.get_nominal_glyph(ord("S"))
    _, bM = outline(font, gM, 1, 0, 0)                 # y-down: bounds[1] is the top
    _, bS = outline(font, gS, 1, 0, 0)
    top, bot = min(bM[1], bS[1]), max(bM[3], bS[3])
    cap = bot - top
    wM, wS = bM[2] - bM[0], bS[2] - bS[0]
    bolt_h = BOLT_HEIGHT * cap
    bolt_w = bolt_h * BOLT_W / BOLT_H
    gap = GAP * cap
    s = width / (wM + gap + bolt_w + gap + wS)
    dM, _ = outline(font, gM, s, -bM[0] * s, -top * s)
    bx = (wM + gap) * s
    by = (cap - bolt_h) / 2 * s
    sx = bx + (bolt_w + gap) * s
    dS, _ = outline(font, gS, s, sx - bS[0] * s, -top * s)
    k = bolt_h * s / BOLT_H
    return [
        f'<path d="{dM}"/>',
        f'<path class="accent" transform="translate({bx:.2f} {by:.2f}) scale({k:.5f})" d="{BOLT}"/>',
        f'<path d="{dS}"/>',
    ], cap * s


def main():
    font, upm, baseline = load()
    name = Row(font, upm, "n", NAME, NAME_WEIGHT, NAME_TRACKING)
    trades = Row(font, upm, "t", TRADES, TRADES_WEIGHT, TRADES_TRACKING)

    em = UNIT / upm                                    # SVG units per font unit at name size
    width = (name.right - name.left) * em
    t_scale = width / (trades.right - trades.left)     # trades size that matches the name's ink
    t_em = t_scale * upm / UNIT                        # ... in ems of the name size

    defs, body = {}, []
    parts, mark_h = mark(font, width)
    body += parts
    y = mark_h + MARK_GAP * UNIT
    body += name.render(em, 0, y + baseline * UNIT, defs)
    y += UNIT + NAME_GAP * UNIT
    rh = RULE_HEIGHT * UNIT
    body.append(f'<rect class="accent" y="{y:.2f}" width="{width:.2f}" height="{rh:.2f}" rx="{rh / 2:.2f}"/>')
    y += rh + RULE_GAP * UNIT
    body += trades.render(t_scale, 0, y + baseline * t_em * UNIT, defs)
    height = y + t_em * UNIT

    ind = " " * 10
    svg = (
        f'<svg class="lockup-art" viewBox="0 0 {width:.2f} {height:.2f}" aria-hidden="true" focusable="false">\n'
        f"{ind}<defs>\n"
        + "".join(f'{ind}  <path id="{k}" d="{d}"/>\n' for k, d in defs.items())
        + f"{ind}</defs>\n"
        + "".join(f"{ind}{e}\n" for e in body)
        + " " * 8 + "</svg>"
    )
    html = PAGE.read_text()
    html, n = re.subn(r'<svg class="lockup-art".*?</svg>', lambda _: svg, html, flags=re.S)
    if n != 1:
        raise SystemExit(f'expected one <svg class="lockup-art"> in {PAGE}, found {n}')
    PAGE.write_text(html)
    print(f"lockup: {width / UNIT:.4f}em wide, name ink starts {name.left / upm:.4f}em in; "
          f"trades at {t_em:.5f}em; {len(svg):,} bytes")


if __name__ == "__main__":
    main()
