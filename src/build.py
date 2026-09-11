"""CLUB ROYALE v1.1"""
import os, json
from sb3 import Project
from blocks import *
import assets_v11 as AV
import assets_v2 as AV2
import assets_v3 as AV3
import assets_v4 as AV4
import assets_v5 as AV5
import assets_v6 as AV6
import json
import sfx as SFXMOD

A = AV.OUT
AV.build()
AV2.build()
AV3.build()
AV4.build()
AV5.build()
AV6.build()
SFXMOD.build()
T = AV.T
from paths import BUILD, SFX_DIR, DIST
T2 = json.load(open(BUILD / "tables2.json"))
T3 = json.load(open(BUILD / "tables3.json"))
T4 = json.load(open(BUILD / "tables4.json"))
T5 = json.load(open(BUILD / "tables5.json"))
T6 = json.load(open(BUILD / "tables6.json"))

FAST = os.environ.get("FAST") == "1"
_rw = wait


def wait(s):                       # noqa: F811
    return _rw(0.01 if FAST else s)


def gl(secs, x, y):
    """glide(), shortened under FAST like wait() is. Animation only."""
    return glide(0.01 if FAST else secs, x, y)


BET = AV.BET_LEVELS
ROWC, ROWSP, ROWHS = AV.ROWCOUNT, AV.ROWSP, AV.ROWHS
BOMBC = AV.BOMBCOUNT
BKV = AV.BUCKET_VALS

# flat payout tables ------------------------------------------------
PLINKO_FLAT = []
for ri, r in enumerate(ROWC):
    for k in AV.RISKNAME:
        t = T["plinko"][f"{r}_{k}"]
        PLINKO_FLAT += [f"{v:g}" for v in t] + ["0"] * (17 - len(t))
MINE_FLAT = []
for b in BOMBC:
    t = T["mines"][str(b)]
    MINE_FLAT += [f"{v:g}" for v in t] + ["0"] * (24 - len(t))

SPOTX = [-180, -150, -150, -150, -120, -120, -120, -90, -90, -90, -60, -60, -60, -30, -30, -30, 0, 0, 0, 30, 30, 30, 60, 60, 60, 90, 90, 90, 120, 120, 120, 150, 150, 150, 180, 180, 180, -30, 30, 90, -90, -150, 150, -105, 15, 135, -105, 15, 135]
SPOTY = [50, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, 24, 50, 76, -34, -34, -34, -34, -34, -34, -6, -6, -6, -62, -62, -62]

p = Project()


def C(t, name, file):
    return t.add_costume(name, os.path.join(A, file + ".png"))


# ===================================================== globals
chips   = p.var("chips", 1000)
screen  = p.var("screen", 0)
betIdx  = p.var("betIdx", 6)
bet     = p.var("bet", 50)
busy    = p.var("busy", 0)
roundOn = p.var("roundOn", 0)
msgId   = p.var("msgId", 1)
win     = p.var("win", 0)
mult    = p.var("mult", 0)
picks   = p.var("picks", 0)
tmp     = p.var("tmp", 0)
tmp2    = p.var("tmp2", 0)
rep     = p.var("rep", 0)
drawn   = p.var("drawn", 0)
holeCard= p.var("holeCard", 0)
hole    = p.var("hole", 0)
dealer  = p.var("dealer", 0)
you     = p.var("you", 0)
sc      = p.var("sc", 0)
aces    = p.var("aces", 0)
i_      = p.var("i", 0)
rowsIdx = p.var("rowsIdx", 2)
riskIdx = p.var("riskIdx", 2)
bombsIdx= p.var("bombsIdx", 2)
ballsUp = p.var("ballsUp", 0)
lastBk  = p.var("lastBucket", 0)
rStake  = p.var("rStake", 0)
rNum    = p.var("rNum", 0)
newChip = p.var("newChip", 0)
stDiff  = p.var("stDiff", 2)
stRow   = p.var("stRow", 1)
stClick = p.var("stClick", 0)
sfxId   = p.var("sfxId", 1)
sfxPitch= p.var("sfxPitch", 0)
you2    = p.var("you2", 0)
bjBet1  = p.var("bjBet1", 0)
bjBet2  = p.var("bjBet2", 0)
insBet  = p.var("insBet", 0)
activeH = p.var("activeH", 1)
didSplit= p.var("didSplit", 0)
bjPhase = p.var("bjPhase", 0)
canDbl  = p.var("canDbl", 0)
canSpl  = p.var("canSpl", 0)
chipsTxt= p.var("chipsTxt", "1000")   # formatted bankroll, <= 7 chars
cTmp    = p.var("cTmp", 0)        # scratch for the formatter only
amSlot  = p.var("amSlot", 0)      # orbs crossed so far
amVal   = p.var("amVal", 1)       # running multiplier
amOrb   = p.var("amOrb", 1)       # orb drawn for this slot
amRoll  = p.var("amRoll", 0)      # the draw that chose it
amAuto  = p.var("amAuto", 1)      # auto cash-out slot, 1 = OFF
amAt    = p.var("amAt", 0)        # multiplier captured on cash-out
amCashed= p.var("amCashed", 0)
amDown  = p.var("amDown", 0)      # 1 once it has ditched
avU     = p.var("avU", 0)         # the raw landing draw
avLand  = p.var("avLand", 0)      # multiplier the plane ditches at
avTick  = p.var("avTick", 0)      # climb counter
avAuto  = p.var("avAuto", 1)      # auto cash-out slot, 1 = OFF
avAt    = p.var("avAt", 0)        # multiplier captured on cash-out
avCashed= p.var("avCashed", 0)
dkMode  = p.var("dkMode", 1)      # 1..4 difficulty
dkLane  = p.var("dkLane", 0)      # lanes crossed so far
dkEgg   = p.var("dkEgg", 0)       # lane hiding the egg, 0 = none
dkGot   = p.var("dkGot", 0)       # egg collected this run
dkTgt   = p.var("dkTgt", 0)       # lane being attempted
dkRoll  = p.var("dkRoll", 0)      # the roll that decided it
dkHit   = p.var("dkHit", 0)       # lane the duck was hit in
bjA     = p.var("bjA", 0)
bjB     = p.var("bjB", 0)
cfCall  = p.var("cfCall", 1)      # 1 = heads, 2 = tails
cfSide  = p.var("cfSide", 1)      # the side the flip came up
cfStreak= p.var("cfStreak", 0)    # correct calls so far
cfSpin  = p.var("cfSpin", 0)      # 1 while the coin is in the air
cfAt    = p.var("cfAt", 0)        # multiplier captured on cash-out
cfCashed= p.var("cfCashed", 0)
dcMode  = p.var("dcMode", 3)      # 1..5 win chance
dcSide  = p.var("dcSide", 1)      # 1 = under, 2 = over
dcInt   = p.var("dcInt", 0)       # the roll, in hundredths: 0..9999
dcFrac  = p.var("dcFrac", 0)      # scratch for the roll formatter only
dcTxt   = p.var("dcTxt", "")      # the roll as it is displayed, "73.42"
dcWon   = p.var("dcWon", 0)
dcRolling = p.var("dcRolling", 0)
dcShown = p.var("dcShown", 0)     # a roll has landed on this visit

spotX   = p.lst("spotX", [str(v) for v in SPOTX])
spotY   = p.lst("spotY", [str(v) for v in SPOTY])
betLevels   = p.lst("betLevels", [str(v) for v in BET])
rowCounts   = p.lst("rowCounts", [str(v) for v in ROWC])
rowSp       = p.lst("rowSp", [str(v) for v in ROWSP])
rowHs       = p.lst("rowHs", [str(v) for v in ROWHS])
plinkoMults = p.lst("plinkoMults", PLINKO_FLAT)
bucketVals  = p.lst("bucketVals", [f"{v:g}" for v in BKV])
mineMults   = p.lst("mineMults", MINE_FLAT)
bombCounts  = p.lst("bombCounts", [str(v) for v in BOMBC])
reelResult  = p.lst("reelResult", ["1", "1", "1"])
bombs       = p.lst("bombs", [])
revealed    = p.lst("revealed", ["1"] * 25)
deck        = p.lst("deck", [])
pHand       = p.lst("pHand", [])
dHand       = p.lst("dHand", [])
rBets   = p.lst("rBets", ["0"] * 49)
rHistI  = p.lst("rHistI", [])
rHistA  = p.lst("rHistA", [])
redNums = p.lst("redNums", [str(v) for v in T2["red"]])
wheelOrd= p.lst("wheelOrder", [str(v) for v in T2["wheel"]])
stState = p.lst("stState", ["0"] * 36)
stBomb  = p.lst("stBomb", ["0"] * 36)
pHand2  = p.lst("pHand2", [])
diffTiles = p.lst("diffTiles", [str(d[1]) for d in T2["diffs"]])
diffBombs = p.lst("diffBombs", [str(d[2]) for d in T2["diffs"]])
stairMults= p.lst("stairMults",
                  [f"{v:g}" for d in T2["diffs"] for v in T2["stairs"][d[0]]])

duckMults = p.lst("duckMults", T3["flat"])   # 96: base 1-48, egg 49-96
duckPct   = p.lst("duckPct", [str(v) for v in T3["pct"]])
duckX     = p.lst("duckX", [str(v) for v in AV3.LANE_X])
avAutoVals = p.lst("avAutoVals", [f"{v:g}" for v in T4["auto"]])
# aviamasters: per-slot ditch odds in thousandths, and the orbs as
# cumulative weights plus the affine pair (a, b) each one applies
amRamp = p.lst("amRamp", [str(v) for v in T5["ditchRamp"]])
amCum  = p.lst("amCum", [str(v) for v in T5["orbCum"]])
amA    = p.lst("amA", [f"{v:g}" for v in T5["orbA"]])
amB    = p.lst("amB", [f"{v:g}" for v in T5["orbB"]])
amLog  = p.lst("amLog", [])   # orbs taken this round, for the harness
coinMults = p.lst("coinMults", [f"{v:g}" for v in T6["coin"]])
coinRungY = p.lst("coinRungY", [f"{v:g}" for v in AV6.RUNG_Y])
diceWin   = p.lst("diceWin", [str(v) for v in T6["diceWin"]])
diceMult  = p.lst("diceMult", [f"{v:g}" for v in T6["diceMult"]])
# index into this list == the Digit costume number, so a glyph is one lookup
digitChars = p.lst("digitChars",
                   [str(d) for d in range(10)] + [".", ",", "", "x", "M", "B"])

SCREENS = {"lobby": 0, "openSlots": 1, "openPlinko": 2, "openMines": 3,
           "openBJ": 4, "openRoulette": 5, "openStairs": 6,
           "openDuck": 7, "openCrash": 8,
           "openAvia": 9, "openCoin": 10, "openDice": 11}

# convenience reporters
ROWS = lambda: item_of(rowCounts, rowsIdx)
SP   = lambda: item_of(rowSp, rowsIdx)
HS   = lambda: item_of(rowHs, rowsIdx)

# ===================================================== sound
sfxs = p.sprite("Sfx")
C(sfxs, "c", "d13")
for n in SFXMOD.SFX:
    sfxs.add_sound(n, str(SFX_DIR / f"{n}.wav"))
sfxs.visible = False
sfxs.script(when_flag(), hide(), goto(0, 400))
sfxs.script(when_bc(p, "sfx"),
            set_sound_effect("PITCH", sfxPitch),
            play_sound_r(sfxId, SFXMOD.SFX[0]))

SFXN = {n: i + 1 for i, n in enumerate(SFXMOD.SFX)}


def SFX(name, pitch=0):
    return [set_var(sfxPitch, pitch), set_var(sfxId, SFXN[name]),
            broadcast(p, "sfx")]


# ===================================================== stage
st = p.stage
C(st, "bg", "bg")

st.script(
    when_flag(),
    set_var(chips, 1000), set_var(betIdx, 6), set_var(bet, 50),
    set_var(busy, 0), set_var(roundOn, 0), set_var(msgId, 1),
    set_var(win, 0), set_var(mult, 0), set_var(picks, 0),
    set_var(rowsIdx, 2), set_var(riskIdx, 2), set_var(bombsIdx, 2),
    set_var(ballsUp, 0), set_var(hole, 0),
    switch_backdrop("bg"),
    broadcast(p, "lobby"),
)

for name, num in SCREENS.items():
    extra = []
    if num == 2:
        extra = [set_var(ballsUp, 0), broadcast(p, "refreshPlinko")]
    if num == 8:
        extra = [set_var(mult, 1), set_var(avTick, 0), set_var(avCashed, 0),
                 set_var(avLand, 0)]
    if num == 9:
        extra = [set_var(mult, 1), set_var(amSlot, 0), set_var(amVal, 1),
                 set_var(amCashed, 0), set_var(amDown, 0)]
    if num == 10:
        extra = [set_var(mult, 1), set_var(cfSpin, 0), set_var(cfSide, 1)]
    if num == 11:
        extra = [set_var(mult, item_of(diceMult, dcMode)),
                 set_var(dcRolling, 0), set_var(dcShown, 0),
                 set_var(dcInt, 0), set_var(dcTxt, "")]
    st.script(
        when_bc(p, name),
        set_var(screen, num),
        set_var(busy, 0), set_var(roundOn, 0), set_var(msgId, 1),
        set_var(mult, 0), set_var(picks, 0), set_var(hole, 0),
        delete_all(pHand), delete_all(dHand),
        set_var(stRow, 1), set_var(bjPhase, 0), set_var(didSplit, 0),
        set_var(dkLane, 0), set_var(dkEgg, 0), set_var(dkGot, 0),
        set_var(dkHit, 0),
        set_var(cfStreak, 0), set_var(cfCashed, 0), set_var(dcWon, 0),
        delete_all(pHand2),
        extra,
        broadcast(p, "screenChanged"),
    )

