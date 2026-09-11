// Coin Flip: plays streaks headlessly and checks every call, every rung of the
// ladder and every payout against an independent implementation of the rules.
//
// Nothing here is statistical. The side is drawn into cfSide before the coin
// moves, so each flip can be judged exactly: the streak advances if and only
// if cfSide === cfCall, the pot must be coinMults[streak] at every rung, and a
// cash-out must pay round(bet * the multiplier that was on screen).
//
//   node tests/play_coin.js <sb3> [rounds]
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
// must match src/tables6.py: rung n pays 0.96 * 2^n, exactly, no rounding
const HOUSE = 0.96, RUNGS = T6.coinRungs;
const ladder = n => Math.round(HOUSE * Math.pow(2, n) * 100) / 100;

function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      return i <= 10 ? String(i - 1)
        : (i === 11 ? '.' : (i === 12 ? ',' : (i === 14 ? 'x' : ''))); })
    .join('');
}
// forever-driven sprites repaint a frame behind the variable they read
// (CLAUDE.md), so let a reading stabilise rather than trusting the first one
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
  const ROUNDS = Number(process.argv[3] || 40);
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await bootSettle();

  const games = sp('MenuTile').getCostumes().length;
  check('boot: one lobby tile per game', cl('MenuTile').length === games,
        `${cl('MenuTile').length} tiles, ${games} games`);
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  check('boot: clone budget under 300', clones < 300, clones + ' clones');
  check('boot: 12 coin spin frames',
        sp('Coin').getCostumes().length === G.coinFrames,
        'got ' + sp('Coin').getCostumes().length);

  // ------------------------------------------------ the table itself
  const tbl = gls('coinMults');
  const want = Array.from({ length: RUNGS }, (_, i) => ladder(i + 1));
  check('table: ladder is 0.96 x 2^n', JSON.stringify(tbl) === JSON.stringify(want),
        JSON.stringify(tbl));
  // the point of the ladder: cashing out on any rung is worth the same
  let edgeBad = 0;
  for (let n = 1; n <= RUNGS; n++) {
    if (Math.abs(tbl[n - 1] / Math.pow(2, n) - HOUSE) > 1e-12) edgeBad++;
  }
  check('table: every rung returns exactly 0.96', edgeBad === 0, edgeBad + ' rungs off');

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(10));
  await until(() => num('screen') === 10, 'nav coin');
  check('nav: coin flip', num('screen') === 10, 'screen ' + num('screen'));
  check('idle: readout shows a ready 1x', num('mult') === 1, 'mult ' + num('mult'));

  const act = sp('ActionBtn'), cash = sp('CashoutBtn');
  const coin = sp('Coin'), pip = sp('CoinPip'), callSel = sp('CallSel');
  setv('chips', 100000000);
  setv('bet', 100);

  await sleep(120);
  check('idle: cash out hidden with no streak', cash.visible === false);
  check('idle: pip hidden with no streak', pip.visible === false);

  const costume = t => t.getCostumes()[t.currentCostume].name;

  // one flip. Returns the side it came up on, or null if the click did nothing.
  async function flip() {
    const preStreak = num('cfStreak'), preRound = num('roundOn');
    click(act);
    await until(() => num('busy') === 1 || num('cfStreak') !== preStreak ||
                      num('roundOn') !== preRound, 'flip start');
    await until(() => num('busy') === 0 && num('msgId') === 1, 'flip end');
    return num('cfSide');
  }

  let callBad = 0, multBad = 0, payBad = 0, stakeBad = 0, faceBad = 0,
      pipBad = 0, readBad = 0, firstBad = '';
  let heads = 0, tails = 0, flips = 0, cashes = 0, busts = 0, deepest = 0;
  const fail = m => { firstBad = firstBad || m; };

  for (let r = 0; r < ROUNDS; r++) {
    await until(settled, 'settle ' + r);
    // alternate the called side so both branches of the comparison are used
    setv('cfCall', (r % 2) + 1);
    await sleep(20);
    const call = num('cfCall'), bet = num('bet'), before = num('chips');
    const bailAt = [1, 2, 3, 1, 4][r % 5];      // rung to try to cash out on

    click(act);
    await until(() => num('chips') === before - bet ||
                      num('roundOn') === 1, 'start ' + r);
    if (num('chips') !== before - bet) {
      stakeBad++;
      fail(`round ${r}: stake ${before - num('chips')}, expected ${bet}`);
    }
    // the first flip is already running inside the same handler
    await until(() => num('busy') === 0 && num('msgId') === 1, 'first flip ' + r);

    let streak = 0, alive = true, staked = num('chips');
    for (let f = 0; f < 40 && alive; f++) {
      const side = f === 0 ? num('cfSide') : await flip();
      flips++;
      if (side === 1) heads++; else tails++;
      const wonCall = side === call;
      if (wonCall) streak++;

      // the streak must track the calls exactly
      const vmStreak = num('cfStreak');
      if (wonCall && vmStreak !== streak) {
        callBad++;
        fail(`round ${r} flip ${f}: called ${call}, got ${side}, streak ${vmStreak} not ${streak}`);
      }
      if (!wonCall && num('roundOn') !== 0) {
        callBad++;
        fail(`round ${r} flip ${f}: called ${call}, got ${side}, round still live`);
      }

      if (!wonCall) {
        busts++;
        alive = false;
        if (num('chips') !== staked) {
          payBad++;
          fail(`round ${r}: a wrong call paid ${num('chips') - staked}`);
        }
        // the coin must be showing the side that actually lost the round
        const face = await stable(() => costume(coin));
        if (face !== `cf${side === 2 ? G.coinTails : G.coinHeads}`) {
          faceBad++;
          fail(`round ${r}: side ${side} but the coin shows ${face}`);
        }
        break;
      }

      deepest = Math.max(deepest, streak);
      if (num('mult') !== ladder(streak)) {
        multBad++;
        fail(`round ${r}: streak ${streak} shows ${num('mult')}, expected ${ladder(streak)}`);
      }
      const face = await stable(() => costume(coin));
      if (face !== `cf${side === 2 ? G.coinTails : G.coinHeads}`) {
        faceBad++;
        fail(`round ${r}: side ${side} but the coin shows ${face}`);
      }
      // the marker must sit on the rung the pot is actually at
      const py = await stable(() => pip.y);
      if (!pip.visible || Math.abs(py - G.rungY[streak - 1]) > 0.51) {
        pipBad++;
        fail(`round ${r}: streak ${streak} pip at y=${py}, rung is ${G.rungY[streak - 1]}`);
      }
      const shown = await stable(() => readout(9));
      if (shown !== `${num('mult')}x`) {
        readBad++;
        fail(`round ${r}: pot ${num('mult')} but the readout says "${shown}"`);
      }

      if (streak >= bailAt) {
        const pre = num('chips');
        click(cash);
        await until(() => num('cfCashed') === 1 || num('busy') === 1, 'cash ' + r);
        await until(settled, 'cash settle ' + r);
        cashes++;
        alive = false;
        const at = num('cfAt'), got = num('chips') - pre;
        const wantPay = Math.round(bet * ladder(streak));
        if (at !== ladder(streak) || got !== wantPay) {
          payBad++;
          fail(`round ${r}: cashed on rung ${streak} at ${at} for ${got}, expected ${ladder(streak)} / ${wantPay}`);
        }
      }
    }
  }

  check('rules: streak tracks the calls', callBad === 0, callBad ? firstBad : flips + ' flips');
  check('rules: stake taken once per run', stakeBad === 0, stakeBad ? firstBad : '');
  check('pot: every rung matches the ladder', multBad === 0, multBad ? firstBad : `deepest ${deepest}`);
  check('pay: cash-outs and busts pay exactly', payBad === 0,
        payBad ? firstBad : `${cashes} cash-outs, ${busts} busts`);
  check('display: coin rests on the side that was drawn', faceBad === 0, faceBad ? firstBad : '');
  check('display: pip sits on the rung the pot is at', pipBad === 0, pipBad ? firstBad : '');
  check('display: readout matches the pot', readBad === 0, readBad ? firstBad : '');
  // a flat coin, loosely: 4 sigma on this many flips
  const dev = Math.abs(heads - flips / 2) / Math.sqrt(flips / 4);
  check('fair: the coin is not weighted', dev < 4,
        `${heads} heads / ${tails} tails over ${flips} (${dev.toFixed(2)} sigma)`);

  // ---------------------------------------------- topping the ladder
  // Rung 12 is one run in 4096, so it is reached by hand rather than waited
  // for (PITFALLS 12). Everything from the final call onward is the game's.
  await until(settled, 'settle before top');
  let topPay = null, topAt = null, topTries = 0;
  while (topPay === null && topTries++ < 40) {
    const bet = num('bet'), before = num('chips');
    click(act);
    await until(() => num('chips') === before - bet, 'top stake');
    await until(() => num('busy') === 0 && num('msgId') === 1, 'top first flip');
    if (num('roundOn') !== 1) continue;              // busted on the first call
    setv('cfStreak', RUNGS - 1);
    setv('mult', ladder(RUNGS - 1));
    await sleep(40);
    const pre = num('chips');
    await flip();
    if (num('cfCashed') === 1) { topPay = num('chips') - pre; topAt = num('cfAt'); }
    await until(settled, 'top settle');
  }
  check('top rung: the ladder pays itself out at 12',
        topPay === Math.round(num('bet') * ladder(RUNGS)) && topAt === ladder(RUNGS),
        topPay === null ? 'never reached in 40 tries'
                        : `paid ${topPay} at ${topAt}, expected ${Math.round(num('bet') * ladder(RUNGS))} at ${ladder(RUNGS)}`);
  check('top rung: the round is closed after it pays',
        num('roundOn') === 0 && num('cfStreak') === 0,
        `roundOn ${num('roundOn')} streak ${num('cfStreak')}`);

  // the call selector is what a player actually has; drive it by clicking
  await until(settled, 'settle before selector');
  setv('cfCall', 2);
  await sleep(40);
  click(callSel);
  await sleep(80);
  check('controls: the call selector cycles and wraps', num('cfCall') === 1,
        'call ' + num('cfCall'));

  // ------------------------------------------------ leaving mid-streak
  await until(settled, 'settle before exit');
  const beforeExit = num('chips');
  click(act);
  await until(() => num('chips') !== beforeExit, 'exit stake');
  await until(() => num('busy') === 0 && num('msgId') === 1, 'exit flip');
  click(sp('BackBtn'));
  await until(() => num('screen') === 0, 'back to lobby');
  await sleep(80);
  check('exit: leaving mid-streak closes the round',
        num('roundOn') === 0 && num('cfStreak') === 0 && num('busy') === 0,
        `roundOn ${num('roundOn')} streak ${num('cfStreak')} busy ${num('busy')}`);

  vm.stopAll();
  console.log('\n============== COIN FLIP ==============');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
