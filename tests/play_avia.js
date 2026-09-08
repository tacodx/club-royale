// Aviamasters: flies the plane headlessly and checks every landing and payout
// against an independent implementation of the crash rules.
//
// The landing point is drawn once at take-off, so it can be verified exactly
// rather than statistically: given the draw the VM made (avU), the plane must
// ditch at HOUSE * PREC / avU, rounded to two places. The climb must follow
// GROWTH^tick. Cash-outs must pay round(bet * the multiplier at the click).
//
//   node tests/play_avia.js <sb3> [rounds]
const fs = require('fs'), VM = require('scratch-vm');
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
// A round is only over once the settlement message has cleared. Waiting on
// `busy` alone races the gap between the climb loop exiting and busy being
// raised, and clicks into that gap are silently dropped.
const settled = () => num('roundOn') === 0 && num('busy') === 0 && num('msgId') === 1;

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

// ---------------------------------------------------------------- the rules
// must match src/tables4.py
const HOUSE = 0.96, PREC = 10000, GROWTH = Math.pow(2, 1 / 84);
const r2 = v => Math.round(v * 100) / 100;
const landFor = u => r2(HOUSE * PREC / u);
const multAtTick = t => r2(Math.pow(10, t * Math.log10(GROWTH)));
// The multiplier is discrete, so a target is really "the first tick at or above
// it". The plane keeps flying only while tick < land, so a target is reachable
// only if that tick is strictly below the landing point - cashing out at the
// exact multiplier it ditches on is a loss, not a win.
function firstTickAtOrAbove(target) {
  for (let t = 1; t <= 3000; t++) { const m = multAtTick(t); if (m >= target) return m; }
  return Infinity;
}

function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      return i <= 10 ? String(i - 1)
        : (i === 11 ? '.' : (i === 12 ? ',' : (i === 14 ? 'x' : ''))); })
    .join('');
}