st.script(
    when_flag(),
    forever(
        if_else(
            lt(chips, 1000),
            [set_var(chipsTxt, chips)],
            [if_else(
                lt(chips, 1000000),
                # n,nnn - pad the remainder so 1,050 does not render as 1,50
                [set_var(cTmp, mod(chips, 1000)),
                 if_else(lt(cTmp, 10),
                         [set_var(cTmp, join("00", cTmp))],
                         [if_(lt(cTmp, 100), set_var(cTmp, join("0", cTmp)))]),
                 set_var(chipsTxt,
                         join(join(mathop("floor", div(chips, 1000)), ","),
                              cTmp))],
                [if_else(
                    lt(chips, 1000000000),
                    [set_var(chipsTxt,
                             join(div(round_(div(chips, 10000)), 100), "M"))],
                    [set_var(chipsTxt,
                             join(div(round_(div(chips, 10000000)), 100),
                                  "B"))])])]),
    ),
)

st.script(
    when_flag(),
    forever(
        if_(and_(lt(chips, item_of(betLevels, 1)),
                 and_(eq(busy, 0), and_(eq(roundOn, 0), eq(ballsUp, 0)))),
            set_var(msgId, 10), SFX("lose"), wait(1.6),
            set_var(chips, 500), set_var(betIdx, 6),
            set_var(bet, item_of(betLevels, 6)), set_var(msgId, 1)),
        wait(0.2)),
)


def vis(screens, extra=None):
    cond = None
    for s in screens:
        c = eq(screen, s)
        cond = c if cond is None else or_(cond, c)
    return forever(if_else(cond, [show()] + (extra or []), [hide()]))


# ===================================================== digits
dig = p.sprite("Digit")
for n in range(1, 17):
    C(dig, f"d{n}", f"d{n}")
dig.visible = False
dSlot = dig.local_var("dSlot", 0)
dField = dig.local_var("dField", 0)
dTxt = dig.local_var("dTxt", "")
dLen = dig.local_var("dLen", 0)

dig.script(
    when_flag(), hide(),
    set_var(dField, 1), set_var(dSlot, 0),
    repeat(7, change_var(dSlot, 1), clone()),
    set_var(dField, 2), set_var(dSlot, 0),
    repeat(4, change_var(dSlot, 1), clone()),
    set_var(dField, 3), set_var(dSlot, 0),
    repeat(7, change_var(dSlot, 1), clone()),
    set_var(dField, 4), set_var(dSlot, 0),
    repeat(2, change_var(dSlot, 1), clone()),
    set_var(dField, 5), set_var(dSlot, 0),
    repeat(6, change_var(dSlot, 1), clone()),
    set_var(dField, 6), set_var(dSlot, 0),
    repeat(2, change_var(dSlot, 1), clone()),
    set_var(dField, 7), set_var(dSlot, 0),
    repeat(2, change_var(dSlot, 1), clone()),
    set_var(dField, 8), set_var(dSlot, 0),
    repeat(2, change_var(dSlot, 1), clone()),
    set_var(dField, 9), set_var(dSlot, 0),
    repeat(8, change_var(dSlot, 1), clone()),
    set_var(dField, 0), set_var(dSlot, 0),
)
dig.script(
    when_clone(),
    go_layer("front"),
    if_(eq(dField, 9), set_size(170)),      # the crash readout is the headline
    forever(
        if_(eq(dField, 1), set_var(dTxt, chipsTxt)),
        if_(eq(dField, 2), set_var(dTxt, bet)),
        if_(eq(dField, 3), set_var(dTxt, mult)),
        if_(eq(dField, 4), set_var(dTxt, rNum)),
        if_(eq(dField, 5), set_var(dTxt, rStake)),
        if_(eq(dField, 6), set_var(dTxt, dealer)),
        if_(eq(dField, 7), set_var(dTxt, you)),
        if_(eq(dField, 8), set_var(dTxt, you2)),
        # dice shows the roll it landed on where the others show a
        # multiplier, so field 9 carries whichever the screen is about
        if_(eq(dField, 9),
            if_else(eq(screen, 11), [set_var(dTxt, dcTxt)],
                    [set_var(dTxt, join(mult, "x"))])),
        set_var(dLen, length_of(dTxt)),
        if_else(
            all_of(
                not_(gt(dSlot, dLen)),
                any_of(
                    eq(dField, 1),
                    all_of(eq(dField, 2), gt(screen, 0), eq(roundOn, 0)),
                    all_of(eq(dField, 3),
                           any_of(eq(screen, 3), eq(screen, 6),
                                  eq(screen, 7))),
                    all_of(eq(dField, 4), eq(screen, 5), eq(busy, 1)),
                    all_of(eq(dField, 5), eq(screen, 5)),
                    all_of(any_of(eq(dField, 6), eq(dField, 7)),
                           eq(screen, 4), gt(bjPhase, 0)),
                    all_of(eq(dField, 8), eq(screen, 4), gt(bjPhase, 0),
                           eq(didSplit, 1)),
                    all_of(eq(dField, 9),
                           any_of(eq(screen, 8), eq(screen, 9),
                                  eq(screen, 10), eq(screen, 11))))),
            [if_(eq(dField, 1), goto(add(-166, mul(15, sub(dSlot, 1))), 163)),
             if_(eq(dField, 2),
                 goto(add(-152, mul(14, sub(sub(dSlot, 1),
                                            div(sub(dLen, 1), 2)))), -157)),
             if_(eq(dField, 3),
                 goto(add(86, mul(14, sub(sub(dSlot, 1),
                                          div(sub(dLen, 1), 2)))), 163)),
             if_(eq(dField, 4),
                 goto(mul(16, sub(sub(dSlot, 1), div(sub(dLen, 1), 2))), -86)),
             if_(eq(dField, 5),
                 goto(add(86, mul(14, sub(sub(dSlot, 1),
                                          div(sub(dLen, 1), 2)))), 163)),
             if_(eq(dField, 6),
                 goto(add(-168, mul(16, sub(sub(dSlot, 1),
                                            div(sub(dLen, 1), 2)))), 74)),
             if_(eq(dField, 7),
                 goto(add(-168, mul(16, sub(sub(dSlot, 1),
                                            div(sub(dLen, 1), 2)))), -38)),
             if_(eq(dField, 8),
                 goto(add(-168, mul(16, sub(sub(dSlot, 1),
                                            div(sub(dLen, 1), 2)))), -66)),
             if_(eq(dField, 9),
                 goto(add(AV4.MULT_XY[0],
                          mul(AV4.MULT_GAP, sub(sub(dSlot, 1),
                                                div(sub(dLen, 1), 2)))),
                      AV4.MULT_XY[1])),
             set_var(tmp2, letter_of(dSlot, dTxt)),
             switch_costume_r(item_num_of(digitChars, tmp2), "d1"),
             go_layer("front"), show()],
            [hide()])),
)

mplq = p.sprite("MultPlaque")
C(mplq, "plq", "plq_mult")
mplq.x, mplq.y, mplq.visible = 0, 163, False
mplq.script(when_flag(), goto(0, 163))
mplq.script(when_flag(), vis([3, 6, 7]))

splq = p.sprite("StakePlaque")
C(splq, "plq", "plq_stake")
splq.x, splq.y, splq.visible = 0, 163, False
splq.script(when_flag(), goto(0, 163))
splq.script(when_flag(), vis([5]))

# ===================================================== slots
frame = p.sprite("SlotFrame")
C(frame, "frame", "slotframe")
frame.x, frame.y, frame.visible = -52, 25, False
frame.script(when_flag(), goto(-52, 25))
frame.script(when_flag(), vis([1]))

R = lambda n: item_of(reelResult, n)
slot_pay = if_else(
    and_(eq(R(1), R(2)), eq(R(2), R(3))),
    [if_else(eq(R(1), 1), [set_var(win, mul(bet, 50))],
             [set_var(win, mul(bet, 12))])],
    [if_(or_(or_(eq(R(1), R(2)), eq(R(2), R(3))), eq(R(1), R(3))),
         if_else(or_(or_(and_(eq(R(1), 1), eq(R(2), 1)),
                         and_(eq(R(2), 1), eq(R(3), 1))),
                     and_(eq(R(1), 1), eq(R(3), 1))),
                 [set_var(win, mul(bet, 4))],
                 [set_var(win, round_(mul(bet, 1.8)))]))],
)

frame.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 1), eq(busy, 0)),
        if_else(lt(chips, bet),
                [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                [set_var(busy, 1), set_var(msgId, 1), set_var(win, 0),
                 change_var(chips, mul(bet, -1)),
                 replace_item(reelResult, 1, rand(1, 8)),
                 replace_item(reelResult, 2, rand(1, 8)),
                 replace_item(reelResult, 3, rand(1, 8)),
                 broadcast(p, "spinReels"), wait(1.45),
                 slot_pay, change_var(chips, win),
                 if_else(gt(win, 0),
                         [if_else(gt(win, mul(bet, 9)),
                                  [set_var(msgId, 11), SFX("bigwin")],
                                  [set_var(msgId, 2), SFX("win")])],
                         [set_var(msgId, 3), SFX("lose")]),
                 wait(1.4), set_var(msgId, 1), set_var(busy, 0)])),
)

pt = p.sprite("Paytable")
C(pt, "pt", "paytable")
pt.x, pt.y, pt.visible = 168, 25, False
pt.script(when_flag(), goto(168, 25))
pt.script(when_flag(), vis([1]))

reel = p.sprite("Reel")
for n in range(1, 9):
    C(reel, f"s{n}", f"sym{n}")
reel.visible = False
rIdx = reel.local_var("rIdx", 0)
reel.script(when_flag(), hide(), set_var(rIdx, 0),
            repeat(3, change_var(rIdx, 1), clone()), set_var(rIdx, 0))
reel.script(
    when_clone(),
    goto(add(-148, mul(96, sub(rIdx, 1))), 24),
    go_layer("front"),
    switch_costume_r(rand(1, 8), "s1"),
    vis([1]),
)
reel.script(
    when_bc(p, "spinReels"),
    if_(and_(eq(screen, 1), gt(rIdx, 0)),
        repeat(add(8, mul(6, rIdx)),
               switch_costume_r(rand(1, 8), "s1"), wait(0.03)),
        switch_costume_r(item_of(reelResult, rIdx), "s1"),
        SFX("reel"),
        change_effect("brightness", 45), wait(0.08), clear_effects()),
)

# ===================================================== plinko
board = p.sprite("PlinkoBoard")
for r in ROWC:
    C(board, f"b{r}", f"board{r}")
board.visible = False
board.script(when_flag(), vis([2]))
board.script(
    when_bc(p, "refreshPlinko"),
    switch_costume_r(rowsIdx, "b8"),
    goto(0, add(-92, div(mul(sub(ROWS(), 1), SP()), 2))),
)

bkt = p.sprite("Bucket")
for n in range(1, len(BKV) + 1):
    C(bkt, f"bk{n}", f"bk{n}")
bkt.visible = False
bIdx = bkt.local_var("bIdx", 0)
bSize = bkt.local_var("bSize", 100)
bkt.script(when_flag(), hide(), set_var(bIdx, 0),
           repeat(17, change_var(bIdx, 1), clone()), set_var(bIdx, 0))
bkt.script(
    when_bc(p, "screenChanged"),
    if_(gt(bIdx, 0),
        if_else(and_(eq(screen, 2), not_(gt(bIdx, add(ROWS(), 1)))),
                [show()], [hide()])),
)
bkt.script(
    when_bc(p, "refreshPlinko"),
    if_(gt(bIdx, 0),
        if_else(and_(eq(screen, 2), not_(gt(bIdx, add(ROWS(), 1)))),
                [show()], [hide()]),
        set_var(bSize, round_(mul(div(HS(), 21), 100))),
        set_size(bSize),
        goto(sub(mul(HS(), sub(bIdx, 1)), div(mul(HS(), ROWS()), 2)), -112),
        set_var(tmp2, item_of(plinkoMults,
                              add(mul(add(mul(sub(rowsIdx, 1), 3),
                                          sub(riskIdx, 1)), 17), bIdx))),
        switch_costume_r(item_num_of(bucketVals, tmp2), "bk1"),
        clear_effects()),
)
bkt.script(
    when_bc(p, "bucketHit"),
    if_(gt(bIdx, 0),
        if_else(eq(bIdx, lastBk),
                [go_layer("front"),
                 change_effect("brightness", 50), set_size(mul(bSize, 1.22)),
                 wait(0.14),
                 clear_effects(), set_size(bSize)],
                [clear_effects(), set_size(bSize)])),
)

ball = p.sprite("PlinkoBall")
C(ball, "ball", "ball")
ball.visible = False
myBet  = ball.local_var("myBet", 0)
myRows = ball.local_var("myRows", 0)
mySp   = ball.local_var("mySp", 0)
myHs   = ball.local_var("myHs", 0)
myOff  = ball.local_var("myOff", 0)
myBk   = ball.local_var("myBk", 0)
myWin  = ball.local_var("myWin", 0)
myStep = ball.local_var("myStep", 0)
born   = ball.local_var("born", 0)

ball.script(when_flag(), hide(), set_var(born, 0))
ball.script(
    when_bc(p, "action"),
    if_(and_(and_(eq(born, 0), lt(ballsUp, 25)),
             and_(eq(screen, 2), not_(lt(chips, bet)))),
        change_var(chips, mul(bet, -1)),
        set_var(myBet, bet),
        set_var(myRows, ROWS()), set_var(mySp, SP()), set_var(myHs, HS()),
        set_var(myOff, mul(add(mul(sub(rowsIdx, 1), 3), sub(riskIdx, 1)), 17)),
        change_var(ballsUp, 1),
        SFX("chip"), clone()),
)
ball.script(
    when_clone(),
    set_var(born, 1),
    goto(0, add(-92, add(mul(sub(myRows, 1), mySp), 24))),
    go_layer("front"), show(),
    set_var(myStep, 0),
    repeat(myRows,
           change_y(mul(mySp, -1)),
           if_else(eq(rand(1, 2), 1),
                   [change_x(div(myHs, 2))], [change_x(mul(div(myHs, 2), -1))]),
           change_var(myStep, 1),
           if_(eq(mod(myStep, 3), 0), SFX("peg")),
           wait(0.05)),
    set_var(myBk, add(add(round_(div(xpos(), myHs)), div(myRows, 2)), 1)),
    glide(0.12, xpos(), -112),
    set_var(myWin, round_(mul(myBet, item_of(plinkoMults, add(myOff, myBk))))),
    change_var(chips, myWin),
    set_var(lastBk, myBk), broadcast(p, "bucketHit"),
    if_(gt(myWin, myBet), SFX("gem")),
    wait(0.12), hide(),
    change_var(ballsUp, -1),
    delete_clone(),
)

