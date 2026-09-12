# Architecture

## The compiler

An `.sb3` is a zip containing `project.json` plus assets named by MD5.
`src/sb3.py` builds that structure; `src/blocks.py` is the DSL you write in.

```python
from sb3 import Project
from blocks import *

p = Project()
chips = p.var("chips", 1000)              # global variable
deck  = p.lst("deck", [])                 # global list
spr   = p.sprite("Reel")
spr.add_costume("s1", "path/to/sym1.png") # 2x art, bitmapResolution 2
idx   = spr.local_var("rIdx", 0)          # per-clone variable

spr.script(
    when_flag(),
    repeat(3, change_var(idx, 1), clone()),
)
p.save("out.sb3")
```

Stack blocks are 4-tuples `(opcode, inputs, fields, mutation)`; reporters are
`Ref` objects. `Target._emit` allocates ids and wires `next`/`parent`
automatically, so scripts are written as flat argument lists and nested
substacks are plain Python lists.

`Proc` and `define()` implement custom blocks including the
`procedures_prototype` mutation. Pass `warp=True` to run without screen refresh.

## Assets

Everything is generated. `deco.py` holds the art-deco style system: the palette,
`gold_fill()` (metallic gradient masked by a shape), `chamfer_pts()` (the
octagonal deco corner), `tracked()` (letter-spaced capitals) and `sunburst()`.

All art is rendered at **2x** and declared `bitmapResolution: 2`, so a costume's
stage-space size equals its `rotationCenterX/Y`. `tools/mock.py` and
`tests/overlap.js` both rely on that to compute bounding boxes.

## Coordinate system

Stage is 480x360, origin centre, so x ∈ [-240, 240] and y ∈ [-180, 180].

| Band | y range | Contents |
|---|---|---|
| Top bar | 146 … 180 | CHIPS label + digits, MULT/STAKE plaque, LOBBY button |
| Table | -128 … 140 | the play area (oxblood panel drawn into the backdrop) |
| Bottom bar | -180 … -136 | bet controls, selectors, action buttons |

Bottom bar x positions, shared across games:

```
-205 BetMinus   -152 BetPlaque   -99 BetPlus
 -45/-40 selector 1     24 selector 2
  52 START (mines/stairs) / GO (duck road) / LAUNCH (crash)
  75 SPIN/DEAL   110 DROP/SPIN   158 CASH OUT
blackjack: -150 HIT  -50 STAND  50 DOUBLE  150 SPLIT
           -60 INSURE  60 NO
```

Bet controls hide whenever `roundOn = 1`, which is what keeps them off the
blackjack action buttons.

## Screen routing

`screen` holds 0–11: lobby, slots, plinko, mines, blackjack, roulette, stairs,
duck road, crash, aviamasters, coin flip, dice.
The stage has one `when I receive` per screen that sets `screen`, resets
per-round state and then broadcasts `screenChanged`.

Sprites choose one of two visibility strategies:

- **`forever` loop** — for visibility that depends on changing state
  (`busy`, `roundOn`, `bjPhase`). Used by buttons, cards, mine tiles, digits.
- **`screenChanged` handler** — for visibility that depends only on `screen`.
  Used by the 49 roulette spots, 36 stair tiles and 17 buckets. This exists to
  keep per-frame work down; see PITFALLS §11.

## Shared state

| Variable | Meaning |
|---|---|
| `chips`, `bet`, `betIdx` | bankroll and stake (18-level ladder) |
| `busy` | an animation is running; buttons hide |
| `roundOn` | a round is live (mines, stairs, blackjack) |
| `bjPhase` | 0 idle, 1 insurance offer, 2 player acting, 3 dealer |
| `msgId` | banner costume; 1 is blank |
| `sfxId`, `sfxPitch` | sound index and pitch shift |

## Payout tables

Solved at build time, stored as **flat lists with computed offsets** because
Scratch has no 2-D lists.

| List | Layout | Index |
|---|---|---|
| `plinkoMults` | 9 blocks of 17 | `((rowsIdx-1)*3 + (riskIdx-1))*17 + bucket` |
| `mineMults` | 4 blocks of 24 | `(bombsIdx-1)*24 + picks` |
| `stairMults` | 5 blocks of 9 | `(stDiff-1)*9 + (stRow-1)` |
| `duckMults` | 2 x 4 blocks of 12 | `(dkMode-1)*12 + dkLane + 48*dkGot` |
| `rBets` | 49 slots | 1 = number 0, 2–37 = numbers 1–36, 38–49 = outside bets |
| `amRamp` | 14 slots | per-slot ditch odds out of 1000, indexed by `amSlot` |
| `amCum`, `amA`, `amB` | 6 orbs | cumulative weight, and the orb's affine map |
| `coinMults` | 12 rungs | `cfStreak`, straight |
| `slStrip` | 3 blocks of 30 | `(reel-1)*30 + strip position` |
| `slPay3`, `slPay2` | 9 slots | the symbol id, which is also its costume number |
| `slLines` | 5 blocks of 3 | `(line-1)*3 + reel` -> the cell it reads |
| `slGrid`, `slHot` | 9 cells | `(col-1)*3 + row`, row 1 at the top |

