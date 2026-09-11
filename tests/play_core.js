const fs = require('fs'), VM = require('scratch-vm');
const path=require('path');
const TBLDIR=path.join(__dirname,'..','build');
const T = JSON.parse(fs.readFileSync(path.join(TBLDIR,'tables.json')));
const vm = new VM();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const FRAME = 34;

const stage = () => vm.runtime.getTargetForStage();
const gv = n => { const s = stage();
  for (const id in s.variables) if (s.variables[id].name === n) return s.variables[id].value;
  throw new Error('no var ' + n); };
const setv = (n, v) => { stage().lookupVariableByNameAndType(n).value = v; };
const gls = n => stage().lookupVariableByNameAndType(n, 'list').value.map(Number);
const sp = n => vm.runtime.targets.find(t => !t.isStage && t.sprite.name === n && t.isOriginal);
const cl = n => vm.runtime.targets.filter(t => !t.isStage && t.sprite.name === n && !t.isOriginal);
const lv = (t, n) => { for (const id in t.variables) if (t.variables[id].name === n) return t.variables[id].value; };
const click = t => vm.runtime.startHats('event_whenthisspriteclicked', null, t);
async function until(p, l, m = 600) { for (let i = 0; i < m; i++) { if (p()) return; await sleep(FRAME); } throw new Error('timeout ' + l); }

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

const ROWC = [8, 12, 16], RISK = ['low', 'med', 'high'], BOMBC = [1, 3, 5, 10];
const BET = [5,10,15,20,25,50,75,100,150,200,250,500,750,1000,1500,2000,2500,5000];

// reconstruct what the digit sprites are actually showing
function readout(field) {
  const parts = cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')));
  return parts.map(t => {
    const nm = t.getCostumes()[t.currentCostume].name;   // d1..d16
    const i = Number(nm.slice(1));
    const GLYPH = { 11: '.', 12: ',', 13: '', 14: 'x', 15: 'M', 16: 'B' };
    return i <= 10 ? String(i - 1) : (GLYPH[i] !== undefined ? GLYPH[i] : '?');
  }).join('');
}

// Clone spawn loops in `when flag clicked` run one clone per frame (PITFALLS 5),
// so the full set is not present for the better part of a second. Wait for the
// count to stop growing rather than guessing a sleep - a fixed 600ms silently
// under-counted once Duck Road added per-frame work.
async function bootSettle(vm, sleep, cap = 6000) {
  const total = () => vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  let last = -1, stable = 0, waited = 0;
  while (waited < cap) {
    await sleep(50); waited += 50;
    const n = total();
    stable = (n === last && n > 0) ? stable + 1 : 0;
    last = n;
    if (stable >= 3) return n;
  }
  return last;
}

