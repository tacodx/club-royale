"""Complete art-deco asset set for v1.1."""
from deco import *
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np, math, json, os
from deco import _flat

from paths import BUILD, ensure_tables
ensure_tables()
T = json.load(open(BUILD / "tables.json"))
T7 = json.load(open(BUILD / "tables7.json"))
BET_LEVELS = [5, 10, 15, 20, 25, 50, 75, 100, 150, 200, 250,
              500, 750, 1000, 1500, 2000, 2500, 5000]
# the solver proves every payout is an exact integer at every one of these
assert T7["betLevels"] == BET_LEVELS, "bet levels drifted from tables7"
ROWCOUNT = [8, 12, 16]
ROWSP    = [22, 17, 13]
ROWHS    = [34, 26, 21]
RISKNAME = ["low", "med", "high"]
BOMBCOUNT = [1, 3, 5, 10]


def fit(text, size, tracking, avail, f=FB, floor=7):
    """Shrink until the tracked string fits."""
    while size > floor * SC:
        fnt = font(size, f)
        w = sum(fnt.getlength(c) for c in text) + tracking * (len(text) - 1)
        if w <= avail:
            break
        size -= SC
        tracking = max(0.6 * SC, tracking * 0.9)
    return size, tracking


def panel(w, h, cut=None, fill=(16, 11, 16, 240), rule=255, inner=None, width=3):
    img = new(w, h)
    W, H = img.size
    cut = cut if cut is not None else int(min(W, H) * 0.24)
    pts = chamfer_pts([2, 2, W - 3, H - 3], cut)
    if fill:
        ImageDraw.Draw(img).polygon(pts, fill=fill)
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, rule), width=width)
    if inner:
        ld.polygon(chamfer_pts([inner * SC, inner * SC, W - 3 - inner * SC,
                                H - 3 - inner * SC], int(cut * 0.7)),
                   outline=(255, 255, 255, 120), width=1)
    return Image.alpha_composite(img, gold_fill(line)), img.size


# ------------------------------------------------------------- buttons
def deco_button(name, label, w, h, primary=False, fs=13, tracking=5):
    img = new(w, h)
    W, H = img.size
    cut = int(min(W, H) * 0.30)
    pts = chamfer_pts([2, 2, W - 3, H - 3], cut)
    if primary:
        grad = Image.new("RGBA", (W, H))
        gd = ImageDraw.Draw(grad)
        for y in range(H):
            t = y / max(1, H - 1)
            c = (tuple(int(GOLD_D[i] + (GOLD_L[i] - GOLD_D[i]) * (t / .45))
                       for i in range(3)) if t < .45 else
                 tuple(int(GOLD_L[i] + (GOLD[i] - GOLD_L[i]) * ((t - .45) / .55))
                       for i in range(3)))
            gd.line([(0, y), (W, y)], fill=c + (255,))
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        grad.putalpha(m)
        img = Image.alpha_composite(img, grad)
        s, tr = fit(label, fs * SC, tracking * SC, W - 18 * SC)
        tracked(img, (W / 2, H / 2), label, s, tr, color=(30, 16, 8),
                anchor="mm", gold=False)
    else:
        ImageDraw.Draw(img).polygon(pts, fill=(16, 11, 16, 238))
        line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(line).polygon(pts, outline=(255, 255, 255, 255), width=3)
        img = Image.alpha_composite(img, gold_fill(line))
        s, tr = fit(label, fs * SC, tracking * SC, W - 16 * SC)
        tracked(img, (W / 2, H / 2), label, s, tr, anchor="mm")
    return save(img, name)


def round_button(name, glyph, dia):
    img = new(dia, dia)
    W = img.size[0]
    ImageDraw.Draw(img).ellipse([2, 2, W - 3, W - 3], fill=(16, 11, 16, 240))
    line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(line).ellipse([2, 2, W - 3, W - 3],
                                 outline=(255, 255, 255, 255), width=3)
    img = Image.alpha_composite(img, gold_fill(line))
    lay = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((W / 2, W / 2 - 2 * SC), glyph, font=font(20 * SC),
                             fill=(255, 255, 255, 255), anchor="mm")
    img.alpha_composite(gold_fill(lay))
    return save(img, name)


def selector(name, caption, value, w=58, h=38):
    img, (W, H) = panel(w, h, cut=int(h * .26 * SC), rule=225, width=2)
    tracked(img, (W / 2, 12 * SC), caption, 7 * SC, 1.6 * SC,
            color=(152, 130, 98), anchor="mm", gold=False)
    s, tr = fit(value, 13 * SC, 1.2 * SC, W - 10 * SC)
    tracked(img, (W / 2, 26 * SC), value, s, tr, anchor="mm")
    return save(img, name)


def plaque(name, caption, w=52, h=30):
    img, (W, H) = panel(w, h, cut=int(h * .26 * SC), rule=210, width=2)
    tracked(img, (W / 2, H / 2), caption, 8 * SC, 2 * SC, anchor="mm")
    return save(img, name)


def bet_plaque():
    img, (W, H) = panel(96, 38, cut=10 * SC, rule=230, width=2)
    tracked(img, (W / 2, 11 * SC), "BET", 7 * SC, 1.8 * SC,
            color=(152, 130, 98), anchor="mm", gold=False)
    return save(img, "bet_plaque")


# -------------------------------------------------------------- digits
DIGIT_CHARS = list("0123456789") + [".", ","]


