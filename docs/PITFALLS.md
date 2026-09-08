# Pitfalls

Scratch execution behaviour that is not obvious. Every entry here cost real
debugging time on this project. Read before writing block logic.

---

## 1. Clones receive broadcasts too

A `when I receive` script runs on the original sprite **and on every clone**.

This caused the worst bug in the project. Each Plinko ball is a clone. The
`action` broadcast (the DROP button) was handled by a script that deducted the
bet and created a ball. Every ball already in flight also received `action`,
deducted the bet again, and spawned another ball. Exponential balls, chips
draining, and `ballsUp` never returning to zero.

It was invisible across 144 single-ball drops because the previous ball had
always been deleted before the next click. It only appeared with two balls
airborne at once.

**Fix:** give the sprite a local variable and gate on it.

```python
born = ball.local_var("born", 0)
ball.script(when_flag(), hide(), set_var(born, 0))          # original: 0
ball.script(when_clone(), set_var(born, 1), ...)            # clone: 1 immediately
ball.script(when_bc(p, "action"), if_(eq(born, 0), ...))    # only the original acts
```

Setting the flag as the **first block** of `when I start as a clone` is safe:
scratch-vm pushes the clone and starts its hats synchronously inside
`create clone of`, so nothing else can run in between.

Where the clone already carries a meaningful index (`bIdx`, `rIdx`, `sIdx`), the
original holds `0` and `if_(gt(idx, 0), ...)` serves the same purpose.

---

## 2. Rebroadcasting restarts a running script

If `when I receive X` is still executing and `X` fires again, the running script
is **stopped and restarted from the top**.

Consequences:
- A handler with `wait` blocks can be cut off mid-way.
- The bucket flash resets to normal on a non-matching broadcast, so a second
  ball landing elsewhere does not leave the first bucket stuck lit.
- A handler with no yielding blocks always completes, because it runs to the end
  inside one `stepThread` call and cannot be interrupted.

---

## 3. `startHats()` bypasses hit-testing

`vm.runtime.startHats('event_whenthisspriteclicked', null, target)` starts the
hat **directly on the target**. It does not check visibility, layering, or
whether another sprite covers the click point.

This means logic harnesses can "click" a button that a real player cannot reach.
It shipped in v3: `HitBtn` sits at x=-150, and the bet plaque plus its digits sat
at x=-152 and stayed visible during a hand because their visibility checked
`screen` but not `roundOn`. Players saw only STAND and DOUBLE respond. Every
logic test passed.

**`tests/overlap.js` exists for exactly this.** It measures each button's
bounding box from costume metadata and flags any visible sprite covering its
centre. Run it on every change that touches visibility or positioning.

The layout mock has the same blind spot if you draw it from assumptions rather
than from the real visibility conditions.

---

## 4. Custom blocks cannot return values

Scratch procedures return nothing. Write the result into a variable.

```python
draw_card = Proc(bjt, "draw card", [], warp=True)
define(bjt, draw_card,
       set_var(tmp, rand(1, len_of(deck))),
       set_var(drawn, item_of(deck, tmp)),      # result lands in `drawn`
       delete_of(deck, tmp))
```

You also cannot index a list by a variable list-name, so "score whichever hand
is active" needs either two near-identical procedures or an `if/else` inside one.

---

## 5. Loops yield one iteration per frame unless warped

A plain `repeat 52` takes 52 frames, roughly 1.7 seconds. Building a deck or
resetting a 25-tile board would visibly stall.

Mark procedures `warp=True` (run without screen refresh) for anything that
should be instant. Everything in `build.py` that rebuilds a list is warped.

Warp still terminates on a `repeat until` — the placement loops that pick random
distinct bomb positions rely on this and finish in a handful of iterations.

---

## 6. `switch costume to (<reporter>)` needs a `CoverMenu`

The costume input normally holds a `looks_costume` **shadow block**, not a
primitive. Dropping a reporter on it produces `[3, reporterId, shadowId]`, where
the shadow is referenced by block id. `sb3.py` handles this via `CoverMenu`;
`blocks.py` exposes it as `switch_costume_r(reporter, default_name)`.

The plain `switch_costume("name")` takes a **costume name**, never a number.
`switch_costume(1)` fails validation because `1` is not a costume in the sprite.

Same mechanism applies to `play_sound_r()` and `switch_backdrop_r()`.

---

## 7. `letter of` returns a character, so `+ 1` breaks on `.`

The digit display picks a costume with `(letter n of number) + 1`, which maps
`"0"`→costume 1 … `"9"`→costume 10. For `"."` the arithmetic yields `1`, which
would render a zero. Branch explicitly:

```python
if_else(eq(tmp2, "."), [switch_costume("d11")],
        [if_else(eq(tmp2, ","), [switch_costume("d12")],
                 [switch_costume_r(add(tmp2, 1), "d1")])])
```

---

## 8. The `broadcasts` dict is id → name

In `project.json` the stage's `broadcasts` maps **id to name**, the opposite of
the natural way to keep the registry in Python. Getting it backwards produces a
file that validates structurally but has no working broadcasts.

---

## 9. Sound assets need `rate` and `sampleCount` to match the file

```json
{"assetId": "<md5>", "name": "win", "dataFormat": "wav",
 "format": "", "rate": 22050, "sampleCount": 11245, "md5ext": "<md5>.wav"}
```

`format` is `""` for uncompressed. 16-bit PCM mono WAV works; `sb3.py` reads the
rate and frame count out of the file with the `wave` module rather than trusting
a constant.

Pitch is shifted per-play by setting the `PITCH` sound effect on the playing
sprite before `play sound`. **10 units = one semitone**, 120 = an octave. The
effect persists, so reset it on every call — `SFX(name, pitch=0)` always writes
`sfxPitch`.

---

## 10. `touching mouse-pointer` needs a renderer

Headless, `isTouchingObject('_mouse_')` always returns false because it goes
through `renderer.drawableTouching`. Hold-to-repeat on the bet buttons uses this
idiom, so testing it requires stubbing that one primitive:

```js
const RT = Object.getPrototypeOf(sp('BetPlus'));
const orig = RT.isTouchingObject;
RT.isTouchingObject = function (o) {
  if (o === '_mouse_') return heldName !== null && this.sprite.name === heldName;
  return orig.call(this, o);
};
```

`when this sprite clicked` fires on **mouse up**, so it cannot drive
hold-to-repeat. A `forever` loop testing `touching mouse-pointer AND mouse down`
is the only way.

---

## 11. Clone limit is 300

Currently 241 are alive: 32 digits, 49 roulette spots, 36 stair tiles, 25 mine
tiles, 18 cards, 17 buckets, 9 stair multipliers, 6 lobby tiles, 3 reels, plus
transient chips and Plinko balls. Scratch silently refuses to create beyond the
cap, so a ball that fails to spawn after the bet was deducted would lose money.
The Plinko spawn is guarded with `ballsUp < 25` for that reason.

Prefer broadcast-driven updates to `forever` loops for large clone groups.
Roulette spots, stair tiles and buckets refresh on `screenChanged` rather than
polling every frame; that removed over a hundred per-frame loops.

---

## 12. Variance will fool you

Two payout paths look broken when they are merely rare. A player blackjack
appears roughly once in 21 hands and roulette lands on zero once in 37 spins.
Short runs produce zero occurrences and a red test.

The blackjack harness therefore runs until every path has been exercised rather
than a fixed count. When a rare-path test fails, check the occurrence count in
the message before assuming a bug.
