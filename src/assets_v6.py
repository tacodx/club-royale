"""v6 additions: Coin Flip and Dice.

Two more felt-and-gold rooms rather than a new visual world - Crash and
Aviamasters already carry the "somewhere else" duty, and these two are table
games.

As with assets_v3/v4/v5 the geometry lives here, not in build.py, so the art
and the sprite coordinates cannot drift apart. build.py imports RUNG_Y,
RAIL_X0/RAIL_X1 and the rest and positions everything from the same numbers
this module draws with.
"""
from deco import *
from assets_v11 import fit, panel, deco_button, selector, _gold
from PIL import Image, ImageDraw, ImageFilter
import math, json

from paths import BUILD, ensure_tables
ensure_tables()
T6 = json.load(open(BUILD / "tables6.json"))
COIN = T6["coin"]
RUNGS = T6["coinRungs"]
DICE_CAPS = T6["diceCaps"]
DICE_WIN = T6["diceWin"]
DICE_MULT = T6["diceMult"]
OUTCOMES = T6["diceOutcomes"]

# ======================================================= coin flip geometry
FELT_W, FELT_H = 224, 230
FELT_XY = (0, -4)                  # x -112..112, y 111..-119
COIN_XY = (0, -22)
COIN_D = 116

LADDER_XY = (176, -12)             # clear of the felt, and of the stage edge
LADDER_W, LADDER_H = 96, 250
HEAD_H, RUNG_H = 22, 19
# centre y of each rung, rung 1 (1.92x) at the bottom, rung 12 at the top.
RUNG_Y = [LADDER_XY[1] + LADDER_H / 2 - HEAD_H
          - RUNG_H * (RUNGS - n) - RUNG_H / 2 for n in range(1, RUNGS + 1)]
PIP_X = LADDER_XY[0] - LADDER_W / 2 - 8      # rides the gap beside the ladder

# ============================================================ dice geometry
DFELT_W, DFELT_H = 440, 214
DFELT_XY = (0, 6)                  # x -220..220, y 113..-101
TRACK_W, TRACK_H = 400, 76
TRACK_XY = (0, -26)                # centred in the felt below the readout
RAIL_X0, RAIL_X1 = -176, 176       # stage x of a 0.00 roll and a 100.00 roll
RAIL_Y = -29                       # rail centre, in stage coords
MARK_XY = (RAIL_X0, RAIL_Y + 5)    # the needle pokes above the rail

# Both rooms borrow Crash's big readout, so they borrow its position too:
# the felt panels are sized and placed around it rather than the other way.
from assets_v4 import MULT_XY as MULT_XY_C, MULT_GAP as MULT_GAP_C

WIN_F = (18, 92, 62)               # the live side of the rail
LOSE_F = (52, 14, 24)


def roll_x(hundredths):
    """Stage x for a roll expressed in hundredths (0..OUTCOMES)."""
    return RAIL_X0 + (RAIL_X1 - RAIL_X0) * hundredths / OUTCOMES


# =============================================================== coin felt
def coin_felt():
    img, (W, H) = panel(FELT_W, FELT_H, cut=22 * SC, fill=(28, 9, 17, 248),
                        inner=8, width=3)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    # a shallow pool of light where the coin lands
    cy = H / 2 + (FELT_XY[1] - COIN_XY[1]) * SC
    ld.ellipse([W * .16, cy - 46 * SC, W * .84, cy + 46 * SC],
               fill=BURG_L + (70,))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(26)))
    _gold(img, lambda d: d.ellipse(
        [W / 2 - 68 * SC, cy - 68 * SC, W / 2 + 68 * SC, cy + 68 * SC],
        outline=(255, 255, 255, 95), width=1))
    tracked(img, (W / 2, 22 * SC), "COIN FLIP", 11 * SC, 5 * SC, anchor="mm")
    return save(img, "coin_felt")


