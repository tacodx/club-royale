"""v4 additions: Aviamasters — sea and sky, the seaplane, ships, the wake.

As with assets_v3, the geometry lives here so the art and the sprite
coordinates in build.py cannot drift apart.
"""
from deco import *
from assets_v11 import fit, panel, deco_button, selector
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, math, json

from paths import BUILD, ensure_tables
ensure_tables()
T4 = json.load(open(BUILD / "tables4.json"))
AUTO = T4["auto"]

# ------------------------------------------------------------- geometry
SEA_W, SEA_H = 420, 210            # panel centred on the stage origin
HORIZON = -21                      # stage y where sky meets water
SHIP_Y = -58                       # ships ride here
PLANE_X0, PLANE_Y0 = -150, -44     # on the water, before take-off
PLANE_X1, PLANE_Y1 = 100, 46       # fully climbed
MULT_XY = (0, 92)                  # the big readout
MULT_GAP = 24                      # digit spacing at 170% size

SKY_HI = (26, 12, 24)
SKY_LO = (74, 20, 38)
SEA_HI = (30, 12, 26)
SEA_LO = (12, 7, 14)


# ============================================================ sea and sky
def sea_panel():
    img = new(SEA_W, SEA_H)
    W, H = img.size
    d = ImageDraw.Draw(img)
    pts = chamfer_pts([2, 2, W - 3, H - 3], 14 * SC)

    # horizon in panel-local pixels
    hy = int((105 - HORIZON) * SC)

    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        if y < hy:                                   # sky, dark at the top
            t = y / max(1, hy - 1)
            c = tuple(int(SKY_HI[i] + (SKY_LO[i] - SKY_HI[i]) * (t ** 1.5))
                      for i in range(3))
        else:                                        # water, darkening down
            t = (y - hy) / max(1, H - hy - 1)
            c = tuple(int(SEA_HI[i] + (SEA_LO[i] - SEA_HI[i]) * t)
                      for i in range(3))
        gd.line([(0, y), (W, y)], fill=c + (252,))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    grad.putalpha(m)
    img = Image.alpha_composite(img, grad)

    # a low sun behind the horizon
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([W * .34, hy - 46 * SC, W * .66, hy + 14 * SC],
                                fill=GOLD + (60,))
    lay = lay.filter(ImageFilter.GaussianBlur(30))
    lay.putalpha(Image.fromarray(
        (np.asarray(lay.split()[3]).astype(float) *
         np.asarray(m) / 255).astype("uint8")))
    img = Image.alpha_composite(img, lay)

    d = ImageDraw.Draw(img)
    # the horizon itself
    d.line([(6 * SC, hy), (W - 6 * SC, hy)], fill=GOLD + (120,), width=2)

    # wave rules: longer and sparser near the horizon, shorter and denser below
    rng = np.random.default_rng(11)
    y = hy + 7 * SC
    while y < H - 7 * SC:
        depth = (y - hy) / max(1, H - hy)
        n = int(3 + depth * 7)
        for _ in range(n):
            wx = rng.integers(10 * SC, W - 26 * SC)
            wl = int((7 + depth * 16) * SC)
            d.line([(wx, y), (wx + wl, y)],
                   fill=CREAM + (int(26 + 44 * depth),), width=2)
        y += int((5 + depth * 7) * SC)

    # the outer rule, matching every other panel
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 240), width=3)
    ld.polygon(chamfer_pts([7 * SC, 7 * SC, W - 3 - 7 * SC, H - 3 - 7 * SC],
                           10 * SC), outline=(255, 255, 255, 105), width=1)
    return save(Image.alpha_composite(img, gold_fill(line)), "avsea")


