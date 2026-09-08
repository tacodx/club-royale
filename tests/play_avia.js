// Aviamasters: flies the route headlessly and checks every orb, every ditch
// and every payout against an independent implementation of the rules.
//
// The whole flight is reconstructible. `amLog` records the orb taken at each
// slot, so the harness can replay the round from 1x - applying each orb's
// affine map, rounding to 2dp and clamping at the cap exactly as the runtime
// does - and demand that the figure paid matches to the penny. Nothing here is
// statistical except the draw frequencies, which are checked against the
// published weights.
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
async function until(p, l, m = 2000) {
  for (let i = 0; i < m; i++) { if (p()) return true; await sleep(12); }
  throw new Error('timeout ' + l);
}
const settled = () => num('roundOn') === 0 && num('busy') === 0 && num('msgId') === 1;

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

// ---------------------------------------------------------------- the rules
// must match src/tables5.py
const HOUSE = 0.96, SLOTS = 14, CAP = 250, PREC = 1000;
const ORBS = [                       // name, weight, a, b   -- v -> a*v + b
  ['EMPTY',  14, 1.0, 0.0],
  ['PLUS05', 24, 1.0, 0.5],
  ['PLUS1',   8, 1.0, 1.0],
  ['MUL2',   13, 2.0, 0.0],
  ['MUL3',    4, 3.0, 0.0],
  ['ROCKET', 37, 0.5, 0.0],
];
const TOTW = ORBS.reduce((s, o) => s + o[1], 0);
const r2 = v => Math.round(v * 100) / 100;
const applyOrb = (v, i) => Math.min(CAP, r2(ORBS[i - 1][2] * v + ORBS[i - 1][3]));
// replay a logged flight from the launch value of 1x
const replay = log => log.reduce((v, i) => applyOrb(v, i), 1);