# =================================================================== coin
def _face(side):
    """One full-width coin face, COIN_D across."""
    D = COIN_D * SC
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, R = D / 2, D / 2 - 1
    d.ellipse([0, 0, D - 1, D - 1], fill=(96, 74, 20, 255))
    d.ellipse([3 * SC, 3 * SC, D - 1 - 3 * SC, D - 1 - 3 * SC],
              fill=(34, 14, 20, 255) if side == "t" else (30, 22, 12, 255))
    # rim: two gold rings with the metallic sweep
    ring = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse([1, 1, D - 2, D - 2], outline=(255, 255, 255, 255), width=4)
    rd.ellipse([9 * SC, 9 * SC, D - 1 - 9 * SC, D - 1 - 9 * SC],
               outline=(255, 255, 255, 190), width=2)
    # milled edge ticks
    for k in range(48):
        a = math.radians(k * 7.5)
        rd.line([(c + math.cos(a) * (R - 3.5 * SC), c + math.sin(a) * (R - 3.5 * SC)),
                 (c + math.cos(a) * (R - 7 * SC), c + math.sin(a) * (R - 7 * SC))],
                fill=(255, 255, 255, 120), width=1)

    emb = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ed = ImageDraw.Draw(emb)
    if side == "h":
        # a deco fan: rays over a stepped crown
        for k in range(11):
            a = math.radians(-170 + k * 14)
            ed.line([(c, c + 6 * SC),
                     (c + math.cos(a) * 30 * SC, c + 6 * SC + math.sin(a) * 30 * SC)],
                    fill=(255, 255, 255, 210), width=2)
        for k, wgt in enumerate([20, 14, 8]):
            ed.rectangle([c - wgt * SC, c + (6 + k * 5) * SC,
                          c + wgt * SC, c + (10 + k * 5) * SC],
                         fill=(255, 255, 255, 255))
    else:
        # a deco lozenge, twice nested
        for s in (30, 19, 9):
            ed.polygon([(c, c - s * SC), (c + s * .62 * SC, c),
                        (c, c + s * SC), (c - s * .62 * SC, c)],
                       outline=(255, 255, 255, 255), width=2)
    img = Image.alpha_composite(img, gold_fill(ring))
    img = Image.alpha_composite(img, gold_fill(emb))
    tracked(img, (c, D - 21 * SC), "HEADS" if side == "h" else "TAILS",
            9 * SC, 2.6 * SC, anchor="mm")
    return img


def coins():
    """A 12-frame spin. Frame 1 rests on heads, frame 7 on tails."""
    D = COIN_D * SC
    faces = {"h": _face("h"), "t": _face("t")}

    edge = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ew = int(D * 0.085)
    ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle([D / 2 - ew / 2, 1, D / 2 + ew / 2, D - 2],
                         radius=ew / 2, fill=(112, 86, 24, 255))
    lay = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle(
        [D / 2 - ew / 2, 1, D / 2 + ew / 2, D - 2], radius=ew / 2,
        outline=(255, 255, 255, 255), width=2)
    edge = Image.alpha_composite(edge, gold_fill(lay, vertical=False))

    # heads -> edge -> tails -> edge -> back, squashing on the way through
    frames = [("h", 1.0), ("h", .62), ("h", .26), ("e", 0),
              ("t", .26), ("t", .62), ("t", 1.0), ("t", .62),
              ("t", .26), ("e", 0), ("h", .26), ("h", .62)]
    for i, (side, f) in enumerate(frames, 1):
        if side == "e":
            save(edge, f"cf{i}")
            continue
        src = faces[side]
        w = max(2, int(D * f))
        sq = src.resize((w, D), Image.LANCZOS)
        img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
        img.alpha_composite(sq, (int((D - w) / 2), 0))
        save(img, f"cf{i}")
    return len(frames)


COIN_FRAMES = 12
COIN_HEADS, COIN_TAILS = 1, 7      # the two costumes a flip can rest on