# ================================================================ the plane
def _plane(name, pitch=0.0, ditched=False):
    """A high-wing seaplane in side view, nose to the right.

    Drawn large-ish and simply: at 44x28 the silhouette has to read at a
    glance, so the wing sits clear above the fuselage rather than crossing it,
    and the floats hang on visible struts.
    """
    img = new(44, 28)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cy = H * 0.44
    u = SC                                    # one design unit

    def rot(px, py):
        a = math.radians(-pitch)
        dx, dy = px - W * 0.46, py - cy
        return (W * 0.46 + dx * math.cos(a) - dy * math.sin(a),
                cy + dx * math.sin(a) + dy * math.cos(a))

    def poly(pts, **kw):
        d.polygon([rot(*q) for q in pts], **kw)

    def line(pts, **kw):
        d.line([rot(*q) for q in pts], **kw)

    # fuselage: tapered, nose at the right
    poly([(W * .07, cy - 1.2 * u), (W * .16, cy - 3.4 * u),
          (W * .62, cy - 3.8 * u), (W * .84, cy - 2.2 * u),
          (W * .91, cy), (W * .84, cy + 2.4 * u),
          (W * .62, cy + 3.8 * u), (W * .16, cy + 3.4 * u),
          (W * .07, cy + 1.2 * u)], fill=(255, 255, 255, 255))

    # tail fin and stabiliser
    poly([(W * .08, cy - 3 * u), (W * .15, cy - 13.5 * u),
          (W * .28, cy - 3 * u)], fill=(255, 255, 255, 255))
    poly([(W * .05, cy - 0.8 * u), (W * .20, cy - 0.8 * u),
          (W * .20, cy + 0.8 * u), (W * .05, cy + 0.8 * u)],
         fill=(255, 255, 255, 235))

    # high wing, held above the fuselage on a short pylon
    poly([(W * .36, cy - 4.8 * u), (W * .40, cy - 3.6 * u),
          (W * .58, cy - 3.6 * u), (W * .54, cy - 4.8 * u)],
         fill=(255, 255, 255, 210))
    poly([(W * .32, cy - 7.4 * u), (W * .74, cy - 6.8 * u),
          (W * .74, cy - 4.8 * u), (W * .32, cy - 5.4 * u)],
         fill=(255, 255, 255, 245))

    # two floats on struts - it is a seaplane
    for fx in (W * .32, W * .58):
        poly([(fx - 6 * u, cy + 9.6 * u), (fx + 5 * u, cy + 9.0 * u),
              (fx + 7 * u, cy + 10.4 * u), (fx + 5 * u, cy + 12.0 * u),
              (fx - 5 * u, cy + 12.0 * u)], fill=(255, 255, 255, 245))
        for sx in (fx - 3 * u, fx + 3 * u):
            line([(sx, cy + 3 * u), (sx, cy + 9.4 * u)],
                 fill=(255, 255, 255, 200), width=2)

    # propeller disc at the nose
    pa, pb = rot(W * .93, cy - 8 * u), rot(W * .93, cy + 8 * u)
    d.line([pa, pb], fill=(255, 255, 255, 130), width=3)

    img = Image.alpha_composite(img, gold_fill(lay))
    # cockpit glass last, so the gold gradient does not wash it out
    d2 = ImageDraw.Draw(img)
    d2.polygon([rot(W * .62, cy - 3.2 * u), rot(W * .78, cy - 1.8 * u),
                rot(W * .78, cy + 0.6 * u), rot(W * .62, cy + 0.6 * u)],
               fill=(14, 10, 16, 240))
    if ditched:
        img = img.rotate(-16, resample=Image.BICUBIC, center=(W * 0.46, cy))
    return save(img, name)


def planes():
    _plane("avplane1", pitch=0)        # level, taxiing
    _plane("avplane2", pitch=14)       # climbing
    _plane("avplane3", pitch=-8, ditched=True)   # down on the water


def splash():
    img = new(34, 18)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for dx, h, a in [(-11, 6, 150), (-6, 10, 200), (0, 12, 235),
                     (6, 10, 200), (11, 6, 150)]:
        x = W / 2 + dx * SC
        d.line([(x, H * .84), (x + dx * 0.28 * SC, H * .84 - h * SC)],
               fill=(255, 255, 255, a), width=3)
    d.arc([W * .10, H * .68, W * .90, H * 1.02], 200, 340,
          fill=(255, 255, 255, 175), width=2)
    return save(Image.alpha_composite(img, gold_fill(lay)), "avsplash")


# ==================================================================== ships
def ships():
    for i, (w, h) in enumerate([(30, 16), (24, 13)], 1):
        img = new(w, h)
        W, H = img.size
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        # hull
        d.polygon([(W * .06, H * .52), (W * .94, H * .52),
                   (W * .80, H * .84), (W * .18, H * .84)],
                  fill=(255, 255, 255, 250))
        # superstructure
        d.rectangle([W * .34, H * .24, W * .60, H * .52],
                    fill=(255, 255, 255, 225))
        # funnel + mast
        d.rectangle([W * .64, H * .30, W * .74, H * .52],
                    fill=(255, 255, 255, 235))
        d.line([(W * .26, H * .50), (W * .26, H * .12)],
               fill=(255, 255, 255, 200), width=2)
        save(Image.alpha_composite(img, gold_fill(lay)), f"avship{i}")


# ================================================================== build
def build():
    sea_panel()
    planes()
    splash()
    ships()
    deco_button("btn_fly", "FLY", 74, 38, primary=True, fs=13, tracking=4)
    for i, a in enumerate(AUTO, 1):
        selector(f"sel_auto{i}", "AUTO", "OFF" if a == 0 else f"{a:g}x", w=72)


if __name__ == "__main__":
    build()
    import os
    print("aviamasters assets ok ->", OUT)
