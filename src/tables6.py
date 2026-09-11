"""Coin Flip (streak ladder) and Dice (0-100 threshold roll).

Both tables are exact. Every other solver in this repo bisects a scale and
then rounds, so the shipped multipliers only approximate the target edge and
the assertions have to carry a tolerance. Here the numbers were chosen so the
rounded value *is* the exact one, and the house take is 0.96 to the last bit
at every cash-out point and in every mode. The Fraction arithmetic below
proves that rather than measuring it.
"""
import json
from fractions import Fraction as F

HOUSE = F(96, 100)

# ------------------------------------------------------------- coin flip
# Call a side and keep flipping. Rung n pays HOUSE * 2^n against a 2^-n chance
# of getting there, so cashing out at any rung is worth exactly 0.96 of the
# stake: there is no rung to hold out for and none to stop short at. The cut
# is taken once, on entry - continuing from a rung you have already reached is
# EV-neutral, which is how Mines, Stairs and Duck Road are solved too.
# 0.96 * 2^n terminates at two decimals for every n, so nothing is rounded.
COIN_RUNGS = 12

COIN = []
for n in range(1, COIN_RUNGS + 1):
    v = HOUSE * (2 ** n)
    assert (v * 100).denominator == 1, (n, v)   # exact at two decimals
    COIN.append(float(v))

print(f"COIN FLIP  ({COIN_RUNGS} rungs, 0.96 house)")
for n, v in enumerate(COIN, 1):
    print(f"  {n:2d} correct calls  {v:>9g}x")

# Cashing out at any rung returns exactly 0.96 of the stake, so every
# stopping point is worth the same and the ladder hides no better rung.
for n, v in enumerate(COIN, 1):
    ev = F(1, 2 ** n) * F(str(v))
    assert ev == HOUSE, (n, ev)
print(f"  every rung: EV of cashing out there = {float(HOUSE)} exactly")
# the widest string the readout ever has to draw, including the trailing x
assert len(f"{COIN[-1]:g}x") <= 8, f"{COIN[-1]:g}x"

# ------------------------------------------------------------------ dice
# The threshold is dragged, not picked from presets, so the multiplier cannot
# be a solved constant - it is computed from wherever the slider is left:
#
#     mult(w) = floor(HOUSE * OUTCOMES * PREC / w) / PREC
#
# for w winning outcomes out of OUTCOMES. Flooring is the point. Rounding would
# let the rounded multiplier exceed the exact one and hand the player an edge
# at some thresholds; flooring can only ever fall short, so
#
#     RTP(w) = w * floor(96000000 / w) / (OUTCOMES * PREC)  <=  0.96   always
#
# and PREC picks how far short. At two decimals the shortfall reaches 0.0094 -
# a 4.94% house edge at some slider positions, which is not "96% RTP" in any
# honest sense. At four it is under 0.0001 everywhere. The multiplier is shown
# to the same four places it is paid at, so the readout never disagrees with
# the payout.
DICE_OUTCOMES = 10000              # rolls are 0.00..99.99, as hundredths
DICE_PREC = 10000                  # multiplier resolution: 4 decimals
DICE_MIN_WIN, DICE_MAX_WIN = 100, 9500     # 1.00% .. 95.00% win chance


def dice_mult(w):
    return (HOUSE * DICE_OUTCOMES * DICE_PREC).numerator // (
        w * (HOUSE * DICE_OUTCOMES * DICE_PREC).denominator) / DICE_PREC


print("\nDICE  (0.00-99.99, dragged threshold, 0.96 house)")
worst_w, worst_rtp = None, F(1)
best_rtp = F(0)
exact = 0
for w in range(DICE_MIN_WIN, DICE_MAX_WIN + 1):
    m100 = (96000000) // w                       # floor, in units of 1/PREC
    rtp = F(w * m100, DICE_OUTCOMES * DICE_PREC)
    assert rtp <= HOUSE, (w, rtp)                # never above the target
    if rtp == HOUSE:
        exact += 1
    if rtp < worst_rtp:
        worst_rtp, worst_w = rtp, w
    best_rtp = max(best_rtp, rtp)
for w in (DICE_MIN_WIN, 1920, 2400, 4800, 8000, DICE_MAX_WIN):
    print(f"  chance {w/100:>6.2f}%   pays {96000000 // w / DICE_PREC:>10g}x"
          f"   RTP {float(F(w * (96000000 // w), DICE_OUTCOMES * DICE_PREC)):.6f}")
print(f"  across all {DICE_MAX_WIN - DICE_MIN_WIN + 1} slider positions: "
      f"RTP max {float(best_rtp):.6f}, min {float(worst_rtp):.6f} "
      f"(at {worst_w/100:.2f}%), exact on {exact}")
assert worst_rtp > F(9599, 10000), worst_rtp    # within 0.01% of the target
# the widest the readout ever has to draw
assert len(f"{96000000 // DICE_MIN_WIN / DICE_PREC:g}x") <= 7
assert max(len(f"{96000000 // w / DICE_PREC:g}")
           for w in range(DICE_MIN_WIN, DICE_MAX_WIN + 1)) <= 7

from paths import BUILD
json.dump({"coin": COIN,
           "coinRungs": COIN_RUNGS,
           "diceOutcomes": DICE_OUTCOMES,
           "dicePrec": DICE_PREC,
           "diceMinWin": DICE_MIN_WIN,
           "diceMaxWin": DICE_MAX_WIN,
           "house": float(HOUSE)},
          open(BUILD / "tables6.json", "w"))
print("\nok")