def digits():
    w, h = 15, 26
    for i, ch in enumerate(DIGIT_CHARS):
        img = new(w, h)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((img.size[0] / 2, img.size[1] / 2 - SC), ch,
                                 font=font(20 * SC), anchor="mm",
                                 fill=(255, 255, 255, 255))
        img.alpha_composite(gold_fill(lay))
        save(img, f"d{i + 1}")
    blank = new(w, h)
    ImageDraw.Draw(blank).point((0, 0), fill=(0, 0, 0, 1))
    save(blank, f"d{len(DIGIT_CHARS) + 1}")
    # a multiplier "x", appended after the blank so every existing costume
    # index keeps its meaning
    # multiplier "x" and the million / billion suffixes, appended after the
    # blank so every existing costume index keeps its meaning
    for off, ch, size in [(2, "x", 15), (3, "M", 16), (4, "B", 16)]:
        img = new(w, h)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).text((img.size[0] / 2, img.size[1] / 2 - SC), ch,
                                 font=font(size * SC), anchor="mm",
                                 fill=(255, 255, 255, 255))
        img.alpha_composite(gold_fill(lay))
        save(img, f"d{len(DIGIT_CHARS) + off}")


# ---------------------------------------------------------- lobby tiles
TW, TH = 196, 90


def tile(name, label, sub, icon):
    img = new(TW, TH)
    W, H = img.size
    pts = chamfer_pts([2, 2, W - 3, H - 3], 20 * SC)
    ImageDraw.Draw(img).polygon(pts, fill=(18, 11, 15, 242))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([W * .1, H * .15, W * .9, H * 1.4],
                                fill=BURG + (95,))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(60)))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 255), width=3)
    ld.polygon(chamfer_pts([9 * SC, 9 * SC, W - 3 - 9 * SC, H - 3 - 9 * SC],
                           14 * SC), outline=(255, 255, 255, 118), width=1)
    img = Image.alpha_composite(img, gold_fill(line))
    icon(img, (42 * SC, H / 2))
    avail = W - 88 * SC
    s, tr = fit(label, 17 * SC, 2.2 * SC, avail)
    tracked(img, (76 * SC, 38 * SC), label, s, tr, anchor="lm")
    s2, tr2 = fit(sub, 8 * SC, 1.5 * SC, avail, floor=6)
    tracked(img, (77 * SC, 58 * SC), sub, s2, tr2, color=(150, 128, 98),
            anchor="lm", gold=False)
    return save(img, name)


def _gold(img, fn):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(lay))
    img.alpha_composite(gold_fill(lay))