`src/tables7.py` solves slots. Each reel is a fixed 30-stop strip and a spin
draws one stop per reel, showing that stop and its two cyclic neighbours - so
the three rows of a column are adjacent strip cells and the weighting is a
property of where a symbol was placed, not of a biased `rand`. All five
paylines see the same marginal triple distribution, so the return is linear in
the per-line pays and one line solves the game. 30 stops is the length that
makes it exact: `0.96 * 30**3` is a whole number of unit stakes and `0.96 *
32**3` is not, so the ladder closes on 24/25 rather than bisecting towards it.
The 3-of-a-kind rungs are then chosen to sit as close to fair odds as integers
allow, which is what keeps every symbol's share of the return between 9.4% and
10.1% instead of letting one jackpot carry the game.

Dice has no table: the threshold is dragged, so `src/tables6.py` fixes the
range and the precision and asserts the invariant, and the multiplier is
computed in the VM as `floor(96000000 / winning outcomes) / 10000`.

Crash needs no table: `src/tables4.py` only fixes the constants and asserts
the distribution, because the failure point is sampled directly as
`HOUSE * PREC / rand(1, PREC)`.

`src/tables5.py` solves Aviamasters per slot rather than as a single ladder.
Every orb is an affine map `v -> a*v + b`, so the value distribution after each
slot can be walked exactly; from that, `alive_k = HOUSE / E[V_k]` gives the
survival curve that makes **every** cash-out point worth 0.96, and
`d_k = 1 - alive_k/alive_(k-1)` the per-slot ditch odds that ship as `amRamp`.
A flat ditch rate does not work — it puts the optimal stopping point at slot 1
— and the docstring records why.

That solver has to round the way *Scratch* rounds, not the way Python does.
The runtime computes `round(v * 100) / 100`, and Scratch's round block is JS
`Math.round`: halves go away from zero. Python's `round()` goes to even, and
the difference is reachable — halving 1.25 gives exactly 0.625, so Python says
0.62 where the game says 0.63. Modelling it Python's way put the shipped ramp
1/1000 out at three slots; `tests/play_avia.js` caught it by solving the table
independently.

`src/tables3.py` solves Duck Road as `HOUSE / (p**n * bonus(n))`, where
`bonus(n)` is the expected golden-egg contribution at lane n. It emits **two**
ladders rather than one: the runtime never multiplies a payout by 3 itself,
because `1.02 * 3` renders as `3.0599999999999996` in the multiplier readout.

`src/tables.py` bisects a scale factor per Plinko table until the binomially
weighted RTP hits 95%, then rounds to display-friendly values and re-checks.
Mines and stairs are closed-form. Roulette needs no solving: every bet type
returns exactly 36/37 by construction, asserted in `tables2.py`.

## Numeric display

There are no Scratch variable monitors anywhere. Numbers are drawn with a
`Digit` sprite carrying 16 costumes (`0`–`9`, `.`, `,`, blank, `x`, `M`, `B`)
and 40 clones split across nine fields. The last three were appended *after* the
blank so every costume index already in use kept its meaning, and a glyph is
picked with a single `item # of digitChars` lookup whose list order is the
costume order:

| Field | Slots | Shows | Where |
|---|---|---|---|
| 1 | 7 | chips, formatted | top-left, left-aligned |
| 2 | 4 | bet | on the bet plaque, hidden while `roundOn` |
| 3 | 7 | multiplier | top bar (mines, stairs, duck road, dice) |
| 9 | 8 | multiplier + `x`, or the dice roll | centre of the panel, at 170% (crash, aviamasters, coin flip, dice) |
| 4 | 2 | roulette result | under the wheel |
| 5 | 6 | roulette stake, or the dice win chance | top bar; bet bar on dice |
| 6/7/8 | 2 each | dealer / hand 1 / hand 2 totals | blackjack left column |

Each clone reads one character of its source string and positions itself from
the string length, so numbers stay centred as they grow. A clone renders its
character *by index*, so a string longer than its field is silently truncated -
the bankroll is formatted (`999,999` / `12.58M` / `1.26B`, never more than seven
characters) rather than trusted to stay short.

## Sound

`sfx.py` synthesises twelve 16-bit PCM mono WAVs with numpy (~149 KB total).
A hidden `Sfx` sprite owns all of them. Callers set `sfxId` and `sfxPitch` then
broadcast `sfx`; the handler applies the pitch effect and plays by index.

Mines rises 10 units (one semitone) per safe tile, stairs 15 per row climbed.
