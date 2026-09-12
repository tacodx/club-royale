# CLAUDE.md

Club Royale is an art-deco casino game for **Scratch 3**. It is not written in the
Scratch editor. A Python compiler in `src/` emits `project.json`, generates every
image and sound, and zips the result into a `.sb3`.

Read `docs/PITFALLS.md` before writing any block logic. It documents Scratch
execution behaviour that is not obvious and that has caused real bugs here.

## Setup (once)

```bash
make deps          # pip install -r requirements.txt && npm install
```

Node is required. The test harnesses load the real `scratch-vm` and play the
game headlessly; without them you cannot verify anything.

## Commands

| Command | What it does | Time |
|---|---|---|
| `make build` | Real-timing build → `dist/ClubRoyale.sb3` (the shippable file) | ~20s |
| `make fast` | Same logic, waits shortened → `build/ClubRoyale_fast.sb3` | ~20s |
| `make check` | Structure + VM load + click-blocking sweep | ~1 min |
| `make test` | Full suite on the fast build | ~10 min |
| `make verify` | Full suite on the shipped file at real speed | 30+ min |
| `make mocks` | Render every screen at exact sprite coordinates → `mocks/` | ~15s |

`FAST=1` only changes `wait` durations. The block logic is identical, so payout
correctness proven on the fast build holds for the real one. Timing-dependent
behaviour is the exception and must be checked with `make verify`.

## Rules

**Run `make test` before claiming any change works.** The compiler happily emits
a valid `.sb3` that plays wrongly. Static validity proves nothing about gameplay.

**Never skip `tests/boot_race.js` either.** Every other harness waits for the
clone count to settle before it touches anything, so none of them can see what
happens when a player clicks a game while the clones are still spawning - and a
player does exactly that, one second after the green flag. Three sprites shipped
broken that way; see the spawn-window rule below.

**Never skip `tests/overlap.js`.** It is the only check that catches a button
covered by another sprite. The logic harnesses call `startHats()`, which fires a
click hat directly on a target and bypasses hit-testing entirely, so they will
happily "click" a button that a real player cannot reach. This exact bug shipped
in v3: the bet plaque sat on top of the HIT button and swallowed its clicks,
while every logic test passed.

**Verify the display, not just the variable.** A v1.1 refactor deleted the
blackjack hand totals from the screen. Tests kept passing because they asserted
on the `you` and `dealer` variables, which were still correct. Nobody could see
them. When a change touches what is shown, assert on what is rendered
(`tests/play_blackjack.js` reconstructs the digit sprites and compares) and run
`make mocks`.

**Watch the clone budget.** Scratch caps clones at 300. Currently 241 clones are
alive at boot (49 RSpot, 40 Digit, 36 StairTile, 25 MineTile, 18 Card, 17
Bucket, 12 DuckMult, 11 MenuTile, 9 Reel, 9 StairMult, 6 Spark, 5 AvOrb, 4
DuckCar), and roulette adds up to 49 chips on top, so the real worst case is
290 — 10 spare. `src/build.py` prints nothing about this, so count before adding a
clone-heavy feature: `tests/play_blackjack.js`, `tests/play_duck.js`,
`tests/play_avia.js`, `tests/play_coin.js` and `tests/play_dice.js` all assert
`< 300`. Coin Flip and Dice cost two clones between them — both render from
single sprites and borrow the existing digit fields on purpose.

**End a round atomically.** Crash (then called Aviamasters) set `roundOn = 0`
when the flight ended and raised `busy` a beat later, leaving one frame where
FLY was visible again while settlement was still pending — a click in that
frame started a second round on top of the first. Whatever ends a round must
clear `roundOn` and raise `busy` in the same non-yielding step.

**Only one thing may pay a round.** Aviamasters pays on landing *and* on
cash-out, and its auto cash-out fires inside the same loop that lands the
plane — so an auto target reached on the final slot paid twice. The landing
branch is guarded on `roundOn` still being 1. Any second payout path needs the
same guard.