def ic_slots(img, c, s=16 * SC):
    """The 3x3 machine with a payline struck through it. Not three reels and
    a seven: the game has neither any more."""
    x, y = c
    def f(d):
        d.polygon(chamfer_pts([x - s, y - s, x + s, y + s], s * 0.26),
                  outline=(255, 255, 255, 255), width=2)
        for i in (-1, 1):
            d.line([(x + i * s / 3, y - s), (x + i * s / 3, y + s)],
                   fill=(255, 255, 255, 175), width=2)
            d.line([(x - s, y + i * s / 3), (x + s, y + i * s / 3)],
                   fill=(255, 255, 255, 175), width=2)
        d.line([(x - s - 3 * SC, y), (x + s + 3 * SC, y)],
               fill=(255, 255, 255, 255), width=2)
        for cx in (x - 2 * s / 3, x, x + 2 * s / 3):
            r = s * 0.17
            d.ellipse([cx - r, y - r, cx + r, y + r], fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_plinko(img, c):
    x, y = c
    def f(d):
        for r in range(5):
            for i in range(r + 1):
                px, py = x + (i - r / 2) * 10 * SC, y - 16 * SC + r * 7.5 * SC
                d.ellipse([px - 2 * SC, py - 2 * SC, px + 2 * SC, py + 2 * SC],
                          fill=(255, 255, 255, 255))
        d.ellipse([x - 4 * SC, y + 14 * SC, x + 4 * SC, y + 22 * SC],
                  fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_mines(img, c):
    x, y = c
    def f(d):
        for r in range(3):
            for cc in range(3):
                bx, by = x + (cc - 1) * 12 * SC, y + (r - 1) * 12 * SC
                d.polygon(chamfer_pts([bx - 5 * SC, by - 5 * SC,
                                       bx + 5 * SC, by + 5 * SC], 2 * SC),
                          outline=(255, 255, 255, 215), width=2)
        d.ellipse([x - 4 * SC, y - 4 * SC, x + 4 * SC, y + 4 * SC],
                  fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_bj(img, c):
    x, y = c
    d = ImageDraw.Draw(img)
    d.polygon(chamfer_pts([x - 17 * SC, y - 17 * SC, x + 1 * SC, y + 9 * SC],
                          3 * SC), fill=(226, 218, 200, 255))
    d.polygon(chamfer_pts([x - 3 * SC, y - 9 * SC, x + 17 * SC, y + 18 * SC],
                          3 * SC), fill=(244, 238, 224, 255))
    _gold(img, lambda dd: dd.polygon(
        chamfer_pts([x - 3 * SC, y - 9 * SC, x + 17 * SC, y + 18 * SC], 3 * SC),
        outline=(255, 255, 255, 255), width=2))
    d.text((x + 7 * SC, y + 4 * SC), "A", font=font(12 * SC, FS), anchor="mm",
           fill=(28, 16, 22))


def title():
    img = new(300, 64)
    W, H = img.size
    tracked(img, (W / 2, 13 * SC), "CLUB", 11 * SC, 6 * SC, anchor="mm")
    tracked(img, (W / 2, 38 * SC), "ROYALE", 30 * SC, 7 * SC, anchor="mm")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.line([(74 * SC, 56 * SC), (226 * SC, 56 * SC)],
            fill=(255, 255, 255, 200), width=2)
    ld.polygon([(150 * SC, 51 * SC), (156 * SC, 56 * SC),
                (150 * SC, 61 * SC), (144 * SC, 56 * SC)],
               fill=(255, 255, 255, 255))
    img.alpha_composite(gold_fill(lay))
    return save(img, "title")


# --------------------------------------------------------------- slots
# THE GOLD ROOM: a 3x3 grid beside its paytable. Every number the plates are
# cut from lives here and is published to build/geom7.json, so build.py
# positions its sprites from the same constants and the JS harness measures
# against them rather than against a second copy that can drift
# (the assets_v6.py contract).
#
# The vertical band is the binding constraint, not the width: the message
# banner's top edge is y=-81 and the felt's top is y=137, so 218 units hold
# the whole machine. 16 + 182 + 10 fills it with 6 clear below and 4 above.
SL_CELL  = 52                    # the symbol plate itself
SL_WIN   = 58                    # the window cut in the frame behind it
SL_PITCH = 62                    # centre to centre, both axes
SL_FRAME = (206, 208)
SL_FRAME_XY = (-97, 29)
SL_PT = (186, 200)
SL_PT_XY = (107, 29)
SL_BAND_TOP, SL_BAND_BOT = 16, 10        # title band, bottom margin
# grid centre sits below the frame centre by half the difference of the bands
SL_GRID_CY = SL_FRAME_XY[1] - (SL_BAND_TOP - SL_BAND_BOT) / 2
SL_COL_X = [SL_FRAME_XY[0] + (c - 1) * SL_PITCH for c in range(3)]
SL_ROW_Y = [SL_GRID_CY + (1 - r) * SL_PITCH for r in range(3)]
SL_TITLE = "THE GOLD ROOM"

# the four commons share one pay row, so the panel lists six rows, not nine
SL_NAMES = T7["names"]
SL_SYMS = len(SL_NAMES)
SL_PAY3 = T7["pay3"]
SL_PAY2 = T7["pay2"]
SL_LINES = T7["lines"]


def sl_rows():
    """The paytable panel's rows, derived from the solved table.

    Never typed. The old panel hard-coded '50x / 12x / 4x / 1.8x', which was
    the third copy of a table that also lived in build.py and in the harness -
    exactly the drift this rework exists to delete.
    """
    n = len(SL_PAY3)
    lines = len(SL_LINES) // 3
    out = []
    seen = set()
    for i in sorted(range(n), key=lambda i: -SL_PAY3[i]):
        ids = tuple(j + 1 for j in range(n) if SL_PAY3[j] == SL_PAY3[i])
        if ids in seen:
            continue
        seen.add(ids)
        out.append((ids, 3, f"{SL_PAY3[i] / lines:g}x"))
    # The near-miss rung is drawn as ONE row against all of its symbols, which
    # is only honest while they all pay the same. If the solver ever split
    # them, the panel would show one figure against three emblems and look
    # perfectly convincing - so it has to split into rows instead.
    two = [i + 1 for i in range(n) if SL_PAY2[i]]
    for v in sorted({SL_PAY2[i - 1] for i in two}, reverse=True):
        ids = tuple(i for i in two if SL_PAY2[i - 1] == v)
        out.append((ids, 2, f"{v / lines:g}x"))
    return out


# The panel's vertical budget is fixed art; sl_rows() is generated. Nothing
# else notices if the table grows a rung and the last row walks off the
# bottom, so the two are reconciled here, where both are in scope.
SL_PT_ROW_H, SL_PT_HEAD_H, SL_PT_TOP, SL_PT_FOOT = 16.5, 12, 30, 147


def _pt_rows_fit():
    rows = sl_rows()
    runs = len({run for _ids, run, _p in rows})
    # the last row is DRAWN at its baseline and the advance happens after it,
    # so the ink reaches half a row past the final baseline, not a whole one
    last = SL_PT_TOP + (len(rows) - 1) * SL_PT_ROW_H + runs * SL_PT_HEAD_H
    bottom = last + SL_PT_ROW_H / 2
    assert bottom <= SL_PT_FOOT, (
        f"the paytable panel has room for rows down to {SL_PT_FOOT} units, but "
        f"{len(rows)} rows in {runs} groups reach {bottom}. The solved table "
        f"grew a rung - widen SL_PT or tighten SL_PT_ROW_H.")
    return rows


def _geometry7():
    """Publish the numbers the art was drawn from (see assets_v6.py)."""
    json.dump({"cell": SL_CELL, "win": SL_WIN, "pitch": SL_PITCH,
               "frame": SL_FRAME, "frameXY": SL_FRAME_XY,
               "pt": SL_PT, "ptXY": SL_PT_XY,
               "colX": SL_COL_X, "rowY": SL_ROW_Y,
               "title": SL_TITLE},
              open(BUILD / "geom7.json", "w"))


# ------------------------------------------------------- symbol emblems
# One emblem library, two consumers. Every emblem renders into its own
# square tile at whatever radius it is asked for, so the 52-unit reel plate
# and the ~15-unit chip in the paytable come out of the same code: the panel
# cannot drift from the reel the way a second set of drawings would.
#
# Reading order the art has to carry, because the payout table does:
#   WILD   84.8x   a gold lozenge monogram - unmistakable, and the only
#                  symbol that is not an object
#   DIAMOND 14.8x  a solid faceted gem, the brightest object on the reel
#   CROWN / COUPE 6.2x  a matched pair of golds, deliberately the same
#                  weight of gold and deliberately opposite silhouettes
#                  (spiked and top-heavy vs. a shallow bowl on a thin stem)
#   FAN     2.8x   pale gold on the same plate: a visible step down
#   J Q K A   2x   cream letterforms under a shared deco double rule; no
#                  gold at all, so the commons never read as a premium
PALE   = (233, 215, 166)         # the fan: a step below the premium golds
PALE_D = (158, 131, 66)
EMBER  = (26, 17, 5)             # the wild lozenge's ground: dark enough
                                 # for the monogram to be gold ON something

_EMCACHE = {}


def _tile(r):
    """A transparent square big enough for an emblem of radius r."""
    s = int(math.ceil(r * 2.3)) | 1
    return Image.new("RGBA", (s, s), (0, 0, 0, 0)), s / 2.0


def _P(c, r, pairs):
    return [(c + x * r, c + y * r) for x, y in pairs]


def _lay(im):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    return lay, ImageDraw.Draw(lay)


def _lw(r, k=0.075):
    return max(1, int(round(r * k)))


# ---- 1 DIAMOND: a brilliant cut seen from the side, table / girdle / pavilion
_DIA = [(-0.50, -0.46), (0.50, -0.46), (0.86, -0.12), (0.0, 0.86),
        (-0.86, -0.12)]
_DIA_FACET = [[(-0.50, -0.46), (-0.86, -0.12)], [(0.50, -0.46), (0.86, -0.12)],
              [(-0.17, -0.46), (-0.52, -0.12)], [(0.17, -0.46), (0.52, -0.12)],
              [(-0.86, -0.12), (0.86, -0.12)],
              [(-0.52, -0.12), (0.0, 0.86)], [(0.52, -0.12), (0.0, 0.86)],
              [(0.0, -0.12), (0.0, 0.86)]]


def _halo(im, c, r, alpha=76):
    """A soft gold bloom. Only the top two rungs get one, so the two symbols
    that carry the paytable are also the two that glow."""
    lay, d = _lay(im)
    d.ellipse([c - r, c - r, c + r, c + r], fill=GOLD + (alpha,))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(r * 0.42)))


def em_diamond(r):
    im, c = _tile(r)
    _halo(im, c, r * 0.86)
    lay, d = _lay(im)
    d.polygon(_P(c, r, _DIA), fill=(255, 255, 255, 255))
    im.alpha_composite(gold_fill(lay))
    dd = ImageDraw.Draw(im)
    for a, b in _DIA_FACET:
        dd.line(_P(c, r, [a, b]), fill=(26, 17, 6, 205), width=_lw(r, 0.055))
    lay, d = _lay(im)
    d.polygon(_P(c, r, _DIA), outline=(255, 255, 255, 255), width=_lw(r, 0.08))
    im.alpha_composite(_flat(lay, GOLD_L))
    return im


# ---- 2 CROWN: three points on a banded circlet
_CR_BODY = [(-0.80, 0.22), (-0.58, -0.52), (-0.27, 0.00), (0.0, -0.76),
            (0.27, 0.00), (0.58, -0.52), (0.80, 0.22)]
_CR_PEAK = [(-0.58, -0.52), (0.0, -0.76), (0.58, -0.52)]


def em_crown(r):
    im, c = _tile(r)
    lay, d = _lay(im)
    d.polygon(_P(c, r, _CR_BODY), fill=(255, 255, 255, 255))
    d.rectangle(_P(c, r, [(-0.88, 0.24), (0.88, 0.64)]),
                fill=(255, 255, 255, 255))
    for p in _CR_PEAK:
        pr = 0.13 * r
        x, y = c + p[0] * r, c + p[1] * r
        d.ellipse([x - pr, y - pr, x + pr, y + pr], fill=(255, 255, 255, 255))
    im.alpha_composite(gold_fill(lay))
    dd = ImageDraw.Draw(im)
    w = _lw(r, 0.055)
    dd.line(_P(c, r, [(-0.84, 0.44), (0.84, 0.44)]), fill=(26, 17, 6, 190),
            width=w)
    for x in (-0.46, 0.0, 0.46):                 # gems set in the band
        dd.polygon(_P(c, r, [(x, 0.30), (x + 0.09, 0.37), (x, 0.44),
                             (x - 0.09, 0.37)]), fill=(26, 17, 6, 205))
    return im


# ---- 8 COUPE: shallow bowl, thin stem, wide foot - the crown's opposite
def em_coupe(r):
    im, c = _tile(r)
    lay, d = _lay(im)
    d.pieslice(_P(c, r, [(-0.82, -0.88), (0.82, 0.04)]), 0, 180,
               fill=(255, 255, 255, 255))
    d.ellipse(_P(c, r, [(-0.82, -0.56), (0.82, -0.28)]),
              fill=(255, 255, 255, 255))
    d.rectangle(_P(c, r, [(-0.075, -0.10), (0.075, 0.44)]),
                fill=(255, 255, 255, 255))
    d.ellipse(_P(c, r, [(-0.44, 0.38), (0.44, 0.60)]), fill=(255, 255, 255, 255))
    for bx, by, br in ((-0.34, -0.72, 0.080), (0.07, -0.86, 0.065),
                       (0.38, -0.66, 0.055)):
        d.ellipse([c + (bx - br) * r, c + (by - br) * r,
                   c + (bx + br) * r, c + (by + br) * r],
                  fill=(255, 255, 255, 255))
    im.alpha_composite(gold_fill(lay))
    dd = ImageDraw.Draw(im)
    dd.ellipse(_P(c, r, [(-0.70, -0.51), (0.70, -0.33)]),
               outline=(26, 17, 6, 215), width=_lw(r, 0.055))
    return im


# ---- 7 FAN: a deco sunburst fan, pale gold - the step below the premiums
def em_fan(r):
    im, c = _tile(r)
    d = ImageDraw.Draw(im)
    piv = c + 0.48 * r
    R = 0.94 * r
    d.pieslice([c - R, piv - R, c + R, piv + R], 180, 360, fill=PALE + (255,))
    w = _lw(r, 0.06)
    for i in range(9):                            # ribs
        a = math.pi * (1.0 + i / 8.0)
        d.line([(c, piv), (c + math.cos(a) * R, piv + math.sin(a) * R)],
               fill=PALE_D + (255,), width=w)
    d.arc([c - R * 0.66, piv - R * 0.66, c + R * 0.66, piv + R * 0.66],
          180, 360, fill=PALE_D + (255,), width=w)
    d.pieslice([c - R * 0.22, piv - R * 0.22, c + R * 0.22, piv + R * 0.22],
               180, 360, fill=PALE_D + (255,))
    lay, ld = _lay(im)
    ld.pieslice([c - R, piv - R, c + R, piv + R], 180, 360,
                outline=(255, 255, 255, 255), width=max(1, _lw(r, 0.075)))
    im.alpha_composite(_flat(lay, GOLD))
    return im


# ---- 3..6 JACK QUEEN KING ACE: cream deco letterforms, one shared rule
def em_letter(ch, r):
    im, c = _tile(r)
    lay, d = _lay(im)
    d.text((c, c - 0.10 * r), ch, font=font(int(r * 1.62), FB), anchor="mm",
           fill=(255, 255, 255, 255))
    im.alpha_composite(_flat(lay, CREAM))
    lay, d = _lay(im)
    w = max(1, _lw(r, 0.075))
    for y, a in ((0.80, 255), (0.94, 150)):
        d.line(_P(c, r, [(-0.60, y), (0.60, y)]), fill=(255, 255, 255, a),
               width=w if a == 255 else max(1, w // 2))
    d.polygon(_P(c, r, [(-0.72, 0.80), (-0.62, 0.73), (-0.62, 0.87)]),
              fill=(255, 255, 255, 255))
    d.polygon(_P(c, r, [(0.72, 0.80), (0.62, 0.73), (0.62, 0.87)]),
              fill=(255, 255, 255, 255))
    im.alpha_composite(gold_fill(lay))
    return im


# ---- 9 WILD: a W monogram struck inside a gold lozenge
_LOZ = [(0.0, -0.97), (1.0, 0.0), (0.0, 0.97), (-1.0, 0.0)]
_WMON = [(-0.50, -0.36), (-0.30, 0.40), (0.0, -0.08), (0.30, 0.40),
         (0.50, -0.36)]


def em_wild(r):
    im, c = _tile(r)
    # 0.88 ran the blurred halo flush to the tile edge, where draw_emblem's
    # crop cut it square - so the wild was the one plate whose chamfered
    # silhouette washed out into its own corners. Pull it inside the chamfer.
    _halo(im, c, r * 0.70, 78)
    d = ImageDraw.Draw(im)
    d.polygon(_P(c, r, _LOZ), fill=EMBER + (255,))
    lay, ld = _lay(im)
    ld.polygon(_P(c, r, _LOZ), outline=(255, 255, 255, 255),
               width=_lw(r, 0.075))
    ld.line(_P(c, r, _WMON), fill=(255, 255, 255, 255), width=_lw(r, 0.150),
            joint="curve")
    im.alpha_composite(gold_fill(lay))
    return im


_EMBLEM = {1: em_diamond, 2: em_crown, 8: em_coupe, 7: em_fan, 9: em_wild,
           3: lambda r: em_letter("J", r), 4: lambda r: em_letter("Q", r),
           5: lambda r: em_letter("K", r), 6: lambda r: em_letter("A", r)}
# how much of the plate's half-width each emblem is allowed to fill
# The emblem tile is sized ceil(r * 2.3), so a scale above ~0.86 makes a tile
# WIDER than the 52-unit plate; draw_emblem then crops it square and the plate's
# chamfered silhouette washes out into its own corners. symbols() asserts this
# rather than trusting the arithmetic.
_EMSCALE = [0.80, 0.78, 0.74, 0.74, 0.74, 0.74, 0.80, 0.84, 0.84]


def emblem(sid, r):
    r = max(4.0, float(int(round(r))))
    key = (sid, r)
    if key not in _EMCACHE:
        _EMCACHE[key] = _EMBLEM[sid](r)
    return _EMCACHE[key]


def draw_emblem(img, sid, cx, cy, r):
    """Centre an emblem tile on (cx, cy). The tile is sized for the emblem's
    own bounding radius, which for the wild lozenge is a shade wider than the
    52-unit plate, so clip rather than hand Pillow a negative destination -
    some versions accept one and some raise."""
    em = emblem(sid, r)
    x, y = int(round(cx - em.width / 2)), int(round(cy - em.height / 2))
    if x < 0 or y < 0:
        em = em.crop((max(0, -x), max(0, -y), em.width, em.height))
        x, y = max(0, x), max(0, y)
    img.alpha_composite(em, (x, y))


def _plate_pts(units):
    w = int(units * SC)
    cut = max(2 * SC, int(round(units * 0.15)) * SC)
    return w, chamfer_pts([2, 2, w - 3, w - 3], cut)


def _plate(units):
    """The chrome every symbol shares: chamfered near-black, thin gold rule."""
    w, pts = _plate_pts(units)
    img = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon(pts, fill=(13, 9, 13, 240))
    line = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    ImageDraw.Draw(line).polygon(pts, outline=(255, 255, 255, 115),
                                 width=max(2, int(round(units * 0.04))))
    return Image.alpha_composite(img, gold_fill(line))


def _clip_to_plate(img, units):
    """Cut a finished plate back to its own chamfered silhouette.

    An emblem's tile is sized for the emblem, not for the plate, and a soft
    halo spreads to the tile's corners - so the widest emblems reached past
    the chamfer and squared the plate off. Masking here means no emblem can
    do that, whatever radius it is drawn at.
    """
    w, pts = _plate_pts(units)
    mask = Image.new("L", (w, w), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    out = img.copy()
    out.putalpha(Image.fromarray(
        (np.asarray(img.split()[3]).astype(float)
         * np.asarray(mask) / 255).astype("uint8")))
    return out


def symbols():
    """One plate per solved symbol, drawn natively at SL_CELL.

    Natively, not scaled down from the old 82-unit plates: overlap.js
    measures real bounding boxes and tools/mock.py composites at true size,
    so a costume that is not the size it claims lies to both.
    """
    chrome = _plate(SL_CELL).getbbox()
    for sid in range(1, SL_SYMS + 1):
        img = _plate(SL_CELL)
        c = img.size[0] / 2.0
        draw_emblem(img, sid, c, c, c * _EMSCALE[sid - 1])
        img = _clip_to_plate(img, SL_CELL)
        # Nothing may reach past the plate's own chamfered edge. A bleed is
        # invisible in the code and obvious on the reel: the plate stops
        # looking chamfered and starts looking square.
        assert img.getbbox() == chrome, (
            f"sym{sid} ({SL_NAMES[sid - 1]}) inks {img.getbbox()}, but the "
            f"plate is {chrome} - its emblem is bleeding past the chrome. "
            f"Lower _EMSCALE[{sid - 1}].")
        save(img, f"sym{sid}")


def slot_frame():
    """The 3x3 machine. Windows are cut on the published lattice, never by
    eye - build.py puts the Reel clones at the same SL_COL_X / SL_ROW_Y, so
    a window drawn anywhere else shows up as a symbol sitting proud of it."""
    img, (W, H) = panel(SL_FRAME[0], SL_FRAME[1], cut=18 * SC,
                        fill=(13, 9, 13, 236), inner=None, width=3)
    d = ImageDraw.Draw(img)
    cxs = [(x - SL_FRAME_XY[0] + SL_FRAME[0] / 2.0) * SC for x in SL_COL_X]
    cys = [(SL_FRAME_XY[1] - y + SL_FRAME[1] / 2.0) * SC for y in SL_ROW_Y]
    h = SL_WIN / 2.0 * SC
    cut = int(round(SL_WIN * 0.15)) * SC
    for cx in cxs:
        for cy in cys:
            pts = chamfer_pts([cx - h, cy - h, cx + h, cy + h], cut)
            d.polygon(pts, fill=(5, 3, 7, 255))
            _gold(img, lambda dd, p=pts: dd.polygon(
                p, outline=(255, 255, 255, 150), width=2))
    ty = SL_BAND_TOP / 2.0 * SC + 1 * SC
    s, tr = fit(SL_TITLE, 10 * SC, 3.0 * SC, (SL_FRAME[0] - 56) * SC)
    tw = tracked(img, (W / 2, ty), SL_TITLE, s, tr, anchor="mm")
    _gold(img, lambda dd: [dd.polygon(
        [(W / 2 + sgn * (tw / 2 + 9 * SC), ty - 4 * SC),
         (W / 2 + sgn * (tw / 2 + 4 * SC), ty),
         (W / 2 + sgn * (tw / 2 + 9 * SC), ty + 4 * SC),
         (W / 2 + sgn * (tw / 2 + 14 * SC), ty)],
        fill=(255, 255, 255, 235)) for sgn in (-1, 1)])
    return save(img, "slotframe")


def _rule(img, y, x0, x1, alpha=200, w=2):
    _gold(img, lambda d: d.line([(x0, y), (x1, y)],
                                fill=(255, 255, 255, alpha), width=w))


def _line_chip(L, box):
    """One ~22x22 payline diagram, read straight out of SL_LINES."""
    n = int(box * SC)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cells = SL_LINES[L * 3:(L + 1) * 3]
    pitch = n * 0.295
    pip = n * 0.085
    c = n / 2.0

    def xy(cell):
        col, row = (cell - 1) // 3 + 1, (cell - 1) % 3 + 1
        return c + (col - 2) * pitch, c + (row - 2) * pitch

    lay, ld = _lay(im)
    ld.polygon(chamfer_pts([1, 1, n - 2, n - 2], int(n * 0.16)),
               outline=(255, 255, 255, 110), width=1)
    im.alpha_composite(gold_fill(lay))
    for cell in range(1, 10):                       # the dark 3x3 lattice
        x, y = xy(cell)
        d.rectangle([x - pip, y - pip, x + pip, y + pip],
                    outline=(96, 84, 60, 255), width=1)
    lay, ld = _lay(im)
    ld.line([xy(cell) for cell in cells], fill=(255, 255, 255, 255),
            width=max(2, int(n * 0.075)), joint="curve")
    for cell in cells:
        x, y = xy(cell)
        ld.rectangle([x - pip, y - pip, x + pip, y + pip],
                     fill=(255, 255, 255, 255))
    im.alpha_composite(gold_fill(lay))
    return im


def paytable():
    """Generated from sl_rows() and SL_LINES. Not one typed multiplier:
    the old panel hard-coded four, which is exactly how a paytable ends up
    describing a game that no longer pays that way."""
    img, (W, H) = panel(SL_PT[0], SL_PT[1], cut=16 * SC,
                        fill=(13, 9, 13, 236), inner=None, width=3)
    U = SC                                          # one stage unit in px
    tracked(img, (W / 2, 14 * U), "PAYS", 10 * U, 3.2 * U, anchor="mm")
    _rule(img, 22 * U, 16 * U, (SL_PT[0] - 16) * U, alpha=170)

    rows = _pt_rows_fit()
    er = 7.0 * U                                    # mini-emblem radius
    y = SL_PT_TOP * U
    run_shown = None
    for ids, run, pay in rows:
        if run != run_shown:                        # "3 IN A LINE", then "2"
            run_shown = run
            tracked(img, (16 * U, y), f"{run} IN A LINE", 6.5 * U, 1.5 * U,
                    color=(142, 121, 92), anchor="lm", gold=False)
            y += SL_PT_HEAD_H * U
        for i, sid in enumerate(ids):
            draw_emblem(img, sid, (25 + i * 17) * U, y, er)
        tracked(img, ((SL_PT[0] - 16) * U, y), pay, 10 * U, 1.4 * U,
                anchor="rm")
        y += SL_PT_ROW_H * U

    _rule(img, SL_PT_FOOT * U, 16 * U, (SL_PT[0] - 16) * U, alpha=170)
    nl = len(SL_LINES) // 3
    tracked(img, (W / 2, 156 * U), f"{nl} LINES", 7.5 * U, 2.4 * U,
            color=(142, 121, 92), anchor="mm", gold=False)
    box = 22
    gap = (SL_PT[0] - 32 - nl * box) / (nl - 1.0)
    for L in range(nl):
        chip = _line_chip(L, box)
        img.alpha_composite(chip, (int((16 + L * (box + gap)) * U),
                                   int(173 * U - chip.height / 2)))
    return save(img, "paytable")


# -------------------------------------------------------------- plinko
def plinko_board(ri):
    rows, sp, hs = ROWCOUNT[ri], ROWSP[ri], ROWHS[ri]
    w = 380
    top, h = 20, 20 + (rows - 1) * sp + 20
    img = new(w, h)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for r in range(rows):
        n = r + 2
        for i in range(n):
            px = W / 2 + (i - (n - 1) / 2) * hs * SC
            py = (top + r * sp) * SC
            rr = 2.4 * SC
            d.ellipse([px - rr, py - rr, px + rr, py + rr],
                      fill=(255, 255, 255, 255))
    img.alpha_composite(gold_fill(lay))
    return save(img, f"board{rows}")


BUCKET_VALS = sorted({v for t in T["plinko"].values() for v in t})


def buckets():
    w, h = 20, 18
    for i, v in enumerate(BUCKET_VALS, 1):
        img = new(w, h)
        W, H = img.size
        hi, mid = v >= 5, 1.0 <= v < 5
        fill = ((92, 66, 12, 250) if hi else
                ((64, 15, 28, 250) if mid else (15, 10, 15, 242)))
        pts = chamfer_pts([1, 1, W - 2, H - 2], 4 * SC)
        ImageDraw.Draw(img).polygon(pts, fill=fill)
        line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(line).polygon(
            pts, outline=(255, 255, 255, 255 if hi else 145), width=2)
        img = Image.alpha_composite(img, gold_fill(line))
        txt = f"{v:g}"
        s, tr = fit(txt, 8 * SC, 0.3 * SC, W - 3 * SC, floor=5)
        tracked(img, (W / 2, H / 2), txt, s, tr, anchor="mm",
                color=CREAM, gold=not hi)
        save(img, f"bk{i}")


def ball():
    img = new(15, 15)
    W = img.size[0]
    lay = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([3 * SC, 3 * SC, 12 * SC, 12 * SC],
                                fill=(255, 255, 255, 255))
    img.alpha_composite(gold_fill(lay))
    return save(Image.alpha_composite(img.filter(ImageFilter.GaussianBlur(4)),
                                      img), "ball")


# --------------------------------------------------------------- mines
def mine_tiles():
    w = 44
    img = new(w, w); W = img.size[0]; c = W / 2
    pts = chamfer_pts([2, 2, W - 3, W - 3], 9 * SC)
    ImageDraw.Draw(img).polygon(pts, fill=(26, 17, 24, 248))
    lay = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([6 * SC, 4 * SC, W - 6 * SC, W + 4 * SC],
                                fill=BURG + (110,))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(26)))
    img.putalpha(Image.fromarray((np.asarray(img.split()[3]).astype(float) *
                                  np.asarray(_poly_mask((W, W), pts)) / 255
                                  ).astype("uint8")))
    line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 235), width=2)
    ld.polygon([(c, c - 7 * SC), (c + 7 * SC, c), (c, c + 7 * SC),
                (c - 7 * SC, c)], outline=(255, 255, 255, 190), width=2)
    save(Image.alpha_composite(img, gold_fill(line)), "tile_hidden")

    img = new(w, w)
    ImageDraw.Draw(img).polygon(pts, fill=(62, 44, 9, 250))
    line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 255), width=2)
    ld.polygon([(c, c - 12 * SC), (c + 11 * SC, c), (c, c + 12 * SC),
                (c - 11 * SC, c)], fill=(255, 255, 255, 255))
    save(Image.alpha_composite(img, gold_fill(line)), "tile_gem")

    img = new(w, w)
    ImageDraw.Draw(img).polygon(pts, fill=(76, 13, 26, 250))
    line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(line).polygon(pts, outline=(255, 255, 255, 210), width=2)
    img = Image.alpha_composite(img, gold_fill(line))
    ImageDraw.Draw(img).ellipse([c - 10 * SC, c - 8 * SC, c + 10 * SC, c + 12 * SC],
                                fill=(12, 9, 12, 255))
    _gold(img, lambda d: d.line([(c + 5 * SC, c - 8 * SC),
                                 (c + 12 * SC, c - 16 * SC)],
                                fill=(255, 255, 255, 255), width=3))
    save(img, "tile_bomb")