# ===================================================== mines
tile = p.sprite("MineTile")
for n, f in [("hidden", "tile_hidden"), ("gem", "tile_gem"), ("bomb", "tile_bomb")]:
    C(tile, n, f)
tile.visible = False
tIdx = tile.local_var("tIdx", 0)
tile.script(when_flag(), hide(), set_var(tIdx, 0),
            repeat(25, change_var(tIdx, 1), clone()), set_var(tIdx, 0))
tile.script(
    when_clone(),
    goto(add(-96, mul(48, mod(sub(tIdx, 1), 5))),
         sub(100, mul(48, mathop("floor", div(sub(tIdx, 1), 5))))),
    forever(if_else(eq(screen, 3),
                    [show(), switch_costume_r(item_of(revealed, tIdx), "hidden")],
                    [hide()])),
)
tile.script(
    when_clicked(),
    if_(and_(and_(eq(screen, 3), eq(roundOn, 1)),
             and_(eq(busy, 0), eq(item_of(revealed, tIdx), 1))),
        if_else(list_contains(bombs, tIdx),
                [set_var(busy, 1), replace_item(revealed, tIdx, 3),
                 SFX("bomb"), broadcast(p, "mineBoom")],
                [replace_item(revealed, tIdx, 2),
                 SFX("gem", mul(picks, 10)),
                 change_var(picks, 1),
                 set_var(mult, item_of(mineMults,
                                       add(mul(sub(bombsIdx, 1), 24), picks)))])),
)

cash = p.sprite("CashoutBtn")
C(cash, "cash", "btn_cashout")
cash.x, cash.y, cash.visible = 158, -152, False
cash.script(when_flag(), goto(158, -152))
cash.script(
    when_flag(),
    forever(if_else(
        any_of(and_(and_(eq(screen, 3), eq(roundOn, 1)),
                    and_(eq(busy, 0), gt(picks, 0))),
               and_(and_(eq(screen, 6), eq(roundOn, 1)),
                    and_(eq(busy, 0), gt(stRow, 1))),
               and_(and_(eq(screen, 7), eq(roundOn, 1)),
                    and_(eq(busy, 0), gt(dkLane, 0))),
               and_(and_(eq(screen, 8), eq(roundOn, 1)), eq(busy, 0)),
               and_(and_(eq(screen, 9), eq(roundOn, 1)),
                    and_(eq(busy, 0), gt(amSlot, 0))),
               and_(and_(eq(screen, 10), eq(roundOn, 1)),
                    and_(eq(busy, 0), gt(cfStreak, 0)))),
        [show()], [hide()])),
)

reset_board = Proc(cash, "reset mines", [], warp=True)
define(cash, reset_board,
       delete_all(revealed), repeat(25, add_to(revealed, 1)),
       delete_all(bombs),
       set_var(tmp2, item_of(bombCounts, bombsIdx)),
       repeat_until(eq(len_of(bombs), tmp2),
                    set_var(tmp, rand(1, 25)),
                    if_(not_(list_contains(bombs, tmp)), add_to(bombs, tmp))),
       x=40, y=40)

reveal_bombs = Proc(cash, "reveal bombs", [], warp=True)
define(cash, reveal_bombs,
       set_var(i_, 0),
       repeat(len_of(bombs),
              change_var(i_, 1),
              replace_item(revealed, item_of(bombs, i_), 3)),
       x=40, y=430)

cash.script(
    when_bc(p, "action"),
    if_(and_(and_(eq(screen, 3), eq(roundOn, 0)), eq(busy, 0)),
        if_else(lt(chips, bet),
                [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
                 set_var(picks, 0), set_var(mult, 0),
                 reset_board.call(), set_var(roundOn, 1)])),
)
cash.script(when_clicked(), if_(eq(screen, 6), broadcast(p, "stairCash")))
cash.script(when_clicked(), if_(eq(screen, 7), broadcast(p, "duckCash")))
cash.script(when_clicked(), if_(eq(screen, 8), broadcast(p, "avCash")))
cash.script(when_clicked(), if_(eq(screen, 9), broadcast(p, "amCash")))
cash.script(when_clicked(), if_(eq(screen, 10), broadcast(p, "coinCash")))
cash.script(
    when_clicked(),
    if_(and_(eq(screen, 3), and_(eq(roundOn, 1), gt(picks, 0))),
        set_var(busy, 1),
        set_var(win, round_(mul(bet, mult))), change_var(chips, win),
        set_var(roundOn, 0), reveal_bombs.call(), set_var(msgId, 9),
        SFX("cash"),
        wait(1.6), set_var(msgId, 1), set_var(busy, 0)),
)
cash.script(
    when_bc(p, "mineBoom"),
    set_var(roundOn, 0), wait(0.35), reveal_bombs.call(),
    set_var(msgId, 8), wait(1.6),
    set_var(msgId, 1), set_var(mult, 0), set_var(busy, 0),
)

# ===================================================== blackjack
bjt = p.sprite("BJTable")
C(bjt, "blank", "msg_blank")
bjt.visible = False
bjt.script(when_flag(), hide())

build_deck = Proc(bjt, "build deck", [], warp=True)
define(bjt, build_deck, delete_all(deck), set_var(tmp, 0),
       repeat(52, change_var(tmp, 1), add_to(deck, tmp)), x=40, y=40)

draw_card = Proc(bjt, "draw card", [], warp=True)
define(bjt, draw_card,
       set_var(tmp, rand(1, len_of(deck))),
       set_var(drawn, item_of(deck, tmp)), delete_of(deck, tmp), x=40, y=300)


def score_body(hand, out):
    return [set_var(sc, 0), set_var(aces, 0), set_var(i_, 0),
            repeat(len_of(hand),
                   change_var(i_, 1),
                   set_var(tmp, add(mod(sub(item_of(hand, i_), 1), 13), 1)),
                   if_(gt(tmp, 10), set_var(tmp, 10)),
                   if_(eq(tmp, 1), change_var(aces, 1), set_var(tmp, 11)),
                   change_var(sc, tmp)),
            repeat_until(or_(not_(gt(sc, 21)), eq(aces, 0)),
                         change_var(sc, -10), change_var(aces, -1)),
            set_var(out, sc)]


score_p = Proc(bjt, "score player", [], warp=True)
define(bjt, score_p, *score_body(pHand, you), x=40, y=560)
score_p2 = Proc(bjt, "score split", [], warp=True)
define(bjt, score_p2, *score_body(pHand2, you2), x=460, y=560)
score_d = Proc(bjt, "score dealer", [], warp=True)
define(bjt, score_d, *score_body(dHand, dealer), x=880, y=560)

# draw to whichever hand is active
draw_active = Proc(bjt, "draw to active", [], warp=True)
define(bjt, draw_active,
       draw_card.call(),
       if_else(eq(activeH, 1), [add_to(pHand, drawn)], [add_to(pHand2, drawn)]),
       score_p.call(), score_p2.call(), x=880, y=40)

# refresh which optional actions are legal
refresh_opts = Proc(bjt, "refresh options", [], warp=True)
define(bjt, refresh_opts,
       set_var(canDbl, 0), set_var(canSpl, 0),
       if_else(eq(activeH, 1),
               [set_var(bjA, len_of(pHand)), set_var(bjB, bjBet1)],
               [set_var(bjA, len_of(pHand2)), set_var(bjB, bjBet2)]),
       if_(and_(eq(bjA, 2), not_(lt(chips, bjB))), set_var(canDbl, 1)),
       if_(and_(and_(eq(didSplit, 0), eq(len_of(pHand), 2)),
                not_(lt(chips, bjBet1))),
           set_var(tmp, add(mod(sub(item_of(pHand, 1), 1), 13), 1)),
           if_(gt(tmp, 10), set_var(tmp, 10)),
           set_var(tmp2, add(mod(sub(item_of(pHand, 2), 1), 13), 1)),
           if_(gt(tmp2, 10), set_var(tmp2, 10)),
           if_(eq(tmp, tmp2), set_var(canSpl, 1))),
       x=1300, y=40)

settle = Proc(bjt, "settle", [], warp=True)
define(bjt, settle,
       set_var(win, 0),
       if_(not_(gt(you, 21)),
           if_else(or_(gt(dealer, 21), gt(you, dealer)),
                   [change_var(win, mul(bjBet1, 2))],
                   [if_(eq(you, dealer), change_var(win, bjBet1))])),
       if_(eq(didSplit, 1),
           if_(not_(gt(you2, 21)),
               if_else(or_(gt(dealer, 21), gt(you2, dealer)),
                       [change_var(win, mul(bjBet2, 2))],
                       [if_(eq(you2, dealer), change_var(win, bjBet2))]))),
       change_var(chips, win),
       set_var(tmp2, add(bjBet1, bjBet2)),
       if_else(gt(win, tmp2), [set_var(msgId, 2)],
               [if_else(eq(win, tmp2), [set_var(msgId, 5)],
                        [if_else(and_(gt(you, 21),
                                      or_(eq(didSplit, 0), gt(you2, 21))),
                                 [set_var(msgId, 4)], [set_var(msgId, 7)])])]),
       x=1300, y=400)

