// Duck Road: plays the game headlessly and settles every run against an
// independently written implementation of the rules.
//
// The ladder is recomputed here from the published constants rather than read
// out of the project, so a wrong table in tables3.py fails this test instead of
// agreeing with itself. Every hop is checked against the roll the VM actually
// made (dkRoll vs duckPct), so a mis-wired comparison shows up as a mismatch
// rather than as luck.
//
//   node tests/play_duck.js <sb3> [runs]
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
async function until(p, l, m = 900) {
  for (let i = 0; i < m; i++) { if (p()) return; await sleep(12); }
  throw new Error('timeout ' + l);
}
const idle = () => until(() => num('busy') === 0, 'busy');

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

// ---------------------------------------------------------------- the rules
// mirrors src/tables3.py, written from the same spec rather than copied
const HOUSE = 0.96, LANES = 12, EGG_ODDS = 0.25, EGG_MULT = 3.0;
const MODES = [['EASY', 0.90], ['MEDIUM', 0.80], ['HARD', 0.65], ['DAREDEVIL', 0.45]];
function nice(v) {
  if (v >= 10000) return Math.round(v);
  if (v >= 100) return Math.round(v * 10) / 10;
  if (v >= 10) return Math.round(v * 100) / 100;
  return Math.round(v * 100) / 100;
}
// ladder[mode 0..3][lane 1..12] -> {base, egg}
const ladder = MODES.map(([, p]) => {
  const rows = [null];
  for (let n = 1; n <= LANES; n++) {
    const raw = HOUSE / (Math.pow(p, n) * (1 + EGG_ODDS * (n / LANES) * (EGG_MULT - 1)));
    rows.push({ base: nice(raw), egg: nice(raw * EGG_MULT) });
  }
  return rows;
});
const expectedMult = (mode, lane, got) =>
  got ? ladder[mode - 1][lane].egg : ladder[mode - 1][lane].base;

// what the multiplier readout is actually showing on screen (field 3)
function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      return i <= 10 ? String(i - 1) : (i === 11 ? '.' : (i === 12 ? ',' : '')); })
    .join('');
}