def _poly_mask(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


# --------------------------------------------------------------- cards
RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
SUITS = [("\u2660", (28, 24, 30)), ("\u2665", (162, 26, 44)),
         ("\u2666", (162, 26, 44)), ("\u2663", (28, 24, 30))]
CW, CH = 52, 74


def card_back():
    img = new(CW, CH); W, H = img.size
    pts = chamfer_pts([1, 1, W - 2, H - 2], 7 * SC)
    ImageDraw.Draw(img).polygon(pts, fill=BURG_D + (255,))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([W * .1, H * .1, W * .9, H * .9],
                                fill=BURG + (175,))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(30)))
    img.putalpha(Image.fromarray((np.asarray(img.split()[3]).astype(float) *
                                  np.asarray(_poly_mask((W, H), pts)) / 255
                                  ).astype("uint8")))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 255), width=3)
    ld.polygon(chamfer_pts([6 * SC, 6 * SC, W - 2 - 6 * SC, H - 2 - 6 * SC],
                           5 * SC), outline=(255, 255, 255, 150), width=1)
    cx, cy = W / 2, H / 2
    for k in range(12):
        a = k / 12 * 2 * math.pi
        ld.line([(cx, cy), (cx + math.cos(a) * 15 * SC,
                            cy + math.sin(a) * 15 * SC)],
                fill=(255, 255, 255, 115), width=1)
    ld.polygon([(cx, cy - 9 * SC), (cx + 6 * SC, cy), (cx, cy + 9 * SC),
                (cx - 6 * SC, cy)], outline=(255, 255, 255, 235), width=2)
    return save(Image.alpha_composite(img, gold_fill(line)), "card_back")