# ---------------- deal
bjt.script(
    when_bc(p, "action"),
    if_(and_(and_(eq(screen, 4), eq(bjPhase, 0)), eq(busy, 0)),
        if_else(lt(chips, bet),
                [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                [set_var(busy, 1), set_var(msgId, 1), set_var(roundOn, 1),
                 change_var(chips, mul(bet, -1)),
                 set_var(bjBet1, bet), set_var(bjBet2, 0), set_var(insBet, 0),
                 set_var(didSplit, 0), set_var(activeH, 1),
                 set_var(you, 0), set_var(you2, 0), set_var(dealer, 0),
                 build_deck.call(),
                 delete_all(pHand), delete_all(pHand2), delete_all(dHand),
                 set_var(hole, 1),
                 draw_card.call(), add_to(pHand, drawn), score_p.call(),
                 SFX("card"), wait(0.3),
                 draw_card.call(), add_to(dHand, drawn), score_d.call(),
                 SFX("card"), wait(0.3),
                 draw_card.call(), add_to(pHand, drawn), score_p.call(),
                 SFX("card"), wait(0.3),
                 draw_card.call(), set_var(holeCard, drawn),
                 SFX("card"), wait(0.35),
                 # up-card rank / value
                 set_var(bjA, add(mod(sub(item_of(dHand, 1), 1), 13), 1)),
                 set_var(bjB, bjA), if_(gt(bjB, 10), set_var(bjB, 10)),
                 # insurance when the dealer shows an ace
                 if_(and_(eq(bjA, 1), not_(lt(chips, round_(div(bet, 2))))),
                     set_var(bjPhase, 1), set_var(busy, 0),
                     wait_until(not_(eq(bjPhase, 1))),
                     set_var(busy, 1)),
                 # dealer peek
                 set_var(tmp, add(mod(sub(holeCard, 1), 13), 1)),
                 if_(or_(and_(eq(bjA, 1), gt(tmp, 9)),
                         and_(and_(eq(bjB, 10), not_(eq(bjA, 1))), eq(tmp, 1))),
                     add_to(dHand, holeCard), set_var(hole, 0), score_d.call(),
                     SFX("card"), wait(0.7),
                     if_(gt(insBet, 0), change_var(chips, mul(insBet, 3))),
                     if_else(and_(eq(len_of(pHand), 2), eq(you, 21)),
                             [change_var(chips, bjBet1), set_var(msgId, 5),
                              SFX("click")],
                             [set_var(msgId, 7), SFX("lose")]),
                     set_var(bjPhase, 0), set_var(roundOn, 0),
                     wait(1.9), set_var(msgId, 1), set_var(busy, 0),
                     stop("this script")),
                 # player natural
                 if_(eq(you, 21),
                     add_to(dHand, holeCard), set_var(hole, 0), score_d.call(),
                     wait(0.6),
                     set_var(win, round_(mul(bjBet1, 2.5))),
                     change_var(chips, win), set_var(msgId, 6), SFX("bigwin"),
                     set_var(bjPhase, 0), set_var(roundOn, 0),
                     wait(1.9), set_var(msgId, 1), set_var(busy, 0),
                     stop("this script")),
                 refresh_opts.call(),
                 set_var(bjPhase, 2), set_var(busy, 0)])),
)

# ---------------- insurance answer
bjt.script(
    when_bc(p, "bjInsure"),
    if_(eq(bjPhase, 1),
        set_var(insBet, round_(div(bjBet1, 2))),
        change_var(chips, mul(insBet, -1)),
        SFX("chip"), set_var(bjPhase, 9)),
)
bjt.script(
    when_bc(p, "bjNoIns"),
    if_(eq(bjPhase, 1), set_var(insBet, 0), SFX("click"), set_var(bjPhase, 9)),
)

# ---------------- hit
bjt.script(
    when_bc(p, "bjHit"),
    if_(and_(and_(eq(screen, 4), eq(bjPhase, 2)), eq(busy, 0)),
        set_var(busy, 1),
        draw_active.call(), SFX("card"), wait(0.4),
        set_var(bjA, you), if_(eq(activeH, 2), set_var(bjA, you2)),
        if_else(not_(lt(bjA, 21)),
                [broadcast(p, "bjAdvance")],
                [refresh_opts.call(), set_var(canDbl, 0), set_var(canSpl, 0),
                 set_var(busy, 0)])),
)

# ---------------- stand
bjt.script(
    when_bc(p, "bjStand"),
    if_(and_(and_(eq(screen, 4), eq(bjPhase, 2)), eq(busy, 0)),
        set_var(busy, 1), SFX("click"), broadcast(p, "bjAdvance")),
)

# ---------------- double
bjt.script(
    when_bc(p, "bjDouble"),
    if_(and_(and_(eq(screen, 4), eq(bjPhase, 2)),
             and_(eq(busy, 0), eq(canDbl, 1))),
        set_var(busy, 1),
        if_else(eq(activeH, 1),
                [change_var(chips, mul(bjBet1, -1)),
                 set_var(bjBet1, mul(bjBet1, 2))],
                [change_var(chips, mul(bjBet2, -1)),
                 set_var(bjBet2, mul(bjBet2, 2))]),
        SFX("chip"),
        draw_active.call(), SFX("card"), wait(0.6),
        broadcast(p, "bjAdvance")),
)

# ---------------- split
bjt.script(
    when_bc(p, "bjSplit"),
    if_(and_(and_(eq(screen, 4), eq(bjPhase, 2)),
             and_(eq(busy, 0), and_(eq(canSpl, 1), eq(didSplit, 0)))),
        set_var(busy, 1),
        change_var(chips, mul(bjBet1, -1)),
        set_var(bjBet2, bjBet1), set_var(didSplit, 1),
        delete_all(pHand2),
        add_to(pHand2, item_of(pHand, 2)), delete_of(pHand, 2),
        SFX("chip"), wait(0.3),
        set_var(activeH, 1), draw_active.call(), SFX("card"), wait(0.35),
        set_var(activeH, 2), draw_active.call(), SFX("card"), wait(0.45),
        set_var(activeH, 1),
        set_var(tmp, add(mod(sub(item_of(pHand, 1), 1), 13), 1)),
        if_else(eq(tmp, 1),
                [broadcast(p, "bjAdvance")],
                [refresh_opts.call(), set_var(canSpl, 0), set_var(busy, 0)])),
)

# ---------------- advance / dealer
bjt.script(
    when_bc(p, "bjAdvance"),
    if_else(and_(eq(didSplit, 1), eq(activeH, 1)),
            [set_var(activeH, 2), refresh_opts.call(), set_var(canSpl, 0),
             set_var(busy, 0)],
            [set_var(bjPhase, 3), broadcast(p, "bjDealer")]),
)
bjt.script(
    when_bc(p, "bjDealer"),
    set_var(busy, 1), set_var(canDbl, 0), set_var(canSpl, 0),
    add_to(dHand, holeCard), set_var(hole, 0), score_d.call(),
    SFX("card"), wait(0.7),
    set_var(bjA, 0),
    if_(not_(gt(you, 21)), set_var(bjA, 1)),
    if_(and_(eq(didSplit, 1), not_(gt(you2, 21))), set_var(bjA, 1)),
    if_(eq(bjA, 1),
        repeat_until(gt(dealer, 16),
                     draw_card.call(), add_to(dHand, drawn), score_d.call(),
                     SFX("card"), wait(0.6))),
    settle.call(),
    if_else(eq(msgId, 2), SFX("win"),
            [if_else(eq(msgId, 5), SFX("click"), SFX("lose"))]),
    set_var(bjPhase, 0), set_var(roundOn, 0),
    wait(2.0), set_var(msgId, 1), set_var(busy, 0),
)

# ---------------- cards (dealer / hand 1 / hand 2)
card = p.sprite("Card")
C(card, "back", "card_back")
for n in range(1, 53):
    C(card, f"c{n}", f"card{n}")
card.visible = False
cSlot = card.local_var("cSlot", 0)
cOwner = card.local_var("cOwner", 0)
cLen = card.local_var("cLen", 0)
cCen = card.local_var("cCen", 0)
cGap = card.local_var("cGap", 0)
card.script(
    when_flag(), hide(),
    set_var(cOwner, 1), set_var(cSlot, 0),
    repeat(6, change_var(cSlot, 1), clone()),
    set_var(cOwner, 2), set_var(cSlot, 0),
    repeat(6, change_var(cSlot, 1), clone()),
    set_var(cOwner, 3), set_var(cSlot, 0),
    repeat(6, change_var(cSlot, 1), clone()),
    set_var(cOwner, 0), set_var(cSlot, 0),
)
card.script(
    when_clone(),
    go_layer("front"),
    forever(
        if_else(
            eq(screen, 4),
            [# geometry per owner
             if_(eq(cOwner, 2),
                 set_var(cLen, add(len_of(dHand), hole)),
                 set_var(cCen, 0), set_var(cGap, 38), set_y(70)),
             if_(eq(cOwner, 1),
                 set_var(cLen, len_of(pHand)), set_y(-42),
                 if_else(eq(didSplit, 1),
                         [set_var(cCen, -45), set_var(cGap, 22)],
                         [set_var(cCen, 0), set_var(cGap, 38)])),
             if_(eq(cOwner, 3),
                 set_var(cLen, len_of(pHand2)), set_y(-42),
                 set_var(cCen, 130), set_var(cGap, 22),
                 if_(eq(didSplit, 0), set_var(cLen, 0))),
             set_x(add(cCen, mul(cGap, sub(sub(cSlot, 1),
                                           div(sub(cLen, 1), 2))))),
             if_else(
                 gt(add(cLen, 1), cSlot),
                 [show(),
                  if_(eq(cOwner, 1),
                      switch_costume_r(add(item_of(pHand, cSlot), 1), "back")),
                  if_(eq(cOwner, 3),
                      switch_costume_r(add(item_of(pHand2, cSlot), 1), "back")),
                  if_(eq(cOwner, 2),
                      if_else(gt(add(len_of(dHand), 1), cSlot),
                              [switch_costume_r(add(item_of(dHand, cSlot), 1),
                                                "back")],
                              [switch_costume("back")])),
                  # dim the hand that is not being played
                  if_else(and_(and_(eq(didSplit, 1), eq(bjPhase, 2)),
                               and_(not_(eq(cOwner, 2)),
                                    not_(eq(cOwner, activeH)))),
                          [set_effect("ghost", 55)],
                          [clear_effects()])],
                 [hide()])],
            [hide()])),
)

# ---------------- action buttons
for nm, f, xx, msg, cond in [
        ("HitBtn", "btn_hit", -150, "bjHit", None),
        ("StandBtn", "btn_stand", -50, "bjStand", None),
        ("DoubleBtn", "btn_double", 50, "bjDouble", "dbl"),
        ("SplitBtn", "btn_split", 150, "bjSplit", "spl")]:
    b = p.sprite(nm)
    C(b, "b", f)
    b.x, b.y, b.visible = xx, -152, False
    base = and_(and_(eq(screen, 4), eq(bjPhase, 2)), eq(busy, 0))
    vis_c = (base if cond is None
             else and_(base, eq(canDbl if cond == "dbl" else canSpl, 1)))
    b.script(when_flag(), goto(xx, -152))
    b.script(when_flag(), forever(if_else(vis_c, [show()], [hide()])))
    b.script(when_clicked(), broadcast(p, msg))

for nm, f, xx, msg in [("InsureBtn", "btn_insure", -60, "bjInsure"),
                       ("NoInsBtn", "btn_noins", 60, "bjNoIns")]:
    b = p.sprite(nm)
    C(b, "b", f)
    b.x, b.y, b.visible = xx, -152, False
    b.script(when_flag(), goto(xx, -152))
    b.script(when_flag(),
             forever(if_else(and_(eq(screen, 4), eq(bjPhase, 1)),
                             [show()], [hide()])))
    b.script(when_clicked(), broadcast(p, msg))

# ---------------- hand overview labels
for nm, f, yy in [("DealerPlq", "plq_dealer", 100), ("YouPlq", "plq_you", -12)]:
    q = p.sprite(nm)
    C(q, "p", f)
    q.x, q.y, q.visible = -168, yy, False
    q.script(when_flag(), goto(-168, yy))
    q.script(when_flag(),
             forever(if_else(and_(eq(screen, 4), gt(bjPhase, 0)),
                             [show()], [hide()])))

# ===================================================== lobby
title = p.sprite("Title")
C(title, "title", "title")
title.x, title.y = 0, 106
title.script(when_flag(), goto(0, 106))
title.script(when_flag(), vis([0]))

menu = p.sprite("MenuTile")
for nm, f in [("slots", "lt_slots"), ("plinko", "lt_plinko"),
              ("mines", "lt_mines"), ("bj", "lt_bj"),
              ("roul", "lt_roulette"), ("stairs", "lt_stairs"),
              ("duck", "lt_duck"), ("crash", "lt_crash"),
              ("avia", "lt_avia"), ("coin", "lt_coin"),
              ("dice", "lt_dice")]:
    C(menu, nm, f)
menu.visible = False
mIdx = menu.local_var("mIdx", 0)
menu.script(when_flag(), hide(), set_var(mIdx, 0),
            repeat(11, change_var(mIdx, 1), clone()), set_var(mIdx, 0))
menu.script(
    when_clone(),
    switch_costume_r(mIdx, "slots"),
    # eleven tiles: six across, five centred beneath. The table felt in the
    # backdrop runs from y 137 down to -125, which is two rows of tiles and
    # no more - a third row would hang off the table and into the bet bar.
    if_else(not_(gt(mIdx, 6)),
            [goto(add(-185, mul(74, sub(mIdx, 1))), 16)],
            [goto(add(-148, mul(74, sub(mIdx, 7))), -62)]),
    forever(if_else(eq(screen, 0),
                    [show(),
                     if_else(touching_mouse(),
                             [set_size(103), set_effect("brightness", 10)],
                             [set_size(100), clear_effects()])],
                    [hide()])),
)
menu.script(
    when_clicked(),
    if_(eq(screen, 0),
        SFX("click"),
        if_(eq(mIdx, 1), broadcast(p, "openSlots")),
        if_(eq(mIdx, 2), broadcast(p, "openPlinko")),
        if_(eq(mIdx, 3), broadcast(p, "openMines")),
        if_(eq(mIdx, 4), broadcast(p, "openBJ")),
        if_(eq(mIdx, 5), broadcast(p, "openRoulette")),
        if_(eq(mIdx, 6), broadcast(p, "openStairs")),
        if_(eq(mIdx, 7), broadcast(p, "openDuck")),
        if_(eq(mIdx, 8), broadcast(p, "openCrash")),
        if_(eq(mIdx, 9), broadcast(p, "openAvia")),
        if_(eq(mIdx, 10), broadcast(p, "openCoin")),
        if_(eq(mIdx, 11), broadcast(p, "openDice"))),
)

# ===================================================== chrome
back = p.sprite("BackBtn")
C(back, "back", "btn_back")
back.x, back.y, back.visible = 192, 163, False
back.script(when_flag(), goto(192, 163))
back.script(when_flag(),
            forever(if_else(and_(gt(screen, 0), eq(busy, 0)),
                            [show()], [hide()])))
back.script(when_clicked(), if_(eq(busy, 0), SFX("click"),
                                broadcast(p, "lobby")))

betp = p.sprite("BetPlaque")
C(betp, "plq", "bet_plaque")
betp.x, betp.y, betp.visible = -152, -152, False
betp.script(when_flag(), goto(-152, -152))
betp.script(when_flag(),
            forever(if_else(and_(gt(screen, 0), eq(roundOn, 0)),
                            [show()], [hide()])))

CANBET = lambda: and_(gt(screen, 0), and_(eq(busy, 0), eq(roundOn, 0)))
HELD = lambda: and_(touching_mouse(), mouse_down())

for nm, f, xx, d in [("BetMinus", "btn_minus", -205, -1),
                     ("BetPlus", "btn_plus", -99, 1)]:
    b = p.sprite(nm)
    C(b, "b", f)
    b.x, b.y, b.visible = xx, -152, False
    b.script(when_flag(), goto(xx, -152))
    b.script(when_flag(),
             forever(if_else(CANBET(), [show()], [hide()])))
    if d > 0:
        step = [if_(and_(lt(betIdx, len_of(betLevels)),
                         not_(gt(item_of(betLevels, add(betIdx, 1)), chips))),
                    change_var(betIdx, 1)),
                set_var(bet, item_of(betLevels, betIdx))]
    else:
        step = [if_(gt(betIdx, 1), change_var(betIdx, -1)),
                set_var(bet, item_of(betLevels, betIdx))]
    b.script(
        when_flag(),
        forever(
            if_(and_(HELD(), CANBET()),
                step, SFX("click"), wait(0.32), set_var(rep, 0),
                repeat_until(not_(and_(HELD(), CANBET())),
                             step, change_var(rep, 1),
                             if_else(gt(rep, 6), [wait(0.045)], [wait(0.11)]))),
            wait(0.02)),
    )

# selectors
for nm, file_pfx, count, var, xx, scr, guard in [
        ("RowsSel", "sel_rows", 3, rowsIdx, -40, 2, "plinko"),
        ("RiskSel", "sel_risk", 3, riskIdx, 24, 2, "plinko"),
        ("BombsSel", "sel_bombs", 4, bombsIdx, -45, 3, "mines"),
        ("DiffSel", "sel_diff", 5, stDiff, -45, 6, "stairs"),
        ("DuckSel", "sel_duck", 4, dkMode, -45, 7, "duck"),
        ("AvSel", "sel_auto", 5, avAuto, -45, 8, "crash"),
        ("AviaSel", "sel_auto", 5, amAuto, -45, 9, "avia"),
        ("CallSel", "sel_call", 2, cfCall, -45, 10, "coin"),
        ("ChanceSel", "sel_chance", 5, dcMode, -45, 11, "dice"),
        ("SideSel", "sel_side", 2, dcSide, 158, 11, "dice")]:
    s = p.sprite(nm)
    for n in range(1, count + 1):
        C(s, f"c{n}", f"{file_pfx}{n}")
    s.x, s.y, s.visible = xx, -152, False
    ok = (and_(eq(screen, scr), eq(ballsUp, 0)) if guard == "plinko"
          else and_(eq(screen, scr), eq(roundOn, 0)))
    s.script(when_flag(), goto(xx, -152))
    s.script(when_flag(),
             forever(switch_costume_r(var, "c1"),
                     if_else(ok, [show()], [hide()])))
    s.script(
        when_clicked(),
        if_(ok,
            SFX("click"),
            change_var(var, 1),
            if_(gt(var, count), set_var(var, 1)),
            {"plinko": lambda: broadcast(p, "refreshPlinko"),
             "stairs": lambda: broadcast(p, "stairRefresh"),
             "duck": lambda: broadcast(p, "duckRefresh"),
             "dice": lambda: set_var(mult, item_of(diceMult, dcMode)),
             }.get(guard, lambda: None)()),
    )

act = p.sprite("ActionBtn")
for nm, f in [("spin", "btn_spin"), ("drop", "btn_drop"),
              ("start", "btn_start"), ("deal", "btn_deal"),
              ("go", "btn_go"), ("fly", "btn_launch"),
              ("takeoff", "btn_takeoff"), ("flip", "btn_flip"),
              ("roll", "btn_roll")]:
    C(act, nm, f)
act.visible = False
act.script(
    when_flag(),
    forever(
        if_else(or_(eq(screen, 0), eq(busy, 1)), [hide()],
                [if_(eq(screen, 1), goto(75, -152), switch_costume("spin"), show()),
                 if_(eq(screen, 2), goto(110, -152), switch_costume("drop"), show()),
                 if_(eq(screen, 3), goto(52, -152), switch_costume("start"),
                     if_else(eq(roundOn, 0), [show()], [hide()])),
                 if_(eq(screen, 4), goto(75, -152), switch_costume("deal"),
                     if_else(eq(bjPhase, 0), [show()], [hide()])),
                 if_(eq(screen, 5), goto(110, -152), switch_costume("spin"),
                     show()),
                 if_(eq(screen, 6), goto(52, -152), switch_costume("start"),
                     if_else(eq(roundOn, 0), [show()], [hide()])),
                 # duck road: GO both starts the run and takes the next lane
                 if_(eq(screen, 7), goto(52, -152), switch_costume("go"),
                     show()),
                 # aviamasters: FLY launches, then CASH OUT is the only control
                 if_(eq(screen, 8), goto(52, -152), switch_costume("fly"),
                     if_else(eq(roundOn, 0), [show()], [hide()])),
                 if_(eq(screen, 9), goto(52, -152), switch_costume("takeoff"),
                     if_else(eq(roundOn, 0), [show()], [hide()])),
                 # coin flip: FLIP both starts the run and takes the next rung
                 if_(eq(screen, 10), goto(52, -152), switch_costume("flip"),
                     show()),
                 if_(eq(screen, 11), goto(52, -152), switch_costume("roll"),
                     if_else(eq(roundOn, 0), [show()], [hide()]))])),
)
act.script(when_clicked(), if_(eq(busy, 0), SFX("click"),
                               broadcast(p, "action")))

msg = p.sprite("Msg")
for nm, _t, _c in AV.MESSAGES:
    C(msg, nm, nm)
msg.x, msg.y, msg.visible = 0, -104, False
msg.script(when_flag(), goto(0, -104), set_var(msgId, 1))
msg.script(when_flag(),
           forever(switch_costume_r(msgId, "msg_blank"),
                   if_else(gt(msgId, 1), [go_layer("front"), show()],
                           [hide()])))


# ===================================================== ROULETTE
spot = p.sprite("RSpot")
for n in range(1, 50):
    C(spot, f"s{n}", f"rs{n}")
spot.visible = False
sIdx = spot.local_var("sIdx", 0)
spot.script(when_flag(), hide(), set_var(sIdx, 0),
            repeat(49, change_var(sIdx, 1), clone()), set_var(sIdx, 0))
spot.script(
    when_clone(),
    switch_costume_r(sIdx, "s1"),
    goto(item_of(spotX, sIdx), item_of(spotY, sIdx)),
    hide(),
)
spot.script(
    when_bc(p, "screenChanged"),
    if_(gt(sIdx, 0),
        clear_effects(),
        if_else(eq(screen, 5), [show()], [hide()])),
)
spot.script(
    when_bc(p, "rHighlight"),
    if_(gt(sIdx, 0),
        if_else(eq(sIdx, add(rNum, 1)),
                [go_layer("front"), change_effect("brightness", 55),
                 repeat(6, change_effect("ghost", 25), wait(0.06),
                        change_effect("ghost", -25), wait(0.06))],
                [clear_effects()])),
)
spot.script(
    when_clicked(),
    if_(and_(and_(eq(screen, 5), eq(busy, 0)), not_(lt(chips, bet))),
        change_var(chips, mul(bet, -1)),
        if_(eq(item_of(rBets, sIdx), 0),
            set_var(newChip, sIdx), clone("RChip")),
        replace_item(rBets, sIdx, add(item_of(rBets, sIdx), bet)),
        change_var(rStake, bet),
        add_to(rHistI, sIdx), add_to(rHistA, bet),
        SFX("chip"), broadcast(p, "rChips")),
)

rchip = p.sprite("RChip")
for n in range(1, 6):
    C(rchip, f"c{n}", f"chip{n}")
rchip.visible = False
cIdx = rchip.local_var("cIdx", 0)
rchip.script(when_flag(), hide(), set_var(cIdx, 0))
rchip.script(
    when_clone(),
    set_var(cIdx, newChip),
    goto(item_of(spotX, cIdx), item_of(spotY, cIdx)),
    go_layer("front"), show(),
)
rchip.script(
    when_bc(p, "rChips"),
    if_(gt(cIdx, 0),
        if_else(eq(item_of(rBets, cIdx), 0),
                [delete_clone()],
                [set_var(tmp2, item_of(rBets, cIdx)),
                 if_else(lt(tmp2, 25), [switch_costume("c1")],
                   [if_else(lt(tmp2, 100), [switch_costume("c2")],
                     [if_else(lt(tmp2, 500), [switch_costume("c3")],
                       [if_else(lt(tmp2, 2000), [switch_costume("c4")],
                                [switch_costume("c5")])])])]),
                 show()])),
)
rchip.script(
    when_bc(p, "screenChanged"),
    if_(and_(gt(cIdx, 0), not_(eq(screen, 5))), delete_clone()),
)

wpanel = p.sprite("WheelPanel")
C(wpanel, "p", "wheelpanel")
wpanel.x, wpanel.y, wpanel.visible = 0, 14, False
wpanel.script(when_flag(), goto(0, 14), hide())
wpanel.script(when_bc(p, "rSpin"), go_layer("front"), show())
wpanel.script(when_bc(p, "rSpinEnd"), hide())
wpanel.script(when_bc(p, "screenChanged"), hide())

wptr = p.sprite("Pointer")
C(wptr, "p", "pointer")
wptr.x, wptr.y, wptr.visible = 0, 133, False
wptr.script(when_flag(), goto(0, 133), hide())
wptr.script(when_bc(p, "rSpin"), show(),
            # re-front for the length of the spin, so the popup
            # cannot land on top of it (same race as the wheel)
            repeat(56, go_layer("front"), wait(0.02)))
wptr.script(when_bc(p, "rSpinEnd"), hide())
wptr.script(when_bc(p, "screenChanged"), hide())

wheel = p.sprite("Wheel")
C(wheel, "w", "wheel")
wheel.x, wheel.y, wheel.visible = 0, 28, False
wTgt = wheel.local_var("wTgt", 0)
wStp = wheel.local_var("wStp", 0)
wU = wheel.local_var("wU", 0)
wheel.script(when_flag(), goto(0, 28), hide(),
             point_dir(90))
wheel.script(when_bc(p, "screenChanged"), hide())
wheel.script(when_bc(p, "rSpinEnd"), hide())
wheel.script(
    when_bc(p, "rSpin"),
    goto(0, 28), go_layer("front"), show(),
    set_var(wTgt, add(mul(sub(item_num_of(wheelOrd, rNum), 1),
                          div(360, 37)), 1440)),
    set_var(wStp, 0),
    repeat(52,
           change_var(wStp, 1),
           set_var(wU, sub(1, div(wStp, 52))),
           if_(eq(mod(wStp, 6), 0), SFX("tick")),
           go_layer("front"),
           point_dir(sub(90, mul(wTgt, sub(1, mul(wU, mul(wU, wU))))))),
    point_dir(sub(90, mul(sub(item_num_of(wheelOrd, rNum), 1), div(360, 37)))),
    go_layer("front"),
)

rctl = p.sprite("RouletteCtrl")
C(rctl, "blank", "msg_blank")
rctl.visible = False
rctl.script(when_flag(), hide())

clear_bets = Proc(rctl, "clear bets", [], warp=True)
define(rctl, clear_bets,
       delete_all(rBets), repeat(49, add_to(rBets, 0)),
       delete_all(rHistI), delete_all(rHistA),
       set_var(rStake, 0), x=40, y=40)

pay_out = Proc(rctl, "resolve", [], warp=True)
define(rctl, pay_out,
       set_var(win, mul(item_of(rBets, add(rNum, 1)), 36)),
       if_(gt(rNum, 0),
           if_else(list_contains(redNums, rNum),
                   [change_var(win, mul(item_of(rBets, 38), 2))],
                   [change_var(win, mul(item_of(rBets, 39), 2))]),
           if_else(eq(mod(rNum, 2), 1),
                   [change_var(win, mul(item_of(rBets, 40), 2))],
                   [change_var(win, mul(item_of(rBets, 41), 2))]),
           if_else(lt(rNum, 19),
                   [change_var(win, mul(item_of(rBets, 42), 2))],
                   [change_var(win, mul(item_of(rBets, 43), 2))]),
           set_var(tmp2, add(mathop("floor", div(sub(rNum, 1), 12)), 1)),
           change_var(win, mul(item_of(rBets, add(43, tmp2)), 3)),
           set_var(tmp2, add(mod(sub(rNum, 1), 3), 1)),
           change_var(win, mul(item_of(rBets, add(46, tmp2)), 3))),
       x=40, y=300)

rctl.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 5), eq(busy, 0)),
        if_else(eq(rStake, 0),
                [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                [set_var(busy, 1), set_var(msgId, 1),
                 set_var(rNum, sub(rand(1, 37), 1)),
                 broadcast(p, "rSpin"),
                 wait(2.9),
                 pay_out.call(),
                 change_var(chips, win),
                 wait(0.8),
                 broadcast(p, "rSpinEnd"),
                 broadcast(p, "rHighlight"),
                 if_else(gt(win, 0),
                         [if_else(gt(win, mul(rStake, 3)),
                                  [set_var(msgId, 11), SFX("bigwin")],
                                  [set_var(msgId, 2), SFX("win")])],
                         [set_var(msgId, 3), SFX("lose")]),
                 wait(1.8),
                 clear_bets.call(), broadcast(p, "rChips"),
                 set_var(msgId, 1), set_var(busy, 0)])),
)
rctl.script(when_bc(p, "lobby"), clear_bets.call(), broadcast(p, "rChips"))

