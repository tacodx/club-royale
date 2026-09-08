# Changelog

Older `.sb3` builds are attached to GitHub Releases rather than committed.
`dist/ClubRoyale.sb3` is always the current build.

## v3.4

**The bankroll no longer lies.** Digit field 1 has seven slots and each clone
renders one character *by index*, so anything longer lost its tail: 12,582,900
displayed as `1258290` - a plausible figure ten times too small, with nothing on
screen to say it was wrong. It had been that way since v1.

Rather than widen the field (a thirteen-digit bankroll would run into the MULT
plaque at x=0), the number is formatted so it can never exceed seven characters:
`999` / `12,450` / `999,999` / `12.58M` / `1.26B`. That also closes the "no
thousands separator" limitation the README has carried since v1.1.

The digit sprite gained `M` and `B` costumes, and picking a glyph is now one
`item # of digitChars` lookup instead of a five-deep if-chain - the list order
is the costume order.

`tests/play_core.js` checks fifteen magnitudes from 7 to 15,690,050,000 and
asserts the readout never exceeds its seven slots.

## v3.3

**Aviamasters.** An eighth game, and the first that is not turn-based: a
seaplane climbs, the multiplier runs, and you bail out before it ditches. The
landing point is drawn once at take-off from the standard crash distribution,
`P(land >= x) = 0.96 / x`, so every cash-out point returns exactly 0.96 and the
whole thing is verifiable per round rather than statistically. Ceiling 9,600x.

**Auto cash-out** at 1.5x / 2x / 5x / 10x, in the selector slot the other games
use for difficulty. It fires inside the climb loop the instant the target is
reached, so it cannot overshoot by a frame.

**Capturing a cash-out is atomic.** Reading the multiplier and crediting the win
happen in one warped procedure, so a click can never land between the two and
pay against a multiplier the player did not see.

**Bug found while testing:** the round ended by setting `roundOn = 0`, then
raised `busy` a beat later. For one frame FLY was visible again while settlement
was still pending, and a click there started a second round on top of the first.
Both now happen in the same non-yielding step. The harness found it by being
unable to start a round, not by seeing a double round — worth remembering.

**A crash readout needs an "x".** The digit sprite gained a 14th costume,
appended after the blank so every existing costume index kept its meaning.

**Lobby** is now a 4x2 grid of eight tiles.

Verified: 17/17 aviamasters (every landing point exact against the formula, the
climb against GROWTH^tick, auto cash-out across three targets), 22/22 duck road,
15/15 blackjack, 22/22 roulette + stairs, 29/29 core, overlap clean across both
new screens. 224 clones at boot, 273 worst case.

**Also:** builds are byte-reproducible now. `zipfile` was stamping each entry
with the current time, so two builds of identical content differed and
`git status` went dirty after every build; entries now carry a fixed timestamp.

**Also:** three harnesses asserted clone counts 600ms after the green flag, but
the spawn loops need ~800ms (one clone per frame, PITFALLS 5) and Duck Road
pushed them over. They now wait for the count to settle. The roulette zero test
kept spinning until zero turned up rather than hoping it appeared in 70 spins —
it has a 15% chance of not.

## v3.2

**Duck Road.** A seventh game: the duck crosses twelve lanes of traffic one hop
at a time, the multiplier climbing with each lane, cash out whenever. Four modes
from EASY (90% a lane) to DAREDEVIL (45%), topping out at 9,281x — or 27,845x
carrying the egg.

**The golden egg.** One run in four hides an egg on a random lane. Reaching it
triples the payout for the rest of the run and the whole on-screen ladder
switches to the egg values. `src/tables3.py` divides the egg's expected
contribution back out of the base ladder, so every cash-out point still returns
exactly 0.96 — asserted against the rounded values that ship, not the exact
ones.

**Traffic is presentation, not physics.** Each hop is rolled before anything
moves and the cars animate to match. Tying the payout to collision timing would
have made correctness unprovable on the fast build.

**Lobby rebuilt** as four tiles across the top and three centred beneath; tiles
shrank from 130x84 to 100x76 to fit four across.

**`tests/overlap.js` never visited the new screen.** It passed on Duck Road
while testing nothing there — the same blind spot that shipped the v3 HIT bug.
It now sweeps screen 7 idle and mid-run, and knows `DuckSel`.

Verified: 22/22 duck road (96-entry table against an independent solve, every
hop checked against the roll the VM made), 15/15 blackjack, 22/22 roulette +
stairs, 29/29 core, overlap clean. 212 clones at boot, 261 worst case.

## v3.1

**Fixed:** HIT was unclickable in blackjack. The bet plaque and its digits sat at
x=-152, HIT at x=-150, and their visibility checked `screen` but not `roundOn`,
so they covered the button during a hand. Reported from play; every logic test
had passed. `tests/overlap.js` was written in response and reproduces it on v3.

**Added:** rising pitch on consecutive safe picks — one semitone per gem in
mines, a step and a half per row in stairs.

Verified: 15/15 blackjack, 22/22 roulette + stairs, 29/29 core, overlap clean.

## v3

**Sound.** 12 synthesised effects (~149 KB): card deals, reel ticks, chip
clinks, plinko pegs, gem reveals, explosions, wheel ticks, win/lose chords.

**Blackjack completed.** Double down, split on equal value (one split, split
aces get one card each, double allowed after split), insurance with dealer peek.

**Regression fixed.** The DEALER/YOU labels and hand totals had been deleted in
v1.1 along with the Scratch variable monitors and never replaced. Tests passed
throughout because they asserted on the variables, not the display.

Verified on the shipped file: 107 blackjack rounds settling exactly against an
independent implementation, covering 9 splits, 19 doubles, 7 insurance offers,
7 dealer blackjacks and the 3:2 natural.

## v2

Roulette (European single zero, 97.30%, stackable chips on 49 spots, spinning
wheel overlay, CLEAR/UNDO) and Stairs (9 rows, 5 modes). Lobby became 3x2.

Verified: 45 spins with 7 simultaneous bets across every bet category, zero
mismatches, including a spin landing on 0.

## v1.1

Art direction rebuilt as art-deco Monte Carlo. All Scratch variable monitors
replaced with gold digit sprites. 18-level bet ladder with hold-to-repeat.
Plinko became multi-ball with rows and risk selectors (9 tables); mines gained a
bomb-count selector (4 tables).

**Bug found by testing:** Plinko ball clones also received the `action`
broadcast, so every ball in flight spawned more balls and re-deducted the bet.
Invisible across 144 single-ball drops.

## v1

First build: lobby, slots, plinko, mines, blackjack. Established the compiler,
the art pipeline and the headless VM harness.
