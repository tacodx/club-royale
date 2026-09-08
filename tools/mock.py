"""Composite every screen at the exact coordinates the sprites use.

Catches collisions and off-stage elements that logic tests cannot see.
Run: make mocks   ->   mocks/*.png
"""
import sys, os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image
import assets_v11 as A11, assets_v2 as A2
from paths import ASSETS, BUILD

A = str(ASSETS)
OUT = ROOT / "mocks"
OUT.mkdir(exist_ok=True)
T = A11.T
T2 = json.load(open(BUILD / "tables2.json"))
ROWC, ROWSP, ROWHS = A11.ROWCOUNT, A11.ROWSP, A11.ROWHS
BKV = A11.BUCKET_VALS
DCH = list("0123456789") + [".", ",", "", "x", "M", "B"]  # "" is the blank, d13


def stage():
    return Image.open(f"{A}/bg.png").convert("RGBA")


def put(c, n, x, y, size=100, ghost=0):
    im = Image.open(f"{A}/{n}.png").convert("RGBA")
    if size != 100:
        im = im.resize((max(1, int(im.width * size / 100)),
                        max(1, int(im.height * size / 100))))
    if ghost:
        im.putalpha(im.split()[3].point(lambda v: int(v * (1 - ghost))))
    c.alpha_composite(im, (int(480 + 2 * x - im.width / 2),
                           int(360 - 2 * y - im.height / 2)))


def dig(c, s, cx, y, gap=16, mode="C"):
    L = len(s)
    for i, ch in enumerate(s, 1):
        x = cx + gap * (i - 1) if mode == "L" else cx + gap * ((i - 1) - (L - 1) / 2)
        put(c, f"d{DCH.index(ch) + 1}", x, y)


def chrome(c, chips="12,450"):
    dig(c, chips, -166, 163, 15, "L")
    put(c, "btn_back", 192, 163)


def betbar(c, amount="100"):
    put(c, "btn_minus", -205, -152)
    put(c, "bet_plaque", -152, -152)
    dig(c, amount, -152, -157, 14)
    put(c, "btn_plus", -99, -152)


