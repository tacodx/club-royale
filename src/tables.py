"""Solve payout tables for Plinko (rows x risk) and Mines (bomb count)."""
from math import comb

TARGET = 0.95
ROWS = [8, 12, 16]
RISKS = ["low", "med", "high"]
# (max multiplier, edge sharpness) per rows/risk
SHAPE = {
    (8,  "low"): (5.6, 3.0),   (8,  "med"): (13,  2.4),  (8,  "high"): (29,   1.9),
    (12, "low"): (8.4, 3.0),   (12, "med"): (33,  2.4),  (12, "high"): (170,  1.9),
    (16, "low"): (16,  3.0),   (16, "med"): (110, 2.4),  (16, "high"): (1000, 1.9),
}


def nice(v):
    if v >= 100:  return float(round(v / 10) * 10)
    if v >= 10:   return float(round(v))
    if v >= 1:    return round(v, 1)
    return max(0.1, round(v, 2))


def table(n, risk):
    M, a = SHAPE[(n, risk)]
    w = [comb(n, k) / 2 ** n for k in range(n + 1)]
    raw = []
    for k in range(n + 1):
        d = abs(2 * k / n - 1)
        raw.append(M ** (d ** a))
    lo, hi = 0.0001, 5.0
    for _ in range(200):                      # bisect the scale for target RTP
        c = (lo + hi) / 2
        vals = [nice(c * r) for r in raw]
        rtp = sum(w[k] * vals[k] for k in range(n + 1))
        if rtp < TARGET: lo = c
        else: hi = c
    vals = [nice(((lo + hi) / 2) * r) for r in raw]
    return vals, sum(w[k] * vals[k] for k in range(n + 1))


PLINKO = {}
print("PLINKO")
for n in ROWS:
    for r in RISKS:
        v, rtp = table(n, r)
        PLINKO[(n, r)] = v
        print(f"  {n:2d} rows {r:>4}  RTP {rtp:.4f}  max {max(v):>7g}  "
              f"centre {v[n//2]:g}")
        print(f"      {[f'{x:g}' for x in v]}")

BOMBS = [1, 3, 5, 10]
MINES = {}
print("\nMINES  (0.96 house)")
for b in BOMBS:
    vals = []
    for k in range(1, 25 - b + 1):
        fair = comb(25, k) / comb(25 - b, k)
        vals.append(nice(fair * 0.96))
    MINES[b] = vals
    print(f"  {b:2d} bombs  {len(vals)} steps  first {vals[0]:g}  "
          f"5th {vals[4]:g}  max {max(vals):g}")

# verify mines edge: expected value of stopping after k picks == 0.96
for b in BOMBS:
    k = 3
    psurv = comb(25 - b, k) / comb(25, k)
    print(f"  check {b:2d} bombs, cash after {k}: p={psurv:.4f} "
          f"x {MINES[b][k-1]:g} = EV {psurv*MINES[b][k-1]:.4f}")

import json
from paths import BUILD
json.dump({"plinko": {f"{n}_{r}": v for (n, r), v in PLINKO.items()},
           "mines": {str(b): v for b, v in MINES.items()}},
          open(BUILD / "tables.json", "w"))
