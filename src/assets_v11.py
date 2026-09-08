"""Complete art-deco asset set for v1.1."""
from deco import *
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np, math, json, os

from paths import BUILD, ensure_tables
ensure_tables()
T = json.load(open(BUILD / "tables.json"))
BET_LEVELS = [5, 10, 15, 20, 25, 50, 75, 100, 150, 200, 250,
              500, 750, 1000, 1500, 2000, 2500, 5000]
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


def ic_slots(img, c):
    x, y = c
    def f(d):
        for i in (-1, 0, 1):
            bx = x + i * 14 * SC
            d.polygon(chamfer_pts([bx - 6 * SC, y - 14 * SC,
                                   bx + 6 * SC, y + 14 * SC], 3 * SC),
                      outline=(255, 255, 255, 255), width=2)
        d.text((x, y), "7", font=font(12 * SC), anchor="mm",
               fill=(255, 255, 255, 255))
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
SYMBOLS = [("7", GOLD, FB, 40), ("BAR", CYAN_NONE := GOLD, FB, 24),
           ("\u2660", CREAM, FR, 40), ("\u2665", (176, 30, 48), FR, 40),
           ("\u2666", (176, 30, 48), FR, 40), ("\u2663", CREAM, FR, 40),
           ("\u2605", GOLD, FR, 38), ("\u265b", CREAM, FR, 38)]


def symbols():
    w = 82
    for i, (ch, col, f, fs) in enumerate(SYMBOLS, 1):
        img = new(w, w)
        W = img.size[0]
        pts = chamfer_pts([2, 2, W - 3, W - 3], 12 * SC)
        ImageDraw.Draw(img).polygon(pts, fill=(13, 9, 13, 240))
        line = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        ImageDraw.Draw(line).polygon(pts, outline=(255, 255, 255, 90), width=2)
        img = Image.alpha_composite(img, gold_fill(line))
        if col in (GOLD,):
            lay = Image.new("RGBA", (W, W), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text((W / 2, W / 2), ch, font=font(fs * SC, f),
                                     anchor="mm", fill=(255, 255, 255, 255))
            img.alpha_composite(gold_fill(lay))
        else:
            ImageDraw.Draw(img).text((W / 2, W / 2), ch, font=font(fs * SC, f),
                                     anchor="mm", fill=col + (255,))
        save(img, f"sym{i}")


def slot_frame():
    img, (W, H) = panel(320, 150, cut=22 * SC, fill=(13, 9, 13, 236),
                        inner=9, width=3)
    d = ImageDraw.Draw(img)
    for i in (-1, 0, 1):
        cx = W / 2 + i * 96 * SC
        d.polygon(chamfer_pts([cx - 45 * SC, 32 * SC, cx + 45 * SC, 122 * SC],
                              10 * SC), fill=(6, 4, 7, 255))
        _gold(img, lambda dd, cx=cx: dd.polygon(
            chamfer_pts([cx - 45 * SC, 32 * SC, cx + 45 * SC, 122 * SC], 10 * SC),
            outline=(255, 255, 255, 150), width=2))
    tracked(img, (W / 2, 18 * SC), "LUCKY SEVENS", 10 * SC, 3.5 * SC, anchor="mm")
    return save(img, "slotframe")


def paytable():
    img, (W, H) = panel(118, 150, cut=14 * SC, fill=(13, 9, 13, 236),
                        inner=7, width=2)
    tracked(img, (W / 2, 18 * SC), "PAYS", 9 * SC, 3 * SC, anchor="mm")
    rows = [("7 7 7", "50x"), ("ANY x3", "12x"), ("7 7", "4x"), ("ANY x2", "1.8x")]
    for i, (a, b) in enumerate(rows):
        y = (42 + i * 24) * SC
        tracked(img, (14 * SC, y), a, 8.5 * SC, 1.2 * SC, color=CREAM,
                anchor="lm", gold=False)
        tracked(img, (W - 14 * SC, y), b, 8.5 * SC, 1.2 * SC, anchor="rm")
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
    tile("tile_slots", "SLOTS", "THREE REEL", ic_slots)
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
    symbols(); slot_frame(); paytable()
    for i in range(3): plinko_board(i)
    buckets(); ball(); mine_tiles(); card_back()
    for n in range(1, 53): card_face(n)
    messages()


if __name__ == "__main__":
    build()
    print("assets:", len(os.listdir(OUT)))
    print("bucket costumes:", len(BUCKET_VALS))
