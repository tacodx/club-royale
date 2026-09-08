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

**Watch the clone budget.** Scratch caps clones at 300. Currently 224 clones are
alive at boot, and roulette adds up to 49 chips on top, so the real worst case
is 273 — under 30 spare. `src/build.py` prints nothing about this, so count before adding a
clone-heavy feature: `tests/play_blackjack.js` and `tests/play_duck.js` both
assert `< 300`.

**End a round atomically.** Aviamasters set `roundOn = 0` when the flight ended
and raised `busy` a beat later, leaving one frame where FLY was visible again
while settlement was still pending — a click in that frame started a second
round on top of the first. Whatever ends a round must clear `roundOn` and raise
`busy` in the same non-yielding step.

**Payout tables are solved, not hand-written.** `src/tables.py`,
`src/tables2.py` and `src/tables3.py` compute every multiplier to a target house
edge and assert the result. Change the target there; never edit a multiplier by
hand. The assertions run against the *rounded* values that ship, not the exact
ones, so what a player is paid is what was verified.

**Decide the outcome before you animate it.** Duck Road rolls the hop, then
plays the traffic to match. If a collision decided the payout instead,
correctness would depend on frame timing and could not be proven on the fast
build - which is the guarantee the whole suite rests on. Real crash games work
this way too.

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
  assets_v4.py   aviamasters: sea and sky, seaplane, ships, splash
                 (likewise owns the flight-path geometry)
  sfx.py         synthesised WAVs (numpy)
  tables.py      plinko (rows x risk) and mines (bomb count) solvers
  tables2.py     stairs (5 modes) solver + roulette constants
  tables3.py     duck road (4 modes) solver, base + golden-egg ladders
  tables4.py     aviamasters crash distribution + climb constants
  build.py       the game itself: sprites, scripts, wiring
tests/
  validate.py         static: every block/costume/variable reference resolves
  load.js             does the real Scratch VM deserialise it
  overlap.js          is any button covered by another visible sprite
  play_blackjack.js   full blackjack rules vs an independent implementation
  play_games.js       roulette (all bet types) + stairs (all 5 modes)
  play_core.js        slots, plinko (9 tables), mines (4 tables), navigation
  play_duck.js        duck road: table vs an independent solve, every hop
  play_avia.js        aviamasters: landing point, climb, cash-out, auto
tools/
  mock.py        composite every screen at exact sprite coordinates
```

## Games

| Game | House edge | Notes |
|---|---|---|
| Slots | 94.3% RTP | 3 reels, 8 symbols, uniform |
| Plinko | ~95.3% RTP | rows 8/12/16 x risk low/med/high = 9 tables |
| Mines | 96% RTP | 1/3/5/10 bombs, 4 tables |
| Blackjack | standard | double, split, insurance, dealer peek, 3:2 naturals |
| Roulette | 97.30% | European single zero; every bet type returns exactly 36/37 |
| Stairs | 96% RTP | 9 rows, 5 modes from 4-tile/1-bomb to 4-tile/3-bomb |
| Duck Road | 96% RTP | 12 lanes, 4 modes; 25% of runs hide a 3x golden egg |
| Aviamasters | 96% RTP | crash; landing point drawn at take-off, up to 9600x, auto cash-out |

## Known limitations

- **No persistence.** A refresh resets chips to 1000. Scratch only persists via
  cloud variables, which need the project shared on scratch.mit.edu, the user
  signed in, and a full Scratcher account. They also store numbers only.
- **No `,` separators** in the chips readout. The digit sprite supports a comma
  costume; nothing formats the number yet.
- **Slots is the weakest game.** Uniform reels, no paylines. A second theme
  would not fix that; weighted reel strips and real paylines would.
