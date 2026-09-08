"""v3 additions: Duck Road — road panel, duck, traffic, lane ladder, egg.

Geometry lives here rather than in build.py so the art and the sprite
coordinates cannot drift apart. build.py imports LANE_X / KERB_X / DUCK_Y and
positions clones from the same numbers this module draws with.
"""
from deco import *
from assets_v11 import fit, panel, deco_button, selector
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, json

from paths import BUILD, ensure_tables
ensure_tables()
T3 = json.load(open(BUILD / "tables3.json"))
MODES = T3["modes"]
LANES = T3["lanes"]

# ------------------------------------------------------------- geometry
# The panel is 420x210 centred on the stage origin, so panel-local x maps to
# stage x by subtracting 210.
ROAD_W, ROAD_H = 420, 210
KERB_L = 40                       # left verge, where the duck waits
LANE_W = 29
ROAD_X0 = -ROAD_W // 2            # -210

LANE_X = [ROAD_X0 + KERB_L + LANE_W * i + LANE_W // 2 for i in range(LANES)]
KERB_X = ROAD_X0 + KERB_L // 2                    # duck's start pad
FINISH_X = ROAD_X0 + KERB_L + LANE_W * LANES + 16  # the far verge

DUCK_Y = -78          # the duck walks along this line
LABEL_Y = 121         # multiplier ladder sits above the road
CAR_TOP, CAR_BOT = 118, -118

ASPHALT = (27, 22, 28)
KERB_F = (44, 14, 26)


# =============================================================== the road
def road_panel():
    img = new(ROAD_W, ROAD_H)
    W, H = img.size
    d = ImageDraw.Draw(img)

    pts = chamfer_pts([2, 2, W - 3, H - 3], 14 * SC)
    d.polygon(pts, fill=ASPHALT + (252,))

    # a faint burgundy glow up the middle so the road is not a flat slab
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([W * .12, -H * .35, W * .88, H * 1.35],
                                fill=BURG + (58,))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(60)))
    img.putalpha(Image.fromarray(
        (np.asarray(img.split()[3]).astype(float) *
         np.asarray(_poly_mask_local((W, H), pts)) / 255).astype("uint8")))

    d = ImageDraw.Draw(img)

    # kerbs: the start verge on the left, the finish verge on the right
    for x0, x1 in [(0, KERB_L * SC),
                   ((KERB_L + LANE_W * LANES) * SC, W)]:
        d.rectangle([x0 + 2, 4 * SC, x1 - 2, H - 4 * SC], fill=KERB_F + (235,))

    # dashed lane dividers
    for k in range(1, LANES):
        x = (KERB_L + LANE_W * k) * SC
        y = 10 * SC
        while y < H - 10 * SC:
            d.line([(x, y), (x, y + 7 * SC)], fill=CREAM + (60,), width=2)
            y += 14 * SC

    # solid edges either side of the carriageway
    for k in (0, LANES):
        x = (KERB_L + LANE_W * k) * SC
        d.line([(x, 5 * SC), (x, H - 5 * SC)], fill=GOLD + (150,), width=2)

    # the outer rule, in gold, matching every other panel in the game
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 240), width=3)
    ld.polygon(chamfer_pts([7 * SC, 7 * SC, W - 3 - 7 * SC, H - 3 - 7 * SC],
                           10 * SC), outline=(255, 255, 255, 105), width=1)
    img = Image.alpha_composite(img, gold_fill(line))

    # verge captions
    tracked(img, (KERB_L * SC / 2, H / 2), "START", 6 * SC, 0.8 * SC,
            anchor="mm")
    fx = (KERB_L + LANE_W * LANES) * SC + (W - (KERB_L + LANE_W * LANES) * SC) / 2
    tracked(img, (fx, H / 2), "HOME", 6 * SC, 0.8 * SC, anchor="mm")
    return save(img, "duckroad")


