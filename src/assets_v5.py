"""v5: Aviamasters — sky and carriers, the plane, the orbs.

A third distinct world: Crash is a cold indigo starfield, the sea games are
oxblood felt, and this is a blue dusk with cloud banks and two carriers. As
with assets_v3 and _v4, the geometry lives here so the art and the sprite
coordinates in build.py cannot drift apart.
"""
from deco import *
from assets_v11 import fit, panel, deco_button, selector
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, math, json

from paths import BUILD, ensure_tables
ensure_tables()
T5 = json.load(open(BUILD / "tables5.json"))
ORB_NAMES = T5["orbNames"]

# ------------------------------------------------------------- geometry
SKY_W, SKY_H = 420, 210            # panel centred on the stage origin
SEA_Y = -66                        # waterline
DECK_Y = -56                       # the carriers' flight decks
CARRIER_L, CARRIER_R = -168, 168   # where the two ships sit
PLANE_X = -52                      # the plane holds station here; the sky moves
PLANE_LO, PLANE_HI = -44, 54       # its altitude band while cruising
ORB_IN, ORB_OUT = 198, -198        # orbs drift in from the right, out the left
                                   # (an orb is 22 wide, so it stays inside +-210)
# The big readout is digit field 9, which crash and aviamasters share; its
# position lives in assets_v4 so the two screens cannot drift apart.

DUSK_HI = (24, 34, 74)             # deep blue at the top
DUSK_LO = (96, 74, 118)            # warmer near the horizon
WATER_HI = (30, 40, 76)
WATER_LO = (12, 16, 34)
CLOUD = (150, 160, 205)
HULL = (54, 58, 82)


# =============================================================== the sky
def sky_panel():
    img = new(SKY_W, SKY_H)
    W, H = img.size
    pts = chamfer_pts([2, 2, W - 3, H - 3], 14 * SC)
    sy = int((105 - SEA_Y) * SC)          # waterline in panel pixels

    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        if y < sy:
            t = y / max(1, sy - 1)
            c = tuple(int(DUSK_HI[i] + (DUSK_LO[i] - DUSK_HI[i]) * (t ** 1.6))
                      for i in range(3))
        else:
            t = (y - sy) / max(1, H - sy - 1)
            c = tuple(int(WATER_HI[i] + (WATER_LO[i] - WATER_HI[i]) * t)
                      for i in range(3))
        gd.line([(0, y), (W, y)], fill=c + (252,))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    grad.putalpha(m)
    img = Image.alpha_composite(img, grad)

    # cloud banks, painted in rather than cloned - the clone budget is spent
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    rng = np.random.default_rng(9)
    for _ in range(26):
        cx = int(rng.integers(10 * SC, W - 10 * SC))
        cy = int(rng.integers(12 * SC, sy - 16 * SC))
        r = int(rng.integers(9, 26)) * SC
        a = int(rng.integers(26, 68))
        for k in range(4):
            ox = int(rng.integers(-r, r))
            rr = int(r * (0.55 + 0.45 * rng.random()))
            ld.ellipse([cx + ox - rr, cy - rr * 0.42,
                        cx + ox + rr, cy + rr * 0.42], fill=CLOUD + (a,))
    lay = lay.filter(ImageFilter.GaussianBlur(7))
    img = Image.alpha_composite(img, lay)

    d = ImageDraw.Draw(img)
    # the waterline, and a few swell rules
    d.line([(6 * SC, sy), (W - 6 * SC, sy)], fill=GOLD + (110,), width=2)
    for k in range(1, 7):
        yy = sy + int(k * 5.5 * SC)
        n = 3 + k
        for _ in range(n):
            wx = int(rng.integers(10 * SC, W - 30 * SC))
            d.line([(wx, yy), (wx + int((8 + k * 3) * SC), yy)],
                   fill=CLOUD + (int(24 + k * 6),), width=2)

    # the two carriers, painted into the panel
    for cx_stage in (CARRIER_L, CARRIER_R):
        cx = int((cx_stage + 210) * SC)
        dy = int((105 - DECK_Y) * SC)
        d.polygon([(cx - 40 * SC, dy), (cx + 40 * SC, dy),
                   (cx + 33 * SC, dy + 9 * SC), (cx - 33 * SC, dy + 9 * SC)],
                  fill=HULL + (255,))
        d.rectangle([cx - 40 * SC, dy - 3 * SC, cx + 40 * SC, dy],
                    fill=(78, 82, 108, 255))
        # island superstructure, on the right of each deck
        d.rectangle([cx + 16 * SC, dy - 14 * SC, cx + 25 * SC, dy - 3 * SC],
                    fill=(70, 74, 100, 255))
        d.rectangle([cx + 19 * SC, dy - 21 * SC, cx + 21 * SC, dy - 14 * SC],
                    fill=(70, 74, 100, 255))
        # deck centreline
        for k in range(-4, 5):
            d.line([(cx + k * 8 * SC - 2 * SC, dy - 1 * SC),
                    (cx + k * 8 * SC + 2 * SC, dy - 1 * SC)],
                   fill=CREAM + (110,), width=2)

    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld2 = ImageDraw.Draw(line)
    ld2.polygon(pts, outline=(255, 255, 255, 240), width=3)
    ld2.polygon(chamfer_pts([7 * SC, 7 * SC, W - 3 - 7 * SC, H - 3 - 7 * SC],
                            10 * SC), outline=(255, 255, 255, 105), width=1)
    return save(Image.alpha_composite(img, gold_fill(line)), "avsky")


