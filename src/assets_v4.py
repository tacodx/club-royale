"""v4: Crash — night sky, launch gantry, the rocket, the burst.

Its own visual world, deliberately: this is the one screen in the casino that
is not oxblood-and-gold felt. A cold indigo night with a gold rocket in it
reads instantly as a different game from the sea, the road or the table.

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
SKY_W, SKY_H = 420, 210            # panel centred on the stage origin
PAD_Y = -88                        # the gantry deck the rocket leaves from
ROCK_X0, ROCK_Y0 = -150, -74       # on the pad
ROCK_X1, ROCK_Y1 = 96, 62          # fully climbed
MULT_XY = (0, 66)                  # the big readout, clear of the panel edge
MULT_GAP = 24                      # digit spacing at 170% size

# a colder palette than the rest of the casino, on purpose
NIGHT_HI = (7, 8, 20)
NIGHT_LO = (34, 26, 62)
STEEL = (58, 54, 78)


# ============================================================== the sky
def sky_panel():
    img = new(SKY_W, SKY_H)
    W, H = img.size
    pts = chamfer_pts([2, 2, W - 3, H - 3], 14 * SC)

    grad = Image.new("RGBA", (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(H):
        t = y / max(1, H - 1)
        c = tuple(int(NIGHT_HI[i] + (NIGHT_LO[i] - NIGHT_HI[i]) * (t ** 1.35))
                  for i in range(3))
        gd.line([(0, y), (W, y)], fill=c + (252,))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    grad.putalpha(m)
    img = Image.alpha_composite(img, grad)

    d = ImageDraw.Draw(img)

    # a static starfield: deterministic, so two builds are identical
    rng = np.random.default_rng(4)
    for _ in range(150):
        sx = int(rng.integers(8 * SC, W - 8 * SC))
        sy = int(rng.integers(8 * SC, H - 30 * SC))
        r = float(rng.choice([0.7, 0.7, 1.0, 1.4]))
        a = int(rng.integers(45, 190))
        d.ellipse([sx - r * SC, sy - r * SC, sx + r * SC, sy + r * SC],
                  fill=CREAM + (a,))

    # the launch gantry, bottom left, drawn into the panel so it costs no clone
    py = int((105 - PAD_Y) * SC)
    gx = int((ROCK_X0 + 210) * SC)
    d.rectangle([gx - 30 * SC, py, gx + 30 * SC, py + 5 * SC],
                fill=STEEL + (255,))
    d.rectangle([gx - 34 * SC, py + 5 * SC, gx + 34 * SC, py + 8 * SC],
                fill=(40, 36, 54, 255))
    # tower and cross-bracing
    d.rectangle([gx + 16 * SC, py - 46 * SC, gx + 21 * SC, py],
                fill=STEEL + (255,))
    for k in range(5):
        y0 = py - (8 + k * 9) * SC
        d.line([(gx + 16 * SC, y0), (gx + 21 * SC, y0 - 9 * SC)],
               fill=(74, 70, 96, 255), width=2)
    # ground haze
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([gx - 70 * SC, py - 10 * SC,
                                 gx + 70 * SC, py + 30 * SC],
                                fill=(90, 80, 140, 70))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(24)))
    img.putalpha(Image.fromarray(
        (np.asarray(img.split()[3]).astype(float) *
         np.asarray(m) / 255).astype("uint8")))

    # the outer rule, in gold, so it still belongs to the casino
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 240), width=3)
    ld.polygon(chamfer_pts([7 * SC, 7 * SC, W - 3 - 7 * SC, H - 3 - 7 * SC],
                           10 * SC), outline=(255, 255, 255, 105), width=1)
    return save(Image.alpha_composite(img, gold_fill(line)), "crsky")


# ============================================================= the rocket
def _rocket(name, flame=0, tumbling=False):
    """Side view, nose up and to the right, climbing at 45 degrees."""
    img = new(30, 42)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, u = W * 0.5, SC

    # body: a tall capsule
    d.polygon([(cx, 2 * u),                       # nose
               (cx + 5 * u, 12 * u), (cx + 5 * u, 27 * u),
               (cx - 5 * u, 27 * u), (cx - 5 * u, 12 * u)],
              fill=(255, 255, 255, 255))
    # fins
    d.polygon([(cx - 5 * u, 20 * u), (cx - 11 * u, 30 * u),
               (cx - 5 * u, 28 * u)], fill=(255, 255, 255, 245))
    d.polygon([(cx + 5 * u, 20 * u), (cx + 11 * u, 30 * u),
               (cx + 5 * u, 28 * u)], fill=(255, 255, 255, 245))
    # a fairing band
    d.rectangle([cx - 5 * u, 15 * u, cx + 5 * u, 17 * u],
                fill=(255, 255, 255, 190))

    img = Image.alpha_composite(img, gold_fill(lay))
    d2 = ImageDraw.Draw(img)
    # porthole, after the gold so it stays dark
    d2.ellipse([cx - 2.6 * u, 9 * u, cx + 2.6 * u, 14 * u],
               fill=(12, 12, 28, 245))
    d2.ellipse([cx - 1.4 * u, 10.2 * u, cx + 1.4 * u, 12.6 * u],
               fill=(150, 190, 255, 120))

    if flame:
        # exhaust: three tongues, hotter in the middle, longer at full thrust
        L = 7 + flame * 5
        for dx, k, col in [(-2.6, 0.62, (255, 150, 60, 210)),
                           (0.0, 1.00, (255, 214, 140, 245)),
                           (2.6, 0.62, (255, 150, 60, 210))]:
            d2.polygon([(cx + dx * u - 2.2 * u, 27 * u),
                        (cx + dx * u + 2.2 * u, 27 * u),
                        (cx + dx * u, 27 * u + L * k * u)], fill=col)
        d2.ellipse([cx - 4 * u, 25 * u, cx + 4 * u, 30 * u],
                   fill=(255, 236, 190, 150))

    # the whole thing leans into its climb
    img = img.rotate(-38 if not tumbling else 122, resample=Image.BICUBIC,
                     center=(cx, H * 0.45), expand=False)
    return save(img, name)


def rockets():
    _rocket("crrocket1", flame=0)          # on the pad
    _rocket("crrocket2", flame=1)          # climbing
    _rocket("crrocket3", flame=2)          # full thrust
    _rocket("crrocket4", flame=0, tumbling=True)   # lost it


def burst():
    """The explosion when the run ends."""
    img = new(46, 46)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = W / 2, H / 2
    for i in range(14):
        a = math.radians(i * (360 / 14) + 7)
        r0, r1 = 6 * SC, (13 + (i % 3) * 5) * SC
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                (cx + math.cos(a) * r1, cy + math.sin(a) * r1)],
               fill=(255, 255, 255, 235), width=3)
    d.ellipse([cx - 7 * SC, cy - 7 * SC, cx + 7 * SC, cy + 7 * SC],
              outline=(255, 255, 255, 255), width=3)
    img = Image.alpha_composite(img, gold_fill(lay))
    d2 = ImageDraw.Draw(img)
    d2.ellipse([cx - 4.5 * SC, cy - 4.5 * SC, cx + 4.5 * SC, cy + 4.5 * SC],
               fill=(255, 236, 190, 230))
    return save(img, "crburst")


# ============================================== drifting stars (parallax)
def sparks():
    """Three sizes of drifting star, to give the climb some speed."""
    for i, r in enumerate([1.2, 1.8, 2.6], 1):
        img = new(8, 8)
        W, H = img.size
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse(
            [W / 2 - r * SC, H / 2 - r * SC, W / 2 + r * SC, H / 2 + r * SC],
            fill=(255, 255, 255, 255))
        save(Image.alpha_composite(img, gold_fill(lay)), f"crspark{i}")


# ================================================================== build
def build():
    sky_panel()
    rockets()
    burst()
    sparks()
    deco_button("btn_launch", "LAUNCH", 84, 38, primary=True, fs=12, tracking=3)
    for i, a in enumerate(AUTO, 1):
        selector(f"sel_auto{i}", "AUTO", "OFF" if a == 0 else f"{a:g}x", w=72)


if __name__ == "__main__":
    build()
    import os
    print("crash assets ok ->", OUT)
