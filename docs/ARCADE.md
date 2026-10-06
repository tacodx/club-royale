# Arcade cabinet

Club Royale runs on the work arcade: a Raspberry Pi cabinet with two player
stations, each with one joystick, A B X Y L R, SELECT and START. The cabinet
side lives in `tacodx/arcade-scratch-pipeline`. That repo packages the `.sb3`,
and its bridge turns each player's stick and buttons into key presses. This
page is the contract between the two repos: which keys the game reads, and
what each one does.

Nothing in the game knows it is on a cabinet. It reads keys, and the mouse
still works as it always has.

## The keys

| Panel | Key the game reads | Does |
|---|---|---|
| Stick | `up/down/left/right arrow` | move the gold frame to the nearest control that way; held, it repeats |
| **A** | `space` | press the framed control; held on BET − / BET +, it repeats |
| **B** | `b` | back to the lobby (refused mid-round, like the LOBBY button) |
| **L** | `l` | bet down; held, it repeats |
| **R** | `r` | bet up; held, it repeats |
| **Y** | `y` | the game's main action: SPIN, DROP, START, DEAL, GO, LAUNCH, TAKE OFF, FLIP, ROLL |
| **X** | `x` | cash out (Mines, Stairs, Duck Road, Crash, Aviamasters, Coin Flip) |
| START | `enter` | press, like A; when you are out of chips, a fresh 1,000 |
| SELECT | `b` | same as B. SELECT + START still quits to Batocera. |

**Both players get the same keys.** It is a one-player casino, and identical
keys mean whoever walks up to either station can play. Two-player play (two
bankrolls on one screen) would be a separate, much bigger change.

Y and X are shortcuts. Everything they do can also be done by moving the frame
to the button and pressing A, so the game is fully playable with only the
stick, A and B.

## game.json for the pipeline

Drop this into `games/clubroyale/game.json` in the pipeline repo, next to the
built `game.sb3` (`dist/ClubRoyale.sb3` from here).

The button layout assumes the panel reads `L X R` on the top row and `Y B A`
on the bottom row, as on a SNES pad, which is how the labels were described.
If the labels sit differently on the real panel, swap the action names
between buttons. The keys stay the same.

```json
{
  "slug": "clubroyale",
  "title": "Club Royale",
  "source": "game.sb3",
  "framerate": 30,
  "interpolation": true,

  "//": "Club Royale reads the arrows plus space / b / l / r / y / x / enter. See docs/ARCADE.md in the club-royale repo. Both players get identical keys - one casino, either station plays it.",
  "//restart": "Not needed: the game offers a fresh 1,000 on START when you are out of chips, and resets itself after 3 minutes untouched.",
  "buttons": {
    "topLeft": "betdown", "topMid": "cash",  "topRight": "betup",
    "botLeft": "action",  "botMid": "back",  "botRight": "press",
    "select": "back"
  },
  "stick": { "up": "up", "down": "down" },

  "controls": {
    "p1": { "left": "left arrow", "right": "right arrow", "up": "up arrow", "down": "down arrow",
            "press": "space", "back": "b", "betdown": "l", "betup": "r",
            "action": "y", "cash": "x", "start": "enter" },
    "p2": { "left": "left arrow", "right": "right arrow", "up": "up arrow", "down": "down arrow",
            "press": "space", "back": "b", "betdown": "l", "betup": "r",
            "action": "y", "cash": "x", "start": "enter" }
  }
}
```

The pipeline's automatic settings should all come out as "not applied". The
project has no `touching color`, so no `renderScale` or `deferStart`. It reads
letter keys, so no automatic `restart` binding either, and it should not get
one, because restarting would wipe a player's bankroll mid-session. The pointer
parking the pipeline injects is harmless: the only hover effect is the lobby
tiles lighting up, and a parked corner pointer touches none of them.

**Check at the cabinet before trusting it.** The costumes come to about 37 MB
of textures. That is under Slime Jump's 46 MB, and Slime Jump runs fine with the
`--disable-gpu-memory-buffer-compositor-resources` flag `cabinet.json` already
sets. It is still the number to watch if the game sticks at 99% while loading.

## What the game does for a cabinet

**The focus frame.** A gold frame sits on one control at a time. It can only
land on a control that is on screen right now. Each control's availability is
the same Python expression its own sprite is shown under, so the frame cannot
reach anything a mouse could not click. A press runs the same blocks a click
runs, generated from one function, so a joystick press and a click cannot
behave differently.

**Where the frame goes by itself.** Each screen has an order of controls. When
the framed control disappears, the frame moves to the first one in that order
that is showing. It keeps following the order for as long as the game, not the
player, placed it. That is what moves it from DEAL to HIT, from START into the
middle of the mines grid, from LAUNCH to CASH OUT, and back to START when a
round ends. Once the player moves it with the stick, it stays where they put it
until that control goes away. Back in the lobby it starts on the tile of the
game just left, so B then A replays it.

**Special cases.**

- Roulette opens on RED, because SPIN with nothing staked does nothing.
- In Stairs the frame names a *column*, not a tile, so it climbs with the live
  row.
- On the Dice slider, left and right drag the threshold: a whole point per tap,
  five per step once held. Up and down leave the slider.

**Out of chips.** There is still no rebuy. But a cabinet has no green flag, so
the end of a session has to be something a player can press. Once nothing is
staked anywhere and the bankroll cannot cover the smallest bet, an OUT OF CHIPS
banner appears (in the lobby it replaces the title). START, or a click on the
banner, does exactly what the green flag does: a fresh 1,000 and the lobby. With
chips left, START is just A and never refills anything.

**Idle reset.** A cabinet is a shared machine. After 3 minutes in which nobody
has played (`idleSecs`), the game resets to a fresh 1,000 in the lobby, whatever
the last player left. "Played" means a key, a click, a change in the bankroll or
a change of screen, so a desk player sitting through a long run of hands with
the mouse still is never reset under them. A half-played Mines board, a Blackjack hand or a Duck
Road run is static and safe to drop. A rocket or plane already in the air is
left to finish first, so a flight's settlement never runs into a fresh
session.

**The mouse.** A click hides the frame. The next push of the stick or press of
A only brings it back, so a mouse player never has a focus they cannot see
pressed for them.

## Verifying it

`tests/play_arcade.js` plays every game using only these keys, posted through
the VM's real keyboard device. It never calls `startHats` and never sets a
variable to fake a press. It walks the frame to every control on every screen,
checks after every step that the frame is drawn on the visible control the
focus names, and covers the broke banner, START, the idle reset and the mouse
hand-off. `tests/boot_race.js` also drives the stick and A from the first frame
after the green flag, the case a player at a cabinet actually creates. Both run
in `make test` and `make verify`.

Keys are held for about three frames, not tapped. Scratch polls the keyboard
once a frame, so a press that starts and ends within a single frame is never
seen. The pipeline README notes the same thing for its own checks.