(async () => {
  const RUNS = Number(process.argv[3] || 40);
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await sleep(900);

  // ------------------------------------------------------------ boot state
  check('boot: 12 lane labels', cl('DuckMult').length === 12, 'got ' + cl('DuckMult').length);
  check('boot: 4 traffic clones', cl('DuckCar').length === 4, 'got ' + cl('DuckCar').length);
  check('boot: 8 lobby tiles', cl('MenuTile').length === 8, 'got ' + cl('MenuTile').length);
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  check('boot: clone budget under 300', clones < 300, clones + ' clones');

  // ------------------------------------------------------- the shipped table
  const flat = gls('duckMults');
  check('table: 96 entries', flat.length === 96, 'got ' + flat.length);
  let tbad = 0, worst = '';
  for (let m = 1; m <= 4; m++) {
    for (let n = 1; n <= LANES; n++) {
      for (const got of [0, 1]) {
        const idx = (m - 1) * 12 + n + got * 48;   // 1-based, as the VM indexes it
        const want = expectedMult(m, n, got);
        if (Math.abs(flat[idx - 1] - want) > 1e-9) {
          tbad++; worst = `m${m} lane${n} egg${got}: ${flat[idx - 1]} vs ${want}`;
        }
      }
    }
  }
  check('table: matches an independent solve', tbad === 0, tbad ? worst : '96/96');

  // house edge, recomputed from the shipped values
  let evbad = 0;
  for (let m = 1; m <= 4; m++) {
    const p = MODES[m - 1][1];
    for (let n = 1; n <= LANES; n++) {
      const q = EGG_ODDS * n / LANES;
      const ev = Math.pow(p, n) * (q * expectedMult(m, n, 1) + (1 - q) * expectedMult(m, n, 0));
      if (Math.abs(ev - HOUSE) > 0.02) evbad++;
    }
  }
  check('table: every cash-out point returns 0.96', evbad === 0, evbad + ' outliers');

  const pct = gls('duckPct');
  check('table: survival odds', JSON.stringify(pct) === JSON.stringify([90, 80, 65, 45]),
        JSON.stringify(pct));

  // ------------------------------------------------------------- navigation
  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(7));
  await until(() => num('screen') === 7, 'nav duck');
  check('nav: duck road', num('screen') === 7, 'screen ' + num('screen'));

  // the mode selector cycles
  const sel = sp('DuckSel');
  const before = num('dkMode');
  click(sel); await sleep(90);
  check('selector: cycles mode', num('dkMode') === (before % 4) + 1,
        `${before} -> ${num('dkMode')}`);
  setv('dkMode', 1);

  // ------------------------------------------------- traffic is actually live
  // cars are presentation, but a road with no cars on it is a broken screen,
  // and nothing else in the suite would notice
  let sawCar = 0, carLanes = new Set();
  for (let i = 0; i < 120; i++) {
    for (const c of cl('DuckCar')) {
      if (c.visible) { sawCar++; carLanes.add(Number(lv(c, 'cLane'))); }
    }
    await sleep(16);
  }
  check('traffic: cars drive on the road', sawCar > 0,
        `${sawCar} sightings across ${carLanes.size} lanes`);

  // --------------------------------------------------------------- play it
  const act = sp('ActionBtn'), cash = sp('CashoutBtn');
  setv('chips', 100000000);
  setv('bet', 100);

  let mismatches = 0, firstBad = '';
  let hops = 0, deaths = 0, eggs = 0, cashes = 0, clears = 0, planted = 0;
  const laneSeen = new Set(), modeSeen = new Set();
  let multFaults = 0, deathPay = 0, deathPayBad = 0;

  for (let run = 0; run < RUNS; run++) {
    const mode = (run % 4) + 1;              // rotate through all four modes
    setv('dkMode', mode);
    modeSeen.add(mode);
    // cash out at a random depth so both endings get exercised
    const bailAt = 1 + Math.floor(Math.random() * LANES);

    await idle();
    const bet = num('bet');
    let chips = num('chips');
    let lane = 0, got = 0;

    // start the run: GO both deducts and takes lane 1
    click(act);
    // catch dkEgg mid-hop: it is drawn before the hop starts and cleared again
    // if the duck dies, which happens at the END of that same hop
    let plantedThisRun = 0;
    for (let i = 0; i < 200; i++) {
      if (num('busy') === 1) { plantedThisRun = num('dkEgg') > 0 ? 1 : 0; break; }
      await sleep(2);
    }
    await idle();
    // the stake is gone the moment the run starts
    const afterStart = num('chips');
    // whether this run hides an egg is decided at the start, independently of
    // how deep the duck then gets
    planted += plantedThisRun;

    let alive = true, ended = false;
    let guard = 0;
    while (alive && !ended && guard++ < 40) {
      const roll = num('dkRoll'), tgt = num('dkTgt');
      const survived = roll <= pct[mode - 1];
      hops++;
      if (tgt !== lane + 1) {
        mismatches++;
        firstBad = firstBad || `run ${run}: target lane ${tgt}, expected ${lane + 1}`;
        break;
      }
      if (survived) {
        lane = tgt;
        laneSeen.add(lane);
        const eggLane = num('dkEgg');
        if (eggLane === lane && !got) { got = 1; eggs++; }
        // Reaching lane 12 ends the run, and the game clears dkEgg/dkGot as
        // part of settling it - so by the time the hop returns, the flag has
        // legitimately been reset. Only assert it while the run is still live.
        if (lane < LANES && num('dkGot') !== got) {
          mismatches++;
          firstBad = firstBad || `run ${run} lane ${lane}: egg flag ${num('dkGot')} vs ${got}`;
          break;
        }
        if (lane >= LANES) {
          // reaching HOME pays out automatically at the top of the ladder
          const want = Math.round(bet * expectedMult(mode, LANES, got));
          const delta = num('chips') - afterStart;
          if (delta !== want) {
            mismatches++;
            firstBad = firstBad || `run ${run} clear: paid ${delta}, expected ${want}`;
          }
          clears++; ended = true; break;
        }
        // the live multiplier must match the ladder, and be on screen
        const want = expectedMult(mode, lane, got);
        if (Math.abs(num('mult') - want) > 1e-9) {
          mismatches++;
          firstBad = firstBad || `run ${run} lane ${lane}: mult ${num('mult')} vs ${want}`;
          break;
        }
        // the digit clones repaint from a forever loop, so let the
        // readout settle before judging it
        let shown = readout(3);
        for (let i = 0; i < 60 && shown !== String(num('mult')); i++) {
          await sleep(12); shown = readout(3);
        }
        if (shown !== String(num('mult'))) {
          multFaults++;
          firstBad = firstBad || `run ${run} lane ${lane}: readout "${shown}" vs mult ${num('mult')}`;
        }

        if (lane >= bailAt) {
          // cash out
          const pre = num('chips');
          click(cash);
          await sleep(20); await idle();
          const delta = num('chips') - pre;
          const wantPay = Math.round(bet * want);
          if (delta !== wantPay) {
            mismatches++;
            firstBad = firstBad || `run ${run} cash at ${lane}: paid ${delta}, expected ${wantPay}`;
          }
          cashes++; ended = true; break;
        }
        click(act);
        await sleep(20); await idle();
      } else {
        // hit: the run is over and nothing is paid back
        deaths++;
        alive = false;
        deathPay++;
        if (num('chips') !== afterStart) {
          deathPayBad++;
          firstBad = firstBad || `run ${run}: death paid ${num('chips') - afterStart}`;
        }
      }
    }
    await idle();
    // between runs the duck is back on the verge with a clean slate
    if (num('roundOn') !== 0 || num('dkLane') !== 0) {
      mismatches++;
      firstBad = firstBad || `run ${run}: not reset (roundOn ${num('roundOn')}, lane ${num('dkLane')})`;
    }
    // the stake was actually taken
    if (afterStart !== chips - bet) {
      mismatches++;
      firstBad = firstBad || `run ${run}: stake ${chips - afterStart}, expected ${bet}`;
    }
  }

  check(`play: ${RUNS} runs settle exactly`, mismatches === 0,
        mismatches ? firstBad : `${hops} hops, 0 mismatches`);
  check('play: multiplier readout matches the variable', multFaults === 0,
        multFaults + ' faults');
  check('play: a hit pays nothing', deathPayBad === 0,
        `${deathPay} deaths, ${deathPayBad} bad`);
  check('play: all four modes exercised', modeSeen.size === 4, [...modeSeen].join(','));
  check('play: deaths occurred', deaths > 0, deaths + ' deaths');
  check('play: cash-outs occurred', cashes > 0, cashes + ' cash-outs');
  check('play: deep lanes reached', Math.max(...laneSeen) >= 6,
        'deepest lane ' + Math.max(...laneSeen));

  // Collecting an egg naturally needs BOTH a 25% roll and surviving to its
  // lane, so demanding one in a short run fails a working game (PITFALLS 12).
  // The deterministic pickup test below is what proves the payout; this checks
  // the thing that does not depend on luck twice over - that eggs are planted
  // at roughly the designed rate.
  const rate = planted / RUNS;
  // 25% by design; allow a wide band because RUNS is small, but tight enough
  // that a broken draw (never, or always) fails
  check('play: eggs planted at the designed 25% rate',
        rate > 0.10 && rate < 0.45,
        `${planted}/${RUNS} runs (${(rate * 100).toFixed(0)}%), ${eggs} reached in play`);

  // ------------------------------------- the egg, forced rather than hoped for
  // 25% x reaching its lane makes a natural pickup rare, so plant one. See
  // PITFALLS 12: a rare path deserves a deterministic test, not a long run.
  setv('dkMode', 1);                       // EASY: 90% per lane
  let eggChecked = 0, eggBad = 0, eggNote = '';
  for (let attempt = 0; attempt < 40 && eggChecked < 3; attempt++) {
    await idle();
    click(act); await sleep(20); await idle();       // start + hop 1
    if (num('roundOn') !== 1) continue;              // died on lane 1
    const plant = num('dkLane') + 1;
    if (plant > LANES) { click(cash); await sleep(20); await idle(); continue; }
    setv('dkEgg', plant);
    const before = num('mult');
    click(act); await sleep(20); await idle();       // hop onto the egg
    if (num('roundOn') !== 1) continue;              // died reaching it
    const lane = num('dkLane');
    if (lane !== plant) { click(cash); await sleep(20); await idle(); continue; }
    if (num('dkGot') !== 1) {
      eggBad++; eggNote = eggNote || `lane ${lane}: egg not picked up`;
    } else {
      const want = expectedMult(1, lane, 1);
      if (Math.abs(num('mult') - want) > 1e-9) {
        eggBad++; eggNote = eggNote || `lane ${lane}: mult ${num('mult')} vs ${want}`;
      } else if (!(num('mult') > before)) {
        eggBad++; eggNote = eggNote || `lane ${lane}: egg did not raise the ladder`;
      } else {
        // and it must actually be paid at the egg rate
        const pre = num('chips'), wantPay = Math.round(num('bet') * want);
        click(cash); await sleep(20); await idle();
        const delta = num('chips') - pre;
        if (delta !== wantPay) {
          eggBad++; eggNote = eggNote || `lane ${lane}: paid ${delta}, expected ${wantPay}`;
        } else eggChecked++;
        continue;
      }
    }
    click(cash); await sleep(20); await idle();
  }
  check('egg: forced pickup switches and pays the egg ladder',
        eggChecked > 0 && eggBad === 0,
        eggBad ? eggNote : `${eggChecked} verified pickups`);

  // -------------------------------------------------- bet controls are safe
  // retry until a run actually survives its first lane
  let uiDone = false;
  for (let attempt = 0; attempt < 30 && !uiDone; attempt++) {
    await idle();
    click(act); await sleep(20); await idle();
    if (num('roundOn') !== 1) continue;
    uiDone = true;
    // both buttons are driven by forever loops, so they need a frame after
    // busy clears before their visibility is meaningful
    for (let i = 0; i < 40 && !sp('CashoutBtn').visible; i++) await sleep(12);
    const betShown = sp('BetPlus').visible, cashShown = sp('CashoutBtn').visible;
    check('ui: bet locked mid-run', !betShown,
          betShown ? 'BetPlus still clickable' : 'hidden as expected');
    check('ui: cash out offered mid-run', cashShown,
          cashShown ? 'shown' : 'CashoutBtn missing');
    click(cash); await sleep(20); await idle();
  }
  if (!uiDone) {
    check('ui: bet locked mid-run', false, 'never got a live run to inspect');
    check('ui: cash out offered mid-run', false, 'never got a live run to inspect');
  }

  vm.stopAll();
  console.log('\n================ DUCK ROAD ================');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(r => r[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
