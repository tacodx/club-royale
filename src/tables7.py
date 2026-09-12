"""Slots: 3x3 grid, 5 paylines, weighted 30-stop reel strips, one wild.

The old slots rolled three independent `rand(1, 8)` and paid a hand-written
ladder for 94.3% RTP. Nothing about it was solved and nothing was weighted, so
a 7 was exactly as likely as a club and the only tension was whether three
uniform draws happened to agree.

This is a real machine. Each reel is a fixed strip of 30 stops; a spin picks
one stop per reel and the column shows that stop and its two cyclic
neighbours, so the three rows of a reel are *adjacent strip cells*. A miss is
visibly a miss by one position rather than three unrelated draws, and how
often a symbol lands is a property of where it was placed on the strip - which
is what a weighted reel is.

Every line takes one cell from each reel, and all five lines are marginally
identical: each sees one uniform stop per reel. So the return is linear in the
per-line pays and the whole game is solved by solving one line:

    RTP = (sum over the 27000 weighted triples of what that triple pays) / 27000

STRIP_LEN = 30 is not decorative. Landing exactly on 24/25 with integer pays
needs 0.96 * STRIP_LEN**3 to be a whole number: 0.96 * 30**3 = 25920 is,
0.96 * 32**3 = 31457.28 is not. Every other solver in this repo bisects a
scale and tolerates the rounding; this one closes on the target exactly, like
tables6.py, and the assertions below are equalities rather than tolerances.

Two knobs are chosen rather than solved, the way tables.py chooses SHAPE and
then solves the scale: which symbols pay from two (the near-miss rung) and
what that rung pays. Everything else - the whole 3-of-a-kind ladder - is
solved to spread the remaining return as evenly across the nine symbols as
integers allow, so no single rung carries the game.
"""
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction as F

HOUSE = F(96, 100)

# --------------------------------------------------------------- symbols
# The id is the Digit-style costume number: sym1..sym9 in assets_v11.py, and
# the index into slPay3/slPay2 in the VM. Ids are frozen - inserting a symbol
# in the middle silently re-maps every strip entry and every pay row, and
# tests/validate.py only checks that a costume *named* s1 exists (PITFALLS 6).
DIAMOND, CROWN, JACK, QUEEN, KING, ACE, FAN, COUPE, WILD = range(1, 10)
SYMS = list(range(1, 10))
NAMES = {DIAMOND: "DIAMOND", CROWN: "CROWN", JACK: "JACK", QUEEN: "QUEEN",
         KING: "KING", ACE: "ACE", FAN: "FAN", COUPE: "COUPE", WILD: "WILD"}
LETTER = {"D": DIAMOND, "C": CROWN, "J": JACK, "Q": QUEEN, "K": KING,
          "A": ACE, "F": FAN, "P": COUPE, "W": WILD}
COMMON = (JACK, QUEEN, KING, ACE)          # the four low symbols, one pay row

# --------------------------------------------------------------- strips
# 30 stops per reel. Reel 2 is wild-heavy (3 of them) and reel 3 is starved
# (one wild, one diamond), which makes "two high symbols and a miss on reel 3"
# the common shape - the near-miss this game is built around. The four commons
# repeat as a JQKA block so that every strip reads as a run of court cards
# broken by a premium, and no premium ever sits next to a copy of itself.
STRIP_LEN = 30
STRIP_TXT = [
    "JQKAFCPDWJQKAFCPJQKAFDWCPJQKAF",
    "JQKACPFWDJQKACPFWJQKADCPFWJQKA",
    "JQKAFCPJQKAFDJQKAWFJQKACPFJQKA",
]
REELS = len(STRIP_TXT)
ROWS = 3
STRIPS = [[LETTER[ch] for ch in s] for s in STRIP_TXT]

for _r, _st in enumerate(STRIPS):
    assert len(_st) == STRIP_LEN, (_r, len(_st))
    # Every occurrence of every symbol must be isolated, read cyclically. A
    # counts-only check would pass a strip whose two diamonds had merged into
    # one run of two - the counts are identical, but the window distribution
    # this solver enumerates is then fiction, because a run of two can show
    # the same symbol twice in one column.
    for _s in set(_st):
        _runs, _i = [], 0
        while _i < STRIP_LEN:
            if _st[_i] == _s:
                _n = 1
                while _n < STRIP_LEN and _st[(_i + _n) % STRIP_LEN] == _s:
                    _n += 1
                _runs.append(_n)
                _i += _n
            else:
                _i += 1
        assert set(_runs) == {1}, (_r, NAMES[_s], _runs)