async function bootSettle(cap = 6000) {
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
  const ROUNDS = Number(process.argv[3] || 24);
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await bootSettle();

  check('boot: 8 lobby tiles', cl('MenuTile').length === 8, 'got ' + cl('MenuTile').length);
  check('boot: 3 ships', cl('AvShip').length === 3, 'got ' + cl('AvShip').length);
  const big = cl('Digit').filter(t => Number(lv(t, 'dField')) === 9).length;
  // 8 slots: "9600.00x" is the widest the readout can ever get
  check('boot: 8-slot crash readout', big === 8, 'got ' + big);
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  check('boot: clone budget under 300', clones < 300, clones + ' clones');

  const auto = gls('avAutoVals');
  check('table: auto targets', JSON.stringify(auto) === JSON.stringify([0, 1.5, 2, 5, 10]),
        JSON.stringify(auto));

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(8));
  await until(() => num('screen') === 8, 'nav avia');
  check('nav: aviamasters', num('screen') === 8, 'screen ' + num('screen'));
  check('idle: readout shows a ready 1x', num('mult') === 1, 'mult ' + num('mult'));

  const act = sp('ActionBtn'), cash = sp('CashoutBtn'), plane = sp('Plane');
  setv('chips', 100000000);
  setv('bet', 100);
  setv('avAuto', 1);                       // manual first

  let landBad = 0, climbBad = 0, payBad = 0, ditchBad = 0, firstBad = '';
  let cashes = 0, ditches = 0, planeMoved = 0, readoutBad = 0;
  let highest = 0, lowest = Infinity;

  for (let r = 0; r < ROUNDS; r++) {
    await until(settled, 'settle ' + r);
    const bet = num('bet'), before = num('chips');
    const bailAt = [1.2, 1.5, 2, 3, 6][r % 5];   // vary where we try to bail

    const x0 = plane.x;
    click(act);
    await until(() => num('roundOn') === 1 || num('busy') === 1 || num('chips') !== before,
                'takeoff ' + r);

    const u = num('avU'), land = num('avLand');
    if (land !== landFor(u)) {
      landBad++;
      firstBad = firstBad || `round ${r}: land ${land}, expected ${landFor(u)} for u=${u}`;
    }
    highest = Math.max(highest, land); lowest = Math.min(lowest, land);
    if (num('chips') !== before - bet) {
      payBad++;
      firstBad = firstBad || `round ${r}: stake ${before - num('chips')}, expected ${bet}`;
    }

    // fly it, bailing out if we get the chance
    let didCash = false, lastMult = 0, guard = 0;
    while (num('roundOn') === 1 && guard++ < 4000) {
      const m = num('mult'), t = num('avTick');
      if (m > 0 && t > 0 && Math.abs(m - multAtTick(t)) > 0.011 && m !== land) {
        climbBad++;
        firstBad = firstBad || `round ${r}: mult ${m} at tick ${t}, expected ${multAtTick(t)}`;
        break;
      }
      if (m < lastMult - 1e-9) {
        climbBad++;
        firstBad = firstBad || `round ${r}: multiplier went backwards ${lastMult} -> ${m}`;
        break;
      }
      lastMult = m;
      if (!didCash && m >= bailAt) {
        const pre = num('chips');
        click(cash);
        await sleep(24);
        if (num('avCashed') === 1) {
          didCash = true; cashes++;
          const at = num('avAt'), want = Math.round(bet * at);
          const got = num('chips') - pre;
          if (got !== want) {
            payBad++;
            firstBad = firstBad || `round ${r}: cash at ${at} paid ${got}, expected ${want}`;
          }
          if (at >= land) {
            payBad++;
            firstBad = firstBad || `round ${r}: cashed at ${at} but it lands at ${land}`;
          }
        }
        break;
      }
      await sleep(12);
    }

    if (!didCash) {
      // it ditched: the stake is gone and nothing comes back
      await until(() => num('roundOn') === 0, 'ditch ' + r);
      ditches++;
      await until(settled, 'settle after ditch ' + r);
      if (num('chips') !== before - bet) {
        ditchBad++;
        firstBad = firstBad || `round ${r}: ditch returned ${num('chips') - (before - bet)}`;
      }
    }
    await until(settled, 'settle end ' + r);
    if (Math.abs(plane.x - x0) > 1 || plane.x !== x0) planeMoved++;
  }

  check(`crash: ${ROUNDS} landing points match the formula`, landBad === 0,
        landBad ? firstBad : `${ROUNDS} exact, range ${lowest}x..${highest}x`);
  check('climb: multiplier follows GROWTH^tick', climbBad === 0,
        climbBad ? firstBad : 'monotonic and exact');
  check('cash: pays round(bet x multiplier)', payBad === 0,
        payBad ? firstBad : `${cashes} cash-outs`);
  check('ditch: pays nothing', ditchBad === 0, `${ditches} ditches, ${ditchBad} bad`);
  check('play: both endings occurred', cashes > 0 && ditches > 0,
        `${cashes} cashed, ${ditches} ditched`);

  // ------------------------------------------------------------ presentation
  // A round can ditch before the plane has moved at all, so keep trying until
  // one actually gets airborne rather than judging the first flight.
  let flyHidden = false, cashShown = false, moved = false, climbTried = 0;
  for (let attempt = 0; attempt < 30 && !moved; attempt++) {
    await until(settled, 'settle before flight checks', 4000);
    click(act);
    await until(() => num('roundOn') === 1 || num('busy') === 1, 'takeoff for ui', 2000);
    if (num('roundOn') !== 1) { await until(settled, 'settle ui skip', 4000); continue; }
    climbTried++;
    // both buttons repaint from forever loops, so give them a frame
    for (let i = 0; i < 40 && (act.visible || !cash.visible); i++) await sleep(12);
    if (!act.visible) flyHidden = true;
    if (cash.visible) cashShown = true;

    const px = plane.x, py = plane.y, t0 = num('avTick');
    for (let i = 0; i < 300 && num('roundOn') === 1 && num('avTick') < t0 + 8; i++) {
      await sleep(10);
    }
    if (plane.x !== px || plane.y !== py) moved = true;

    if (num('roundOn') === 1) {
      let shown = readout(9);
      for (let i = 0; i < 60 && shown !== String(num('mult')) + 'x'; i++) {
        await sleep(12); shown = readout(9);
      }
      if (shown !== String(num('mult')) + 'x') readoutBad++;
      click(cash);
    }
    await until(settled, 'settle after ui', 4000);
  }

  check('ui: FLY hidden in flight', flyHidden, flyHidden ? 'hidden' : 'still shown');
  check('ui: CASH OUT live in flight', cashShown, cashShown ? 'shown' : 'missing');
  check('ui: the plane climbs', moved,
        moved ? `moves with the multiplier (${climbTried} flights)` : 'never moved');
  check('ui: crash readout matches the multiplier', readoutBad === 0, readoutBad + ' faults');

  // -------------------------------------------------- auto cash-out is exact
  let autoBad = 0, autoFired = 0, autoNote = '';
  for (const slot of [2, 3, 4]) {           // 1.5x, 2x, 5x
    setv('avAuto', slot);
    const target = auto[slot - 1];
    for (let r = 0; r < 8; r++) {
      await until(settled, 'settle auto');
      const bet = num('bet'), before = num('chips');
      click(act);
      await until(() => num('roundOn') === 1 || num('chips') !== before, 'auto takeoff');
      const land = num('avLand');
      await until(() => num('roundOn') === 0, 'auto end', 4000);
      await until(settled, 'auto settle', 4000);
      const delta = num('chips') - before;
      const tick = firstTickAtOrAbove(target);
      const shouldFire = tick < land;
      if (shouldFire) {
        if (num('avCashed') !== 1) {
          autoBad++;
          autoNote = autoNote || `target ${target}, land ${land}: never fired (tick ${tick})`;
        } else {
          autoFired++;
          const at = num('avAt');
          // it must fire on exactly the first tick at or above the target -
          // never a frame late, which would silently pay a different number
          if (at !== tick) {
            autoBad++;
            autoNote = autoNote || `target ${target}: fired at ${at}, expected ${tick}`;
          }
          if (delta !== Math.round(bet * at) - bet) {
            autoBad++;
            autoNote = autoNote || `target ${target}: net ${delta}, expected ${Math.round(bet * at) - bet}`;
          }
        }
      } else if (num('avCashed') === 1) {
        autoBad++;
        autoNote = autoNote || `fired at ${num('avAt')} though it ditched at ${land}`;
      }
    }
  }
  check('auto: fires at or above the target and pays exactly', autoBad === 0,
        autoBad ? autoNote : `${autoFired} auto cash-outs across 1.5x/2x/5x`);

  vm.stopAll();
  console.log('\n================ AVIAMASTERS ================');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
