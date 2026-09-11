// Dice: drags the slider and rolls headlessly, checking the threshold, the
// multiplier it implies and every payout against an independent implementation.
//
// The threshold is no longer one of five presets, so the multiplier is computed
// rather than looked up: floor(96000000 / winning outcomes) / 10000. That makes
// two things worth proving rather than assuming - that the VM's arithmetic
// agrees with JS exactly at every reachable position, and that the return is
// never above the house 0.96 anywhere on the rail.
//
// The slider is driven through ioDevices.mouse, which is the real control: the
// sprite reads `mouse x` / `mouse y` rather than `touching mouse-pointer`
// (PITFALLS 10), precisely so the harness can move the actual pointer instead
// of testing a stand-in.
//
//   node tests/play_dice.js <sb3> [rounds]
const fs = require('fs'), path = require('path'), VM = require('scratch-vm');
const BUILD = path.join(__dirname, '..', 'build');
const T6 = JSON.parse(fs.readFileSync(path.join(BUILD, 'tables6.json')));
const G = JSON.parse(fs.readFileSync(path.join(BUILD, 'geom6.json')));
const vm = new VM();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const stage = () => vm.runtime.getTargetForStage();
const gv = n => { const s = stage();
  for (const id in s.variables) if (s.variables[id].name === n) return s.variables[id].value;
  throw new Error('no var ' + n); };
const num = n => Number(gv(n));
const setv = (n, v) => { stage().lookupVariableByNameAndType(n).value = v; };
const sp = n => vm.runtime.targets.find(t => !t.isStage && t.sprite.name === n && t.isOriginal);
const cl = n => vm.runtime.targets.filter(t => !t.isStage && t.sprite.name === n && !t.isOriginal);
const lv = (t, n) => { for (const id in t.variables) if (t.variables[id].name === n) return t.variables[id].value; };
const click = t => vm.runtime.startHats('event_whenthisspriteclicked', null, t);
async function until(p, l, m = 1500) {
  for (let i = 0; i < m; i++) { if (p()) return true; await sleep(12); }
  throw new Error('timeout ' + l);
}
const settled = () => num('roundOn') === 0 && num('busy') === 0 && num('msgId') === 1;

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

// ---------------------------------------------------------------- the rules
// must match src/tables6.py
const HOUSE = 0.96, OUT = T6.diceOutcomes, PREC = T6.dicePrec;
const MINW = T6.diceMinWin, MAXW = T6.diceMaxWin;
const NUM = HOUSE * OUT * PREC;                       // 96000000
const multFor = w => Math.floor(NUM / w) / PREC;
const winsFor = (t, side) => side === 1 ? t : OUT - t;
const wins = (roll, t, side) => side === 1 ? roll < t : roll >= t;
const clampT = (t, side) => side === 1
  ? Math.min(MAXW, Math.max(MINW, t))
  : Math.min(OUT - MINW, Math.max(OUT - MAXW, t));
const railX = t => G.railX0 + G.railW * t / OUT;
const two = v => `${Math.floor(v / 100)}.${String(v % 100).padStart(2, '0')}`;

function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      return i <= 10 ? String(i - 1)
        : (i === 11 ? '.' : (i === 12 ? ',' : (i === 14 ? 'x' : ''))); })
    .join('');
}
async function stable(read, tries = 30) {
  let last = read();
  for (let i = 0; i < tries; i++) {
    await sleep(16);
    const now = read();
    if (now === last) return now;
    last = now;
  }
  return last;
}
// Move the real pointer. With a 480x360 canvas postData reduces to
// scratchX = round(x - 240) and scratchY = round(180 - y), so the offset has to
// be exactly 240/180 - a half-unit nudge lands the pointer a whole stage unit
// out. The epsilon is only there because postData tests `if (data.x)`, which
// would silently drop an x of 0 (stage x -240, the left end of the rail).
function pointer(x, y, isDown) {
  vm.runtime.ioDevices.mouse.postData({
    x: x + 240 + 1e-4, y: 180 - y + 1e-4,
    canvasWidth: 480, canvasHeight: 360, isDown });
}
async function dragTo(stageX) {
  pointer(stageX, G.railY, true);
  await sleep(90);
  pointer(stageX, G.railY, false);
  await sleep(60);
}