COUNTS = [Counter(st) for st in STRIPS]
for _s in SYMS:                              # every symbol reachable on every reel
    for _r in range(REELS):
        assert COUNTS[_r][_s] > 0, (_r, NAMES[_s])

TOT = STRIP_LEN ** REELS                     # 27000 triples per line
TARGET = HOUSE.numerator * TOT // HOUSE.denominator
assert TARGET * HOUSE.denominator == HOUSE.numerator * TOT, "strip length not exact"

# -------------------------------------------------------------- paylines
# Cell index is (col - 1) * 3 + row, rows top to bottom. The VM reads these
# from one flat 15-entry list because Scratch has no 2-D lists.
LINES = [(1, 1, 1),        # middle row
         (0, 0, 0),        # top row
         (2, 2, 2),        # bottom row
         (0, 1, 2),        # diagonal down
         (2, 1, 0)]        # diagonal up
LINES_FLAT = [c * ROWS + r + 1 for line in LINES for c, r in enumerate(line)]
assert len(LINES_FLAT) == len(LINES) * REELS == 15


def evaluate(a, b, c):
    """The one payline rule, stated once. Returns (symbol, run length).

    A line pays on its leading run from reel 1 only. WILD substitutes for
    everything, so the line's symbol is the first non-wild cell scanning left
    to right - and if all three are wild, the symbol is WILD itself. The run
    is 3 when reels 2 and 3 both match-or-wild, 2 when only reel 2 does, and
    1 otherwise. A line pays at most one value; there is no second pay path
    and no scatter.
    """
    base = a if a != WILD else (b if b != WILD else c)
    if b == base or b == WILD:
        run = 3 if (c == base or c == WILD) else 2
    else:
        run = 1
    return base, run


# How many of the 27000 triples land on each (symbol, run) rung. This is the
# closed form the ladder is solved against; the joint enumeration further down
# re-derives the same histogram a second way and asserts they agree.
COEF = Counter()
for _a, _na in COUNTS[0].items():
    for _b, _nb in COUNTS[1].items():
        for _c, _nc in COUNTS[2].items():
            _base, _run = evaluate(_a, _b, _c)
            if _run >= 2:
                COEF[(_base, _run)] += _na * _nb * _nc
assert sum(COEF[(s, 3)] for s in SYMS) + sum(COEF[(s, 2)] for s in SYMS) <= TOT
# A leading WILD WILD always resolves to whatever reel 3 shows, so the line is
# either a 3-run of that symbol or a 3-run of wilds. (WILD, 2) cannot happen,
# and the ladder must not quietly price a rung that no spin can reach.
assert (WILD, 2) not in COEF, COEF[(WILD, 2)]

# ------------------------------------------------------------ the ladder
# CHOSEN, not solved (the tables.py SHAPE precedent): the three premium
# symbols pay from two, at 2 unit stakes. It is the near-miss rung - two
# crowns and a miss on reel 3 pays 0.4x the total bet rather than nothing -
# and it costs 13.0% of the return, which is the price of the game feeling
# alive between 3-of-a-kinds.
PAY_FROM_TWO = (DIAMOND, CROWN, COUPE)
PAY2_UNITS = 2
PAY2 = {s: (PAY2_UNITS if s in PAY_FROM_TWO else 0) for s in SYMS}
ROOM = TARGET - sum(COEF[(s, 2)] * PAY2[s] for s in SYMS)

# SOLVED: the 3-of-a-kind ladder. Fair odds for a symbol is TOT / COEF[s, 3]
# unit stakes - pay that, scaled, and every symbol returns the same share of
# the RTP, so the ladder hides no better rung and none of it rests on one
# jackpot. Integers cannot sit on fair odds exactly, so the objective is to
# minimise the largest relative miss (then the total miss to break ties),
# subject to: equal odds pay equally, and the ladder is strictly ordered by
# rarity - a rarer symbol never pays less than a commoner one.
GROUPS = {}                                  # 3-run coefficient -> [symbol ids]
for _s in SYMS:
    GROUPS.setdefault(COEF[(_s, 3)], []).append(_s)
