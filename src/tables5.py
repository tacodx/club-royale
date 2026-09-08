"""Aviamasters — collect orbs along a route, then land on the far carrier.

Modelled on BGaming's Avia Masters: a plane leaves one carrier and flies a
random route to another. The sky holds floating orbs; numbers ADD to the
running multiplier, multiplier orbs MULTIPLY it, and rockets HALVE it without
ending the round. Land and you are paid; ditch in the water and the stake is
gone. You may bail out early for whatever the multiplier reads at that moment.

THE ORBS ARE AFFINE MAPS

Every orb transforms the running value v the same way:

    +n      v -> v + n        (a=1, b=n)
    xm      v -> v * m        (a=m, b=0)
    rocket  v -> v / 2        (a=0.5, b=0)
    empty   v -> v            (a=1, b=0)

Orbs are drawn independently per slot, so the expectation composes in closed
form, E[V_k] = Ea * E[V_(k-1)] + Eb - though the numbers below come from an
exact walk of the whole value distribution instead, because the x250 cap bends
the tail and the readout rounds to two places. What is asserted is therefore
the expectation of the figure a player is actually paid.

THE RISK IS SOLVED PER SLOT, NOT SET

The obvious designs do not work, and both failures are worth recording:

  * A FLAT ditch rate puts the optimal stopping point at slot 1, always. The
    growth ratio E[V_k]/E[V_(k-1)] starts at Ea+Eb and decays monotonically
    toward Ea, so each factor (1-d)*ratio_k is smaller than the last. Solved
    for a 0.96 edge it wanted a 43.4% flat ditch rate, and 0.03% of flights
    landed.
  * A RISING ramp cannot fix it either. EV(1) = (1-d_1) * E[V_1], so if the
    first slot is cheap the edge is already lost there and no amount of danger
    later pulls the maximum back down to 0.96.

The constraint is simply that the FIRST cash-out point has to carry the edge,
and every later one has to be worth exactly the same. That is the same
condition the Stairs and Duck Road ladders satisfy, so solve it the same way -
per slot, backwards from the requirement:

    alive_k = HOUSE / E[V_k]                (survival needed to make k worth HOUSE)
    d_k     = 1 - alive_k / alive_(k-1)     (the per-slot risk that produces it)

which gives EV(k) = alive_k * E[V_k] = HOUSE at every k. No stopping point is
worth preferring, so there is no strategy to find, and the edge does not depend
on how well the player reads the sky.

The player cannot see which orb is coming: the sky is full of them but the
route decides what is actually collected, drawn at launch. Cashing out is a
hedge against the ditch, never a dodge around a rocket.
"""
import json
import math

HOUSE = 0.96
SLOTS = 14                 # orbs on the route from one carrier to the other
CAP = 250                  # max win, as in the real game
PREC = 1000                # rand(1, PREC) resolution for the per-slot ditch

# name, weight, a, b   -- v -> a*v + b.  Weights are percentages.
# Chosen for feel as much as for maths - the edge is solved per slot either
# way, so the mix is free. Rockets are deliberately the commonest orb: they are
# the game's signature hazard and they stop the multiplier running away, which
# is what keeps a decent share of flights landing.
ORBS = [
    ("EMPTY",  14, 1.0, 0.0),
    ("PLUS05", 24, 1.0, 0.5),
    ("PLUS1",   8, 1.0, 1.0),
    ("MUL2",   13, 2.0, 0.0),
    ("MUL3",    4, 3.0, 0.0),
    ("ROCKET", 37, 0.5, 0.0),
]

TOTW = sum(w for _n, w, _a, _b in ORBS)
assert TOTW == 100, TOTW

Ea = sum(w * a for _n, w, a, _b in ORBS) / TOTW
Eb = sum(w * b for _n, w, _a, b in ORBS) / TOTW


def r2(x):
    """Round to 2dp the way Scratch does, NOT the way Python does.

    The runtime evaluates round(v * 100) / 100, and Scratch's round block is
    JS Math.round: halves go away from zero. Python's round() goes to even, and
    the difference is reachable here - halving a value like 1.25 gives exactly
    0.625, which is exactly representable, so Python says 0.62 and the game says
    0.63. Modelling it Python's way put the shipped ditch ramp 1/1000 out at
    three slots; tests/play_avia.js caught it by solving the table again.
    """
    return math.floor(x * 100 + 0.5) / 100