def card_face(n):
    r, s = (n - 1) % 13, (n - 1) // 13
    glyph, col = SUITS[s]
    img = new(CW, CH); W, H = img.size
    pts = chamfer_pts([1, 1, W - 2, H - 2], 7 * SC)
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=(243, 237, 222, 255))
    d.polygon(pts, outline=(198, 188, 166, 255), width=2)
    rf = font((14 if len(RANKS[r]) == 1 else 11) * SC, FS)
    sf = font(11 * SC, FR)
    d.text((6 * SC, 5 * SC), RANKS[r], font=rf, fill=col + (255,), anchor="lt")
    d.text((6 * SC, 21 * SC), glyph, font=sf, fill=col + (255,), anchor="lt")
    d.text((W / 2, H / 2 + 3 * SC), glyph, font=font(29 * SC, FR),
           fill=col + (255,), anchor="mm")
    cor = Image.new("RGBA", (22 * SC, 34 * SC), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cor)
    cd.text((2 * SC, 0), RANKS[r], font=rf, fill=col + (255,), anchor="lt")
    cd.text((2 * SC, 16 * SC), glyph, font=sf, fill=col + (255,), anchor="lt")
    img.alpha_composite(cor.rotate(180), (W - 24 * SC, H - 36 * SC))
    return save(img, f"card{n}")