async function bootSettle(cap = 6000) {
  const total = () => vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  let last = -1, st = 0, waited = 0;
  while (waited < cap) {
    await sleep(50); waited += 50;
    const n = total();
    st = (n === last && n > 0) ? st + 1 : 0;
    last = n;
    if (st >= 3) return n;
  }
  return last;
}

(async () => {
  const ROUNDS = Number(process.argv[3] || 60);
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await bootSettle();

  const games = sp('MenuTile').getCostumes().length;
  check('boot: one lobby tile per game', cl('MenuTile').length === games,
        `${cl('MenuTile').length} tiles, ${games} games`);
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  check('boot: clone budget under 300', clones < 300, clones + ' clones');

  // ---------------------------------------- the payout rule, over the whole rail
  // Not a sample: every one of the reachable win-chance values, checked for the
  // invariant that matters - the house never takes less than its 0.96.
  let over = 0, worst = 1, worstAt = 0, exact = 0;
  for (let w = MINW; w <= MAXW; w++) {
    const rtp = w * Math.floor(NUM / w) / (OUT * PREC);
    if (rtp > HOUSE + 1e-12) over++;
    if (rtp === HOUSE) exact++;
    if (rtp < worst) { worst = rtp; worstAt = w; }
  }
  check('table: no slider position returns more than 0.96', over === 0, over + ' do');
  check('table: and none returns less than 0.9599', worst > 0.9599,
        `worst ${worst.toFixed(6)} at ${(worstAt / 100).toFixed(2)}%, exact on ${exact}`);

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(11));
  await until(() => num('screen') === 11, 'nav dice');
  check('nav: dice', num('screen') === 11, 'screen ' + num('screen'));

  const act = sp('ActionBtn'), mark = sp('DiceMark'), thr = sp('DiceThresh');
  const bandL = sp('DiceBandL'), bandR = sp('DiceBandR'), sideSel = sp('SideSel');
  setv('chips', 100000000);
  setv('bet', 100);
  await sleep(150);
  check('idle: needle hidden before the first roll', mark.visible === false);

  // -------------------------------------------------------- the slider
  let dragBad = 0, handleBad = 0, bandBad = 0, multBad = 0, chanceBad = 0;
  let firstBad = '';
  const fail = m => { firstBad = firstBad || m; };

  for (const side of [1, 2]) {
    setv('dcSide', side);
    await sleep(60);
    for (const x of [-176, -150, -100, -40, 0, 35, 90, 140, 176]) {
      await dragTo(x);
      const wantT = clampT(Math.round((x - G.railX0) * OUT / G.railW), side);
      const gotT = num('dcT');
      if (gotT !== wantT) {
        dragBad++;
        fail(`side ${side} drag to x=${x}: dcT ${gotT}, expected ${wantT}`);
      }
      const w = winsFor(gotT, side);
      if (num('dcWinN') !== w) {
        dragBad++;
        fail(`side ${side} t=${gotT}: winN ${num('dcWinN')}, expected ${w}`);
      }
      // the VM's own arithmetic must agree with JS exactly
      if (num('mult') !== multFor(w)) {
        multBad++;
        fail(`side ${side} w=${w}: mult ${num('mult')}, expected ${multFor(w)}`);
      }
      if (gv('dcChance') !== two(w)) {
        chanceBad++;
        fail(`side ${side} w=${w}: chance "${gv('dcChance')}", expected "${two(w)}"`);
      }
      // the handle and the two bars must be standing where the number says
      const hx = await stable(() => thr.x);
      if (Math.abs(hx - railX(gotT)) > 0.6) {
        handleBad++;
        fail(`t=${gotT}: handle at ${hx}, expected ${railX(gotT).toFixed(2)}`);
      }
      const lx = bandL.x, rx = bandR.x;
      const cost = t => t.getCostumes()[t.currentCostume].name;
      if (Math.abs(lx - (railX(gotT) - G.railW / 2)) > 0.6 ||
          Math.abs(rx - (railX(gotT) + G.railW / 2)) > 0.6) {
        bandBad++;
        fail(`t=${gotT}: bars at ${lx}/${rx}, expected ${(railX(gotT) - G.railW / 2).toFixed(1)}/${(railX(gotT) + G.railW / 2).toFixed(1)}`);
      }
      if (cost(bandL) !== (side === 1 ? 'win' : 'lose') ||
          cost(bandR) !== (side === 1 ? 'lose' : 'win')) {
        bandBad++;
        fail(`side ${side}: bars coloured ${cost(bandL)}/${cost(bandR)}`);
      }
    }
  }
  check('slider: the drag sets the threshold it points at', dragBad === 0, dragBad ? firstBad : '');
  check('slider: the multiplier matches the solver exactly', multBad === 0, multBad ? firstBad : '');
  check('slider: the chance readout matches', chanceBad === 0, chanceBad ? firstBad : '');
  check('display: the handle stands on the threshold', handleBad === 0, handleBad ? firstBad : '');
  check('display: the bars split the rail on the threshold', bandBad === 0, bandBad ? firstBad : '');

  // ------------------------------------------------------------ the limits
  // Dragging past the ends must stop at the solved range, not run off it -
  // a 0% chance would be an infinite multiplier and a 100% one a free win.
  setv('dcSide', 1); await sleep(60);
  await dragTo(-240);
  const loU = num('dcT');
  await dragTo(240);
  const hiU = num('dcT');
  setv('dcSide', 2); await sleep(60);
  await dragTo(-240);
  const loO = num('dcT');
  await dragTo(240);
  const hiO = num('dcT');
  check('limits: under stops at 1% and 95%', loU === MINW && hiU === MAXW,
        `${loU}..${hiU}, expected ${MINW}..${MAXW}`);
  check('limits: over stops at 95% and 1%',
        loO === OUT - MAXW && hiO === OUT - MINW,
        `${loO}..${hiO}, expected ${OUT - MAXW}..${OUT - MINW}`);
  check('limits: the extremes pay what the solver says',
        multFor(MINW) === 96 && Math.abs(multFor(MAXW) - 1.0105) < 1e-9,
        `${multFor(MINW)}x and ${multFor(MAXW)}x`);

  // the slider must be dead while a roll is in the air
  setv('dcSide', 1); await dragTo(0);
  const beforeRoll = num('dcT');

  // ------------------------------------------------------------- the rounds
  let wonBad = 0, payBad = 0, stakeBad = 0, fmtBad = 0, readBad = 0,
      markBad = 0, multShown = 0, rangeBad = 0, lockBad = 0;
  const seen = { lo: OUT, hi: -1 };
  const BUCKETS = 5;
  const hist = new Array(BUCKETS).fill(0);
  let leadZero = 0, winsSeen = 0;

  for (let r = 0; r < ROUNDS; r++) {
    await until(settled, 'settle ' + r);
    // sweep the rail rather than sampling one spot, both sides
    const side = (r % 2) + 1;
    const xs = [-150, -90, -20, 40, 110, 165];
    setv('dcSide', side); await sleep(40);
    await dragTo(xs[r % xs.length]);
    const t = num('dcT'), w = num('dcWinN'), m = num('mult');

    const bet = num('bet'), before = num('chips');
    click(act);
    await until(() => num('chips') === before - bet, 'stake ' + r);
    if (num('chips') !== before - bet) {
      stakeBad++;
      fail(`round ${r}: stake ${before - num('chips')}, expected ${bet}`);
    }
    // dragging mid-roll must not move the threshold under the settled bet
    pointer(-170, G.railY, true); await sleep(40); pointer(-170, G.railY, false);
    if (num('dcT') !== t) {
      lockBad++;
      fail(`round ${r}: threshold moved mid-roll, ${t} -> ${num('dcT')}`);
    }
    await until(() => num('dcRolling') === 0 && num('dcShown') === 1, 'roll ' + r);

    const roll = num('dcInt');
    if (!(Number.isInteger(roll) && roll >= 0 && roll < OUT)) {
      rangeBad++;
      fail(`round ${r}: roll ${roll} outside 0..${OUT - 1}`);
    }
    seen.lo = Math.min(seen.lo, roll); seen.hi = Math.max(seen.hi, roll);
    hist[Math.floor(roll * BUCKETS / OUT)]++;
    if (roll % 100 < 10) leadZero++;

    const want = wins(roll, t, side);
    if (want) winsSeen++;
    if ((num('dcWon') === 1) !== want) {
      wonBad++;
      fail(`round ${r}: roll ${roll} t ${t} side ${side} -> ${num('dcWon')}, expected ${want ? 1 : 0}`);
    }
    if (gv('dcTxt') !== two(roll)) {
      fmtBad++;
      fail(`round ${r}: roll ${roll} formatted "${gv('dcTxt')}", expected "${two(roll)}"`);
    }
    const shown = await stable(() => readout(9));
    if (shown !== two(roll)) {
      readBad++;
      fail(`round ${r}: roll ${roll} but the readout says "${shown}"`);
    }
    const mShown = await stable(() => readout(3));
    if (mShown !== String(m)) {
      multShown++;
      fail(`round ${r}: mult ${m} but the plaque says "${mShown}"`);
    }
    const mx = await stable(() => mark.x);
    if (!mark.visible || Math.abs(mx - railX(roll)) > 0.6) {
      markBad++;
      fail(`round ${r}: roll ${roll} needle at x=${mx}, expected ${railX(roll).toFixed(2)}`);
    }

    await until(settled, 'settle after ' + r);
    const got = num('chips') - (before - bet);
    const wantPay = want ? Math.round(bet * multFor(w)) : 0;
    if (got !== wantPay) {
      payBad++;
      fail(`round ${r}: roll ${roll} t ${t} side ${side} paid ${got}, expected ${wantPay}`);
    }
  }

  check('rules: win test matches the threshold', wonBad === 0, wonBad ? firstBad : ROUNDS + ' rolls');
  check('rules: stake taken once per roll', stakeBad === 0, stakeBad ? firstBad : '');
  check('rules: the slider is dead once the bet is placed', lockBad === 0, lockBad ? firstBad : '');
  check('rules: roll stays inside 0.00-99.99', rangeBad === 0,
        rangeBad ? firstBad : `saw ${two(seen.lo)} to ${two(seen.hi)}`);
  check('pay: every threshold and side pays exactly', payBad === 0,
        payBad ? firstBad : `${winsSeen} wins of ${ROUNDS}`);
  check('display: roll formats to two decimals', fmtBad === 0,
        fmtBad ? firstBad : `${leadZero} of them below .10`);
  check('display: readout matches the roll', readBad === 0, readBad ? firstBad : '');
  check('display: the plaque matches the multiplier being paid', multShown === 0,
        multShown ? firstBad : '');
  check('display: needle stands on the roll', markBad === 0, markBad ? firstBad : '');

  const rolls = hist.reduce((a, b) => a + b, 0);
  const exp = rolls / BUCKETS;
  const chi = hist.reduce((a, o) => a + (o - exp) * (o - exp) / exp, 0);
  check('spread: the roll covers the rail evenly', chi < 25,
        `buckets ${hist.join('/')} over ${rolls} rolls, chi2 ${chi.toFixed(1)}`);

  // the side selector is a real control too
  await until(settled, 'settle before side');
  setv('dcSide', 2); await sleep(60);
  click(sideSel); await sleep(120);
  check('controls: the side selector cycles and wraps', num('dcSide') === 1,
        'side ' + num('dcSide'));

  vm.stopAll();
  console.log('\n================ DICE ================');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
