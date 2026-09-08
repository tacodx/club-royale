"""CLUB ROYALE v1.1"""
import os, json
from sb3 import Project
from blocks import *
import assets_v11 as AV
import assets_v2 as AV2
import json
import sfx as SFXMOD

A = AV.OUT
AV.build()
AV2.build()
SFXMOD.build()
T = AV.T
from paths import BUILD, SFX_DIR, DIST
T2 = json.load(open(BUILD / "tables2.json"))

FAST = os.environ.get("FAST") == "1"
_rw = wait


def wait(s):                       # noqa: F811
    return _rw(0.01 if FAST else s)


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
bjA     = p.var("bjA", 0)
bjB     = p.var("bjB", 0)

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

SCREENS = {"lobby": 0, "openSlots": 1, "openPlinko": 2, "openMines": 3,
           "openBJ": 4, "openRoulette": 5, "openStairs": 6}

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
    st.script(
        when_bc(p, name),
        set_var(screen, num),
        set_var(busy, 0), set_var(roundOn, 0), set_var(msgId, 1),
        set_var(mult, 0), set_var(picks, 0), set_var(hole, 0),
        delete_all(pHand), delete_all(dHand),
        set_var(stRow, 1), set_var(bjPhase, 0), set_var(didSplit, 0),
        delete_all(pHand2),
        extra,
        broadcast(p, "screenChanged"),
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
for n in range(1, 14):
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
    set_var(dField, 0), set_var(dSlot, 0),
)
dig.script(
    when_clone(),
    go_layer("front"),
    forever(
        if_(eq(dField, 1), set_var(dTxt, chips)),
        if_(eq(dField, 2), set_var(dTxt, bet)),
        if_(eq(dField, 3), set_var(dTxt, mult)),
        if_(eq(dField, 4), set_var(dTxt, rNum)),
        if_(eq(dField, 5), set_var(dTxt, rStake)),
        if_(eq(dField, 6), set_var(dTxt, dealer)),
        if_(eq(dField, 7), set_var(dTxt, you)),
        if_(eq(dField, 8), set_var(dTxt, you2)),
        set_var(dLen, length_of(dTxt)),
        if_else(
            all_of(
                not_(gt(dSlot, dLen)),
                any_of(
                    eq(dField, 1),
                    all_of(eq(dField, 2), gt(screen, 0), eq(roundOn, 0)),
                    all_of(eq(dField, 3), any_of(eq(screen, 3), eq(screen, 6))),
                    all_of(eq(dField, 4), eq(screen, 5), eq(busy, 1)),
                    all_of(eq(dField, 5), eq(screen, 5)),
                    all_of(any_of(eq(dField, 6), eq(dField, 7)),
                           eq(screen, 4), gt(bjPhase, 0)),
                    all_of(eq(dField, 8), eq(screen, 4), gt(bjPhase, 0),
                           eq(didSplit, 1)))),
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
             set_var(tmp2, letter_of(dSlot, dTxt)),
             if_else(eq(tmp2, "."), [switch_costume("d11")],
                     [if_else(eq(tmp2, ","), [switch_costume("d12")],
                              [switch_costume_r(add(tmp2, 1), "d1")])]),
             show()],
            [hide()])),
)

mplq = p.sprite("MultPlaque")
C(mplq, "plq", "plq_mult")
mplq.x, mplq.y, mplq.visible = 0, 163, False
mplq.script(when_flag(), goto(0, 163))
mplq.script(when_flag(), vis([3, 6]))

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
        or_(and_(and_(eq(screen, 3), eq(roundOn, 1)),
                 and_(eq(busy, 0), gt(picks, 0))),
            and_(and_(eq(screen, 6), eq(roundOn, 1)),
                 and_(eq(busy, 0), gt(stRow, 1)))),
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
              ("roul", "lt_roulette"), ("stairs", "lt_stairs")]:
    C(menu, nm, f)
menu.visible = False
mIdx = menu.local_var("mIdx", 0)
menu.script(when_flag(), hide(), set_var(mIdx, 0),
            repeat(6, change_var(mIdx, 1), clone()), set_var(mIdx, 0))
menu.script(
    when_clone(),
    switch_costume_r(mIdx, "slots"),
    goto(add(-140, mul(140, mod(sub(mIdx, 1), 3))),
         sub(24, mul(96, mathop("floor", div(sub(mIdx, 1), 3))))),
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
        if_(eq(mIdx, 6), broadcast(p, "openStairs"))),
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
        ("DiffSel", "sel_diff", 5, stDiff, -45, 6, "stairs")]:
    s = p.sprite(nm)
    for n in range(1, count + 1):
        C(s, f"c{n}", f"{file_pfx}{n}")
    s.x, s.y, s.visible = xx, -152, False
    ok = (and_(eq(screen, 2), eq(ballsUp, 0)) if guard == "plinko"
          else (and_(eq(screen, 3), eq(roundOn, 0)) if guard == "mines"
                else and_(eq(screen, 6), eq(roundOn, 0))))
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
            broadcast(p, "refreshPlinko") if guard == "plinko"
            else (broadcast(p, "stairRefresh") if guard == "stairs" else None)),
    )

act = p.sprite("ActionBtn")
for nm, f in [("spin", "btn_spin"), ("drop", "btn_drop"),
              ("start", "btn_start"), ("deal", "btn_deal")]:
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
wptr.script(when_bc(p, "rSpin"), go_layer("front"), show())
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
           point_dir(sub(90, mul(wTgt, sub(1, mul(wU, mul(wU, wU))))))),
    point_dir(sub(90, mul(sub(item_num_of(wheelOrd, rNum), 1), div(360, 37)))),
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

out = str(BUILD / "ClubRoyale_fast.sb3") if FAST else str(DIST / "ClubRoyale.sb3")
os.makedirs(os.path.dirname(out), exist_ok=True)
p.save(out)
print("targets:", len(p.targets), " blocks:",
      sum(len(t.blocks) for t in p.targets),
      " assets:", len(p.assets),
      " size:", round(os.path.getsize(out) / 1024), "KB")