# ================================================================= ladder
def coin_ladder():
    img, (W, H) = panel(LADDER_W, LADDER_H, cut=12 * SC, fill=(14, 9, 14, 246),
                        inner=None, width=2)
    d = ImageDraw.Draw(img)
    tracked(img, (W / 2, 12 * SC), "PAYS", 8 * SC, 2.4 * SC, anchor="mm")
    _gold(img, lambda dd: dd.line([(8 * SC, HEAD_H * SC), (W - 8 * SC, HEAD_H * SC)],
                                  fill=(255, 255, 255, 170), width=1))
    for n in range(1, RUNGS + 1):
        cy = (HEAD_H + RUNG_H * (RUNGS - n) + RUNG_H / 2) * SC
        if n % 2 == 0:
            d.rectangle([5 * SC, cy - RUNG_H / 2 * SC + 1,
                         W - 5 * SC, cy + RUNG_H / 2 * SC - 1],
                        fill=(38, 12, 22, 190))
        lab = f"{COIN[n - 1]:g}x"
        s, tr = fit(lab, 11 * SC, 1.0 * SC, W - 16 * SC, floor=5)
        tracked(img, (W / 2, cy), lab, s, tr, anchor="mm",
                color=CREAM, gold=(n == RUNGS))
    return save(img, "coin_ladder")


def coin_pip():
    img = new(16, 20)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(2, H / 2), (W - 3, 3), (W - 3, H - 4)],
                                fill=(255, 255, 255, 255))
    return save(Image.alpha_composite(img, gold_fill(lay, vertical=False)),
                "coin_pip")


# ============================================================== dice felt
def dice_felt():
    img, (W, H) = panel(DFELT_W, DFELT_H, cut=22 * SC, fill=(28, 9, 17, 248),
                        inner=8, width=3)
    tracked(img, (W / 2, 22 * SC), "DICE", 11 * SC, 6 * SC, anchor="mm")
    return save(img, "dice_felt")


def dice_tracks():
    """One full track costume per (mode, side): 5 x 2 = 10.

    The winning span is painted, so what pays is on the screen rather than in
    the player's head, and the threshold and multiplier are set in the art
    from the same solved table the payout uses.
    """
    W, H = TRACK_W * SC, TRACK_H * SC
    x0 = (RAIL_X0 - (TRACK_XY[0] - TRACK_W / 2)) * SC      # rail ends, local px
    x1 = (RAIL_X1 - (TRACK_XY[0] - TRACK_W / 2)) * SC
    ry = (TRACK_XY[1] + TRACK_H / 2 - RAIL_Y) * SC         # rail centre, local
    rh = 11 * SC

    for mi, (cap, wins, mult) in enumerate(zip(DICE_CAPS, DICE_WIN, DICE_MULT), 1):
        for side in ("u", "o"):
            img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            # UNDER t wins below t; OVER t wins above OUTCOMES - t. Both are
            # `wins` outcomes wide, which is why one table serves both sides.
            thresh = wins if side == "u" else OUTCOMES - wins
            tx = x0 + (x1 - x0) * thresh / OUTCOMES
            lo_f = WIN_F if side == "u" else LOSE_F
            hi_f = LOSE_F if side == "u" else WIN_F
            d.rectangle([x0, ry - rh, tx, ry + rh], fill=lo_f + (255,))
            d.rectangle([tx, ry - rh, x1, ry + rh], fill=hi_f + (255,))

            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.rectangle([x0, ry - rh, x1, ry + rh],
                         outline=(255, 255, 255, 255), width=2)
            ld.line([(tx, ry - rh - 5 * SC), (tx, ry + rh + 5 * SC)],
                    fill=(255, 255, 255, 255), width=3)
            for k in range(0, 101, 5):
                kx = x0 + (x1 - x0) * k / 100
                big = (k % 25 == 0)
                ld.line([(kx, ry + rh), (kx, ry + rh + (6 if big else 3) * SC)],
                        fill=(255, 255, 255, 235 if big else 120), width=2 if big else 1)
            img = Image.alpha_composite(img, gold_fill(lay))

            for k in range(0, 101, 25):
                kx = x0 + (x1 - x0) * k / 100
                tracked(img, (kx, ry + rh + 13 * SC), str(k), 7 * SC, 0.8 * SC,
                        anchor="mm", color=(150, 132, 104), gold=False)
            lbl = f"{'UNDER' if side == 'u' else 'OVER'} {thresh / 100:.2f}"
            tracked(img, (x0 + 2 * SC, 11 * SC), lbl, 10 * SC, 2.4 * SC,
                    anchor="lm")
            tracked(img, (x1 - 2 * SC, 11 * SC), f"PAYS {mult:.2f}x", 10 * SC,
                    2.4 * SC, anchor="rm")
            save(img, f"dice_tr{mi}{side}")


