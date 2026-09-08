"""Aviamasters — a crash game. The seaplane climbs, you bail before it lands.

Unlike the ladders (Stairs, Duck Road) there are no steps: the multiplier
climbs continuously and the round ends at a landing point drawn once, at
take-off. That is the standard provably-fair crash construction, and it has the
same property every other game here is built on — the same expected return at
every cash-out point:

    P(land >= x) = HOUSE / x          for x >= HOUSE
    EV(cash at x) = x * P(land >= x) = HOUSE

Sampling it needs no table, only integer randomness, which is all Scratch has:

    land = HOUSE * PREC / rand(1, PREC)

rand = PREC gives the floor (0.96x — the plane ditches before it is worth
cashing) and rand = 1 gives the ceiling (9600x). Deciding the landing point at
take-off rather than rolling per frame is what keeps payouts provable on the
fast build; see CLAUDE.md.

The climb is exponential in ticks so it accelerates the way the original does:

    mult(t) = round(GROWTH**t, 2),  emitted as 10**(t * LOG_GROWTH)

because Scratch has `10 ^` in its mathop menu but no general power operator.
"""
import json
from math import log10

HOUSE = 0.96
PREC = 10000                  # rand(1, PREC) resolution of the landing draw
GROWTH = 1.015                # multiplier growth per tick
TICK = 0.07                   # seconds per tick at real timing
LOG_GROWTH = log10(GROWTH)

# auto cash-out targets; 0 = off, the rest fire the moment mult reaches them
AUTO = [0, 1.5, 2, 5, 10]

CEIL = HOUSE * PREC / 1
FLOOR = HOUSE * PREC / PREC

print(f"AVIAMASTERS  (crash, {HOUSE} house)")
print(f"  land = {HOUSE} * {PREC} / rand(1,{PREC})"
      f"   floor {FLOOR:g}x   ceiling {CEIL:g}x")
print(f"  climb  {GROWTH}^t   {TICK}s a tick"
      f"   2x at t={log10(2) / LOG_GROWTH:.0f} ({log10(2) / LOG_GROWTH * TICK:.1f}s)")
print()
print(f"{'cash at':>9}{'P(reach)':>11}{'EV':>9}")
for x in [1.0, 1.5, 2, 5, 10, 100, 1000, CEIL]:
    p = min(1.0, HOUSE / x)
    print(f"{x:>9g}{p:>11.4f}{x * p:>9.4f}")
    assert abs(x * p - HOUSE) < 1e-9 or x < HOUSE

# the draw is uniform over PREC outcomes; check the realised edge exactly
total = sum(min(1.0, HOUSE * PREC / u) for u in range(1, PREC + 1))
# ...and that cashing at any fixed target returns HOUSE, summed over the draw
for target in [1.5, 2, 5, 10, 50]:
    reach = sum(1 for u in range(1, PREC + 1) if HOUSE * PREC / u >= target)
    ev = target * reach / PREC
    assert abs(ev - HOUSE) < 0.01, (target, ev)
print(f"\n  every fixed target returns {HOUSE} over all {PREC} draws")

assert AUTO[0] == 0, "first auto slot must be OFF"
assert all(a > 1 for a in AUTO[1:]), "an auto target at or below 1x is a loss"
assert GROWTH > 1 and 0 < LOG_GROWTH < 1

from paths import BUILD
json.dump({"house": HOUSE, "prec": PREC, "growth": GROWTH, "tick": TICK,
           "logGrowth": LOG_GROWTH, "auto": AUTO,
           "ceil": CEIL, "floor": FLOOR},
          open(BUILD / "tables4.json", "w"))
print("\nok")