clr = p.sprite("ClearBtn")
C(clr, "b", "btn_clear")
clr.x, clr.y, clr.visible = -40, -152, False
clr.script(when_flag(), goto(-40, -152))
clr.script(when_flag(),
           forever(if_else(and_(eq(screen, 5), and_(eq(busy, 0), gt(rStake, 0))),
                           [show()], [hide()])))
clr.script(
    when_clicked(),
    if_(and_(eq(screen, 5), eq(busy, 0)),
        change_var(chips, rStake),
        clear_bets.call() if False else None,
        broadcast(p, "rClear")),
)
rctl.script(when_bc(p, "rClear"), clear_bets.call(), broadcast(p, "rChips"))

und = p.sprite("UndoBtn")
C(und, "b", "btn_undo")
und.x, und.y, und.visible = 24, -152, False
und.script(when_flag(), goto(24, -152))
und.script(when_flag(),
           forever(if_else(and_(eq(screen, 5), and_(eq(busy, 0), gt(rStake, 0))),
                           [show()], [hide()])))
und.script(
    when_clicked(),
    if_(and_(and_(eq(screen, 5), eq(busy, 0)), gt(len_of(rHistI), 0)),
        set_var(tmp, item_of(rHistI, len_of(rHistI))),
        set_var(tmp2, item_of(rHistA, len_of(rHistA))),
        replace_item(rBets, tmp, sub(item_of(rBets, tmp), tmp2)),
        change_var(rStake, mul(tmp2, -1)),
        change_var(chips, tmp2),
        delete_of(rHistI, len_of(rHistI)),
        delete_of(rHistA, len_of(rHistA)),
        broadcast(p, "rChips")),
)

# ===================================================== STAIRS
stile = p.sprite("StairTile")
for n, f in [("hidden", "st_hidden"), ("safe", "st_safe"),
             ("bomb", "st_bomb"), ("pick", "st_pick")]:
    C(stile, n, f)
stile.visible = False
stR = stile.local_var("stR", 0)
stC = stile.local_var("stC", 0)
stile.script(
    when_flag(), hide(), set_var(stR, 0), set_var(stC, 0),
    repeat(9,
           change_var(stR, 1), set_var(stC, 0),
           repeat(4, change_var(stC, 1), clone())),
    set_var(stR, 0), set_var(stC, 0),
)
stile.script(
    when_clone(),
    set_y(add(-98, mul(26, sub(stR, 1)))),
    hide(),
)
stile.script(
    when_bc(p, "stairRefresh"),
    if_(gt(stR, 0),
        set_var(tmp2, item_of(diffTiles, stDiff)),
        if_else(and_(eq(screen, 6), not_(gt(stC, tmp2))),
                [set_x(add(-35, mul(50, sub(sub(stC, 1), div(sub(tmp2, 1), 2))))),
                 switch_costume_r(add(item_of(stState,
                                              add(mul(sub(stR, 1), 4), stC)), 1),
                                  "hidden"),
                 if_else(and_(eq(roundOn, 1), eq(stR, stRow)),
                         [set_size(104), set_effect("brightness", 18)],
                         [set_size(100), clear_effects()]),
                 show()],
                [hide()])),
)
stile.script(when_bc(p, "screenChanged"), broadcast(p, "stairRefresh"))
stile.script(
    when_clicked(),
    if_(and_(and_(eq(screen, 6), eq(roundOn, 1)),
             and_(eq(busy, 0),
                  and_(eq(stR, stRow),
                       not_(gt(stC, item_of(diffTiles, stDiff)))))),
        set_var(stClick, add(mul(sub(stR, 1), 4), stC)),
        broadcast(p, "stairPick")),
)