**Payout tables are solved, not hand-written.** `src/tables.py` through
`src/tables6.py` compute every multiplier to a target house
edge and assert the result. Change the target there; never edit a multiplier by
hand. The assertions run against the *rounded* values that ship, not the exact
ones, so what a player is paid is what was verified. Dice is the one game with
no table - its threshold is dragged, so the multiplier is computed in the VM -
and the same rule applies: `tables6.py` fixes the range and the precision and
asserts the invariant across every reachable position.

**Decide the outcome before you animate it.** Duck Road rolls the hop, then
plays the traffic to match. If a collision decided the payout instead,
correctness would depend on frame timing and could not be proven on the fast
build - which is the guarantee the whole suite rests on. Real crash games work
this way too.

**Spawn clones inside a warped procedure.** An unwarped `repeat ... create
clone` takes one frame per clone (PITFALLS 5), and for those frames the
*original* sprite is still carrying the loop's index. Every broadcast-driven
sprite here guards its refresh with `if idx > 0` to exclude the original - so a
refresh arriving mid-spawn passed that guard and drew the original as if it were
a clone. Worse, the end of the loop resets the index to 0, which then excluded
the original from every later refresh, so nothing ever hid it again: a stray
stairs tile sat on top of the lobby, and of every other screen, until the green
flag. Clones born after that refresh never got one either, so the board came up
missing its last row. Warping the loop makes the whole thing - clones and the
reset - one non-yielding step, and there is no window to race.

**Render animation from state, not from an animation script.** A `when I
receive` animation is restarted by the next broadcast (PITFALLS 2) and takes as
many frames as it has steps — but under `FAST=1` a whole round can finish in
one. A coin spun by its own script could therefore still be mid-tumble, or
showing the previous flip's face, when the round that paid it is over, and a
test asserting on the face would go red for something that is not a bug. The
coin and the dice needle instead repaint every frame from `cfSpin`/`cfSide` and
`dcRolling`/`dcInt`, so what is on screen cannot disagree with what was paid,
at either speed.

**Round the way Scratch rounds, not the way Python does.** Scratch's `round`
block is JS `Math.round` — halves go away from zero. Python's `round()` goes to
even. Anywhere a solver models a value the *runtime* computes, the two must
agree: halving 1.25 gives exactly 0.625, and Python says 0.62 where the game
says 0.63. That put the Aviamasters ditch ramp 1/1000 out at three slots.
`src/tables5.py` has an `r2()` that matches the VM.

**A digit field can only render as many characters as it has clones.** Each
clone draws one character *by index*, so a string longer than the field simply
loses its tail - silently, and looking entirely plausible. The bankroll shipped
this way for eight versions: 12,582,900 rendered as `1258290`. Format the value
to fit the field rather than trusting it to be short.

**Sprites driven by `forever` loops need a frame to catch up.** Button
visibility and the digit readouts repaint from `forever` loops, so reading them
in the same tick that `busy` clears gives you the *previous* frame. Three
assertions in `tests/play_duck.js` failed this way before they were made to
settle first; none of them was a real bug. Poll until the value stabilises
rather than asserting immediately.

## Layout

