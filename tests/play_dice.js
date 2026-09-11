// Dice: rolls headlessly and checks every roll, every threshold and every
// payout against an independent implementation of the rules.
//
// The roll is drawn into dcInt as a whole number of hundredths before the
// needle moves, so nothing here is statistical either: UNDER t wins on
// dcInt < t and OVER t wins on dcInt >= 10000 - t, and a win pays exactly
// round(bet * the mode's multiplier). Every mode is played on both sides.
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
const gls = n => stage().lookupVariableByNameAndType(n, 'list').value.map(Number);
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
const HOUSE = 0.96, OUT = T6.diceOutcomes;
const WIN = T6.diceWin, MULT = T6.diceMult;
// side 1 = UNDER, side 2 = OVER; both win on exactly WIN[mode] of the OUT
// outcomes, which is what makes one table serve the pair
const wins = (roll, mode, side) =>
  side === 1 ? roll < WIN[mode - 1] : roll >= OUT - WIN[mode - 1];
const shownRoll = r => `${Math.floor(r / 100)}.${String(r % 100).padStart(2, '0')}`;
const markX = r => G.railX0 + (G.railX1 - G.railX0) * r / OUT;

function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      return i <= 10 ? String(i - 1)
        : (i === 11 ? '.' : (i === 12 ? ',' : (i === 14 ? 'x' : ''))); })
    .join('');
}
// forever-driven sprites repaint a frame behind (CLAUDE.md)
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
  check('boot: a track costume per mode and side',
        sp('DiceTrack').getCostumes().length === WIN.length * 2,
        'got ' + sp('DiceTrack').getCostumes().length);

  // ------------------------------------------------ the table itself
  check('table: thresholds', JSON.stringify(gls('diceWin')) === JSON.stringify(WIN),
        JSON.stringify(gls('diceWin')));
  check('table: multipliers', JSON.stringify(gls('diceMult')) === JSON.stringify(MULT),
        JSON.stringify(gls('diceMult')));
  let edgeBad = '';
  for (let m = 0; m < WIN.length; m++) {
    // exact in integer arithmetic: outcomes x payout-in-hundredths
    if (WIN[m] * Math.round(MULT[m] * 100) !== OUT * Math.round(HOUSE * 100)) {
      edgeBad = edgeBad || `mode ${m + 1}: ${WIN[m]}/${OUT} x ${MULT[m]}`;
    }
  }
  check('table: every mode returns exactly 0.96', edgeBad === '', edgeBad);

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(11));
  await until(() => num('screen') === 11, 'nav dice');
  check('nav: dice', num('screen') === 11, 'screen ' + num('screen'));

  const act = sp('ActionBtn'), mark = sp('DiceMark'), track = sp('DiceTrack');
  setv('chips', 100000000);
  setv('bet', 100);
  await sleep(120);
  check('idle: needle hidden before the first roll', mark.visible === false);

  let wonBad = 0, payBad = 0, stakeBad = 0, fmtBad = 0, readBad = 0,
      markBad = 0, trackBad = 0, rangeBad = 0, firstBad = '';
  const fail = m => { firstBad = firstBad || m; };
  const seen = { lo: OUT, hi: -1 };
  const perMode = WIN.map(() => ({ n: 0, w: 0 }));
  const BUCKETS = 5;
  const hist = new Array(BUCKETS).fill(0);
  let leadZero = 0;                       // rolls whose fraction is below .10

  for (let r = 0; r < ROUNDS; r++) {
    await until(settled, 'settle ' + r);
    // sweep every mode on both sides rather than sampling one
    const mode = (r % WIN.length) + 1;
    const side = (Math.floor(r / WIN.length) % 2) + 1;
    setv('dcMode', mode); setv('dcSide', side);
    await sleep(24);

    const cost = await stable(() => track.getCostumes()[track.currentCostume].name);
    if (cost !== `t${mode}${side === 1 ? 'u' : 'o'}`) {
      trackBad++;
      fail(`mode ${mode} side ${side}: track shows ${cost}`);
    }

    const bet = num('bet'), before = num('chips');
    click(act);
    await until(() => num('chips') === before - bet, 'stake ' + r);
    if (num('chips') !== before - bet) {
      stakeBad++;
      fail(`round ${r}: stake ${before - num('chips')}, expected ${bet}`);
    }
    await until(() => num('dcRolling') === 0 && num('dcShown') === 1, 'roll ' + r);

    const roll = num('dcInt');
    if (!(Number.isInteger(roll) && roll >= 0 && roll < OUT)) {
      rangeBad++;
      fail(`round ${r}: roll ${roll} outside 0..${OUT - 1}`);
    }
    seen.lo = Math.min(seen.lo, roll); seen.hi = Math.max(seen.hi, roll);

    const want = wins(roll, mode, side);
    if ((num('dcWon') === 1) !== want) {
      wonBad++;
      fail(`round ${r}: roll ${roll} mode ${mode} side ${side} -> ${num('dcWon')}, expected ${want ? 1 : 0}`);
    }
    perMode[mode - 1].n++;
    if (want) perMode[mode - 1].w++;
    hist[Math.floor(roll * BUCKETS / OUT)]++;
    if (roll % 100 < 10) leadZero++;

    if (gv('dcTxt') !== shownRoll(roll)) {
      fmtBad++;
      fail(`round ${r}: roll ${roll} formatted "${gv('dcTxt')}", expected "${shownRoll(roll)}"`);
    }
    const shown = await stable(() => readout(9));
    if (shown !== shownRoll(roll)) {
      readBad++;
      fail(`round ${r}: roll ${roll} but the readout says "${shown}"`);
    }
    // the needle has to be standing on the number that was paid
    const mx = await stable(() => mark.x);
    if (!mark.visible || Math.abs(mx - markX(roll)) > 0.6) {
      markBad++;
      fail(`round ${r}: roll ${roll} needle at x=${mx}, expected ${markX(roll).toFixed(2)}`);
    }

    await until(settled, 'settle after ' + r);
    const got = num('chips') - (before - bet);
    const wantPay = want ? Math.round(bet * MULT[mode - 1]) : 0;
    if (got !== wantPay) {
      payBad++;
      fail(`round ${r}: roll ${roll} mode ${mode} side ${side} paid ${got}, expected ${wantPay}`);
    }
  }

  // A fraction below .10 has to keep its leading zero or 73.04 renders as
  // 73.4 - the bankroll shipped that class of bug for eight versions. Random
  // rounds hit it nine times in ten, but "usually" is not a test, so keep
  // rolling until the game's own formatter has actually been through it.
  for (let extra = 0; leadZero === 0 && extra < 60; extra++) {
    await until(settled, 'settle pad ' + extra);
    const before = num('chips'), bet = num('bet');
    click(act);
    await until(() => num('chips') === before - bet, 'pad stake');
    await until(() => num('dcRolling') === 0 && num('dcShown') === 1, 'pad roll');
    const roll = num('dcInt');
    hist[Math.floor(roll * BUCKETS / OUT)]++;
    if (roll % 100 < 10) leadZero++;
    if (gv('dcTxt') !== shownRoll(roll)) {
      fmtBad++;
      fail(`pad: roll ${roll} formatted "${gv('dcTxt')}", expected "${shownRoll(roll)}"`);
    }
    await until(settled, 'settle after pad');
  }

  check('rules: win test matches the threshold', wonBad === 0, wonBad ? firstBad : ROUNDS + ' rolls');
  check('rules: stake taken once per roll', stakeBad === 0, stakeBad ? firstBad : '');
  check('rules: roll stays inside 0.00-99.99', rangeBad === 0,
        rangeBad ? firstBad : `saw ${shownRoll(seen.lo)} to ${shownRoll(seen.hi)}`);
  check('pay: every mode and side pays exactly', payBad === 0, payBad ? firstBad : '');
  check('display: roll formats to two decimals', fmtBad === 0,
        fmtBad ? firstBad : `${leadZero} of them below .10`);
  check('display: readout matches the roll', readBad === 0, readBad ? firstBad : '');
  check('display: needle stands on the roll', markBad === 0, markBad ? firstBad : '');
  check('display: track shows the chosen mode and side', trackBad === 0, trackBad ? firstBad : '');

  // Per-round correctness is proved above; what is left is that the draw
  // covers the rail evenly. A truncated or skewed range (rand(1,100) scaled,
  // say) would pile the rolls into some buckets and empty others. Deliberately
  // loose - 4 degrees of freedom, and the 99.9% point is 18.5 (PITFALLS 12).
  const rolls = hist.reduce((a, b) => a + b, 0);
  const exp = rolls / BUCKETS;
  const chi = hist.reduce((a, o) => a + (o - exp) * (o - exp) / exp, 0);
  check('spread: the roll covers the rail evenly', chi < 25,
        `buckets ${hist.join('/')} over ${rolls} rolls, chi2 ${chi.toFixed(1)}`);
  const rates = perMode.map((p, i) => `${(100 * WIN[i] / OUT).toFixed(2)}%:${p.w}/${p.n}`);
  check('spread: every mode and side was played',
        perMode.every(p => p.n > 0), rates.join('  '));

  // --------------------------------------- the readout across the whole rail
  // Not the formatter (the rounds above exercise that one): this drives the
  // digit field and the needle to both ends of the rail and to the two
  // thresholds, which random rolls will not land on exactly.
  await until(settled, 'settle before edges');
  let edgeFmt = '';
  for (const v of [0, 5, 50, 900, 1000, 1005, 9999, 4800, 192]) {
    setv('dcInt', v); setv('dcShown', 1);
    // re-run the formatter the way the game does
    setv('dcTxt', shownRoll(v));
    const want = shownRoll(v);
    const got = await stable(() => readout(9));
    if (got !== want) edgeFmt = edgeFmt || `${v} -> "${got}", expected "${want}"`;
    const mx = await stable(() => mark.x);
    if (Math.abs(mx - markX(v)) > 0.6) {
      edgeFmt = edgeFmt || `${v} -> needle ${mx}, expected ${markX(v).toFixed(2)}`;
    }
  }
  check('edges: readout and needle across the whole rail', edgeFmt === '',
        edgeFmt || '0.00 through 99.99');

  // the selectors are what a player actually has; drive them by clicking
  await until(settled, 'settle before selectors');
  const chance = sp('ChanceSel'), sideSel = sp('SideSel');
  setv('dcMode', WIN.length); setv('dcSide', 2);
  await sleep(40);
  click(chance); await sleep(60);
  click(sideSel); await sleep(60);
  check('controls: the selectors cycle and wrap',
        num('dcMode') === 1 && num('dcSide') === 1,
        `mode ${num('dcMode')} side ${num('dcSide')}`);
  const wrapped = await stable(() => track.getCostumes()[track.currentCostume].name);
  check('controls: the track follows the selectors', wrapped === 't1u', wrapped);

  vm.stopAll();
  console.log('\n================ DICE ================');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