def value_rows():
    """Exact value distribution after each slot, ignoring the ditch.

    rows[k] = {value: probability}. Values are rounded to 2dp (what the readout
    shows) and clamped to CAP, so the expectation is of the number actually paid.
    The ditch is independent of the orbs, so it factors out and is applied after.
    """
    rows = [{1.0: 1.0}]
    for _k in range(SLOTS):
        nxt = {}
        for v, pv in rows[-1].items():
            for _n, w, a, b in ORBS:
                nv = min(CAP, r2(a * v + b))
                nxt[nv] = nxt.get(nv, 0.0) + pv * (w / TOTW)
        rows.append(nxt)
    return rows


ROWS = value_rows()
EV = [sum(v * p for v, p in row.items()) for row in ROWS]   # E[V_k], no ditch

# ------------------------------------------------- solve the per-slot risk
# alive_k is the survival probability that makes crossing k slots worth HOUSE.
alive = [1.0] + [HOUSE / EV[k] for k in range(1, SLOTS + 1)]
RAMP = []
for k in range(1, SLOTS + 1):
    d = 1 - alive[k] / alive[k - 1]
    RAMP.append(round(d * PREC))
# re-derive the survival curve from the integers that actually ship
shipped = [1.0]
for r in RAMP:
    shipped.append(shipped[-1] * (1 - r / PREC))
curve = [shipped[k] * EV[k] for k in range(SLOTS + 1)]

land = shipped[SLOTS]
print(f"AVIAMASTERS  ({SLOTS} slots, cap x{CAP}, house {HOUSE})")
print(f"  orb map : Ea={Ea:.4f}  Eb={Eb:.4f}")
print(f"  ditch   : {RAMP[0]/PREC:.1%} at the first orb, "
      f"{RAMP[-1]/PREC:.1%} at the last")
print(f"  landings: {land:.1%} of flights make the far carrier")
print()
print(f"{'orbs':>5}{'ditch':>9}{'still flying':>14}{'mean x':>9}"
      f"{'median x':>10}{'EV':>9}")
for k in range(1, SLOTS + 1):
    vals = sorted(ROWS[k].items())
    run, med = 0.0, vals[-1][0]
    for v, pp in vals:
        run += pp
        if run >= 0.5:
            med = v
            break
    print(f"{k:>5}{RAMP[k-1]/PREC:>9.1%}{shipped[k]:>14.1%}"
          f"{EV[k]:>9.2f}{med:>10g}{curve[k]:>9.4f}")

# every cash-out point is worth the same, to within the integer ditch rounding
for k in range(1, SLOTS + 1):
    assert abs(curve[k] - HOUSE) < 0.01, (k, curve[k])
assert all(0 < r < PREC for r in RAMP), RAMP
assert land > 0.10, f"only {land:.1%} of flights land - the route is too deadly"
assert EV[SLOTS] > EV[1], "the multiplier should grow along the route"

final = ROWS[SLOTS]
big = sum(p for v, p in final.items() if v >= 50)
capped = final.get(float(CAP), 0.0)
print()
print(f"  of flights that land: {big:.2%} pay 50x or better, "
      f"{capped:.3%} hit the {CAP}x cap")

# ---------------------------------------------- what the runtime needs
cum, acc = [], 0
for _n, w, _a, _b in ORBS:
    acc += w
    cum.append(acc)

from paths import BUILD
json.dump({
    "house": HOUSE, "slots": SLOTS, "cap": CAP, "prec": PREC,
    "ditchRamp": RAMP,
    "orbNames": [n for n, _w, _a, _b in ORBS],
    "orbCum": cum,
    "orbA": [a for _n, _w, a, _b in ORBS],
    "orbB": [b for _n, _w, _a, b in ORBS],
    "ev": EV, "alive": shipped, "evCurve": curve,
}, open(BUILD / "tables5.json", "w"))
print("\nok")