```
src/
  paths.py       repo-relative paths; everything generated lands in build/
  sb3.py         the .sb3 compiler (project.json + zip)
  blocks.py      block DSL: when_flag(), if_else(), item_of(), Proc(), ...
  deco.py        art style system: palette, gold gradients, chamfered panels
  assets_v11.py  backdrop, buttons, cards, slots, plinko, mines, digits
  assets_v2.py   roulette layout + wheel, stairs, lobby tiles
  assets_v3.py   duck road: road panel, duck, traffic, lane ladder, egg
                 (owns the lane geometry build.py positions sprites from)
  assets_v4.py   crash: night sky, launch gantry, rocket, burst
                 (likewise owns the flight-path geometry, and the shared
                 big-multiplier readout position used by crash and aviamasters)
  assets_v5.py   aviamasters: dusk sky, two carriers, biplane, collectible orbs
  assets_v6.py   coin flip: felt, 12-frame coin, the payout ladder; dice: the
                 0-100 rail, its two sliding bars and the frame that masks them
                 (owns both games' geometry, and writes build/geom6.json so the
                 harnesses measure against the numbers the art was drawn from)
  sfx.py         synthesised WAVs (numpy)
  tables.py      plinko (rows x risk) and mines (bomb count) solvers
  tables2.py     stairs (5 modes) solver + roulette constants
  tables3.py     duck road (4 modes) solver, base + golden-egg ladders
  tables4.py     crash distribution + climb constants
  tables5.py     aviamasters orb mix + the per-slot ditch ramp
  tables6.py     coin flip ladder (exact, no rounding) + the dice range and
                 precision, asserted over all 9401 slider positions
  tables7.py     slots: the three reel strips, the five paylines and the
                 3-of-a-kind ladder, solved to exactly 24/25 and asserted
                 over all 27000 screens
  build.py       the game itself: sprites, scripts, wiring
tests/
  validate.py         static: every block/costume/variable reference resolves
  load.js             does the real Scratch VM deserialise it
  overlap.js          is any button covered by another visible sprite
  play_blackjack.js   full blackjack rules vs an independent implementation
  play_games.js       roulette (all bet types) + stairs (all 5 modes)
  play_core.js        slots, plinko (9 tables), mines (4 tables), navigation
  play_duck.js        duck road: table vs an independent solve, every hop
  play_crash.js       crash: failure point, climb, cash-out, auto
  play_avia.js        aviamasters: replays every flight from its orb log
  play_coin.js        coin flip: every call, every rung, the coin's own face
  play_dice.js        dice: drives the real slider, every threshold and side
  play_slots.js       slots: the window rule, every one of the 729 triples on a
                      line, the grid as rendered, and what each spin paid
  boot_race.js        opens every game mid-spawn: the only check for a sprite
                      left visible on a screen it does not belong to
tools/
  mock.py        composite every screen at exact sprite coordinates
```

## Games

| Game | House edge | Notes |
|---|---|---|
| Slots | 96% RTP | 3x3 on weighted 30-stop strips, 5 paylines, one wild |
| Plinko | ~95.3% RTP | rows 8/12/16 x risk low/med/high = 9 tables |
| Mines | 96% RTP | 1/3/5/10 bombs, 4 tables |
| Blackjack | standard | double, split, insurance, dealer peek, 3:2 naturals |
| Roulette | 97.30% | European single zero; every bet type returns exactly 36/37 |
| Stairs | 96% RTP | 9 rows, 5 modes from 4-tile/1-bomb to 4-tile/3-bomb |
| Duck Road | 96% RTP | 12 lanes, 4 modes; 25% of runs hide a 3x golden egg |
| Crash | 96% RTP | rocket climb; failure point drawn at launch, up to 9600x, auto cash-out |
| Aviamasters | 96% RTP | 14 orbs on the route; rockets halve, cap 250x; every cash-out point worth the same |
| Coin Flip | 96% RTP | call a side; 12 rungs of exactly 0.96 x 2^n, cash out on any of them |
| Dice | 96% RTP | drag the threshold along 0.00-99.99, under or over; 1.01x to 96x, never above 0.96 |

## Known limitations

- **No rebuy.** Running out of chips ends the session; the green flag starts you
  at 1000 again. There used to be a free 500 at zero, which made the bankroll
  meaningless.
- **No persistence.** A refresh resets chips to 1000. Scratch only persists via
  cloud variables, which need the project shared on scratch.mit.edu, the user
  signed in, and a full Scratcher account. They also store numbers only.
- **The bankroll is abbreviated above a million** (`12.58M`, `1.26B`) rather
  than shown in full. Seven digit slots is what the top bar has room for before
  the readout runs into the MULT plaque at x=0.