# ============================================================= the plane
def _plane(name, pitch=0.0, ditched=False):
    """A stubby propeller plane, nose right. Warm red so it reads against blue."""
    # PSC scales the whole drawing: x offsets are fractions of W, y offsets are
    # multiples of u, so both follow the canvas.
    PSC = 1.45
    img = new(34 * PSC, 22 * PSC)
    W, H = img.size
    d = ImageDraw.Draw(img)
    cy = H * 0.5
    u = SC * PSC
    BODY = (206, 66, 48)
    BODY_D = (150, 38, 30)

    def rot(px, py):
        a = math.radians(-pitch)
        dx, dy = px - W * 0.5, py - cy
        return (W * 0.5 + dx * math.cos(a) - dy * math.sin(a),
                cy + dx * math.sin(a) + dy * math.cos(a))

    def poly(pts, **kw):
        d.polygon([rot(*q) for q in pts], **kw)

    # fuselage
    poly([(W * .08, cy - 1.4 * u), (W * .20, cy - 3.2 * u),
          (W * .70, cy - 3.0 * u), (W * .88, cy - 1.0 * u),
          (W * .92, cy + 0.6 * u), (W * .70, cy + 3.2 * u),
          (W * .20, cy + 3.4 * u), (W * .08, cy + 1.4 * u)],
         fill=BODY + (255,))
    # tail
    poly([(W * .09, cy - 2.6 * u), (W * .16, cy - 10 * u),
          (W * .30, cy - 2.6 * u)], fill=BODY + (255,))
    poly([(W * .04, cy - 0.8 * u), (W * .22, cy - 0.8 * u),
          (W * .22, cy + 0.8 * u), (W * .04, cy + 0.8 * u)],
         fill=BODY_D + (255,))
    # lower wing, swept back and down - a biplane silhouette
    poly([(W * .34, cy + 1.5 * u), (W * .62, cy + 1.5 * u),
          (W * .52, cy + 6.5 * u), (W * .24, cy + 6.5 * u)],
         fill=BODY_D + (250,))
    # upper wing on struts
    poly([(W * .30, cy - 7.6 * u), (W * .68, cy - 7.6 * u),
          (W * .68, cy - 5.4 * u), (W * .30, cy - 5.4 * u)],
         fill=BODY + (250,))
    for sx in (W * .38, W * .58):
        d.line([rot(sx, cy - 5.6 * u), rot(sx, cy - 2.6 * u)],
               fill=BODY_D + (255,), width=2)
    # cockpit
    d.ellipse([*rot(W * .52, cy - 3.4 * u), *rot(W * .64, cy - 0.6 * u)],
              fill=(20, 24, 44, 240))
    # propeller
    pa, pb = rot(W * .93, cy - 7 * u), rot(W * .93, cy + 7 * u)
    d.line([pa, pb], fill=(240, 226, 190, 150), width=3)
    # a gold trim line, so it still belongs to the casino
    d.line([rot(W * .20, cy + 3.0 * u), rot(W * .70, cy + 2.8 * u)],
           fill=GOLD_L + (200,), width=2)

    if ditched:
        img = img.rotate(-24, resample=Image.BICUBIC, center=(W / 2, cy))
    return save(img, name)