# ------------------------------------------------------------ messages
MESSAGES = [("msg_blank", "", None), ("msg_win", "YOU WIN", GOLD),
            ("msg_lose", "NO WIN", None), ("msg_bust", "BUST", None),
            ("msg_push", "PUSH", GOLD), ("msg_bj", "BLACKJACK", GOLD),
            ("msg_dealer", "DEALER WINS", None), ("msg_boom", "BOOM", None),
            ("msg_cashed", "CASHED OUT", GOLD), ("msg_broke", "NOT ENOUGH CHIPS", None),
            ("msg_bigwin", "BIG WIN", GOLD)]


def messages():
    for name, txt, col in MESSAGES:
        if not txt:
            img = new(240, 46)
            ImageDraw.Draw(img).point((0, 0), fill=(0, 0, 0, 1))
            save(img, name); continue
        img, (W, H) = panel(240, 46, cut=12 * SC,
                            fill=(10, 6, 11, 244) if col else (58, 11, 22, 244),
                            inner=6, width=3)
        s, tr = fit(txt, 17 * SC, 4 * SC, W - 30 * SC)
        tracked(img, (W / 2, H / 2), txt, s, tr, anchor="mm",
                color=CREAM, gold=bool(col))
        save(img, name)


# ---------------------------------------------------------------- main
def build():
    backdrop(); title(); digits(); bet_plaque()
    tile("tile_slots", "SLOTS", f"{len(SL_LINES) // 3} PAYLINES", ic_slots)
    tile("tile_plinko", "PLINKO", "DROP & PRAY", ic_plinko)
    tile("tile_mines", "MINES", "CLIMB OR CASH", ic_mines)
    tile("tile_bj", "BLACKJACK", "BEAT THE HOUSE", ic_bj)
    deco_button("btn_back", "LOBBY", 92, 30, fs=10, tracking=4)
    for n, l in [("spin", "SPIN"), ("drop", "DROP"), ("start", "START"),
                 ("deal", "DEAL")]:
        deco_button("btn_" + n, l, 108, 38, primary=True, fs=15, tracking=6)
    deco_button("btn_hit", "HIT", 96, 38, primary=True, fs=15, tracking=6)
    deco_button("btn_stand", "STAND", 96, 38, fs=14, tracking=4)
    deco_button("btn_cashout", "CASH OUT", 100, 38, fs=11, tracking=3)
    round_button("btn_minus", "\u2212", 38)
    round_button("btn_plus", "+", 38)
    for i, r in enumerate(ROWCOUNT, 1):   selector(f"sel_rows{i}", "ROWS", str(r))
    for i, r in enumerate(["LOW", "MED", "HIGH"], 1):
        selector(f"sel_risk{i}", "RISK", r)
    for i, b in enumerate(BOMBCOUNT, 1):  selector(f"sel_bombs{i}", "BOMBS", str(b))
    plaque("plq_mult", "MULT")
    _geometry7(); symbols(); slot_frame(); paytable()
    for i in range(3): plinko_board(i)
    buckets(); ball(); mine_tiles(); card_back()
    for n in range(1, 53): card_face(n)
    messages()


if __name__ == "__main__":
    build()
    print("assets:", len(os.listdir(OUT)))
    print("bucket costumes:", len(BUCKET_VALS))
