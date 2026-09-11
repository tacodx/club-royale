# Changelog

Older `.sb3` builds are attached to GitHub Releases rather than committed.
`dist/ClubRoyale.sb3` is always the current build.

## v4.1

**A sprite could be left on top of every screen until the green flag.** Click a
game about a second after loading and one tile of it stayed visible in the lobby
and in every other game. Two things caused it, both from the same window.
Spawning is `repeat 36 [create clone]`, one clone per frame, so for 36 frames
the *original* sprite still carries the loop's index - and every
broadcast-driven sprite guards its refresh with `if idx > 0` precisely to
exclude the original. A refresh arriving mid-spawn therefore drew the original
as a 37th tile, and the end of the loop then reset the index to 0, excluding it
from every later refresh, so nothing ever hid it again. Clones born after that
refresh never received one either, which is why the board also came up missing
its top row. StairTile, RSpot and Bucket all had it. Their spawn loops are
warped now, so clone creation and the reset are one non-yielding step and there
is no window.

`tests/boot_race.js` is new and is the only check that can see this: it opens
every game at eight timings across the spawn window and asserts that no sprite
original is left visible and that each board is complete. It fails on the
previous build and passes on this one.

**Dice is a slider now.** The five preset chances are gone; the threshold is
dragged anywhere along the rail, which is what the game is in every real
casino. The drag reads `mouse x` / `mouse y` rather than `touching
mouse-pointer` - the latter needs a renderer and is always false headless
(PITFALLS 10), so reading the pointer directly is what lets the harness drive
the real control instead of a stand-in.

With a free threshold the multiplier cannot be a solved constant, so it is
computed where the slider is left: `floor(96000000 / winning outcomes) / 10000`.
Flooring rather than rounding is the point - rounding would let some thresholds
pay more than the exact figure and hand back the edge, while flooring can only
fall short. `src/tables6.py` proves the return is at or under 0.96 at all 9401
reachable positions and never more than 0.0001 under, and the multiplier is
shown to the same four places it is paid at so the readout cannot disagree with
the payout. The range is 1% to 95% win chance, 96x down to 1.0105x.

The win/lose split cannot be a baked costume any more. It is drawn by two plain
bars, each exactly one rail wide, that share an edge on the threshold; whatever
they overhang is covered by `DiceFrame`, whose opaque part is cut from a real
composite of the backdrop and the felt so it replaces exactly what it covers.
Scaling a single bar would have been simpler and does not work: scratch-vm
clamps `set size` to `1.5 x stage / costume height`, so a costume tall enough to
still fill the rail at a 1% width cannot be scaled up at all. Both readouts
reuse idle digit fields, so the rebuild costs no clones.

**The coin flip call is live between flips.** It was locked for the whole run,
so a long streak needed the same side to keep landing. A streak is a sequence of
independent 50/50 calls, so the side is now re-pickable before every flip and
only locked while a coin is in the air. The maths is untouched.

**The lobby is three rows.** Eleven tiles were crammed into six-over-five at
68x66 because the table felt in the backdrop only runs from y 137 to y -125. The
lobby now has its own backdrop with a taller table and no bet-bar strip - it
shows no bet controls, so those 44 units were dead space - and the tiles are
back to the 82x70 of the nine-game lobby, four over four over three.

**No more free chips at zero.** Running out ends the session; the green flag
starts you at 1000 again. `tests/play_core.js` asserted the rebuy happened and
now asserts it does not, and that a broke player is refused rather than wedged.

## v4.0

**Two more games: Coin Flip and Dice.** Eleven now.

**Coin Flip** is a streak, not a single toss. Call heads or tails, and every
correct call doubles the pot; one wrong call takes the stake. The ladder is
`0.96 * 2^n` for twelve rungs, 1.92x to 3932.16x, and cashing out on any of
them returns exactly 0.96 of the stake — the cut is taken on entry, so there
is no rung worth holding out for. Unlike every other table in the project this
one needs no rounding at all: `0.96 * 2^n` terminates at two decimals for
every n, so `src/tables6.py` proves the edge in `Fraction` arithmetic instead
of asserting it within a tolerance. `3932.16x` is eight characters, which is
exactly what the big readout has slots for.

**Dice** rolls 0.00–99.99 against a threshold, under or over. The roll is drawn
as a whole number of hundredths out of 10,000 and every comparison is made on
that integer, so what pays never depends on how a float prints. The five
chances — 80%, 48%, 24%, 9.6%, 1.92% — were picked so that
`chance x payout` is exactly 0.96 in every mode, which makes the check
`wins * payout-in-hundredths == 10000 * 96` in integers. UNDER t and OVER
(100 - t) are the same number of outcomes, so one table serves both sides.

**The lobby is six across and five beneath.** Eleven tiles at 68x66. Nine fitted
as five-over-four at 82x70, but six across would need 528 of the 480 stage, and
three rows of 70 hang off the table felt in the backdrop — it runs from y 137
down to y -125, which is two rows and no more. The tiles shrank instead, and the
label padding shrank with them so the longest name still fits the octagon.

