"""v2 additions: roulette + stairs art, 6-slot lobby."""
from deco import *
from assets_v11 import (fit, panel, deco_button, round_button, selector,
                        plaque, _gold, _poly_mask)
import assets_v11 as A11
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np, math, json

from paths import BUILD, ensure_tables
ensure_tables()
T2 = json.load(open(BUILD / "tables2.json"))
WHEEL = T2["wheel"]; REDS = set(T2["red"]); DIFFS = T2["diffs"]
STAIR_ROWS = 9

RED_F  = (146, 24, 40)
BLK_F  = (22, 18, 24)
GRN_F  = (16, 78, 54)

# =============================================== roulette spot tiles
def _tile(w, h, fill, label, fs, cut=4, rule=175, tracking=0.6, gold=True,
          col=CREAM):
    img = new(w, h)
    W, H = img.size
    pts = chamfer_pts([1, 1, W - 2, H - 2], cut * SC)
    ImageDraw.Draw(img).polygon(pts, fill=fill + (250,))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(line).polygon(pts, outline=(255, 255, 255, rule), width=2)
    img = Image.alpha_composite(img, gold_fill(line))
    if label:
        s, tr = fit(label, fs * SC, tracking * SC, W - 6 * SC, floor=5)
        tracked(img, (W / 2, H / 2), label, s, tr, anchor="mm",
                color=col, gold=gold)
    return img


def roulette_spots():
    # 1 = zero, 2..37 = numbers 1..36, 38..49 = outside bets
    save(_tile(29, 78, GRN_F, "0", 15, cut=5, rule=210, gold=False), "rs1")
    for n in range(1, 37):
        fill = RED_F if n in REDS else BLK_F
        save(_tile(29, 25, fill, str(n), 12, gold=False), f"rs{n + 1}")
    outs = [("RED", 62, 24, RED_F), ("BLACK", 62, 24, BLK_F),
            ("ODD", 62, 24, (20, 14, 20)), ("EVEN", 62, 24, (20, 14, 20)),
            ("1-18", 62, 24, (20, 14, 20)), ("19-36", 62, 24, (20, 14, 20)),
            ("1st 12", 118, 24, (20, 14, 20)), ("2nd 12", 118, 24, (20, 14, 20)),
            ("3rd 12", 118, 24, (20, 14, 20)),
            ("COL 1", 118, 24, (20, 14, 20)), ("COL 2", 118, 24, (20, 14, 20)),
            ("COL 3", 118, 24, (20, 14, 20))]
    order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    # slot order: 38 RED 39 BLACK 40 ODD 41 EVEN 42 LOW 43 HIGH
    #             44,45,46 dozens   47,48,49 columns
    for i, oi in enumerate(order):
        lab, w, h, fill = outs[oi]
        save(_tile(w, h, fill, lab, 9.5, cut=5, rule=195, tracking=1.4),
             f"rs{38 + i}")


def chips():
    for i, d in enumerate([13, 15, 17, 19, 21], 1):
        img = new(d, d)
        W = img.size[0]
        ImageDraw.Draw(img).ellipse([1, 1, W - 2, W - 2], fill=(120, 22, 38, 255))
        line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        ld = ImageDraw.Draw(line)
        ld.ellipse([1, 1, W - 2, W - 2], outline=(255, 255, 255, 255), width=3)
        ld.ellipse([4 * SC, 4 * SC, W - 4 * SC, W - 4 * SC],
                   outline=(255, 255, 255, 160), width=1)
        save(Image.alpha_composite(img, gold_fill(line)), f"chip{i}")


