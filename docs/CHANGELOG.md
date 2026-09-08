# Changelog

Older `.sb3` builds are attached to GitHub Releases rather than committed.
`dist/ClubRoyale.sb3` is always the current build.

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