GROUP_KEYS = sorted(GROUPS, reverse=True)    # commonest group first
FAIR = {s: F(ROOM, COEF[(s, 3)] * len(SYMS)) for s in SYMS}


def _base_ladder():
    """Fair-odds pays rounded to integers, before the residual is closed."""
    return {s: max(1, int(FAIR[s] + F(1, 2))) for s in SYMS}


def _ordered(pay):
    """Strictly decreasing in commonness, and every win worth having."""
    seq = [pay[GROUPS[k][0]] for k in GROUP_KEYS]
    return all(a < b for a, b in zip(seq, seq[1:])) and seq[0] >= 1


def solve():
    base = _base_ladder()
    weight = {k: COEF[(GROUPS[k][0], 3)] * len(GROUPS[k]) for k in GROUP_KEYS}
    rarest = GROUP_KEYS[-1]                  # smallest coefficient: closes exactly
    # Search a delta per group, proportional to that group's own pay so the
    # grid means the same thing at 10 units and at 400, and read the last
    # group off the residual instead of searching it.
    spans = [range(-max(2, base[GROUPS[k][0]] // 4),
                   max(2, base[GROUPS[k][0]] // 4) + 1) for k in GROUP_KEYS[:-1]]
    best = None
    stack = [(0, ROOM - sum(COEF[(s, 3)] * base[s] for s in SYMS), {})]
    while stack:
        depth, res, deltas = stack.pop()
        if depth == len(spans):
            if res % weight[rarest]:
                continue
            pay = dict(base)
            for k, d in deltas.items():
                for s in GROUPS[k]:
                    pay[s] += d
            for s in GROUPS[rarest]:
                pay[s] += res // weight[rarest]
            if min(pay.values()) < 1 or not _ordered(pay):
                continue
            miss = [abs(F(pay[s]) - FAIR[s]) / FAIR[s] for s in SYMS]
            score = (max(miss), sum(miss))
            if best is None or score < best[0]:
                best = (score, pay)
            continue
        k = GROUP_KEYS[depth]
        for d in spans[depth]:
            stack.append((depth + 1, res - weight[k] * d, {**deltas, k: d}))
    assert best, "no integer ladder closes on the target exactly"
    return best[1]


PAY3 = solve()
assert (sum(COEF[(s, 3)] * PAY3[s] for s in SYMS)
        + sum(COEF[(s, 2)] * PAY2[s] for s in SYMS)) == TARGET, "inexact close"
# Each symbol pays at least the stake back on three of a kind: the commonest
# win in the game must not be a dribble. Fair odds already puts it well above,
# so this is a check on the solve rather than a clamp on it.
assert min(PAY3[s] for s in COMMON) >= len(LINES), PAY3
# No line pays more than the whole strip space is worth - a sanity bound that
# catches a runaway residual landing entirely on the rarest symbol.
assert max(PAY3.values()) * max(COEF[(s, 3)] for s in SYMS) < TARGET * 100

# Every rung's pay is the *rounded* integer that ships, and the per-line
# return is exactly 24/25 of one line's stake - not within a tolerance of it.
LINE_EV = F(sum(COEF[(s, 3)] * PAY3[s] for s in SYMS)
            + sum(COEF[(s, 2)] * PAY2[s] for s in SYMS), TOT)
assert LINE_EV == HOUSE, LINE_EV

# ------------------------------------------------------------- bet model
# One `bet` buys all five lines, so a line's stake is bet/5 and a win is
# bet * units / 5. Every bet level is a multiple of 5, so that is an exact
# integer at every level and the VM's round block never fires - which is the
# only reason Scratch's round-half-away-from-zero cannot disagree with the
# Python that solved the table (the tables5.py r2() hazard).
BET_LEVELS = [5, 10, 15, 20, 25, 50, 75, 100, 150, 200, 250,
              500, 750, 1000, 1500, 2000, 2500, 5000]
assert all(b % len(LINES) == 0 for b in BET_LEVELS), BET_LEVELS

# --------------------------------------------- full joint enumeration
# Everything above solves one line in closed form. This walks all 27000
# screens with all five lines evaluated on each, which re-derives the same
# numbers by a different route and is where the player-facing statistics -
# hit frequency, volatility, the top prize - actually come from. None of it
# is sampled.
HIST = Counter()                             # total units won -> screens
RUNGS = Counter()                            # (symbol, run) -> lines paid
TOP = (-1, None, None, None)                 # units, stops, columns, lit cells
for q0 in range(STRIP_LEN):
    col0 = [STRIPS[0][(q0 + k - 1) % STRIP_LEN] for k in range(ROWS)]
    for q1 in range(STRIP_LEN):
        col1 = [STRIPS[1][(q1 + k - 1) % STRIP_LEN] for k in range(ROWS)]
        for q2 in range(STRIP_LEN):
            col2 = [STRIPS[2][(q2 + k - 1) % STRIP_LEN] for k in range(ROWS)]
            cols = (col0, col1, col2)
            units, hot = 0, set()
            for li, line in enumerate(LINES):
                sym, run = evaluate(*(cols[c][r] for c, r in enumerate(line)))
                if run >= 2:
                    RUNGS[(sym, run)] += 1
                u = PAY3[sym] if run == 3 else (PAY2[sym] if run == 2 else 0)
                if u:
                    hot.update(LINES_FLAT[li * REELS:li * REELS + run])
                units += u
            HIST[units] += 1
            if units > TOP[0]:
                TOP = (units, (q0 + 1, q1 + 1, q2 + 1), cols, sorted(hot))

SCREENS = sum(HIST.values())
assert SCREENS == TOT * 1, SCREENS
# The joint walk and the closed form must agree rung for rung, not just in the
# mean: a bug that moved return between two rungs would leave the RTP intact.
assert set(RUNGS) == set(COEF), (set(RUNGS) ^ set(COEF))
for (s, run), n in COEF.items():
    assert RUNGS[(s, run)] == n * len(LINES), (NAMES[s], run, RUNGS[(s, run)], n)
RTP = F(sum(k * v for k, v in HIST.items()), SCREENS * len(LINES))
assert RTP == HOUSE == LINE_EV, RTP

HIT = F(SCREENS - HIST[0], SCREENS)
OVER = F(sum(v for k, v in HIST.items() if k > len(LINES)), SCREENS)
MAX_UNITS = max(HIST)
MEAN = F(sum(k * v for k, v in HIST.items()), SCREENS)
VAR = F(sum((F(k) - MEAN) ** 2 * v for k, v in HIST.items()), SCREENS)
SD = math.sqrt(float(VAR)) / len(LINES)      # in units of the total bet

# The MULT readout borrows Digit field 3, which has 7 character slots. A
# string wider than that loses its tail silently (the bankroll shipped that
# way for eight versions), so the widest multiplier the game can ever show
# has to fit before it ships, not after someone notices.
WIDEST = max((f"{k / len(LINES):g}" for k in HIST if k), key=len)
assert len(WIDEST) <= 7, WIDEST
# Every reachable payout is an exact integer number of chips at every bet
# level, so nothing the VM computes is fractional and round() never runs.
for _b in BET_LEVELS:
    for _u in HIST:
        _exact = _b * _u
        assert _exact % len(LINES) == 0, (_b, _u)
        assert (math.floor(_exact / len(LINES) + 0.5)
                == _exact // len(LINES)), (_b, _u)

# ----------------------------------------------------------------- print
print("SLOTS  3x3, 5 lines, 30-stop strips, one wild")
for r, txt in enumerate(STRIP_TXT):
    print(f"  reel {r + 1}  {txt}")
    print("          " + "  ".join(
        f"{NAMES[s][:4]}:{COUNTS[r][s]}" for s in SYMS))
print("\nPAYTABLE   units of one line stake (bet/5); x = of the TOTAL bet")
for s in sorted(SYMS, key=lambda s: -PAY3[s]):
    share = F(COEF[(s, 3)] * PAY3[s], TARGET)
    print(f"  {NAMES[s]:<8} x3  {PAY3[s]:>4} u = {PAY3[s] / len(LINES):>6g}x"
          f"   p/line {COEF[(s, 3)]:>4}/{TOT}"
          f"   fair {float(FAIR[s]):>6.2f} u"
          f"   RTP share {float(share) * 100:5.2f}%")
for s in PAY_FROM_TWO:
    share = F(COEF[(s, 2)] * PAY2[s], TARGET)
    print(f"  {NAMES[s]:<8} x2  {PAY2[s]:>4} u = {PAY2[s] / len(LINES):>6g}x"
          f"   p/line {COEF[(s, 2)]:>4}/{TOT}"
          f"   RTP share {float(share) * 100:5.2f}%")
print(f"\n  unit sum {sum(COEF[(s, 3)] * PAY3[s] for s in SYMS) + sum(COEF[(s, 2)] * PAY2[s] for s in SYMS)}"
      f" == target {TARGET}   EXACT")
print(f"  per-line EV = {LINE_EV} = {float(LINE_EV):.10f} of its own stake")
print(f"\nJOINT  (all {TOT} stop combinations x {len(LINES)} lines)")
print(f"  RTP            {RTP} = {float(RTP):.10f}   EXACT")
print(f"  hit frequency  {float(HIT) * 100:.4f}%   (1 in {1 / float(HIT):.2f})")
print(f"  pays >= stake  {float(OVER) * 100:.4f}%")
print(f"  max win        {MAX_UNITS} u = {MAX_UNITS / len(LINES):g}x"
      f"   p = {HIST[MAX_UNITS]}/{TOT}")
print(f"  sd of return   {SD:.4f}   distinct totals {len(HIST)}")
for x in (5, 10, 20, 50):
    p = F(sum(v for k, v in HIST.items() if k >= x * len(LINES)), SCREENS)
    print(f"  >= {x:>3}x        {float(p) * 100:.4f}%   1 in {1 / float(p):.0f}")
print(f"  widest MULT string {WIDEST!r} = {len(WIDEST)} chars (field 3 has 7)")
# More than one screen can reach the top prize, so WHICH one this is depends on
# the order the walk happens to visit them in. It is published rather than
# quoted anywhere else for exactly that reason: a strip change moves it, and
# nothing downstream should go red for that.
TOP_GRID = [TOP[2][c][r] for c in range(REELS) for r in range(ROWS)]
print(f"\n  top screen: stops {TOP[1]} -> {TOP[0] / len(LINES):g}x"
      f"   ({HIST[TOP[0]]} screens reach it)")
for r in range(ROWS):
    print("     " + "  ".join(NAMES[TOP[2][c][r]][:4].rjust(4)
                              for c in range(REELS)))

STRIP_FLAT = [s for st in STRIPS for s in st]
print("\nSCRATCH LISTS")
print(f"  slStrip ({len(STRIP_FLAT)}) = {STRIP_FLAT}")
print(f"  slPay3  ({len(SYMS)}) = {[PAY3[s] for s in SYMS]}")
print(f"  slPay2  ({len(SYMS)}) = {[PAY2[s] for s in SYMS]}")
print(f"  slLines ({len(LINES_FLAT)}) = {LINES_FLAT}")

from paths import BUILD  # noqa: E402

# The strips ship pre-flattened into the exact index layout the VM reads, so
# build.py cannot get the layout wrong (the tables3.py precedent), and the JS
# harness measures against the same published numbers the art was drawn from.
# The digest is this file's own source: paths.ensure_tables() re-solves when it
# stops matching, so editing the solver without `make tables` cannot ship the
# previous table to a build and a harness that then agree with each other.
json.dump({"strips": STRIP_FLAT,
           "house": [HOUSE.numerator, HOUSE.denominator],
           "maxStops": list(TOP[1]),
           "maxGrid": TOP_GRID,
           "maxHot": TOP[3],
           "stripLen": STRIP_LEN,
           "reels": REELS,
           "rows": ROWS,
           "pay3": [PAY3[s] for s in SYMS],
           "pay2": [PAY2[s] for s in SYMS],
           "lines": LINES_FLAT,
           "names": [NAMES[s] for s in SYMS],
           "wild": WILD,
           "payFromTwo": list(PAY_FROM_TWO),
           "betLevels": BET_LEVELS,
           "rtp": float(RTP),
           "hitFreq": float(HIT),
           "sd": SD,
           "maxUnits": MAX_UNITS,
           "digest": hashlib.sha256(
               open(__file__, "rb").read()).hexdigest()},
          open(BUILD / "tables7.json", "w"))
print("\nok")