smul = p.sprite("StairMult")
for n in range(1, 46):
    C(smul, f"m{n}", f"sm{n}")
smul.visible = False
mRow = smul.local_var("mRow", 0)
smul.script(when_flag(), hide(), set_var(mRow, 0),
            repeat(9, change_var(mRow, 1), clone()), set_var(mRow, 0))
smul.script(when_clone(), goto(125, add(-98, mul(26, sub(mRow, 1)))), hide())
smul.script(
    when_bc(p, "stairRefresh"),
    if_(gt(mRow, 0),
        if_else(eq(screen, 6),
                [switch_costume_r(add(mul(sub(stDiff, 1), 9), mRow), "m1"),
                 if_else(and_(eq(roundOn, 1), eq(mRow, stRow)),
                         [clear_effects()], [set_effect("ghost", 55)]),
                 show()],
                [hide()])),
)

sctl = p.sprite("StairsCtrl")
C(sctl, "blank", "msg_blank")
sctl.visible = False
sctl.script(when_flag(), hide())

reset_stairs = Proc(sctl, "reset stairs", [], warp=True)
define(sctl, reset_stairs,
       delete_all(stState), repeat(36, add_to(stState, 0)),
       delete_all(stBomb), repeat(36, add_to(stBomb, 0)),
       set_var(i_, 0),
       repeat(9,
              change_var(i_, 1),
              set_var(sc, 0),
              repeat_until(eq(sc, item_of(diffBombs, stDiff)),
                           set_var(tmp, rand(1, item_of(diffTiles, stDiff))),
                           if_(eq(item_of(stBomb,
                                          add(mul(sub(i_, 1), 4), tmp)), 0),
                               replace_item(stBomb,
                                            add(mul(sub(i_, 1), 4), tmp), 1),
                               change_var(sc, 1)))),
       x=40, y=40)

reveal_row = Proc(sctl, "reveal row", [], warp=True)
define(sctl, reveal_row,
       set_var(aces, 0),
       repeat(4,
              change_var(aces, 1),
              set_var(tmp, add(mul(sub(stRow, 1), 4), aces)),
              if_(eq(item_of(stState, tmp), 0),
                  if_else(eq(item_of(stBomb, tmp), 1),
                          [replace_item(stState, tmp, 2)],
                          [replace_item(stState, tmp, 1)]))),
       x=40, y=340)

sctl.script(
    when_bc(p, "action"),
    if_(and_(and_(eq(screen, 6), eq(roundOn, 0)), eq(busy, 0)),
        if_else(lt(chips, bet),
                [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
                 set_var(stRow, 1), set_var(mult, 0),
                 reset_stairs.call(), set_var(roundOn, 1),
                 broadcast(p, "stairRefresh")])),
)
sctl.script(
    when_bc(p, "stairPick"),
    if_(and_(eq(screen, 6), and_(eq(roundOn, 1), eq(busy, 0))),
        if_else(eq(item_of(stBomb, stClick), 1),
                [set_var(busy, 1), SFX("bomb"),
                 replace_item(stState, stClick, 2),
                 reveal_row.call(), set_var(roundOn, 0),
                 broadcast(p, "stairRefresh"),
                 wait(0.35), set_var(msgId, 8),
                 wait(1.6), set_var(msgId, 1), set_var(mult, 0),
                 set_var(busy, 0), broadcast(p, "stairRefresh")],
                [replace_item(stState, stClick, 3),
                 SFX("gem", mul(sub(stRow, 1), 15)),
                 reveal_row.call(),
                 change_var(stRow, 1),
                 set_var(mult, item_of(stairMults,
                                       add(mul(sub(stDiff, 1), 9),
                                           sub(stRow, 1)))),
                 broadcast(p, "stairRefresh"),
                 if_(gt(stRow, 9),
                     set_var(busy, 1),
                     set_var(win, round_(mul(bet, mult))),
                     change_var(chips, win),
                     set_var(roundOn, 0), set_var(msgId, 11), SFX("bigwin"),
                     wait(2), set_var(msgId, 1), set_var(busy, 0),
                     broadcast(p, "stairRefresh"))])),
)
sctl.script(
    when_bc(p, "stairCash"),
    if_(and_(eq(screen, 6), and_(eq(roundOn, 1), gt(stRow, 1))),
        set_var(busy, 1),
        set_var(win, round_(mul(bet, mult))), change_var(chips, win),
        set_var(roundOn, 0), set_var(msgId, 9), SFX("cash"),
        broadcast(p, "stairRefresh"),
        wait(1.6), set_var(msgId, 1), set_var(busy, 0),
        broadcast(p, "stairRefresh")),
)


# ===================================================== DUCK ROAD
# The duck crosses one lane at a time. Every hop is decided by a single roll
# against duckPct before anything animates; the traffic is presentation, so
# payout correctness never depends on timing and holds on the fast build.
LANEX, KERBX = AV3.LANE_X, AV3.KERB_X
DUCKY, LABELY = AV3.DUCK_Y, AV3.LABEL_Y
CARTOP, CARBOT = 88, -88        # inside the road, clear of the labels

road = p.sprite("RoadPanel")
C(road, "road", "duckroad")
road.x, road.y, road.visible = 0, 0, False
road.script(when_flag(), goto(0, 0), go_layer("back"))
road.script(when_flag(), vis([7], [go_layer("back")]))

# --- multiplier ladder, one label above each lane
dmul = p.sprite("DuckMult")
for n in range(1, 97):
    C(dmul, f"m{n}", f"dm{n}")
dmul.visible = False
dLane = dmul.local_var("dLane", 0)
dmul.script(when_flag(), hide(), set_var(dLane, 0),
            repeat(12, change_var(dLane, 1), clone()), set_var(dLane, 0))
dmul.script(when_clone(), goto(item_of(duckX, dLane), LABELY), hide())
dmul.script(
    when_bc(p, "duckRefresh"),
    if_(gt(dLane, 0),
        if_else(eq(screen, 7),
                [switch_costume_r(add(add(mul(sub(dkMode, 1), 12), dLane),
                                      mul(dkGot, 48)), "m1"),
                 if_else(and_(eq(roundOn, 1), eq(dLane, dkLane)),
                         [clear_effects()], [set_effect("ghost", 55)]),
                 show()],
                [hide()])),
)

# --- the duck
duck = p.sprite("Duck")
for n in range(1, 5):
    C(duck, f"d{n}", f"duck{n}")
duck.x, duck.y, duck.visible = KERBX, DUCKY, False
duck.script(when_flag(), goto(KERBX, DUCKY), switch_costume("d1"))
duck.script(when_flag(), vis([7]))
duck.script(
    when_bc(p, "duckRefresh"),
    if_(eq(screen, 7),
        switch_costume("d1"), go_layer("front"),
        if_else(gt(dkLane, 0),
                [goto(item_of(duckX, dkLane), DUCKY)],
                [goto(KERBX, DUCKY)])),
)
duck.script(
    when_bc(p, "duckHop"),
    if_(eq(screen, 7),
        go_layer("front"), switch_costume("d2"),
        gl(0.26, item_of(duckX, dkTgt), add(DUCKY, 9)),
        goto(item_of(duckX, dkTgt), DUCKY), switch_costume("d1")),
)
duck.script(when_bc(p, "duckDie"), if_(eq(screen, 7), switch_costume("d3")))
duck.script(when_bc(p, "duckWin"), if_(eq(screen, 7), switch_costume("d4")))

# --- the golden egg, carried once found
degg = p.sprite("DuckEgg")
C(degg, "egg", "degg")
degg.visible = False
degg.script(when_flag(), hide())
degg.script(
    when_bc(p, "duckRefresh"),
    if_else(and_(eq(screen, 7), eq(dkGot, 1)),
            [go_layer("front"),
             if_else(gt(dkLane, 0),
                     [goto(item_of(duckX, dkLane), add(DUCKY, 24))],
                     [goto(KERBX, add(DUCKY, 24))]),
             show()],
            [hide()]),
)

# --- traffic. The original sprite is the car that actually hits the duck;
# the clones are ambient traffic, dimmed and shrunk so the two never read as
# the same thing (PITFALLS 1: clones hear every broadcast, so gate on cIdx).
car = p.sprite("DuckCar")
for n in range(1, 4):
    C(car, f"c{n}", f"dcar{n}")
car.visible = False
cIdx = car.local_var("cIdx", 0)
cLane = car.local_var("cLane", 0)
car.script(when_flag(), hide(), set_var(cIdx, 0),
           repeat(4, change_var(cIdx, 1), clone()), set_var(cIdx, 0))
car.script(
    when_clone(),
    hide(), set_size(84), set_effect("ghost", 42),
    forever(
        if_else(eq(screen, 7),
                [set_var(cLane, rand(1, 12)),
                 # never drive through the lane the duck is standing in or
                 # hopping into - the strike car owns that moment
                 if_(not_(or_(eq(cLane, dkLane),
                              and_(eq(roundOn, 1), eq(cLane, dkTgt)))),
                     switch_costume_r(rand(1, 3), "c1"),
                     goto(item_of(duckX, cLane), CARTOP),
                     show(),
                     gl(1.15, item_of(duckX, cLane), CARBOT),
                     hide()),
                 wait(rand(0.25, 1.1))],
                [hide(), wait(0.2)])),
)
car.script(
    when_bc(p, "duckStrike"),
    if_(eq(cIdx, 0),
        set_size(100), clear_effects(),
        switch_costume_r(rand(1, 3), "c1"),
        goto(item_of(duckX, dkHit), CARTOP),
        go_layer("front"), show(),
        gl(0.26, item_of(duckX, dkHit), DUCKY),
        gl(0.30, item_of(duckX, dkHit), CARBOT),
        hide()),
)
car.script(when_bc(p, "screenChanged"),
           if_(not_(eq(screen, 7)), hide()))

# --- the round
dctl = p.sprite("DuckCtrl")
C(dctl, "blank", "msg_blank")
dctl.visible = False
dctl.script(when_flag(), hide())
dctl.script(when_bc(p, "screenChanged"), broadcast(p, "duckRefresh"))

# NOT warped: this procedure waits and glides. A warp procedure that yields
# makes scratch-vm re-run the yielding block instead of yielding, burning the
# whole 500ms warp budget per wait and starving every other script.
hop = Proc(dctl, "duck hop", [], warp=False)
define(
    dctl, hop,
    set_var(busy, 1),
    set_var(dkTgt, add(dkLane, 1)),
    # the outcome is settled here, before a single pixel moves
    set_var(dkRoll, rand(1, 100)),
    broadcast(p, "duckHop"),
    wait(0.3),
    if_else(
        not_(gt(dkRoll, item_of(duckPct, dkMode))),
        [set_var(dkLane, dkTgt),
         if_(and_(eq(dkEgg, dkLane), eq(dkGot, 0)),
             set_var(dkGot, 1), SFX("bigwin")),
         set_var(mult, item_of(duckMults,
                               add(add(mul(sub(dkMode, 1), 12), dkLane),
                                   mul(dkGot, 48)))),
         SFX("gem", mul(sub(dkLane, 1), 10)),
         broadcast(p, "duckRefresh"),
         # reaching HOME cashes out automatically
         if_(not_(lt(dkLane, 12)),
             set_var(win, round_(mul(bet, mult))), change_var(chips, win),
             set_var(roundOn, 0), broadcast(p, "duckWin"),
             set_var(msgId, 11), SFX("bigwin"),
             wait(1.4), set_var(msgId, 1),
             set_var(dkLane, 0), set_var(dkGot, 0), set_var(dkEgg, 0),
             broadcast(p, "duckRefresh"))],
        [set_var(dkHit, dkTgt),
         broadcast(p, "duckStrike"), wait(0.26),
         SFX("bomb"), broadcast(p, "duckDie"),
         set_var(roundOn, 0), set_var(mult, 0),
         wait(0.15), set_var(msgId, 8),
         wait(0.9), set_var(msgId, 1),
         set_var(dkLane, 0), set_var(dkGot, 0), set_var(dkEgg, 0),
         broadcast(p, "duckRefresh")]),
    set_var(busy, 0),
    x=40, y=40,
)

dctl.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 7), eq(busy, 0)),
        if_else(
            eq(roundOn, 0),
            [if_else(lt(chips, bet),
                     [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                     [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
                      set_var(dkLane, 0), set_var(dkGot, 0), set_var(mult, 0),
                      # one run in four hides an egg, on a lane of its own
                      if_else(eq(rand(1, 4), 1),
                              [set_var(dkEgg, rand(1, 12))],
                              [set_var(dkEgg, 0)]),
                      set_var(roundOn, 1), broadcast(p, "duckRefresh"),
                      hop.call()])],
            [hop.call()])),
)
dctl.script(
    when_bc(p, "duckCash"),
    if_(and_(eq(screen, 7), and_(eq(roundOn, 1), gt(dkLane, 0))),
        set_var(busy, 1),
        set_var(win, round_(mul(bet, mult))), change_var(chips, win),
        set_var(roundOn, 0), broadcast(p, "duckWin"),
        set_var(msgId, 9), SFX("cash"),
        broadcast(p, "duckRefresh"),
        wait(1.6), set_var(msgId, 1), set_var(busy, 0),
        set_var(dkLane, 0), set_var(dkGot, 0), set_var(dkEgg, 0),
        broadcast(p, "duckRefresh")),
)


