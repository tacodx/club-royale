"""Duck Road tables — a cash-out ladder with a hidden golden-egg lane.

The duck crosses LANES lanes one at a time. Each lane it survives with
probability p (set by the mode) and the multiplier climbs; a car ends the run
and the stake is lost. Cash out at any point.

One run in 1/EGG_ODDS hides a golden egg on a uniformly random lane. Reaching
that lane multiplies the payout by EGG_MULT for the rest of the run.

The ladder is solved so **every cash-out point has the same expected return**,
exactly as Stairs does in tables2.py. The egg contributes to the expected
return of lane n only in proportion to how likely it is to have been crossed
by then, so the base ladder is divided back out by that expectation:

    P(holding egg at lane n) = EGG_ODDS * n / LANES
    bonus(n)                 = 1 + P(holding egg at n) * (EGG_MULT - 1)
    base(n)                  = HOUSE / (p**n * bonus(n))

giving EV(cash after n) = p**n * bonus(n) * base(n) = HOUSE for every n.

Two ladders are emitted, not one. The runtime never multiplies a payout by
EGG_MULT itself: 1.02 * 3 in Scratch's floating point renders as
3.0599999999999996 in the multiplier readout. Both ladders are rounded here
and the EV assertions below run against the *rounded* values that actually
ship, so what the player is paid is what was verified.
"""
import json

HOUSE = 0.96
LANES = 12
EGG_ODDS = 0.25          # fraction of runs that hide an egg
EGG_MULT = 3.0           # what the egg multiplies the payout by

# name, survival probability per lane
MODES = [("EASY", 0.90), ("MEDIUM", 0.80), ("HARD", 0.65), ("DAREDEVIL", 0.45)]


def nice(v):
    """Round to something readable without moving the value much."""
    if v >= 10000: return float(round(v))
    if v >= 100:   return round(v, 1)
    if v >= 10:    return round(v, 2)
    return round(v, 2)


def egg_chance(n):
    """Probability the duck is carrying the egg having crossed n lanes."""
    return EGG_ODDS * n / LANES


DUCK, DUCK_EGG = {}, {}
print(f"DUCK ROAD  ({LANES} lanes, {HOUSE} house, "
      f"egg {EGG_ODDS:.0%} of runs x{EGG_MULT:g})")
for name, p in MODES:
    base, withegg = [], []
    for n in range(1, LANES + 1):
        raw = HOUSE / (p ** n * (1 + egg_chance(n) * (EGG_MULT - 1)))
        base.append(nice(raw))
        withegg.append(nice(raw * EGG_MULT))
    DUCK[name], DUCK_EGG[name] = base, withegg

    print(f"  {name:<10} p={p:.2f}  lane1 {base[0]:g}  lane6 {base[5]:g}  "
          f"clear {base[-1]:g}  (with egg {withegg[-1]:g})")

    # every cash-out point returns HOUSE, using the rounded values that ship
    for n in range(1, LANES + 1):
        q = egg_chance(n)
        ev = p ** n * (q * withegg[n - 1] + (1 - q) * base[n - 1])
        assert abs(ev - HOUSE) < 0.02, (name, n, ev)

    # the ladder must never hand back less than the stake, and must climb
    assert base[0] >= 1.0, (name, "lane 1 pays under 1x", base[0])
    assert all(b > a for a, b in zip(base, base[1:])), (name, "not monotonic")
    assert all(e > b for b, e in zip(base, withegg)), (name, "egg not a gain")

assert EGG_MULT > 1
assert EGG_ODDS * (EGG_MULT - 1) <= LANES * (HOUSE / MODES[0][1] - 1) + 1e-9, \
    "egg dilutes EASY lane 1 below 1x"

# the runtime indexes one flat list: (mode-1)*LANES + lane, plus 48 when the
# egg is held. Build it here so build.py cannot get the layout wrong.
FLAT = []
for tbl in (DUCK, DUCK_EGG):
    for name, _p in MODES:
        FLAT += [f"{v:g}" for v in tbl[name]]
assert len(FLAT) == 2 * len(MODES) * LANES

from paths import BUILD
json.dump({"duck": DUCK, "duckEgg": DUCK_EGG, "flat": FLAT,
           "lanes": LANES, "house": HOUSE,
           "eggOdds": EGG_ODDS, "eggMult": EGG_MULT,
           "pct": [int(round(p * 100)) for _n, p in MODES],
           "modes": [[n, p] for n, p in MODES]},
          open(BUILD / "tables3.json", "w"))
print("\nok")