# ====================================================== the wheel
def wheel(dia=196):
    img = new(dia, dia)
    W = img.size[0]
    c = W / 2
    R = c - 5 * SC
    d = ImageDraw.Draw(img)
    step = 360 / 37
    for k, n in enumerate(WHEEL):
        a0 = -90 + k * step - step / 2
        fill = GRN_F if n == 0 else (RED_F if n in REDS else BLK_F)
        d.pieslice([c - R, c - R, c + R, c + R], a0, a0 + step,
                   fill=fill + (255,))
    # solid hub over the wedge fills
    d.ellipse([c - R * 0.56, c - R * 0.56, c + R * 0.56, c + R * 0.56],
              fill=(14, 10, 14, 255))
    d.ellipse([c - R * 0.30, c - R * 0.30, c + R * 0.30, c + R * 0.30],
              fill=(34, 10, 18, 255))
    # pocket separators + rim
    line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    for k in range(37):
        a = math.radians(-90 + k * step - step / 2)
        ld.line([(c + math.cos(a) * R * 0.56, c + math.sin(a) * R * 0.56),
                 (c + math.cos(a) * R, c + math.sin(a) * R)],
                fill=(255, 255, 255, 150), width=1)
    ld.ellipse([c - R, c - R, c + R, c + R], outline=(255, 255, 255, 255), width=3)
    ld.ellipse([c - R * 0.56, c - R * 0.56, c + R * 0.56, c + R * 0.56],
               outline=(255, 255, 255, 220), width=2)
    ld.ellipse([c - R * 0.30, c - R * 0.30, c + R * 0.30, c + R * 0.30],
               outline=(255, 255, 255, 190), width=2)
    for k in range(12):
        a = math.radians(k * 30)
        ld.line([(c + math.cos(a) * R * 0.30, c + math.sin(a) * R * 0.30),
                 (c + math.cos(a) * R * 0.56, c + math.sin(a) * R * 0.56)],
                fill=(255, 255, 255, 120), width=1)
    img = Image.alpha_composite(img, gold_fill(line))
    # numbers
    fnt = font(9 * SC)
    for k, n in enumerate(WHEEL):
        a = math.radians(-90 + k * step)
        tx, ty = c + math.cos(a) * R * 0.78, c + math.sin(a) * R * 0.78
        lab = Image.new("RGBA", (26 * SC, 16 * SC), (0, 0, 0, 0))
        ImageDraw.Draw(lab).text((13 * SC, 8 * SC), str(n), font=fnt,
                                 anchor="mm", fill=(245, 238, 222, 255))
        lab = lab.rotate(-(math.degrees(a) + 90), expand=False,
                         resample=Image.BICUBIC)
        img.alpha_composite(lab, (int(tx - 13 * SC), int(ty - 8 * SC)))
    return save(img, "wheel")


def wheel_panel():
    img, (W, H) = panel(232, 236, cut=26 * SC, fill=(10, 6, 11, 246),
                        inner=10, width=3)
    return save(img, "wheelpanel")


def pointer():
    img = new(18, 16)
    W, H = img.size
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([(W / 2, H - 2), (W - 2, 2), (2, 2)],
                                fill=(255, 255, 255, 255))
    img.alpha_composite(gold_fill(lay))
    return save(img, "pointer")


# ========================================================== stairs
def stair_tiles():
    w, h = 46, 22
    pts = lambda W, H: chamfer_pts([1, 1, W - 2, H - 2], 5 * SC)
    # hidden
    img = new(w, h); W, H = img.size
    ImageDraw.Draw(img).polygon(pts(W, H), fill=(24, 16, 22, 246))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts(W, H), outline=(255, 255, 255, 175), width=2)
    ld.line([(W / 2 - 5 * SC, H / 2 + 2 * SC), (W / 2, H / 2 - 3 * SC),
             (W / 2 + 5 * SC, H / 2 + 2 * SC)], fill=(255, 255, 255, 140),
            width=2, joint="curve")
    save(Image.alpha_composite(img, gold_fill(line)), "st_hidden")
    # safe (revealed, not picked)
    img = new(w, h)
    ImageDraw.Draw(img).polygon(pts(W, H), fill=(30, 22, 12, 220))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts(W, H), outline=(255, 255, 255, 105), width=2)
    ld.polygon([(W / 2, H / 2 - 5 * SC), (W / 2 + 5 * SC, H / 2),
                (W / 2, H / 2 + 5 * SC), (W / 2 - 5 * SC, H / 2)],
               outline=(255, 255, 255, 150), width=2)
    save(Image.alpha_composite(img, gold_fill(line)), "st_safe")
    # picked
    img = new(w, h)
    ImageDraw.Draw(img).polygon(pts(W, H), fill=(74, 54, 10, 250))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts(W, H), outline=(255, 255, 255, 255), width=2)
    ld.polygon([(W / 2, H / 2 - 6 * SC), (W / 2 + 6 * SC, H / 2),
                (W / 2, H / 2 + 6 * SC), (W / 2 - 6 * SC, H / 2)],
               fill=(255, 255, 255, 255))
    save(Image.alpha_composite(img, gold_fill(line)), "st_pick")
    # bomb
    img = new(w, h)
    ImageDraw.Draw(img).polygon(pts(W, H), fill=(80, 14, 28, 250))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(line).polygon(pts(W, H), outline=(255, 255, 255, 205), width=2)
    img = Image.alpha_composite(img, gold_fill(line))
    ImageDraw.Draw(img).ellipse([W / 2 - 6 * SC, H / 2 - 5 * SC,
                                 W / 2 + 6 * SC, H / 2 + 7 * SC],
                                fill=(12, 9, 12, 255))
    _gold(img, lambda d: d.line([(W / 2 + 3 * SC, H / 2 - 5 * SC),
                                 (W / 2 + 8 * SC, H / 2 - 10 * SC)],
                                fill=(255, 255, 255, 255), width=2))
    save(img, "st_bomb")