# ===================================================== CRASH
# A rocket climbs and the multiplier runs with it; bail out before it goes.
# The point at which it goes is drawn once, at launch, from the standard crash
# distribution P(fail >= x) = 0.96 / x - so every cash-out point returns the
# same, and nothing depends on frame timing (CLAUDE.md).
#
# `busy` deliberately stays 0 for the whole climb: bailing out mid-animation is
# the entire game, so CASH OUT must remain live.
PADY = AV4.PAD_Y
PX0, PY0 = AV4.ROCK_X0, AV4.ROCK_Y0
PX1, PY1 = AV4.ROCK_X1, AV4.ROCK_Y1
LOGG = T4["logGrowth"]
PRECN = T4["prec"]

sky = p.sprite("SkyPanel")
C(sky, "sky", "crsky")
sky.x, sky.y, sky.visible = 0, 0, False
sky.script(when_flag(), goto(0, 0), go_layer("back"))
sky.script(when_flag(), vis([8], [go_layer("back")]))

# --- drifting stars, to give the climb some speed
spark = p.sprite("Spark")
for n in range(1, 4):
    C(spark, f"s{n}", f"crspark{n}")
spark.visible = False
kIdx = spark.local_var("kIdx", 0)
kY = spark.local_var("kY", 0)
kX = spark.local_var("kX", 0)
spark.script(when_flag(), hide(), set_var(kIdx, 0),
             repeat(6, change_var(kIdx, 1), clone()), set_var(kIdx, 0))
spark.script(
    when_clone(),
    switch_costume_r(add(mod(kIdx, 3), 1), "s1"),
    set_var(kX, sub(mul(kIdx, 64), 190)),
    set_var(kY, sub(mul(kIdx, 33), 95)),
    set_effect("ghost", 45),
    forever(
        if_else(eq(screen, 8),
                [show(),
                 # nearer stars fall faster; the rocket climbs, so they descend
                 change_var(kY, sub(-0.5, mul(mod(kIdx, 3), 0.45))),
                 if_(lt(kY, -98), set_var(kY, 98)),
                 goto(kX, kY)],
                [hide()])),
)

# --- the rocket
rock = p.sprite("Rocket")
for n in range(1, 5):
    C(rock, f"r{n}", f"crrocket{n}")
rock.x, rock.y, rock.visible = PX0, PY0, False
rProg = rock.local_var("rProg", 0)
rock.script(when_flag(), goto(PX0, PY0), switch_costume("r1"))
rock.script(when_flag(), vis([8]))
rock.script(
    when_bc(p, "avReset"),
    if_(eq(screen, 8),
        go_layer("front"), switch_costume("r1"), clear_effects(),
        set_size(100), goto(PX0, PY0)),
)
rock.script(
    when_bc(p, "avFly"),
    if_(eq(screen, 8),
        go_layer("front"),
        # log10 of the multiplier, normalised so 10x is a full climb
        set_var(rProg, mathop("log", mult)),
        if_(gt(rProg, 1), set_var(rProg, 1)),
        if_(lt(rProg, 0), set_var(rProg, 0)),
        # full thrust once it is really moving
        if_else(gt(rProg, 0.35), [switch_costume("r3")], [switch_costume("r2")]),
        goto(add(PX0, mul(PX1 - PX0, rProg)),
             add(PY0, mul(PY1 - PY0, rProg)))),
)
rock.script(
    when_bc(p, "avDitch"),
    if_(eq(screen, 8),
        switch_costume("r4"),
        gl(0.45, add(xpos(), 26), sub(ypos(), 54)),
        set_effect("ghost", 55)),
)

# The burst lands where the rocket does. Sprites cannot read each other's
# position through this DSL, so it recomputes the same point from `mult`,
# which is pinned to avLand by the time avDitch fires.
bst = p.sprite("Burst")
C(bst, "b", "crburst")
bst.visible = False
bProg = bst.local_var("bProg", 0)
bst.script(when_flag(), hide())
bst.script(
    when_bc(p, "avDitch"),
    if_(eq(screen, 8),
        set_var(bProg, mathop("log", mult)),
        if_(gt(bProg, 1), set_var(bProg, 1)),
        if_(lt(bProg, 0), set_var(bProg, 0)),
        goto(add(PX0, mul(PX1 - PX0, bProg)),
             add(PY0, mul(PY1 - PY0, bProg))),
        go_layer("front"), set_size(70), show(),
        repeat(6, change_size(14), wait(0.02)),
        wait(0.5), hide()),
)
bst.script(when_bc(p, "avReset"), hide())
bst.script(when_bc(p, "screenChanged"), hide())

# --- the round
avc = p.sprite("CrashCtrl")
C(avc, "blank", "msg_blank")
avc.visible = False
avc.script(when_flag(), hide())

# Capturing the multiplier and paying happens inside one warped procedure, so
# a cash-out cannot land between reading `mult` and crediting the win.
do_cash = Proc(avc, "crash cash", [], warp=True)
define(avc, do_cash,
       if_(and_(eq(screen, 8), eq(roundOn, 1)),
           set_var(avAt, mult),
           set_var(win, round_(mul(bet, avAt))),
           change_var(chips, win),
           set_var(avCashed, 1),
           set_var(roundOn, 0), set_var(busy, 1)),
       x=40, y=40)

avc.script(when_bc(p, "avCash"), do_cash.call())

avc.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 8), and_(eq(roundOn, 0), eq(busy, 0))),
        if_else(
            lt(chips, bet),
            [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
            [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
             set_var(avCashed, 0), set_var(avTick, 0), set_var(mult, 1),
             set_var(avAt, 0),
             # draw where it fails, once, before anything moves
             set_var(avU, rand(1, PRECN)),
             set_var(avLand, div(round_(mul(div(mul(T4["house"], PRECN), avU),
                                            100)), 100)),
             set_var(roundOn, 1),
             broadcast(p, "avReset"), SFX("reel"),
             repeat_until(
                 eq(roundOn, 0),
                 change_var(avTick, 1),
                 set_var(tmp, div(round_(mul(mathop("10 ^", mul(avTick, LOGG)),
                                             100)), 100)),
                 if_else(
                     lt(tmp, avLand),
                     [set_var(mult, tmp), broadcast(p, "avFly"),
                      # auto cash-out fires the moment the target is reached
                      if_(and_(gt(avAuto, 1),
                               not_(lt(mult, item_of(avAutoVals, avAuto)))),
                          do_cash.call()),
                      # no wait: repeat_until already yields once per frame,
                      # which is a deterministic tick with no rounding up
                      ],
                     [set_var(mult, avLand), set_var(roundOn, 0),
                      set_var(busy, 1)])),
             set_var(busy, 1),
             if_(eq(screen, 8),
                 if_else(eq(avCashed, 1),
                         [set_var(msgId, 9), SFX("cash")],
                         [broadcast(p, "avDitch"), SFX("bomb"),
                          wait(0.5), set_var(msgId, 3)]),
                 wait(1.6), set_var(msgId, 1)),
             set_var(mult, 1), set_var(busy, 0),
             broadcast(p, "avReset")])),
)



# ===================================================== AVIAMASTERS
# Fly from one carrier to the other collecting orbs: numbers add to the running
# multiplier, x-orbs multiply it, rockets halve it without ending the round.
# Land and you are paid; ditch and the stake is gone; bail out any time for
# whatever the readout says.
#
# Both project rules hold. The orb and the ditch for each slot are rolled at
# that slot and applied before anything animates, so no payout depends on where
# a sprite happens to be; and src/tables5.py solves the per-slot ditch odds so
# every cash-out point is worth exactly the house 0.96, which means there is no
# stopping strategy to find. `busy` stays 0 for the whole flight, because
# bailing out mid-animation is the point.
AMSLOTS = T5["slots"]
AMPREC = T5["prec"]
AMCAP = T5["cap"]
PLX, PLO, PHI = AV5.PLANE_X, AV5.PLANE_LO, AV5.PLANE_HI
DECKY, CARL, CARR = AV5.DECK_Y, AV5.CARRIER_L, AV5.CARRIER_R

amsky = p.sprite("AvSky")
C(amsky, "sky", "avsky")
amsky.x, amsky.y, amsky.visible = 0, 0, False
amsky.script(when_flag(), goto(0, 0), go_layer("back"))
amsky.script(when_flag(), vis([9], [go_layer("back")]))

# --- orbs drifting across the sky. These are scenery: the route decides what
# the plane actually collects, so what floats past tells the player nothing and
# cannot be read for an edge. The one being collected is set to the real orb.
orb = p.sprite("AvOrb")
for n in range(1, len(T5["orbNames"]) + 1):
    C(orb, f"o{n}", f"avorb{n}")
orb.visible = False
oIdx = orb.local_var("oIdx", 0)
oX = orb.local_var("oX", 0)
oY = orb.local_var("oY", 0)
orb.script(when_flag(), hide(), set_var(oIdx, 0),
           repeat(5, change_var(oIdx, 1), clone()), set_var(oIdx, 0))
orb.script(
    when_clone(),
    set_var(oX, sub(mul(oIdx, 86), 180)),
    set_var(oY, add(mul(oIdx, 23), sub(PLO, 30))),
    forever(
        if_else(eq(screen, 9),
                [switch_costume_r(add(mod(add(oIdx, mathop("floor",
                                                           div(oX, 53))), 4), 2),
                                  "o2"),
                 show(), set_effect("ghost", 30),
                 change_var(oX, -1.6),
                 if_(lt(oX, AV5.ORB_OUT),
                     set_var(oX, AV5.ORB_IN),
                     set_var(oY, add(PLO, rand(-24, 74)))),
                 goto(oX, oY)],
                [hide()])),
)

# --- the plane
apl = p.sprite("AvPlane")
for n in range(1, 4):
    C(apl, f"p{n}", f"avplane{n}")
apl.x, apl.y, apl.visible = CARL, DECKY + 6, False
aProg = apl.local_var("aProg", 0)
apl.script(when_flag(), goto(CARL, DECKY + 6), switch_costume("p1"))
apl.script(when_flag(), vis([9]))
apl.script(
    when_bc(p, "amReset"),
    if_(eq(screen, 9),
        go_layer("front"), switch_costume("p1"), clear_effects(),
        goto(CARL, DECKY + 6)),
)
apl.script(
    when_bc(p, "amFly"),
    if_(eq(screen, 9),
        go_layer("front"), switch_costume("p2"),
        # climb out over the first two orbs, then hold station while the sky
        # moves past, then settle back down for the far deck
        set_var(aProg, div(amSlot, AMSLOTS)),
        if_else(lt(aProg, 0.18),
                [gl(0.2, add(CARL, mul(sub(PLX, CARL), div(aProg, 0.18))),
                    add(DECKY + 6, mul(sub(PLO, DECKY - 6), div(aProg, 0.18))))],
                [if_else(gt(aProg, 0.86),
                         [gl(0.2, add(PLX, mul(sub(CARR, PLX),
                                               div(sub(aProg, 0.86), 0.14))),
                             add(PLO, mul(sub(DECKY + 6, PLO),
                                          div(sub(aProg, 0.86), 0.14))))],
                         [gl(0.2, PLX, add(PLO, mul(sub(PHI, PLO), aProg)))])])),
)
apl.script(
    when_bc(p, "amDitch"),
    if_(eq(screen, 9),
        switch_costume("p3"),
        gl(0.5, add(xpos(), 30), AV5.SEA_Y - 6),
        set_effect("ghost", 50)),
)
apl.script(
    when_bc(p, "amLand"),
    if_(eq(screen, 9),
        switch_costume("p1"), gl(0.3, CARR, DECKY + 6)),
)

# --- the orb the plane just took, popped at the plane
pick = p.sprite("AvPick")
for n in range(1, len(T5["orbNames"]) + 1):
    C(pick, f"o{n}", f"avorb{n}")
pick.visible = False
pick.script(when_flag(), hide())
pick.script(
    when_bc(p, "amCollect"),
    if_(and_(eq(screen, 9), gt(amOrb, 1)),
        switch_costume_r(amOrb, "o1"),
        goto(add(PLX, 30), ypos()), go_layer("front"),
        set_size(100), clear_effects(), show(),
        repeat(7, change_x(-4), change_size(6), change_effect("ghost", 12)),
        hide()),
)
pick.script(when_bc(p, "amReset"), hide())
pick.script(when_bc(p, "screenChanged"), hide())
pick.script(
    when_bc(p, "amFly"),
    if_(eq(screen, 9), goto(add(PLX, 30), add(PLO, mul(sub(PHI, PLO),
                                                       div(amSlot, AMSLOTS))))),
)

# --- the round
amc = p.sprite("AviaCtrl")
C(amc, "blank", "msg_blank")
amc.visible = False
amc.script(when_flag(), hide())

# Reading the multiplier and paying happen in one warped procedure, so a
# cash-out cannot land between the two and pay against a figure the player
# never saw. No waits in here - see PITFALLS on warp procedures that yield.
am_cash = Proc(amc, "avia cash", [], warp=True)
define(amc, am_cash,
       if_(and_(eq(screen, 9), and_(eq(roundOn, 1), gt(amSlot, 0))),
           set_var(amAt, amVal),
           set_var(win, round_(mul(bet, amAt))),
           change_var(chips, win),
           set_var(amCashed, 1),
           set_var(roundOn, 0), set_var(busy, 1)),
       x=40, y=40)

amc.script(when_bc(p, "amCash"), am_cash.call())
amc.script(when_bc(p, "screenChanged"), broadcast(p, "amReset"))

