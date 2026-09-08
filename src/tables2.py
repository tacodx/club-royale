"""Stairs (Dragon Tower) tables + European roulette constants."""
import json
from math import gcd

HOUSE = 0.96
ROWS = 9
# name, tiles per row, bombs per row
DIFFS = [("EASY", 4, 1), ("MEDIUM", 3, 1), ("HARD", 2, 1),
         ("EXPERT", 3, 2), ("MASTER", 4, 3)]


def nice(v):
    if v >= 10000: return float(round(v))
    if v >= 1000:  return round(v, 1)
    if v >= 100:   return round(v, 1)
    if v >= 10:    return round(v, 2)
    return round(v, 2)


STAIRS = {}
print("STAIRS  (9 rows, 0.96 house)")
for name, tiles, bombs in DIFFS:
    p = (tiles - bombs) / tiles
    vals = [nice(HOUSE * (1 / p) ** n) for n in range(1, ROWS + 1)]
    STAIRS[name] = vals
    print(f"  {name:<7} {tiles} tiles / {bombs} bomb(s)  p={p:.3f}  "
          f"step1 {vals[0]:g}  step5 {vals[4]:g}  clear {vals[-1]:g}")
    ev = p * vals[0]
    assert abs(ev - HOUSE) < 0.02, (name, ev)

# ------------------------------------------------------- roulette
WHEEL = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8,
         23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12,
         35, 3, 26]
RED = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
assert len(WHEEL) == 37 and len(set(WHEEL)) == 37
assert len(RED) == 18
BLACK = [n for n in range(1, 37) if n not in RED]
assert len(BLACK) == 18

# verify every bet type returns exactly 36/37
checks = {
    "straight": (1 / 37) * 36,
    "red": (18 / 37) * 2,
    "odd": (18 / 37) * 2,
    "low": (18 / 37) * 2,
    "dozen": (12 / 37) * 3,
    "column": (12 / 37) * 3,
}
print("\nROULETTE  (European, single zero)")
for k, v in checks.items():
    print(f"  {k:<9} RTP {v:.4f}")
assert all(abs(v - 36 / 37) < 1e-9 for v in checks.values())
print(f"  house edge {100 * (1 - 36/37):.2f}%")

# column/dozen membership sanity
for n in range(1, 37):
    assert 1 <= (n - 1) % 3 + 1 <= 3
    assert 1 <= (n - 1) // 12 + 1 <= 3

from paths import BUILD
json.dump({"stairs": STAIRS,
           "wheel": WHEEL, "red": RED, "black": BLACK,
           "diffs": [[n, t, b] for n, t, b in DIFFS]},
          open(BUILD / "tables2.json", "w"))
print("\nok")