**Neither game runs an animation script.** The coin repaints every frame from
`cfSpin`/`cfSide` and the dice needle from `dcRolling`/`dcInt`. A `when I
receive` spin would be restarted by the next flip (PITFALLS 2) and takes as many
frames as it has steps, but under `FAST=1` a whole round finishes in one — so
the coin could still be tumbling, or showing the previous flip, when the round
that paid it was over. Rendering from state means the face on screen cannot
disagree with the side that was paid, at either speed, and both harnesses assert
on it.

**Both games borrow the existing readout rather than adding digit clones.**
Field 9 was crash's; it now carries the coin's pot and the dice roll too, and
the two games cost two clones between them — the extra lobby tiles. Boot is 235
of the 300, worst case 284 once roulette lays 49 chips.

**Two clone-budget assertions were measuring the wrong number.**
`play_blackjack.js` and `play_games.js` compared `runtime.targets.length`
against 300, but Scratch's cap is on clones alone: `Runtime.MAX_CLONES` is
checked against `_cloneCounter`, and `makeClone()` is the only thing that
increments it — sprite originals are not part of the budget. With 65 originals
in the count the reading was 298, two under a limit it was not actually
approaching, and twelve new sprites took it to 312 while the real clone count
moved 233 → 235. Both now count clones, as `play_duck.js` and `play_avia.js`
always did.

## v3.9

**Aviamasters, properly this time.** The ninth game, and the second attempt at
this name — v3.7 admitted the first one was a crash curve wearing the label, and
kept it as Crash. The real BGaming game is a collection game: a plane flies from
one carrier to another, and the sky is full of orbs. Numbers add to the running
multiplier, x-orbs multiply it, and rockets *halve* it without ending the round.
Land and you are paid; ditch and the stake is gone; bail out any time for
whatever the readout says.

Every orb is an affine map, `v -> a*v + b`, so the value distribution after each
slot walks out exactly. `src/tables5.py` solves the danger **per slot** from
that: `alive_k = HOUSE / E[V_k]` is the survival needed to make crossing k orbs
worth 0.96, and `d_k = 1 - alive_k/alive_(k-1)` the ditch odds that produce it.
Two designs that do not work are recorded in the docstring — a flat ditch rate
puts the optimal stopping point at slot 1 (and lands 0.03% of flights), and a
rising ramp cannot fix it, because if the first slot is cheap the edge is
already lost there. Solved per slot, every cash-out point is worth exactly the
same, so there is no strategy to find. 21.1% of flights land; the cap is 250x.

**The solver was rounding the wrong way.** Scratch's `round` block is JS
`Math.round`, so halves go away from zero; Python's `round()` goes to even. That
is reachable here — halving 1.25 gives exactly 0.625, so Python modelled 0.62
where the game produces 0.63 — and it put the shipped ditch ramp 1/1000 out at
three of the fourteen slots. `tests/play_avia.js` caught it on its first run by
solving the table from the published constants instead of reading it back.

**An auto cash-out on the final slot paid twice.** It fires inside the same
loop iteration that lands the plane, so the cash-out paid and then the landing
paid the same flight again. The landing branch is now guarded on `roundOn`.

**A clean checkout could not build.** `ensure_tables()` never learned about
`tables4` and `tables5`, so anything but an already-populated `build/` failed on
a missing JSON. CI passed only because `make tables` ran first and the crash
table happened to be committed. `make tables` now solves all five.

**`tests/play_avia.js`** replays every flight rather than sampling it. The
runtime logs the orb taken at each slot to `amLog`, so the harness can start at
1x, apply each orb's map, round and clamp exactly as the game does, and demand
the payout match to the penny — landings, manual cash-outs and auto cash-outs
alike. Nothing in it is statistical except the draw frequencies, which are
checked against the published weights. 23 assertions.

**The lobby is five across the top and four beneath.** Nine tiles at 82x70.

Boot clone count is 233 of 300, worst case 282 with roulette's chips down.

## v3.8

**Roulette's wheel hid behind its own popup** — reported from play, and caused
by v3.6 fixing `go_layer()`. WheelPanel, Wheel and Pointer all send themselves
to the front on the same `rSpin` broadcast, so which ends up on top depends on
handler order. While the opcode was dead that was harmless: static creation
order put the wheel above the panel. The moment the block started working, the
panel could win the race and swallow the wheel. The wheel and pointer now
re-front for the length of the spin.

`tests/play_games.js` asserts it, using `runtime.executableTargets` — which
scratch-vm keeps in lockstep with the renderer's draw list, so z-order is
checkable headless after all.

**Two Duck Road assertions were reading state the game had already reset.**
The egg flag was checked after the hop returned, but reaching lane 12 ends the
run and clears it as part of settling — a mismatch needing an egg *at* lane 12
and a full 12-lane survival, about one run in 170. And the plant-rate check
read `dkEgg` after the hop, where a death has already cleared it, so it
reported 10% against a designed 25% and passed only because its bound was
loose. Both now sample while the run is live; the rate reads 23%.

