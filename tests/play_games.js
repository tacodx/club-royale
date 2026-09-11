const fs = require('fs'), VM = require('scratch-vm');
const path=require('path');
const TBLDIR=path.join(__dirname,'..','build');
const T2 = JSON.parse(fs.readFileSync(path.join(TBLDIR,'tables2.json')));
const vm = new VM();
const sleep = ms => new Promise(r => setTimeout(r, ms));
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
async function until(p, l, m = 700) { for (let i = 0; i < m; i++) { if (p()) return; await sleep(34); } throw new Error('timeout ' + l); }

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);
const RED = new Set(T2.red);
const DIFFS = T2.diffs;               // [name, tiles, bombs]

// expected roulette return for a stake map {slot: amount} given winning number w
function rouletteExpect(bets, w) {
  let pay = 0;
  const g = i => bets[i] || 0;
  pay += g(w + 1) * 36;                       // straight (slot 1 == number 0)
  if (w > 0) {
    pay += (RED.has(w) ? g(38) : g(39)) * 2;  // red / black
    pay += (w % 2 === 1 ? g(40) : g(41)) * 2; // odd / even
    pay += (w < 19 ? g(42) : g(43)) * 2;      // low / high
    pay += g(43 + Math.floor((w - 1) / 12) + 1) * 3;  // dozen
    pay += g(46 + ((w - 1) % 3) + 1) * 3;             // column
  }
  return pay;
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

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  const act = sp('ActionBtn'), back = sp('BackBtn');
  const spot = i => cl('RSpot').find(t => Number(lv(t, 'sIdx')) === i);

  const games = sp('MenuTile').getCostumes().length;
  check('boot: one lobby tile per game', cl('MenuTile').length === games,
        `${cl('MenuTile').length} tiles, ${games} games`);
  check('boot: 49 roulette spots', cl('RSpot').length === 49, 'got ' + cl('RSpot').length);
  check('boot: 36 stair tiles', cl('StairTile').length === 36, 'got ' + cl('StairTile').length);
  check('boot: 9 stair mult labels', cl('StairMult').length === 9);
  // Runtime.MAX_CLONES is checked against _cloneCounter, which only makeClone()
  // increments - the sprite originals are not part of the budget, so count
  // clones rather than targets (this read 298 of "300" with 65 originals in it).
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  check('boot: clone budget under 300', clones < 300, clones + ' clones');

  // ================================================ ROULETTE
  click(tile(5)); await sleep(300);
  check('nav: roulette', Number(gv('screen')) === 5, 'screen ' + gv('screen'));

  // place / undo / clear
  setv('chips', 100000); await sleep(100);
  const b = Number(gv('bet'));
  click(spot(18)); await sleep(90);          // straight on 17
  click(spot(38)); await sleep(90);          // red
  check('roulette: stake tracks', Number(gv('rStake')) === 2 * b, 'stake ' + gv('rStake'));
  check('roulette: chips debited on place', gv('chips') === 100000 - 2 * b);
  check('roulette: chips appear', cl('RChip').length === 2, cl('RChip').length + ' chips');
  click(sp('UndoBtn')); await sleep(140);
  check('roulette: undo refunds', Number(gv('rStake')) === b && gv('chips') === 100000 - b,
        `stake ${gv('rStake')} chips ${gv('chips')}`);
  check('roulette: undo removes chip', cl('RChip').length === 1, cl('RChip').length);
  click(sp('ClearBtn')); await sleep(160);
  check('roulette: clear refunds all', Number(gv('rStake')) === 0 && gv('chips') === 100000);
  check('roulette: clear removes chips', cl('RChip').length === 0, cl('RChip').length);

  // exact payouts, every bet category on every spin
  const N = Number(process.argv[3] || 90);
  let rbad = 0, zeroSeen = 0, hits = {};
  const plan = { 1: 5, 18: 5, 38: 10, 40: 10, 42: 10, 45: 10, 49: 10 };
  //             0    17   RED    ODD    LOW    2nd12  COL3
  async function spinOnce() {
    setv('chips', 100000); await sleep(40);
    for (const k of Object.keys(plan)) {
      const want = plan[k];
      // set the bet ladder to the exact amount by writing bet directly
      setv('bet', want);
      click(spot(Number(k)));
      await sleep(40);
    }
    const staked = Object.values(plan).reduce((a, c) => a + c, 0);
    const afterPlace = gv('chips');
    if (afterPlace !== 100000 - staked) { rbad++; console.log('  stake mismatch', afterPlace); }
    click(act);
    await until(() => Number(gv('busy')) === 1, 'spin start', 120);
    await until(() => Number(gv('busy')) === 0, 'spin end', 700);
    await sleep(40);
    const w = Number(gv('rNum'));
    if (w === 0) zeroSeen++;
    hits[w] = (hits[w] || 0) + 1;
    const exp = rouletteExpect(plan, w);
    const got = gv('chips') - afterPlace;
    if (got !== exp) { rbad++;
      if (rbad < 6) console.log(`  ROULETTE MISMATCH n=${w} got ${got} exp ${exp}`); }
    if (Number(gv('rStake')) !== 0) { rbad++; console.log('  stake not cleared'); }
    return w;
  }

  for (let n = 0; n < N; n++) await spinOnce();
  // Zero lands once in 37, so a fixed count leaves a ~15% chance of never
  // seeing it and failing a working wheel (PITFALLS 12). Keep spinning until
  // it turns up, the way the blackjack harness exercises its rare paths.
  let extra = 0;
  while (zeroSeen === 0 && extra < 400) { await spinOnce(); extra++; }
  check(`roulette: ${N} spins exact across all bet types`, rbad === 0, rbad + ' mismatches');
  const nums = Object.keys(hits).map(Number);
  check('roulette: numbers within 0..36',
        Math.min(...nums) >= 0 && Math.max(...nums) <= 36,
        `range ${Math.min(...nums)}..${Math.max(...nums)}, ${nums.length} distinct`);
  // The wheel, the pointer and the darkened popup all send themselves to the
  // front on the same broadcast, so which ends up on top depends on handler
  // order. That was harmless while go_layer() was a dead opcode, and became a
  // real bug the moment it started working: the popup swallowed the wheel.
  // scratch-vm keeps executableTargets in lockstep with the renderer's draw
  // list - index 0 is the back, last is the front.
  const zOf = n => vm.runtime.executableTargets.indexOf(sp(n));
  setv('bet', 10);
  click(spot(18)); await sleep(60);
  click(act);
  await until(() => Number(gv('busy')) === 1, 'spin start for z-check', 200);
  let zOk = 0, zBad = 0;
  for (let i = 0; i < 400 && Number(gv('busy')) === 1; i++) {
    const zp = zOf('WheelPanel'), zw = zOf('Wheel');
    if (zp >= 0 && zw >= 0) { if (zw > zp) zOk++; else zBad++; }
    await sleep(8);
  }
  await until(() => Number(gv('busy')) === 0, 'spin end for z-check', 600);
  const zPct = zOk / Math.max(1, zOk + zBad);
  check('roulette: the wheel draws on top of its own popup', zPct > 0.9,
        `wheel above the panel on ${Math.round(zPct * 100)}% of ${zOk + zBad} frames`);

  check('roulette: zero occurred and paid correctly', zeroSeen > 0,
        `${zeroSeen} zeros in ${N + extra} spins` +
        (extra ? ` (${extra} extra to find one)` : ''));

  // ================================================ STAIRS
  click(back); await sleep(250); click(tile(6)); await sleep(300);
  check('nav: stairs', Number(gv('screen')) === 6, 'screen ' + gv('screen'));
  const diffSel = sp('DiffSel');
  const stile = (r, c) => cl('StairTile').find(t =>
    Number(lv(t, 'stR')) === r && Number(lv(t, 'stC')) === c);

  let sbad = 0, bombBad = 0;
  for (let di = 1; di <= 5; di++) {
    for (let i = 0; i < 7 && Number(gv('stDiff')) !== di; i++) { click(diffSel); await sleep(150); }
    if (Number(gv('stDiff')) !== di) { check('stairs: select diff ' + di, false); continue; }
    const [name, tiles, bombs] = DIFFS[di - 1];
    const tab = T2.stairs[name];
    setv('chips', 1000000); setv('bet', 100); await sleep(80);
    click(act);
    await until(() => Number(gv('roundOn')) === 1, 'stairs start');
    await sleep(100);
    const bl = gls('stBomb');
    // every row must have exactly `bombs` bombs, all within `tiles` columns
    for (let r = 1; r <= 9; r++) {
      let cnt = 0;
      for (let c = 1; c <= 4; c++) {
        const v = bl[(r - 1) * 4 + c - 1];
        if (v === 1) { cnt++; if (c > tiles) bombBad++; }
      }
      if (cnt !== bombs) bombBad++;
    }
    // climb 4 rows on safe tiles, checking the multiplier ladder
    for (let r = 1; r <= 4; r++) {
      let safe = 0;
      for (let c = 1; c <= tiles; c++) if (bl[(r - 1) * 4 + c - 1] === 0) { safe = c; break; }
      click(stile(r, safe));
      await sleep(170);
      if (Number(gv('stRow')) !== r + 1) { sbad++; console.log(`  row didn't advance ${name} r${r}`); }
      if (Math.abs(Number(gv('mult')) - tab[r - 1]) > 1e-6) { sbad++;
        console.log(`  STAIRS MISMATCH ${name} row ${r}: ${gv('mult')} vs ${tab[r - 1]}`); }
    }
    const pre = gv('chips'), m = Number(gv('mult')), bb = Number(gv('bet'));
    click(sp('CashoutBtn'));
    await until(() => Number(gv('roundOn')) === 0, 'stairs cashout');
    await sleep(150);
    if (gv('chips') !== pre + Math.round(bb * m)) { sbad++;
      console.log(`  cashout wrong ${name}: ${gv('chips') - pre} vs ${Math.round(bb * m)}`); }
    await until(() => Number(gv('busy')) === 0, 'idle', 400);
  }
  check('stairs: bomb layout correct for all 5 modes', bombBad === 0, bombBad + ' faults');
  check('stairs: multiplier ladder + cashout exact', sbad === 0, sbad + ' mismatches');

  // bomb path
  for (let i = 0; i < 7 && Number(gv('stDiff')) !== 3; i++) { click(diffSel); await sleep(150); }
  setv('chips', 100000); setv('bet', 100); await sleep(80);
  click(act); await until(() => Number(gv('roundOn')) === 1, 'start bomb'); await sleep(100);
  const bl2 = gls('stBomb');
  let bombCol = 0;
  for (let c = 1; c <= 2; c++) if (bl2[c - 1] === 1) bombCol = c;
  const preB = gv('chips');
  click(stile(1, bombCol));
  await until(() => Number(gv('roundOn')) === 0, 'bomb'); await sleep(1000);
  check('stairs: bomb pays nothing', gv('chips') === preB, 'delta ' + (gv('chips') - preB));
  const st = gls('stState');
  check('stairs: bomb tile revealed', st[bombCol - 1] === 2, 'state ' + st[bombCol - 1]);
  await until(() => Number(gv('busy')) === 0, 'idle2', 400);

  // full clear on EASY pays the top multiplier
  for (let i = 0; i < 7 && Number(gv('stDiff')) !== 1; i++) { click(diffSel); await sleep(150); }
  setv('chips', 100000); setv('bet', 100); await sleep(80);
  click(act); await until(() => Number(gv('roundOn')) === 1, 'start clear'); await sleep(100);
  const bl3 = gls('stBomb'); const preC = gv('chips');
  for (let r = 1; r <= 9; r++) {
    let safe = 0;
    for (let c = 1; c <= 4; c++) if (bl3[(r - 1) * 4 + c - 1] === 0) { safe = c; break; }
    click(stile(r, safe)); await sleep(170);
  }
  await until(() => Number(gv('roundOn')) === 0, 'auto cashout', 400);
  await sleep(300);
  const top = T2.stairs.EASY[8];
  check('stairs: clearing 9 rows pays top multiplier',
        gv('chips') === preC + Math.round(100 * top),
        `delta ${gv('chips') - preC} vs ${Math.round(100 * top)} (${top}x)`);

  vm.stopAll();
  console.log('\n================ v2 RESULTS ================');
  let f = 0;
  for (const [s, n, e] of R) { if (s === 'FAIL') f++;
    console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`); }
  console.log(`\n${R.length - f}/${R.length} passed`);
  process.exit(f ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.message); process.exit(2); });