amc.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 9), and_(eq(roundOn, 0), eq(busy, 0))),
        if_else(
            lt(chips, bet),
            [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
            [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
             set_var(amSlot, 0), set_var(amVal, 1), set_var(mult, 1),
             set_var(amCashed, 0), set_var(amDown, 0), set_var(amAt, 0),
             delete_all(amLog),
             set_var(roundOn, 1),
             broadcast(p, "amReset"), SFX("reel"),
             repeat_until(
                 eq(roundOn, 0),
                 change_var(amSlot, 1),
                 # the ditch for this slot, rolled before anything moves
                 if_else(
                     not_(gt(rand(1, AMPREC), item_of(amRamp, amSlot))),
                     [set_var(amDown, 1), set_var(amVal, 0), set_var(mult, 0),
                      set_var(roundOn, 0), set_var(busy, 1)],
                     [# which orb this slot holds
                      set_var(amRoll, rand(1, 100)),
                      set_var(amOrb, 1),
                      repeat_until(not_(gt(amRoll, item_of(amCum, amOrb))),
                                   change_var(amOrb, 1)),
                      set_var(amVal,
                              div(round_(mul(add(mul(item_of(amA, amOrb), amVal),
                                                 item_of(amB, amOrb)), 100)),
                                  100)),
                      if_(gt(amVal, AMCAP), set_var(amVal, AMCAP)),
                      add_to(amLog, amOrb),
                      set_var(mult, amVal),
                      broadcast(p, "amFly"),
                      broadcast(p, "amCollect"),
                      if_(eq(item_of(amB, amOrb), 0),
                          if_else(lt(item_of(amA, amOrb), 1),
                                  [SFX("bomb")], [SFX("gem", 20)])),
                      if_(gt(item_of(amB, amOrb), 0), SFX("chip")),
                      # auto cash-out fires the instant the target is reached
                      if_(and_(gt(amAuto, 1),
                               not_(lt(amVal, item_of(avAutoVals, amAuto)))),
                          am_cash.call()),
                      # `roundOn` still 1 means nothing has paid yet. Without
                      # that guard an auto cash-out on the LAST slot pays, and
                      # then the landing below pays the same flight again.
                      if_(and_(not_(lt(amSlot, AMSLOTS)), eq(roundOn, 1)),
                          # made the far carrier: everything collected is paid
                          set_var(amAt, amVal),
                          set_var(win, round_(mul(bet, amAt))),
                          change_var(chips, win),
                          set_var(roundOn, 0), set_var(busy, 1),
                          broadcast(p, "amLand")),
                      wait(0.34)])),
             if_(eq(screen, 9),
                 if_else(eq(amDown, 1),
                         [broadcast(p, "amDitch"), SFX("bomb"),
                          wait(0.5), set_var(msgId, 3)],
                         [set_var(msgId, 9), SFX("cash")]),
                 wait(1.5), set_var(msgId, 1)),
             set_var(mult, 1), set_var(amVal, 1), set_var(amSlot, 0),
             set_var(busy, 0),
             broadcast(p, "amReset")])),
)

# ===================================================== COIN FLIP
# Call a side and keep flipping. Every correct call doubles the pot; one wrong
# call takes the stake. src/tables6.py solves the ladder as 0.96 * 2^n, so
# cashing out on any rung returns exactly the house 0.96 - the cut is taken on
# entry and there is no rung worth holding out for.
#
# The side is drawn before the coin moves, and the coin renders from `cfSpin`
# and `cfSide` in a forever loop rather than running a spin animation of its
# own. An animation script would be restarted by the next flip (PITFALLS 2) and
# on the fast build a round finishes in a frame, so the face on screen could
# outlive the flip that produced it. Rendering from state cannot disagree with
# what was paid.
CF_RUNGS = T6["coinRungs"]

cfelt = p.sprite("CoinFelt")
C(cfelt, "felt", "coin_felt")
cfelt.x, cfelt.y, cfelt.visible = AV6.FELT_XY[0], AV6.FELT_XY[1], False
cfelt.script(when_flag(), goto(*AV6.FELT_XY), go_layer("back"))
cfelt.script(when_flag(), vis([10], [go_layer("back")]))

clad = p.sprite("CoinLadder")
C(clad, "lad", "coin_ladder")
clad.x, clad.y, clad.visible = AV6.LADDER_XY[0], AV6.LADDER_XY[1], False
clad.script(when_flag(), goto(*AV6.LADDER_XY), go_layer("back"))
clad.script(when_flag(), vis([10], [go_layer("back")]))

# the marker rides the gap beside the ladder, on the rung the streak reached
cpip = p.sprite("CoinPip")
C(cpip, "pip", "coin_pip")
cpip.visible = False
cpip.script(
    when_flag(),
    forever(if_else(and_(eq(screen, 10), gt(cfStreak, 0)),
                    [goto(AV6.PIP_X, item_of(coinRungY, cfStreak)),
                     go_layer("front"), show()],
                    [hide()])),
)

coin = p.sprite("Coin")
for n in range(1, AV6.COIN_FRAMES + 1):
    C(coin, f"cf{n}", f"cf{n}")
coin.x, coin.y, coin.visible = AV6.COIN_XY[0], AV6.COIN_XY[1], False
cfF = coin.local_var("cfF", 1)
coin.script(
    when_flag(), goto(*AV6.COIN_XY), set_var(cfF, 1),
    forever(
        if_else(eq(screen, 10), [go_layer("front"), show()], [hide()]),
        if_else(
            eq(cfSpin, 1),
            [change_var(cfF, 1),
             if_(gt(cfF, AV6.COIN_FRAMES), set_var(cfF, 1)),
             switch_costume_r(cfF, "cf1")],
            # at rest it shows the side that was actually drawn
            [if_else(eq(cfSide, 2),
                     [switch_costume(f"cf{AV6.COIN_TAILS}"),
                      set_var(cfF, AV6.COIN_TAILS)],
                     [switch_costume(f"cf{AV6.COIN_HEADS}"),
                      set_var(cfF, AV6.COIN_HEADS)])])),
)

# --- the round
cfc = p.sprite("CoinCtrl")
C(cfc, "blank", "msg_blank")
cfc.visible = False
cfc.script(when_flag(), hide())

# Capturing the multiplier and paying happen in one warped procedure, and it is
# the only thing in the game that credits a coin flip: topping the ladder calls
# this rather than paying a second time of its own.
cf_cash = Proc(cfc, "coin cash", [], warp=True)
define(cfc, cf_cash,
       if_(and_(eq(screen, 10), and_(eq(roundOn, 1), gt(cfStreak, 0))),
           set_var(cfAt, mult),
           set_var(win, round_(mul(bet, cfAt))),
           change_var(chips, win),
           set_var(cfCashed, 1),
           set_var(roundOn, 0), set_var(busy, 1)),
       x=40, y=40)

# NOT warped: it waits while the coin is in the air. A warp procedure that
# yields re-runs the yielding block instead of yielding (see PITFALLS).
cf_flip = Proc(cfc, "coin flip", [], warp=False)
define(
    cfc, cf_flip,
    set_var(busy, 1),
    # the side is settled here, before a single frame of the spin
    set_var(cfSide, rand(1, 2)),
    set_var(cfSpin, 1), SFX("reel"),
    wait(0.62),
    set_var(cfSpin, 0),
    if_else(
        eq(cfSide, cfCall),
        [change_var(cfStreak, 1),
         set_var(mult, item_of(coinMults, cfStreak)),
         SFX("gem", mul(sub(cfStreak, 1), 6)),
         # the ladder tops out: paid through the one cash-out path
         if_(not_(lt(cfStreak, CF_RUNGS)),
             cf_cash.call(),
             set_var(msgId, 11), SFX("bigwin"),
             wait(1.5), set_var(msgId, 1),
             set_var(cfStreak, 0), set_var(mult, 1))],
        # the call was wrong: roundOn drops while busy is already raised, so
        # there is no frame in which FLIP is live over a settled round
        [set_var(mult, 0), set_var(roundOn, 0),
         SFX("bomb"), set_var(msgId, 3),
         wait(1.3), set_var(msgId, 1),
         set_var(cfStreak, 0), set_var(mult, 1)]),
    set_var(busy, 0),
    x=40, y=40,
)

cfc.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 10), eq(busy, 0)),
        if_else(
            eq(roundOn, 0),
            [if_else(lt(chips, bet),
                     [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
                     [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
                      set_var(win, 0),
                      set_var(cfStreak, 0), set_var(cfCashed, 0),
                      set_var(cfAt, 0), set_var(mult, 1),
                      set_var(roundOn, 1),
                      cf_flip.call()])],
            [cf_flip.call()])),
)

cfc.script(
    when_bc(p, "coinCash"),
    if_(and_(and_(eq(screen, 10), eq(busy, 0)),
             and_(eq(roundOn, 1), gt(cfStreak, 0))),
        cf_cash.call(),
        set_var(msgId, 9), SFX("cash"),
        wait(1.6), set_var(msgId, 1),
        set_var(cfStreak, 0), set_var(mult, 1), set_var(busy, 0)),
)


# ===================================================== DICE
# Roll 0.00-99.99 against a threshold, betting that it lands under or over.
# The roll is drawn as an integer number of hundredths and every comparison is
# made on that integer, so what pays never depends on how a float prints.
# src/tables6.py picks the five chances so that chance x payout is exactly the
# house 0.96 in every mode and on either side.
DC_OUT = T6["diceOutcomes"]

dfelt = p.sprite("DiceFelt")
C(dfelt, "felt", "dice_felt")
dfelt.x, dfelt.y, dfelt.visible = AV6.DFELT_XY[0], AV6.DFELT_XY[1], False
dfelt.script(when_flag(), goto(*AV6.DFELT_XY), go_layer("back"))
dfelt.script(when_flag(), vis([11], [go_layer("back")]))

# The winning span is painted into the costume from the same solved table the
# payout reads, so what pays is on the screen rather than in the player's head.
dtrk = p.sprite("DiceTrack")
for _m in range(1, len(T6["diceWin"]) + 1):
    for _sd in ("u", "o"):
        C(dtrk, f"t{_m}{_sd}", f"dice_tr{_m}{_sd}")
dtrk.x, dtrk.y, dtrk.visible = AV6.TRACK_XY[0], AV6.TRACK_XY[1], False
dtrk.script(when_flag(), goto(*AV6.TRACK_XY))
dtrk.script(
    when_flag(),
    forever(
        # costume order is mode-major: 1 under, 1 over, 2 under, 2 over, ...
        switch_costume_r(add(mul(sub(dcMode, 1), 2), dcSide), "t1u"),
        if_else(eq(screen, 11), [go_layer("front"), show()], [hide()])),
)

# The needle is positioned from dcInt every frame rather than glided to it, for
# the same reason the coin renders from state: on the fast build the round is
# over before an animation script could finish, and a needle left mid-glide
# would be showing a different number from the one that was paid.
dmark = p.sprite("DiceMark")
C(dmark, "mark", "dice_marker")
dmark.visible = False
dmark.script(
    when_flag(),
    forever(
        if_else(
            and_(eq(screen, 11), or_(eq(dcRolling, 1), eq(dcShown, 1))),
            [if_else(eq(dcRolling, 1),
                     [goto(rand(AV6.RAIL_X0, AV6.RAIL_X1), AV6.MARK_XY[1])],
                     [goto(add(AV6.RAIL_X0,
                               div(mul(AV6.RAIL_X1 - AV6.RAIL_X0, dcInt),
                                   DC_OUT)),
                           AV6.MARK_XY[1])]),
             go_layer("front"), show()],
            [hide()])),
)

# --- the round
dcc = p.sprite("DiceCtrl")
C(dcc, "blank", "msg_blank")
dcc.visible = False
dcc.script(when_flag(), hide())

dcc.script(
    when_bc(p, "action"),
    if_(and_(eq(screen, 11), and_(eq(busy, 0), eq(roundOn, 0))),
        if_else(
            lt(chips, bet),
            [set_var(msgId, 10), wait(1.2), set_var(msgId, 1)],
            [change_var(chips, mul(bet, -1)), set_var(msgId, 1),
             set_var(busy, 1), set_var(roundOn, 1), set_var(win, 0),
             set_var(mult, item_of(diceMult, dcMode)),
             # the roll and what it pays are settled here, before the needle
             # moves - 0..DC_OUT-1 hundredths, compared as an integer
             set_var(dcInt, rand(0, DC_OUT - 1)),
             if_else(
                 eq(dcSide, 1),
                 # UNDER t wins below t; OVER t wins at or above DC_OUT - t.
                 # Both are `diceWin` outcomes wide, so one table serves both.
                 [if_else(lt(dcInt, item_of(diceWin, dcMode)),
                          [set_var(dcWon, 1)], [set_var(dcWon, 0)])],
                 [if_else(not_(lt(dcInt, sub(DC_OUT, item_of(diceWin, dcMode)))),
                          [set_var(dcWon, 1)], [set_var(dcWon, 0)])]),
             # the readout stays blank while the needle scans, so the number
             # arrives with the needle rather than ahead of it
             set_var(dcTxt, ""), set_var(dcRolling, 1), SFX("reel"),
             wait(0.7),
             set_var(dcRolling, 0), set_var(dcShown, 1),
             set_var(dcFrac, mod(dcInt, 100)),
             if_(lt(dcFrac, 10), set_var(dcFrac, join("0", dcFrac))),
             set_var(dcTxt, join(join(mathop("floor", div(dcInt, 100)), "."),
                                 dcFrac)),
             SFX("tick"),
             wait(0.45),
             if_else(eq(dcWon, 1),
                     [set_var(win, round_(mul(bet, mult))),
                      change_var(chips, win),
                      if_else(gt(win, mul(bet, 9)),
                              [set_var(msgId, 11), SFX("bigwin")],
                              [set_var(msgId, 2), SFX("win")])],
                     [set_var(win, 0), set_var(msgId, 3), SFX("lose")]),
             # the round ends with busy still raised from the top
             set_var(roundOn, 0),
             wait(1.4), set_var(msgId, 1), set_var(busy, 0)])),
)


out = str(BUILD / "ClubRoyale_fast.sb3") if FAST else str(DIST / "ClubRoyale.sb3")
os.makedirs(os.path.dirname(out), exist_ok=True)
p.save(out)
print("targets:", len(p.targets), " blocks:",
      sum(len(t.blocks) for t in p.targets),
      " assets:", len(p.assets),
      " size:", round(os.path.getsize(out) / 1024), "KB")