(async () => {
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await bootSettle(vm, sleep);

  // ------------------------------------------------ boot
  check('boot: chips 1000', Number(gv('chips')) === 1000);
  check('boot: bet 50', Number(gv('bet')) === 50);
  check('boot: clone counts',
    cl('MenuTile').length === sp('MenuTile').getCostumes().length &&
    cl('Reel').length === 3 &&
    cl('MineTile').length === 25 && cl('Card').length === 18 &&
    cl('Digit').length === 40 && cl('Bucket').length === 17,
    `menu ${cl('MenuTile').length} reel ${cl('Reel').length} mine ${cl('MineTile').length} card ${cl('Card').length} digit ${cl('Digit').length} bucket ${cl('Bucket').length}`);
  check('digits: chips readout matches', readout(1) === '1,000', 'showing ' + readout(1));

  // The bankroll used to render by character index into 7 slots, so anything
  // over 9,999,999 silently lost its tail: 12,582,900 displayed as "1258290",
  // a plausible figure ten times too small. It is formatted now, and must
  // never exceed the 7 slots that exist.
  const fmt = n => n < 1000 ? String(n)
    : n < 1e6 ? Math.floor(n / 1000) + ',' + String(n % 1000).padStart(3, '0')
    : n < 1e9 ? String(Math.round(n / 1e4) / 100) + 'M'
    : String(Math.round(n / 1e7) / 100) + 'B';
  let wide = 0, wrong = 0, firstWrong = '';
  for (const v of [7, 999, 1000, 1005, 1050, 12450, 999999,
                   1000000, 1234567, 12582900, 99999999, 999999999,
                   1000000000, 1258290000, 15690050000]) {
    setv('chips', v);
    let shown = readout(1);
    for (let i = 0; i < 40 && shown !== fmt(v); i++) { await sleep(12); shown = readout(1); }
    if (shown !== fmt(v)) { wrong++; firstWrong = firstWrong || `${v} -> "${shown}", expected "${fmt(v)}"`; }
    if (shown.length > 7) wide++;
  }
  check('digits: bankroll never truncates', wrong === 0, wrong ? firstWrong : '15 magnitudes exact');
  check('digits: bankroll fits its 7 slots', wide === 0, wide + ' too wide');
  setv('chips', 1000);
  await sleep(60);

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  const act = sp('ActionBtn'), back = sp('BackBtn');

  // ------------------------------------------------ bet ladder
  click(tile(1)); await sleep(250);
  setv('chips', 100000);
  await sleep(120);
  check('digits: bet readout matches', readout(2) === String(gv('bet')),
        'showing ' + readout(2) + ' vs ' + gv('bet'));

  // hold-to-repeat: press and hold the + button
  const plus = sp('BetPlus'), minus = sp('BetMinus');
  // headless has no renderer, so stub only the mouse hit-test primitive
  let heldName = null;
  const RT = Object.getPrototypeOf(plus);
  const origTouch = RT.isTouchingObject;
  RT.isTouchingObject = function (o) {
    if (o === '_mouse_') return heldName !== null && this.sprite.name === heldName;
    return origTouch.call(this, o);
  };
  const holdOn = t => { heldName = t.sprite.name;
    vm.runtime.ioDevices.mouse._isDown = true; };
  const holdOff = () => { heldName = null;
    vm.runtime.ioDevices.mouse._isDown = false; };

  const beforeHold = Number(gv('betIdx'));
  holdOn(plus); await sleep(1500); holdOff(); await sleep(200);
  check('bet: hold ramps up', Number(gv('betIdx')) > beforeHold + 3,
        `${beforeHold} -> ${gv('betIdx')}`);
  holdOn(plus); await sleep(3000); holdOff(); await sleep(200);
  check('bet: clamps at top', Number(gv('bet')) === 5000, 'got ' + gv('bet'));
  holdOn(minus); await sleep(4000); holdOff(); await sleep(200);
  check('bet: clamps at bottom', Number(gv('bet')) === 5, 'got ' + gv('bet'));

  // affordability guard
  setv('chips', 60); await sleep(150);
  holdOn(plus); await sleep(2000); holdOff(); await sleep(200);
  check('bet: cannot exceed chips', Number(gv('bet')) <= 60, 'bet ' + gv('bet') + ' chips ' + gv('chips'));
  setv('chips', 1000000);

  // ------------------------------------------------ slots still exact
  click(back); await sleep(200); click(tile(1)); await sleep(250);
  const slotExp = (r, b) => { const [a, x, c] = r;
    if (a === x && x === c) return a === 1 ? b * 50 : b * 12;
    if (a === x || x === c || a === c)
      return ((a === x && a === 1) || (x === c && x === 1) || (a === c && a === 1))
        ? b * 4 : Math.round(b * 1.8);
    return 0; };
  let sbad = 0;
  const NSLOT=Number(process.argv[3]||90);
  for (let i = 0; i < NSLOT; i++) {
    setv('chips', 100000); const b = Number(gv('bet'));
    click(act); await sleep(150);
    await until(() => Number(gv('busy')) === 0, 'spin', 300); await sleep(30);
    const got = gv('chips') - 100000 + b;
    if (got !== slotExp(gls('reelResult'), b)) sbad++;
  }
  check('slots: '+NSLOT+' spins exact', sbad === 0, sbad + ' mismatches');

  // ------------------------------------------------ PLINKO all 9 tables
  click(back); await sleep(200); click(tile(2)); await sleep(300);
  check('nav: plinko', Number(gv('screen')) === 2);

  const rowsSel = sp('RowsSel'), riskSel = sp('RiskSel');
  const setSel = async (spr, v, name) => {
    for (let i = 0; i < 6 && Number(gv(name)) !== v; i++) { click(spr); await sleep(160); }
    return Number(gv(name)) === v; };

  let pbad = 0, pboundsBad = 0, tablesRun = 0, totalBalls = 0;
  const seenBuckets = {};
  for (let ri = 1; ri <= 3; ri++) {
    for (let ki = 1; ki <= 3; ki++) {
      if (!await setSel(rowsSel, ri, 'rowsIdx')) { check('sel rows ' + ri, false); continue; }
      if (!await setSel(riskSel, ki, 'riskIdx')) { check('sel risk ' + ki, false); continue; }
      await sleep(150);
      const rows = ROWC[ri - 1];
      const tab = T.plinko[`${rows}_${RISK[ki - 1]}`];
      tablesRun++;
      const NBALL=Number(process.argv[4]||16);
      for (let n = 0; n < NBALL; n++) {
        setv('chips', 100000);
        const b = Number(gv('bet'));
        click(act);
        await until(() => Number(gv('ballsUp')) >= 1, 'ball spawn', 120);
        await until(() => Number(gv('ballsUp')) === 0, 'ball land', 600);
        await sleep(40);
        const bk = Number(gv('lastBucket'));
        totalBalls++;
        seenBuckets[rows] = seenBuckets[rows] || new Set();
        seenBuckets[rows].add(bk);
        if (bk < 1 || bk > rows + 1) { pboundsBad++; continue; }
        const exp = Math.round(b * tab[bk - 1]);
        const got = gv('chips') - 100000 + b;
        if (got !== exp) { pbad++;
          if (pbad < 5) console.log(`  MISMATCH ${rows}/${RISK[ki-1]} bucket ${bk} got ${got} exp ${exp}`); }
      }
    }
  }
  check('plinko: all 9 tables run', tablesRun === 9, tablesRun + '/9');
  check('plinko: bucket index in range', pboundsBad === 0, pboundsBad + ' out of range');
  check('plinko: ' + totalBalls + ' drops exact', pbad === 0, pbad + ' mismatches');
  check('plinko: bucket counts match rows',
    [8, 12, 16].every(r => !seenBuckets[r] || Math.max(...seenBuckets[r]) <= r + 1),
    JSON.stringify(Object.fromEntries(Object.entries(seenBuckets)
      .map(([k, v]) => [k, `${Math.min(...v)}..${Math.max(...v)}`]))));

  // ------------------------------------------------ multi-ball
  await setSel(rowsSel, 2, 'rowsIdx'); await setSel(riskSel, 2, 'riskIdx');
  await sleep(150);
  setv('chips', 100000);
  const K = 10, b0 = Number(gv('bet'));
  let peak = 0;
  for (let i = 0; i < K; i++) { click(act); await sleep(45);
    peak = Math.max(peak, Number(gv('ballsUp'))); }
  await until(() => Number(gv('ballsUp')) === 0, 'all balls land', 900);
  await sleep(100);
  check('plinko: balls fly concurrently', peak >= 4, 'peak ' + peak + ' concurrent');
  const net = gv('chips') - 100000;
  check('plinko: multi-ball accounting sane', net >= -K * b0 && net <= K * b0 * 400,
        'net ' + net + ' over ' + K + ' balls');
  check('plinko: ballsUp returns to zero', Number(gv('ballsUp')) === 0);

  // ------------------------------------------------ MINES all 4 counts
  click(back); await sleep(220); click(tile(3)); await sleep(300);
  const bombSel = sp('BombsSel');
  let mbad = 0, mcountBad = 0;
  for (let bi = 1; bi <= 4; bi++) {
    if (!await setSel(bombSel, bi, 'bombsIdx')) { check('sel bombs ' + bi, false); continue; }
    setv('chips', 100000);
    click(act);
    await until(() => Number(gv('roundOn')) === 1, 'mines start');
    await sleep(80);
    const bl = gls('bombs');
    if (bl.length !== BOMBC[bi - 1] || new Set(bl).size !== bl.length) mcountBad++;
    const tab = T.mines[String(BOMBC[bi - 1])];
    const safe = [];
    for (let i = 1; i <= 25 && safe.length < 3; i++) if (!bl.includes(i)) safe.push(i);
    for (let k = 0; k < safe.length; k++) {
      click(cl('MineTile').find(t => Number(lv(t, 'tIdx')) === safe[k]));
      await sleep(140);
      if (Math.abs(Number(gv('mult')) - tab[k]) > 1e-6) { mbad++;
        console.log(`  MINES MISMATCH ${BOMBC[bi-1]} bombs pick ${k+1}: ${gv('mult')} vs ${tab[k]}`); }
    }
    const pre = gv('chips'), m = Number(gv('mult')), bb = Number(gv('bet'));
    click(sp('CashoutBtn'));
    await until(() => Number(gv('roundOn')) === 0, 'cashout');
    await sleep(150);
    if (gv('chips') !== pre + Math.round(bb * m)) mbad++;
    await until(() => Number(gv('busy')) === 0, 'idle', 300);
  }
  check('mines: bomb counts correct', mcountBad === 0, mcountBad + ' wrong');
  check('mines: multipliers + cashout exact across 4 tables', mbad === 0, mbad + ' mismatches');

  // bomb path with 10 bombs
  await setSel(bombSel, 4, 'bombsIdx');
  setv('chips', 100000); click(act);
  await until(() => Number(gv('roundOn')) === 1, 'start2'); await sleep(80);
  const b2 = gls('bombs'); const preBoom = gv('chips');
  click(cl('MineTile').find(t => Number(lv(t, 'tIdx')) === b2[0]));
  await until(() => Number(gv('roundOn')) === 0, 'boom'); await sleep(900);
  const rev = gls('revealed');
  check('mines: boom pays nothing', gv('chips') === preBoom);
  check('mines: all 10 bombs revealed', b2.every(x => rev[x - 1] === 3));
  await until(() => Number(gv('busy')) === 0, 'idle3', 300);

  // ------------------------------------------------ BLACKJACK
  click(back); await sleep(220); click(tile(4)); await sleep(300);
  const rank = c => ((c - 1) % 13) + 1;
  const hv = h => { let s = 0, a = 0;
    for (const c of h) { let v = rank(c); if (v > 10) v = 10; if (v === 1) { a++; v = 11; } s += v; }
    while (s > 21 && a > 0) { s -= 10; a--; } return s; };
  let bjr = 0, valOK = true, dealOK = true, dupOK = true, drawOK = true;
  const NBJ=Number(process.argv[5]||14);
  for (let r = 0; r < NBJ; r++) {
    await until(() => Number(gv('busy')) === 0 && Number(gv('roundOn')) === 0, 'bj idle', 400);
    setv('chips', 100000);
    click(act); await sleep(200);
    await until(() => Number(gv('busy')) === 0 || Number(gv('roundOn')) === 0, 'deal', 400);
    if (Number(gv('bjPhase')) === 1) {              // insurance prompt (v3+)
      click(sp('NoInsBtn'));
      await until(() => Number(gv('bjPhase')) !== 1, 'insurance', 300);
      await until(() => Number(gv('busy')) === 0 ||
                        Number(gv('roundOn')) === 0, 'post-ins', 500);
    }
    if (Number(gv('roundOn')) === 0) { bjr++; continue; }
    if (gls('pHand').length !== 2 || gls('dHand').length !== 1) dealOK = false;
    if (hv(gls('pHand')) !== Number(gv('you'))) valOK = false;
    if (Number(gv('you')) < 12 && Number(gv('bjPhase')) === 2) { click(sp('HitBtn')); await sleep(120);
      await until(() => Number(gv('busy')) === 0, 'hit', 400); await sleep(60); }
    let sg = 0;
    while (Number(gv('bjPhase')) === 2 && sg++ < 4) {   // split needs two stands
      await until(() => Number(gv('busy')) === 0, 'pre-stand', 400);
      if (Number(gv('bjPhase')) !== 2) break;
      click(sp('StandBtn'));
      await sleep(160);
    }
    if (Number(gv('roundOn')) === 1 || sg > 0) {
      await until(() => Number(gv('roundOn')) === 0, 'settle', 700); await sleep(120);
      const all = gls('pHand').concat(gls('dHand'));
      if (new Set(all).size !== all.length) dupOK = false;
      if (hv(gls('pHand')) <= 21 && hv(gls('dHand')) < 17) drawOK = false;
      if (hv(gls('dHand')) !== Number(gv('dealer'))) valOK = false;
    }
    bjr++;
  }
  check('bj: rounds played', bjr >= NBJ - 2, 'got ' + bjr);
  check('bj: deal 2+1', dealOK);
  check('bj: values match', valOK);
  check('bj: no duplicate cards', dupOK);
  check('bj: dealer draws to 17', drawOK);

  // ------------------------------------------------ economy
  // There is no rebuy: broke is broke until the green flag. Nothing may hand
  // the player chips back, and nothing may hang waiting for it to happen.
  click(back); await sleep(250);
  setv('chips', 0);
  await sleep(2600);                     // longer than the old rebuy's 1.6s wait
  check('economy: no rebuy at zero', Number(gv('chips')) === 0,
        'chips ' + gv('chips'));
  // and a game must still refuse the bet rather than paying out of an empty
  // bankroll or wedging
  click(tile(1)); await sleep(300);
  const beforeBroke = Number(gv('chips'));
  click(act); await sleep(900);
  check('economy: broke cannot spin', Number(gv('chips')) === beforeBroke &&
        Number(gv('busy')) === 0, `chips ${gv('chips')} busy ${gv('busy')}`);
  click(back); await sleep(250);

  vm.stopAll();
  console.log('\n================ v1.1 RESULTS ================');
  let f = 0;
  for (const [s, n, e] of R) { if (s === 'FAIL') f++;
    console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`); }
  console.log(`\n${R.length - f}/${R.length} passed`);
  process.exit(f ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.message); process.exit(2); });