def stair_mults():
    """45 labels: 5 difficulties x 9 rows."""
    i = 0
    for name, _t, _b in DIFFS:
        for v in T2["stairs"][name]:
            i += 1
            img = new(46, 18)
            W, H = img.size
            txt = f"{v:g}x"
            s, tr = fit(txt, 9 * SC, 0.5 * SC, W - 4 * SC, floor=5)
            tracked(img, (W / 2, H / 2), txt, s, tr, anchor="mm")
            save(img, f"sm{i}")


# ========================================================= lobby v2
LW, LH = 130, 84


def lobby_tile(name, label, icon):
    img = new(LW, LH)
    W, H = img.size
    pts = chamfer_pts([2, 2, W - 3, H - 3], 16 * SC)
    ImageDraw.Draw(img).polygon(pts, fill=(18, 11, 15, 242))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([W * .08, H * .1, W * .92, H * 1.4],
                                fill=BURG + (100,))
    img = Image.alpha_composite(img, lay.filter(ImageFilter.GaussianBlur(48)))
    img.putalpha(Image.fromarray((np.asarray(img.split()[3]).astype(float) *
                                  np.asarray(_poly_mask((W, H), pts)) / 255
                                  ).astype("uint8")))
    line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.polygon(pts, outline=(255, 255, 255, 255), width=3)
    ld.polygon(chamfer_pts([8 * SC, 8 * SC, W - 3 - 8 * SC, H - 3 - 8 * SC],
                           11 * SC), outline=(255, 255, 255, 115), width=1)
    img = Image.alpha_composite(img, gold_fill(line))
    icon(img, (W / 2, 30 * SC))
    s, tr = fit(label, 13 * SC, 2.4 * SC, W - 22 * SC)
    tracked(img, (W / 2, 64 * SC), label, s, tr, anchor="mm")
    return save(img, name)