## v3.7

**Aviamasters was never Aviamasters.** It was built from "crash-style" rather
than from the real game, and reported back as such. Researching BGaming's Avia
Masters shows it is a different animal: a propeller plane launches from an
aircraft carrier and flies a random route collecting floating orbs - numbers
(+1, +2, +5, +10) add to the multiplier and multiplier orbs (x2..x5) multiply
it - while rockets HALVE it without ending the round. You win by landing on the
far carrier; ditching in the water loses the stake. 97% RTP, max x250.

So the game that shipped is now simply **Crash**, with its own identity rather
than a borrowed one: a cold indigo starfield instead of the oxblood sea, a
launch gantry drawn into the panel, and a gold rocket that climbs on exhaust
and tumbles when the run ends. `SeaPanel` -> `SkyPanel`, `Plane` -> `Rocket`,
the scenic ships -> drifting stars with parallax, `Splash` -> `Burst`, FLY ->
LAUNCH, and `tests/play_avia.js` -> `tests/play_crash.js`.

The maths is untouched and still exact: the failure point is drawn once at
launch from P(fail >= x) = 0.96 / x.

## v3.6

Reported from play: Duck Road froze on every hop, Aviamasters ran in slow
motion, and text was hidden behind the game panel on both. Three root causes,
two of which had been in the project since v1.

**`go_layer()` had never worked.** `src/blocks.py` emitted the opcode
`looks_goto_front_back`; the real Scratch opcode is `looks_gotofrontback`.
scratch-vm skips an unknown opcode silently - no warning, no error, the block
simply never runs - so all 22 "go to front/back layer" blocks in the project
were dead, and the v3.5 fix that relied on one changed nothing. That is why the
Aviamasters readout and the Duck Road banner sat behind the panel; it is also
why the bet amount was hidden behind its own plaque on every screen, the
roulette winning number sat behind the wheel, and the stairs banner sat behind
the bottom row of tiles.

`tests/load.js` now fails the build if any non-shadow block uses an opcode
scratch-vm cannot execute. It catches this class outright.

**Duck Road's freeze was a warp procedure that waits.** `Proc.__init__`
defaulted to `warp=True`, and `duck hop` was the one call site that omitted the
keyword - so a procedure containing five `wait`s was marked "run without screen
refresh". In warp mode scratch-vm re-executes a yielding block instead of
yielding, and `control_wait` compares against a clock that only advances once
per frame, so each wait busy-spun for the full 500ms warp budget and starved
every other thread in the project.

Measured on the shipped build: a survive hop took 536ms and rendered 2 frames
(3.7fps); a death took 3043ms and rendered 6 (2.0fps); a full 12-lane clear
took 8.44s and drew 28 frames in total. The duck's glide never ran at all - it
teleported. After: 309ms and 18 frames (59fps) for a hop, 1625ms and 95 frames
for a death.

The default is now `warp=False`, which is a no-op for the other fifteen call
sites (they all pass it explicitly), and `tests/validate.py` rejects any warp
procedure containing a time-based yield.

**Aviamasters ran 43% slow** because `wait(0.07)` is not a whole number of
frames: it resolved on the third, a measured 99.7ms tick. The climb now yields
once per frame for an exact 1/30s tick, and the growth is re-solved to reach 2x
in 2.8s. The plane also barely moved - full travel needed 100x, which 1% of
rounds reach - so the mapping now completes at 10x, roughly tripling the travel
of a typical flight, and updates at 30Hz instead of 10Hz.

**Also:** ambient cars ran off the road onto the felt and covered the lane
labels; ships sailed out of the water at their wrap points; the death sequence
held 1.9s with nothing on screen moving, now 1.05s.

## v3.5

**Reported from play: text hidden behind the game panel** on both new screens -
the Aviamasters multiplier readout and the Duck Road win/lose banner.

One cause, not two. `RoadPanel` and `SeaPanel` are full-stage backgrounds and
were the only sprites in the game that never set their layer; being created last
in `build.py`, they sat in front of the digit readouts and the `Msg` banner.
Every other overlay calls `go_layer("front")`. They now hold the back layer and
re-assert it while visible.

The geometry says the same thing: the Aviamasters readout spans y=70..114 and
the panel's top edge is at y=105, so exactly 9px of the digits cleared it.

Ambient traffic and the ships had to stop sending themselves to the back at the
same time - with the panels holding that layer, anything else going there would
have been drawn behind the road and the sea, and vanished.

**Flaky check replaced.** `play: golden egg found` needed both a 25% roll and
the duck surviving to that lane, so a working game failed it whenever neither
happened - 0 eggs in 30 runs is ordinary. It now checks that eggs are *planted*
at the designed rate, which depends on one roll rather than two; the
deterministic forced-pickup test already proves the payout.

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