def dice_marker():
    img = new(14, 38)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.polygon([(W / 2, H - 2), (W - 2, H - 15), (W - 2, 6), (W / 2, 1),
                (2, 6), (2, H - 15)], fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, gold_fill(lay))
    ImageDraw.Draw(img).line([(W / 2, 8), (W / 2, H - 12)],
                             fill=(38, 16, 10, 220), width=2)
    return save(img, "dice_marker")


# =========================================================== lobby icons
def ic_coin(img, c):
    x, y = c
    d = ImageDraw.Draw(img)
    d.ellipse([x - 15 * SC, y - 15 * SC, x + 15 * SC, y + 15 * SC],
              fill=(34, 20, 14, 255))

    def f(dd):
        dd.ellipse([x - 15 * SC, y - 15 * SC, x + 15 * SC, y + 15 * SC],
                   outline=(255, 255, 255, 255), width=2)
        dd.ellipse([x - 10 * SC, y - 10 * SC, x + 10 * SC, y + 10 * SC],
                   outline=(255, 255, 255, 160), width=1)
        for k in range(9):
            a = math.radians(-160 + k * 17.5)
            dd.line([(x, y + 4 * SC),
                     (x + math.cos(a) * 8 * SC, y + 4 * SC + math.sin(a) * 8 * SC)],
                    fill=(255, 255, 255, 230), width=1)
        dd.rectangle([x - 7 * SC, y + 4 * SC, x + 7 * SC, y + 7 * SC],
                     fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_dice(img, c):
    x, y = c
    d = ImageDraw.Draw(img)
    box = [x - 14 * SC, y - 14 * SC, x + 14 * SC, y + 14 * SC]
    d.polygon(chamfer_pts(box, 5 * SC), fill=(238, 231, 214, 255))
    for px, py in [(-7, -7), (7, -7), (0, 0), (-7, 7), (7, 7)]:
        d.ellipse([x + (px - 2.6) * SC, y + (py - 2.6) * SC,
                   x + (px + 2.6) * SC, y + (py + 2.6) * SC],
                  fill=(38, 16, 24, 255))
    _gold(img, lambda dd: dd.polygon(chamfer_pts(box, 5 * SC),
                                     outline=(255, 255, 255, 255), width=2))


def _geometry():
    """Hand the numbers this module draws with to build.py's harnesses.

    The tests assert on where sprites actually are, so they have to measure
    against the same geometry the art was drawn from rather than a second
    copy of it that can drift.
    """
    json.dump({"rungY": RUNG_Y, "pipX": PIP_X, "coinXY": list(COIN_XY),
               "coinFrames": COIN_FRAMES, "coinHeads": COIN_HEADS,
               "coinTails": COIN_TAILS,
               "railX0": RAIL_X0, "railX1": RAIL_X1, "railY": RAIL_Y,
               "markY": MARK_XY[1], "trackXY": list(TRACK_XY)},
              open(BUILD / "geom6.json", "w"))


# ================================================================== build
def build():
    from assets_v2 import lobby_tile
    coin_felt(); coins(); coin_ladder(); coin_pip()
    dice_felt(); dice_tracks(); dice_marker()
    deco_button("btn_flip", "FLIP", 108, 38, primary=True, fs=15, tracking=6)
    deco_button("btn_roll", "ROLL", 108, 38, primary=True, fs=15, tracking=6)
    for i, s in enumerate(["HEADS", "TAILS"], 1):
        selector(f"sel_call{i}", "CALL", s, w=64)
    for i, cap in enumerate(DICE_CAPS, 1):
        selector(f"sel_chance{i}", "CHANCE", cap, w=64)
    for i, s in enumerate(["UNDER", "OVER"], 1):
        selector(f"sel_side{i}", "ROLL", s, w=64)
    lobby_tile("lt_coin", "COIN FLIP", ic_coin)
    lobby_tile("lt_dice", "DICE", ic_dice)
    _geometry()


if __name__ == "__main__":
    build()
    print("coin flip + dice assets ok ->", OUT)