def ic_slots(img, c):
    x, y = c
    def f(d):
        for i in (-1, 0, 1):
            bx = x + i * 12 * SC
            d.polygon(chamfer_pts([bx - 5 * SC, y - 12 * SC,
                                   bx + 5 * SC, y + 12 * SC], 3 * SC),
                      outline=(255, 255, 255, 255), width=2)
        d.text((x, y), "7", font=font(11 * SC), anchor="mm",
               fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_plinko(img, c):
    x, y = c
    def f(d):
        for r in range(4):
            for i in range(r + 1):
                px, py = x + (i - r / 2) * 9 * SC, y - 13 * SC + r * 7 * SC
                d.ellipse([px - 2 * SC, py - 2 * SC, px + 2 * SC, py + 2 * SC],
                          fill=(255, 255, 255, 255))
        d.ellipse([x - 3.5 * SC, y + 12 * SC, x + 3.5 * SC, y + 19 * SC],
                  fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_mines(img, c):
    x, y = c
    def f(d):
        for r in range(3):
            for cc in range(3):
                bx, by = x + (cc - 1) * 11 * SC, y + (r - 1) * 11 * SC
                d.polygon(chamfer_pts([bx - 4.5 * SC, by - 4.5 * SC,
                                       bx + 4.5 * SC, by + 4.5 * SC], 2 * SC),
                          outline=(255, 255, 255, 215), width=2)
        d.ellipse([x - 3.5 * SC, y - 3.5 * SC, x + 3.5 * SC, y + 3.5 * SC],
                  fill=(255, 255, 255, 255))
    _gold(img, f)


def ic_bj(img, c):
    x, y = c
    d = ImageDraw.Draw(img)
    d.polygon(chamfer_pts([x - 15 * SC, y - 15 * SC, x + 1 * SC, y + 8 * SC],
                          3 * SC), fill=(226, 218, 200, 255))
    d.polygon(chamfer_pts([x - 3 * SC, y - 8 * SC, x + 15 * SC, y + 16 * SC],
                          3 * SC), fill=(244, 238, 224, 255))
    _gold(img, lambda dd: dd.polygon(
        chamfer_pts([x - 3 * SC, y - 8 * SC, x + 15 * SC, y + 16 * SC], 3 * SC),
        outline=(255, 255, 255, 255), width=2))
    d.text((x + 6 * SC, y + 3 * SC), "A", font=font(10 * SC, FS), anchor="mm",
           fill=(28, 16, 22))


def ic_roulette(img, c):
    x, y = c
    d = ImageDraw.Draw(img)
    R = 14 * SC
    for k in range(12):
        a0 = -90 + k * 30
        d.pieslice([x - R, y - R, x + R, y + R], a0, a0 + 30,
                   fill=(RED_F if k % 2 else BLK_F) + (255,))
    def f(dd):
        dd.ellipse([x - R, y - R, x + R, y + R], outline=(255, 255, 255, 255),
                   width=2)
        dd.ellipse([x - R * .38, y - R * .38, x + R * .38, y + R * .38],
                   outline=(255, 255, 255, 220), width=2)
        for k in range(12):
            a = math.radians(k * 30)
            dd.line([(x + math.cos(a) * R * .38, y + math.sin(a) * R * .38),
                     (x + math.cos(a) * R, y + math.sin(a) * R)],
                    fill=(255, 255, 255, 130), width=1)
    _gold(img, f)


def ic_stairs(img, c):
    x, y = c
    def f(d):
        for i in range(4):
            sx = x - 15 * SC + i * 8 * SC
            sy = y + 12 * SC - i * 7 * SC
            d.polygon(chamfer_pts([sx, sy - 5 * SC, sx + 9 * SC, sy], 1.5 * SC),
                      outline=(255, 255, 255, 235), width=2)
        d.polygon([(x + 12 * SC, y - 15 * SC), (x + 16 * SC, y - 9 * SC),
                   (x + 8 * SC, y - 9 * SC)], fill=(255, 255, 255, 255))
    _gold(img, f)


def build():
    deco_button("btn_double", "DOUBLE", 92, 38, fs=11, tracking=3)
    deco_button("btn_split", "SPLIT", 92, 38, fs=11, tracking=3)
    deco_button("btn_insure", "INSURE", 92, 38, primary=True, fs=11, tracking=3)
    deco_button("btn_noins", "NO", 92, 38, fs=12, tracking=3)
    plaque("plq_dealer", "DEALER", w=62)
    plaque("plq_you", "YOU", w=62)
    roulette_spots(); chips(); wheel(); wheel_panel(); pointer()
    stair_tiles(); stair_mults()
    for i, (n, _t, _b) in enumerate(DIFFS, 1):
        selector(f"sel_diff{i}", "MODE", n, w=64)
    deco_button("btn_clear", "CLEAR", 58, 38, fs=9, tracking=2)
    deco_button("btn_undo", "UNDO", 58, 38, fs=9, tracking=2)
    plaque("plq_stake", "STAKE", w=58)
    lobby_tile("lt_slots", "SLOTS", ic_slots)
    lobby_tile("lt_plinko", "PLINKO", ic_plinko)
    lobby_tile("lt_mines", "MINES", ic_mines)
    lobby_tile("lt_bj", "BLACKJACK", ic_bj)
    lobby_tile("lt_roulette", "ROULETTE", ic_roulette)
    lobby_tile("lt_stairs", "STAIRS", ic_stairs)


if __name__ == "__main__":
    A11.build(); build()
    import os
    print("total assets:", len(os.listdir(OUT)))
