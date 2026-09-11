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
# The roll is an integer 0..9999 shown as 0.00..99.99, so a threshold in
# hundredths is an exact outcome count and the comparison never touches a
# float. UNDER t wins on roll < t, OVER t wins on roll >= 10000 - t; both
# are t outcomes out of 10000, so one table serves both sides.
DICE_OUTCOMES = 10000

# (selector caption, winning outcomes, multiplier)
DICE_MODES = [("80%",   8000, 1.20),
              ("48%",   4800, 2.00),
              ("24%",   2400, 4.00),
              ("9.6%",   960, 10.00),
              ("1.92%",  192, 50.00)]

print("\nDICE  (0.00-99.99, 0.96 house)")
for cap, out, mult in DICE_MODES:
    rtp = F(out, DICE_OUTCOMES) * F(str(mult))
    assert rtp == HOUSE, (cap, rtp)
    assert 0 < out < DICE_OUTCOMES
    print(f"  chance {cap:>6}  under {out/100:>5g} / over {(DICE_OUTCOMES-out)/100:>5g}"
          f"   pays {mult:>5g}x   RTP {float(rtp):.4f}")
print(f"  every mode and side: RTP = {float(HOUSE)} exactly")

from paths import BUILD
json.dump({"coin": COIN,
           "coinRungs": COIN_RUNGS,
           "diceOutcomes": DICE_OUTCOMES,
           "diceCaps":   [m[0] for m in DICE_MODES],
           "diceWin":    [m[1] for m in DICE_MODES],
           "diceMult":   [m[2] for m in DICE_MODES],
           "house": float(HOUSE)},
          open(BUILD / "tables6.json", "w"))
print("\nok")