SPOTX = [-180] + [-150 + ((n - 1) // 3) * 30 for n in range(1, 37)] + \
        [-30, 30, 90, -90, -150, 150] + [-105, 15, 135] + [-105, 15, 135]
SPOTY = [50] + [24 + ((n - 1) % 3) * 26 for n in range(1, 37)] + \
        [-34] * 6 + [-6] * 3 + [-62] * 3


def lobby():
    c = stage(); put(c, "title", 0, 106)
    # nine tiles: five across the top, four centred beneath (see build.py)
    for i, t in enumerate(["lt_slots", "lt_plinko", "lt_mines", "lt_bj",
                           "lt_roulette", "lt_stairs", "lt_duck", "lt_crash",
                           "lt_avia"], 1):
        if i <= 5:
            put(c, t, -176 + 88 * (i - 1), 30)
        else:
            put(c, t, -132 + 88 * (i - 6), -58)
    chrome(c); return c


def slots():
    c = stage()
    put(c, "slotframe", -52, 25); put(c, "paytable", 168, 25)
    for i, s in enumerate(["sym1", "sym1", "sym5"]):
        put(c, s, -148 + 96 * i, 24)
    betbar(c); put(c, "btn_spin", 75, -152); put(c, "msg_bigwin", 0, -104)
    chrome(c); return c


def plinko(ri, risk="med"):
    rows, sp, hs = ROWC[ri], ROWSP[ri], ROWHS[ri]
    c = stage()
    put(c, f"board{rows}", 0, -92 + (rows - 1) * sp / 2)
    tab = T["plinko"][f"{rows}_{risk}"]
    for b in range(1, rows + 2):
        put(c, f"bk{BKV.index(tab[b - 1]) + 1}",
            hs * (b - 1) - hs * rows / 2, -112, size=hs / 21 * 100)
    y0 = -92 + (rows - 1) * sp
    for bx, by in [(0, y0 + 24), (-hs / 2, y0 - sp), (hs, y0 - 4 * sp)]:
        put(c, "ball", bx, by)
    betbar(c)
    put(c, f"sel_rows{ri + 1}", -40, -152)
    put(c, f"sel_risk{['low','med','high'].index(risk) + 1}", 24, -152)
    put(c, "btn_drop", 110, -152); chrome(c); return c


def mines():
    c = stage()
    bombs, gems = {7, 13, 22}, {1, 2, 3, 6, 11}
    for i in range(1, 26):
        t = ("tile_gem" if i in gems else
             ("tile_bomb" if i in bombs else "tile_hidden"))
        put(c, t, -96 + 48 * ((i - 1) % 5), 100 - 48 * ((i - 1) // 5))
    betbar(c); put(c, "sel_bombs2", -45, -152)
    put(c, "btn_start", 52, -152); put(c, "btn_cashout", 158, -152)
    put(c, "plq_mult", 0, 163); dig(c, "2.28", 86, 163, 14)
    chrome(c); return c


def stairs():
    c = stage(); tiles = 3
    for r in range(1, 10):
        for col in range(1, tiles + 1):
            x = -35 + 50 * ((col - 1) - (tiles - 1) / 2)
            y = -98 + 26 * (r - 1)
            if r < 4:
                n = ("st_pick" if col == 2 else
                     ("st_bomb" if col == 1 else "st_safe"))
            else:
                n = "st_hidden"
            put(c, n, x, y)
        put(c, f"sm{9 + r}", 125, -98 + 26 * (r - 1),
            ghost=0 if r == 4 else 0.55)
    betbar(c); put(c, "sel_diff2", -45, -152)
    put(c, "btn_start", 52, -152); put(c, "btn_cashout", 158, -152)
    put(c, "plq_mult", 0, 163); dig(c, "4.86", 86, 163, 14)
    chrome(c); return c


def duck(lane=5, egg=True):
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import assets_v3 as AV3
    c = stage()
    put(c, "duckroad", 0, 0)
    mode = 2                                   # MEDIUM
    for i in range(1, 13):
        idx = (mode - 1) * 12 + i + (48 if egg and i <= lane else 0)
        put(c, f"dm{idx}", AV3.LANE_X[i - 1], AV3.LABEL_Y,
            ghost=0 if i == lane else 0.55)
    # ambient traffic in lanes the duck is not standing in
    for i, cn in [(2, "dcar1"), (8, "dcar3"), (11, "dcar2")]:
        put(c, cn, AV3.LANE_X[i - 1], 40 - 22 * i, size=84, ghost=0.42)
    x = AV3.LANE_X[lane - 1] if lane else AV3.KERB_X
    put(c, "duck1", x, AV3.DUCK_Y)
    if egg:
        put(c, "degg", x, AV3.DUCK_Y + 24)
    betbar(c); put(c, "sel_duck2", -45, -152)
    put(c, "btn_go", 52, -152); put(c, "btn_cashout", 158, -152)
    put(c, "plq_mult", 0, 163); dig(c, "7.27", 86, 163, 14)
    chrome(c); return c


def crash(mult="4.86", flying=True):
    import sys, math
    sys.path.insert(0, str(ROOT / "src"))
    import assets_v4 as AV4
    c = stage()
    put(c, "crsky", 0, 0)
    for i, (sn, sx, sy) in enumerate([("crspark3", -120, 40), ("crspark2", 30, -20),
                                      ("crspark1", 150, 70), ("crspark2", -60, -60)], 1):
        put(c, sn, sx, sy, ghost=0.45)
    prog = min(1.0, math.log10(float(mult))) if flying else 0.0
    rx = AV4.ROCK_X0 + (AV4.ROCK_X1 - AV4.ROCK_X0) * prog
    ry = AV4.ROCK_Y0 + (AV4.ROCK_Y1 - AV4.ROCK_Y0) * prog
    put(c, "crrocket3" if prog > 0.35 else ("crrocket2" if flying else "crrocket1"),
        rx, ry)
    dig(c, mult + "x", AV4.MULT_XY[0], AV4.MULT_XY[1], AV4.MULT_GAP)
    betbar(c); put(c, "sel_auto3", -45, -152)
    if flying:
        put(c, "btn_cashout", 158, -152)
    else:
        put(c, "btn_launch", 52, -152)
    chrome(c); return c


def avia(slot=6, mult="3.75", flying=True):
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import assets_v4 as AV4, assets_v5 as AV5
    c = stage()
    put(c, "avsky", 0, 0)
    # scenery orbs drifting past, one per clone
    for i, ox in enumerate([150, 60, -40, -130, 190], 1):
        put(c, f"avorb{2 + (i % 5)}", ox, AV5.PLANE_LO + 12 + 22 * (i % 4),
            ghost=0.3)
    prog = slot / 14
    if not flying:
        px, py, cost = AV5.CARRIER_L, AV5.DECK_Y + 6, "avplane1"
    else:
        px = AV5.PLANE_X
        py = AV5.PLANE_LO + (AV5.PLANE_HI - AV5.PLANE_LO) * prog
        cost = "avplane2"
    put(c, cost, px, py)
    if flying:                                    # the orb just collected
        put(c, "avorb4", px + 30, py, size=118, ghost=0.15)
    dig(c, mult + "x", AV4.MULT_XY[0], AV4.MULT_XY[1], AV4.MULT_GAP)
    betbar(c); put(c, "sel_auto3", -45, -152)
    if flying:
        put(c, "btn_cashout", 158, -152)
    else:
        put(c, "btn_takeoff", 52, -152)
    chrome(c); return c


def roulette(spinning=False):
    c = stage()
    for i in range(1, 50):
        put(c, f"rs{i}", SPOTX[i - 1], SPOTY[i - 1])
    if spinning:
        put(c, "wheelpanel", 0, 14); put(c, "wheel", 0, 28)
        put(c, "pointer", 0, 133); dig(c, "17", 0, -86, 16)
        put(c, "btn_spin", 110, -152)
    else:
        for i, tier in [(18, 3), (38, 4), (45, 2), (2, 1)]:
            put(c, f"chip{tier}", SPOTX[i - 1], SPOTY[i - 1])
        put(c, "btn_clear", -40, -152); put(c, "btn_undo", 24, -152)
        put(c, "btn_spin", 110, -152)
    betbar(c)
    put(c, "plq_stake", 0, 163); dig(c, "250", 86, 163, 14)
    chrome(c); return c


def blackjack(mode="hand"):
    c = stage()
    if mode == "idle":
        betbar(c); put(c, "btn_deal", 75, -152); chrome(c); return c
    for i, n in enumerate([9, 22], 1):
        put(c, f"card{n}", (i - 1 - 0.5) * 38, 70)
    put(c, "card_back", 0.5 * 38, 70)
    put(c, "plq_dealer", -168, 100); dig(c, "9", -168, 74)
    put(c, "plq_you", -168, -12)
    if mode == "split":
        for i, n in enumerate([8, 34, 5, 17, 29, 41], 1):
            put(c, f"card{n}", -45 + 22 * ((i - 1) - 2.5), -42, ghost=.55)
        for i, n in enumerate([21, 45, 3, 11, 50], 1):
            put(c, f"card{n}", 130 + 22 * ((i - 1) - 2), -42)
        dig(c, "19", -168, -38); dig(c, "14", -168, -66)
        put(c, "btn_hit", -150, -152); put(c, "btn_stand", -50, -152)
    elif mode == "insurance":
        for i, n in enumerate([24, 37], 1):
            put(c, f"card{n}", (i - 1 - 0.5) * 38, -42)
        dig(c, "21", -168, -38)
        put(c, "btn_insure", -60, -152); put(c, "btn_noins", 60, -152)
    else:
        for i, n in enumerate([8, 21], 1):
            put(c, f"card{n}", (i - 1 - 0.5) * 38, -42)
        dig(c, "18", -168, -38)
        put(c, "btn_hit", -150, -152); put(c, "btn_stand", -50, -152)
        put(c, "btn_double", 50, -152); put(c, "btn_split", 150, -152)
    chrome(c); return c


SCREENS = {
    "lobby": lobby, "slots": slots,
    "plinko_8": lambda: plinko(0, "low"),
    "plinko_12": lambda: plinko(1, "med"),
    "plinko_16": lambda: plinko(2, "high"),
    "mines": mines, "stairs": stairs,
    "duck_road": lambda: duck(5, True),
    "duck_start": lambda: duck(0, False),
    "crash_flight": lambda: crash("4.86", True),
    "crash_idle": lambda: crash("1.00", False),
    "avia_flight": lambda: avia(6, "3.75", True),
    "avia_idle": lambda: avia(0, "1.00", False),
    "roulette_bets": lambda: roulette(False),
    "roulette_spin": lambda: roulette(True),
    "blackjack_idle": lambda: blackjack("idle"),
    "blackjack_hand": lambda: blackjack("hand"),
    "blackjack_split": lambda: blackjack("split"),
    "blackjack_insurance": lambda: blackjack("insurance"),
}

# the nine screens that go in the README banner, one per game
BANNER = ["slots", "plinko_12", "mines", "blackjack_hand", "roulette_bets",
          "stairs", "duck_road", "crash_flight", "avia_flight"]


def banner(cols=3, cell_w=490, gap=4):
    """docs/screens.png, composed from the rendered screens.

    Hand-assembled until v3.9, which is why it still showed eight games after
    the ninth shipped. Generated from BANNER now, so adding a game to SCREENS
    and to that list is all it takes.
    """
    cell_h = round(cell_w * 720 / 960)
    rows = (len(BANNER) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * gap,
                              rows * cell_h + (rows + 1) * gap), (10, 8, 12))
    for i, name in enumerate(BANNER):
        im = Image.open(OUT / f"{name}.png").convert("RGB").resize((cell_w, cell_h))
        sheet.paste(im, (gap + (i % cols) * (cell_w + gap),
                         gap + (i // cols) * (cell_h + gap)))
    out = ROOT / "docs" / "screens.png"
    sheet.save(out)
    print(f"  docs/screens.png ({len(BANNER)} games)")


if __name__ == "__main__":
    A11.build(); A2.build()
    want = sys.argv[1:] or list(SCREENS)
    for name in want:
        SCREENS[name]().convert("RGB").save(OUT / f"{name}.png")
        print("  mocks/" + name + ".png")
    sheet = Image.new("RGB", (1930, 725 * ((len(want) + 1) // 2)), (14, 12, 16))
    for i, name in enumerate(want):
        sheet.paste(Image.open(OUT / f"{name}.png"),
                    (10 + (i % 2) * 965, 10 + (i // 2) * 725))
    sheet.save(OUT / "_all.png")
    print(f"{len(want)} screens -> mocks/_all.png")
    if all(n in want for n in BANNER):
        banner()