def _poly_mask_local(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


# ==================================================== the multiplier ladder
def compact(v):
    """At most five characters, so it fits a 29-wide lane."""
    if v >= 1000:  return f"{v:.0f}x"
    if v >= 100:   return f"{v:.0f}x"
    if v >= 10:    return f"{v:.1f}x"
    return f"{v:.2f}x"


def duck_mults():
    """96 labels in the same order as tables3.FLAT: the base ladder in
    1..48, the egg ladder in 49..96, each 4 modes x 12 lanes. The runtime
    indexes it as (mode-1)*12 + lane + 48*carrying_egg, so the whole ladder
    switches the instant the duck picks the egg up."""
    for i, v in enumerate(T3["flat"], 1):
        img = new(LANE_W, 16)
        W, H = img.size
        txt = compact(float(v))
        s, tr = fit(txt, 8 * SC, 0.4 * SC, W - 3 * SC, floor=5)
        tracked(img, (W / 2, H / 2), txt, s, tr, anchor="mm")
        save(img, f"dm{i}")


# ================================================================= the duck
def _duck(name, lift=0, splat=False, cheer=False):
    img = new(20, 20)
    W, H = img.size
    d = ImageDraw.Draw(img)
    cy = H * 0.60 - lift * SC
    body = CREAM if not splat else (150, 130, 120)

    if splat:
        # flattened: a wider, shorter body, no lift
        d.ellipse([W * .10, cy - 3 * SC, W * .90, cy + 5 * SC],
                  fill=body + (255,))
        d.ellipse([W * .58, cy - 5 * SC, W * .92, cy + 1 * SC],
                  fill=body + (255,))
    else:
        d.ellipse([W * .16, cy - 4 * SC, W * .82, cy + 6 * SC],
                  fill=body + (255,))
        # head
        hy = cy - 7 * SC - (1 * SC if cheer else 0)
        d.ellipse([W * .54, hy - 3.5 * SC, W * .92, hy + 3.5 * SC],
                  fill=body + (255,))
        # wing
        d.ellipse([W * .28, cy - 2 * SC, W * .66, cy + 3.5 * SC],
                  fill=(214, 202, 180, 255))
        # beak
        d.polygon([(W * .90, hy - 0.6 * SC), (W * .90, hy + 1.8 * SC),
                   (W * 1.02, hy + 0.6 * SC)], fill=GOLD + (255,))
        # eye
        d.ellipse([W * .74, hy - 1.8 * SC, W * .80, hy - 0.4 * SC],
                  fill=INK + (255,))
        # legs
        ly = cy + 5 * SC
        for lx in (W * .40, W * .58):
            d.line([(lx, ly), (lx, ly + (2 if lift else 3) * SC)],
                   fill=GOLD_D + (255,), width=2)

    if cheer:
        # a little gold sparkle over the head
        for ang, r in [(-40, 8), (0, 9), (40, 8)]:
            import math
            ax = W * .72 + math.cos(math.radians(ang - 90)) * r * SC
            ay = cy - 11 * SC + math.sin(math.radians(ang - 90)) * r * SC
            d.ellipse([ax - 1.2 * SC, ay - 1.2 * SC,
                       ax + 1.2 * SC, ay + 1.2 * SC], fill=GOLD_L + (255,))
    return save(img, name)


def ducks():
    _duck("duck1")                 # standing
    _duck("duck2", lift=3)         # mid-hop
    _duck("duck3", splat=True)     # hit
    _duck("duck4", cheer=True)     # cashed out


# ================================================================== traffic
def cars():
    for i, col in enumerate([(150, 26, 44), (28, 24, 34), (96, 20, 60)], 1):
        img = new(21, 34)
        W, H = img.size
        d = ImageDraw.Draw(img)
        pts = chamfer_pts([2 * SC, 1 * SC, W - 2 * SC, H - 1 * SC], 4 * SC)
        d.polygon(pts, fill=col + (250,))
        # roof / windscreen
        d.rectangle([W * .22, H * .34, W * .78, H * .60],
                    fill=(16, 14, 20, 220))
        # gold trim down the flanks
        line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(line).polygon(pts, outline=(255, 255, 255, 190), width=2)
        img = Image.alpha_composite(img, gold_fill(line))
        d = ImageDraw.Draw(img)
        # headlights at the leading (bottom) edge, since cars drive downward
        for lx in (W * .30, W * .70):
            d.ellipse([lx - 2 * SC, H - 5 * SC, lx + 2 * SC, H - 1 * SC],
                      fill=GOLD_L + (255,))
        save(img, f"dcar{i}")


# ============================================================= golden egg
def egg():
    img = new(16, 20)
    W, H = img.size
    m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(m).ellipse([W * .14, H * .10, W * .86, H * .92],
                              fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, gold_fill(m))
    d = ImageDraw.Draw(img)
    d.ellipse([W * .30, H * .24, W * .46, H * .44], fill=GOLD_L + (210,))
    return save(img, "degg")


# ================================================================== build
def build():
    road_panel()
    duck_mults()
    ducks()
    cars()
    egg()
    deco_button("btn_go", "GO", 74, 38, primary=True, fs=13, tracking=3)
    for i, (n, _p) in enumerate(MODES, 1):
        selector(f"sel_duck{i}", "MODE", n, w=72)


if __name__ == "__main__":
    build()
    import os
    print("duck road assets ok ->", OUT)