def planes():
    _plane("avplane1", pitch=0)       # on the deck / level
    _plane("avplane2", pitch=11)      # climbing
    _plane("avplane3", pitch=-30, ditched=True)   # going down


# ================================================================= orbs
ORB_FACE = {
    "PLUS05": ("+0.5", (58, 150, 92), (92, 200, 130)),
    "PLUS1":  ("+1",   (58, 150, 92), (92, 200, 130)),
    "MUL2":   ("x2",   (40, 86, 176), (86, 148, 232)),
    "MUL3":   ("x3",   (40, 86, 176), (86, 148, 232)),
    "ROCKET": ("",     (168, 42, 46), (226, 92, 76)),
}


def orbs():
    """One costume per collectible, in the order tables5.py lists them.

    EMPTY has no orb - the plane simply passes clear sky - so it gets a blank
    costume and keeps the costume index aligned with the table.
    """
    w = 22
    for i, nm in enumerate(ORB_NAMES, 1):
        img = new(w, w)
        W, H = img.size
        if nm == "EMPTY":
            ImageDraw.Draw(img).point((0, 0), fill=(0, 0, 0, 1))
            save(img, f"avorb{i}")
            continue
        label, dark, light = ORB_FACE[nm]
        d = ImageDraw.Draw(img)
        # a soft glow behind, so orbs read against the cloud banks
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([2, 2, W - 2, H - 2], fill=light + (110,))
        img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(img)
        d.ellipse([W * .16, H * .16, W * .84, H * .84], fill=dark + (250,))
        d.ellipse([W * .16, H * .16, W * .84, H * .84],
                  outline=light + (255,), width=2)
        d.ellipse([W * .28, H * .24, W * .52, H * .42], fill=light + (120,))

        if nm == "ROCKET":
            # a little rocket, nose up-right, instead of a label
            cx, cy2, u = W * .5, H * .5, SC
            d.polygon([(cx + 5 * u, cy2 - 6 * u), (cx + 1 * u, cy2 - 1 * u),
                       (cx - 4 * u, cy2 + 4 * u), (cx - 1 * u, cy2 + 6 * u),
                       (cx + 4 * u, cy2 + 1 * u)], fill=(250, 232, 214, 255))
            d.polygon([(cx - 4 * u, cy2 + 4 * u), (cx - 6 * u, cy2 + 3 * u),
                       (cx - 3 * u, cy2 + 7 * u)], fill=(250, 232, 214, 235))
        else:
            s, tr = fit(label, 9 * SC, 0.4 * SC, W - 7 * SC, floor=5)
            tracked(img, (W / 2, H / 2 + 0.5 * SC), label, s, tr, anchor="mm",
                    color=(252, 248, 240), gold=False)
        save(img, f"avorb{i}")


# ================================================== the collection sparkle
def spark():
    img = new(30, 30)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = W / 2, H / 2
    for i in range(10):
        a = math.radians(i * 36 + 9)
        r0, r1 = 4 * SC, (9 + (i % 2) * 4) * SC
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * r1, cy + math.sin(a) * r1)],
               fill=(255, 255, 255, 230), width=3)
    return save(Image.alpha_composite(img, gold_fill(lay)), "avspark")


# ================================================================== build
def build():
    sky_panel()
    planes()
    orbs()
    spark()
    deco_button("btn_takeoff", "TAKE OFF", 92, 38, primary=True, fs=11, tracking=2)


if __name__ == "__main__":
    build()
    import os
    print("aviamasters assets ok ->", OUT)