// the exact value distribution after each slot, ignoring the ditch - the same
// walk tables5.py does, redone here so the shipped ramp is checked against a
// second implementation rather than against itself
function solve() {
  let row = new Map([[1, 1]]);
  const EV = [1];
  for (let k = 0; k < SLOTS; k++) {
    const nxt = new Map();
    for (const [v, pv] of row) for (let i = 1; i <= ORBS.length; i++) {
      const nv = applyOrb(v, i), w = pv * (ORBS[i - 1][1] / TOTW);
      nxt.set(nv, (nxt.get(nv) || 0) + w);
    }
    row = nxt;
    let ev = 0; for (const [v, pv] of row) ev += v * pv;
    EV.push(ev);
  }
  const alive = [1];
  for (let k = 1; k <= SLOTS; k++) alive.push(HOUSE / EV[k]);
  const ramp = [];
  for (let k = 1; k <= SLOTS; k++) ramp.push(Math.round((1 - alive[k] / alive[k - 1]) * PREC));
  const shipped = [1];
  for (const r of ramp) shipped.push(shipped[shipped.length - 1] * (1 - r / PREC));
  return { EV, ramp, shipped, final: row };
}
const SOLVED = solve();

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
  const ROUNDS = Number(process.argv[3] || 120);
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await bootSettle();

  // ------------------------------------------------------------------- boot
  const games = sp('MenuTile').getCostumes().length;
  check('boot: one lobby tile per game', cl('MenuTile').length === games,
        `${cl('MenuTile').length} tiles, ${games} games`);
  check('boot: 5 drifting orbs', cl('AvOrb').length === 5, 'got ' + cl('AvOrb').length);
  const big = cl('Digit').filter(t => Number(lv(t, 'dField')) === 9).length;
  check('boot: 8-slot multiplier readout', big === 8, 'got ' + big);
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  check('boot: clone budget under 300', clones < 300, clones + ' clones');

  // ----------------------------------------------------- the shipped tables
  const ramp = gls('amRamp'), cum = gls('amCum'), aList = gls('amA'), bList = gls('amB');
  check('table: ditch ramp matches an independent solve',
        JSON.stringify(ramp) === JSON.stringify(SOLVED.ramp),
        JSON.stringify(ramp) + ' vs ' + JSON.stringify(SOLVED.ramp));
  let acc = 0; const wantCum = ORBS.map(o => (acc += o[1]));
  check('table: orb weights', JSON.stringify(cum) === JSON.stringify(wantCum),
        JSON.stringify(cum));
  check('table: orb maps', JSON.stringify(aList) === JSON.stringify(ORBS.map(o => o[2]))
        && JSON.stringify(bList) === JSON.stringify(ORBS.map(o => o[3])),
        JSON.stringify(aList) + ' / ' + JSON.stringify(bList));
  // every cash-out point has to be worth the same, or there is a strategy
  let evBad = 0, evNote = '';
  for (let k = 1; k <= SLOTS; k++) {
    const ev = SOLVED.shipped[k] * SOLVED.EV[k];
    if (Math.abs(ev - HOUSE) > 0.01) { evBad++; evNote = evNote || `slot ${k}: EV ${ev.toFixed(4)}`; }
  }
  check('table: every cash-out point returns the house 0.96', evBad === 0,
        evBad ? evNote : `${SLOTS} slots, all ${HOUSE}`);
  check('table: enough flights land to be a game',
        SOLVED.shipped[SLOTS] > 0.15, (SOLVED.shipped[SLOTS] * 100).toFixed(1) + '% land');

  // ------------------------------------------------------------------- play
  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(9));
  await until(() => num('screen') === 9, 'nav avia');
  check('nav: aviamasters', num('screen') === 9, 'screen ' + num('screen'));
  check('idle: readout shows a ready 1x', num('mult') === 1, 'mult ' + num('mult'));

  const act = sp('ActionBtn'), cash = sp('CashoutBtn'), plane = sp('AvPlane');
  setv('chips', 100000000);
  setv('bet', 100);
  setv('amAuto', 1);                        // manual first

  let valBad = 0, payBad = 0, logBad = 0, capBad = 0, firstBad = '';
  let lands = 0, ditches = 0, cashes = 0;
  let staked = 0, returned = 0;
  const orbSeen = ORBS.map(() => 0);
  let slotsPlayed = 0, ditchSlots = 0;

  for (let r = 0; r < ROUNDS; r++) {
    await until(settled, 'settle ' + r);
    const bet = num('bet'), before = num('chips');
    // bail out on some rounds, at a value we only decide once airborne
    const bailAt = r % 3 === 0 ? [1.5, 2, 4][(r / 3 | 0) % 3] : Infinity;

    click(act);
    await until(() => num('roundOn') === 1 || num('busy') === 1 || num('chips') !== before,
                'launch ' + r);
    staked += bet;
    if (num('chips') > before - bet) {
      payBad++;
      firstBad = firstBad || `round ${r}: stake ${before - num('chips')}, expected ${bet}`;
    }

    // fly it
    let didCash = false, guard = 0, maxSlot = 0;
    while (num('roundOn') === 1 && guard++ < 5000) {
      const s = num('amSlot'), v = num('amVal');
      maxSlot = Math.max(maxSlot, s);
      if (v > CAP + 1e-9) {
        capBad++;
        firstBad = firstBad || `round ${r}: value ${v} above the ${CAP}x cap`;
      }
      if (bailAt !== Infinity && v >= bailAt && s > 0) {
        const pre = num('chips');
        click(cash);
        await sleep(24);
        if (num('amCashed') === 1) {
          didCash = true; cashes++;
          const at = num('amAt'), log = gls('amLog');
          const want = replay(log);
          if (at !== want) {
            valBad++;
            firstBad = firstBad || `round ${r}: cashed at ${at}, replay says ${want} for [${log}]`;
          }
          const got = num('chips') - pre;
          if (got !== Math.round(bet * at)) {
            payBad++;
            firstBad = firstBad || `round ${r}: cash at ${at} paid ${got}, expected ${Math.round(bet * at)}`;
          }
          returned += got;
        }
        break;
      }
      await sleep(8);
    }

    if (!didCash) {
      await until(() => num('roundOn') === 0, 'end ' + r, 4000);
      const down = num('amDown') === 1, at = num('amAt'), log = gls('amLog');
      for (const i of log) orbSeen[i - 1]++;
      slotsPlayed += log.length;
      if (down) {
        ditches++; ditchSlots += log.length + 1;
        // the ditch is rolled BEFORE the slot's orb, so a flight that goes
        // down at slot k has logged exactly k-1 orbs
        if (log.length >= SLOTS) {
          logBad++;
          firstBad = firstBad || `round ${r}: ditched but logged all ${SLOTS} orbs`;
        }
        await until(settled, 'settle ditch ' + r, 4000);
        if (num('chips') !== before - bet) {
          payBad++;
          firstBad = firstBad || `round ${r}: ditch returned ${num('chips') - (before - bet)}`;
        }
      } else {
        lands++;
        if (log.length !== SLOTS) {
          logBad++;
          firstBad = firstBad || `round ${r}: landed with ${log.length} orbs, expected ${SLOTS}`;
        }
        const want = replay(log);
        if (at !== want) {
          valBad++;
          firstBad = firstBad || `round ${r}: landed at ${at}, replay says ${want} for [${log}]`;
        }
        await until(settled, 'settle land ' + r, 4000);
        const got = num('chips') - (before - bet);
        if (got !== Math.round(bet * at)) {
          payBad++;
          firstBad = firstBad || `round ${r}: landing at ${at} paid ${got}, expected ${Math.round(bet * at)}`;
        }
        returned += got;
      }
    } else {
      await until(settled, 'settle cash ' + r, 4000);
      for (const i of gls('amLog')) orbSeen[i - 1]++;
      slotsPlayed += gls('amLog').length;
    }
  }

  check(`play: ${ROUNDS} flights replay to the exact multiplier`, valBad === 0,
        valBad ? firstBad : `${lands} landed, ${cashes} cashed, ${ditches} ditched`);
  check('pay: every payout is round(bet x multiplier)', payBad === 0,
        payBad ? firstBad : `${staked} staked, ${returned} returned`);
  check('log: the orb count matches how the flight ended', logBad === 0, firstBad || 'consistent');
  check(`cap: no flight pays above ${CAP}x`, capBad === 0, capBad + ' over cap');
  check('play: all three endings occurred', lands > 0 && ditches > 0 && cashes > 0,
        `${lands} landed, ${ditches} ditched, ${cashes} cashed`);

  // the runtime must draw orbs at the published weights, not merely apply them
  let wBad = 0, wNote = '';
  if (slotsPlayed > 200) {
    for (let i = 0; i < ORBS.length; i++) {
      const want = ORBS[i][1] / TOTW, got = orbSeen[i] / slotsPlayed;
      const sd = Math.sqrt(want * (1 - want) / slotsPlayed);
      if (Math.abs(got - want) > 4.5 * sd + 0.01) {
        wBad++;
        wNote = wNote || `${ORBS[i][0]}: ${(got * 100).toFixed(1)}% vs ${(want * 100).toFixed(0)}%`;
      }
    }
  }
  check('draw: orbs appear at their published weights', wBad === 0,
        wNote || `${slotsPlayed} orbs drawn`);

  // ------------------------------------------------------------ presentation
  let flyHidden = false, cashShown = false, moved = false, readoutBad = 0, tries = 0;
  for (let attempt = 0; attempt < 40 && !moved; attempt++) {
    await until(settled, 'settle before ui', 4000);
    const px = plane.x, py = plane.y;
    click(act);
    await until(() => num('roundOn') === 1 || num('busy') === 1, 'ui launch', 2000);
    if (num('roundOn') !== 1) { await until(settled, 'ui skip', 4000); continue; }
    tries++;
    for (let i = 0; i < 40 && (act.visible || !cash.visible); i++) await sleep(12);
    if (!act.visible) flyHidden = true;
    if (cash.visible) cashShown = true;
    for (let i = 0; i < 300 && num('roundOn') === 1 && num('amSlot') < 3; i++) await sleep(10);
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
  check('ui: TAKE OFF hidden in flight', flyHidden, flyHidden ? 'hidden' : 'still shown');
  check('ui: CASH OUT live in flight', cashShown, cashShown ? 'shown' : 'missing');
  check('ui: the plane flies the route', moved,
        moved ? `moves with the slot (${tries} flights)` : 'never moved');
  check('ui: readout matches the multiplier', readoutBad === 0, readoutBad + ' faults');

  // the sky panel must not bury the readout - this shipped broken once
  const z = n => vm.runtime.executableTargets.indexOf(sp(n));
  const digitZ = Math.min(...cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === 9 && t.visible)
    .map(t => vm.runtime.executableTargets.indexOf(t)));
  check('z: the multiplier draws above the sky panel', digitZ > z('AvSky'),
        `digits ${digitZ}, sky ${z('AvSky')}`);

  // -------------------------------------------------- auto cash-out is exact
  const auto = gls('avAutoVals');
  let autoBad = 0, autoFired = 0, autoNote = '';
  for (const slot of [2, 3, 4]) {            // 1.5x, 2x, 5x
    setv('amAuto', slot);
    const target = auto[slot - 1];
    for (let r = 0; r < 10; r++) {
      await until(settled, 'settle auto', 4000);
      const bet = num('bet'), before = num('chips');
      click(act);
      await until(() => num('roundOn') === 1 || num('chips') !== before, 'auto launch', 2000);
      await until(() => num('roundOn') === 0, 'auto end', 6000);
      await until(settled, 'auto settle', 4000);
      const log = gls('amLog'), delta = num('chips') - before;
      // walk the same log: auto must fire on the FIRST slot at or above target
      let v = 1, fireAt = null;
      for (const i of log) { v = applyOrb(v, i); if (fireAt === null && v >= target) fireAt = v; }
      const down = num('amDown') === 1;
      if (fireAt !== null) {
        if (num('amCashed') !== 1) {
          autoBad++;
          autoNote = autoNote || `target ${target}: reached ${fireAt} but never fired [${log}]`;
        } else {
          autoFired++;
          if (num('amAt') !== fireAt) {
            autoBad++;
            autoNote = autoNote || `target ${target}: fired at ${num('amAt')}, expected ${fireAt} [${log}]`;
          }
          if (delta !== Math.round(bet * fireAt) - bet) {
            autoBad++;
            autoNote = autoNote || `target ${target}: net ${delta}, expected ${Math.round(bet * fireAt) - bet}`;
          }
        }
      } else if (num('amCashed') === 1) {
        autoBad++;
        autoNote = autoNote || `target ${target}: fired at ${num('amAt')} without reaching it [${log}]`;
      } else if (!down && log.length === SLOTS) {
        // landed under the target: paid the landing value, not the target
        if (delta !== Math.round(bet * replay(log)) - bet) {
          autoBad++;
          autoNote = autoNote || `target ${target}: landed net ${delta} [${log}]`;
        }
      }
    }
  }
  check('auto: fires on the first slot at or above the target', autoBad === 0,
        autoBad ? autoNote : `${autoFired} auto cash-outs across 1.5x/2x/5x`);

  vm.stopAll();
  console.log('\n============= AVIAMASTERS =============');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
