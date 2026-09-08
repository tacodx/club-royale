const fs = require('fs'), VM = require('scratch-vm');
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
async function until(p, l, m = 800) { for (let i = 0; i < m; i++) { if (p()) return; await sleep(34); } throw new Error('timeout ' + l); }

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

const rank = c => ((c - 1) % 13) + 1;
const val = c => Math.min(rank(c), 10);
const hv = h => { let s = 0, a = 0;
  for (const c of h) { let v = val(c); if (v === 1) { a++; v = 11; } s += v; }
  while (s > 21 && a > 0) { s -= 10; a--; } return s; };

function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      return i <= 10 ? String(i - 1) : (i === 11 ? '.' : (i === 12 ? ',' : '')); })
    .join('');
}

// independent implementation of the payout rules
function expectedReturn(s) {
  const dv = hv(s.dHand), pv = hv(s.pHand), pv2 = hv(s.pHand2);
  const dealerBJ = s.dHand.length === 2 && dv === 21;
  const playerBJ = !s.didSplit && s.pHand.length === 2 && pv === 21;
  let ret = 0;
  if (dealerBJ) {
    ret += s.insBet * 3;
    if (playerBJ) ret += s.bjBet1;
  } else if (playerBJ) {
    ret += Math.round(s.bjBet1 * 2.5);
  } else {
    if (pv <= 21) ret += (dv > 21 || pv > dv) ? s.bjBet1 * 2 : (pv === dv ? s.bjBet1 : 0);
    if (s.didSplit && pv2 <= 21)
      ret += (dv > 21 || pv2 > dv) ? s.bjBet2 * 2 : (pv2 === dv ? s.bjBet2 : 0);
  }
  return ret;
}

(async () => {
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  await sleep(600);

  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  const act = sp('ActionBtn');

  check('boot: 18 card clones', cl('Card').length === 18, 'got ' + cl('Card').length);
  check('boot: 32 digit clones', cl('Digit').length === 32, 'got ' + cl('Digit').length);
  check('boot: sounds attached',
    vm.runtime.targets.reduce((a, t) => a + t.getSounds().length, 0) === 12);
  check('boot: clone budget', vm.runtime.targets.length < 300, vm.runtime.targets.length);

  click(tile(4)); await sleep(300);
  check('nav: blackjack', Number(gv('screen')) === 4);

  const N = Number(process.argv[3] || 60);
  let rounds = N;
  let bad = 0, splits = 0, doubles = 0, insur = 0, naturals = 0, dealerBJs = 0;
  let overviewBad = 0, seenSplitOverview = 0;

  for (let r = 0; r < N; r++) {
    await until(() => Number(gv('bjPhase')) === 0 && Number(gv('busy')) === 0,
                'idle', 500);
    setv('chips', 1000000); setv('bet', 100);
    await sleep(60);
    const before = gv('chips');
    click(act);
    await sleep(180);

    // insurance offer?
    await until(() => Number(gv('bjPhase')) !== 0 || Number(gv('busy')) === 0,
                'phase', 500);
    if (Number(gv('bjPhase')) === 1) {
      insur++;
      check_offer: {
        if (!sp('InsureBtn').visible || !sp('NoInsBtn').visible) overviewBad++;
      }
      click(r % 2 === 0 ? sp('InsureBtn') : sp('NoInsBtn'));
      await sleep(150);
    }
    await until(() => Number(gv('bjPhase')) === 2 || Number(gv('bjPhase')) === 0,
                'settle or act', 600);

    // hand overview must be on screen and correct while a hand is live
    if (Number(gv('bjPhase')) === 2) {
      if (readout(6) !== String(gv('dealer'))) overviewBad++;
      if (readout(7) !== String(gv('you'))) overviewBad++;
      if (!sp('DealerPlq').visible || !sp('YouPlq').visible) overviewBad++;
    }

    // play out
    let guard = 0;
    while (Number(gv('bjPhase')) === 2 && guard++ < 24) {
      await until(() => Number(gv('busy')) === 0 || Number(gv('bjPhase')) !== 2,
                  'act idle', 500);
      if (Number(gv('bjPhase')) !== 2) break;
      const ah = Number(gv('activeH'));
      const v = ah === 1 ? Number(gv('you')) : Number(gv('you2'));
      if (Number(gv('canSpl')) === 1) {
        splits++; click(sp('SplitBtn'));
      } else if (Number(gv('canDbl')) === 1 && v >= 9 && v <= 11) {
        doubles++; click(sp('DoubleBtn'));
      } else if (v < 17) {
        click(sp('HitBtn'));
      } else {
        click(sp('StandBtn'));
      }
      await sleep(140);
      if (Number(gv('didSplit')) === 1 && Number(gv('bjPhase')) === 2) {
        if (readout(8) !== String(gv('you2'))) overviewBad++;
        seenSplitOverview++;
      }
    }

    console.log(`  round ${r + 1}: nat=${naturals} dbj=${dealerBJs} spl=${splits} dbl=${doubles} ins=${insur}`);
    await until(() => Number(gv('bjPhase')) === 0, 'round end', 700);
    await until(() => Number(gv('busy')) === 0, 'round idle', 700);
    await sleep(60);

    const st = {
      pHand: gls('pHand'), pHand2: gls('pHand2'), dHand: gls('dHand'),
      bjBet1: Number(gv('bjBet1')), bjBet2: Number(gv('bjBet2')),
      insBet: Number(gv('insBet')), didSplit: Number(gv('didSplit')) === 1,
    };
    if (st.dHand.length === 2 && hv(st.dHand) === 21) dealerBJs++;
    if (!st.didSplit && st.pHand.length === 2 && hv(st.pHand) === 21) naturals++;
    const staked = st.bjBet1 + st.bjBet2 + st.insBet;
    const exp = expectedReturn(st) - staked;
    const got = gv('chips') - before;
    if (got !== exp) { bad++;
      if (bad < 6) console.log(`  MISMATCH r${r} got ${got} exp ${exp} ` +
        `p=${JSON.stringify(st.pHand)}(${hv(st.pHand)}) ` +
        `p2=${JSON.stringify(st.pHand2)} d=${JSON.stringify(st.dHand)}(${hv(st.dHand)}) ` +
        `b1=${st.bjBet1} b2=${st.bjBet2} ins=${st.insBet} split=${st.didSplit}`); }
    // no duplicate cards anywhere
    const all = st.pHand.concat(st.pHand2, st.dHand);
    if (new Set(all).size !== all.length) { bad++; console.log('  duplicate cards'); }
    // dealer must reach 17 whenever a live hand remained
    const live = (hv(st.pHand) <= 21) || (st.didSplit && hv(st.pHand2) <= 21);
    const bjEnd = (st.dHand.length === 2 && hv(st.dHand) === 21) ||
                  (!st.didSplit && st.pHand.length === 2 && hv(st.pHand) === 21);
    if (live && !bjEnd && hv(st.dHand) < 17) { bad++; console.log('  dealer stopped short'); }
    if (r >= 18 && naturals >= 1 && dealerBJs >= 1 && splits >= 1 &&
        doubles >= 1 && insur >= 1) { rounds = r + 1; break; }
  }

  check(`blackjack: ${rounds} rounds settle exactly`, bad === 0, bad + ' mismatches');
  check('blackjack: splits exercised', splits > 0, splits + ' splits');
  check('blackjack: doubles exercised', doubles > 0, doubles + ' doubles');
  check('blackjack: insurance offered', insur > 0, insur + ' offers');
  check('blackjack: player naturals paid 3:2', naturals > 0, naturals + ' naturals');
  check('blackjack: dealer blackjack path hit', dealerBJs > 0, dealerBJs + ' dealer BJs');
  check('overview: totals + labels correct every round', overviewBad === 0,
        overviewBad + ' faults');
  check('overview: split hand total shown', seenSplitOverview > 0,
        seenSplitOverview + ' checks');

  // buttons must not appear when illegal
  await until(() => Number(gv('bjPhase')) === 0, 'idle end', 400);
  await sleep(200);
  check('buttons: hidden outside a hand',
        !sp('HitBtn').visible && !sp('StandBtn').visible &&
        !sp('DoubleBtn').visible && !sp('SplitBtn').visible &&
        !sp('InsureBtn').visible);
  check('buttons: DEAL shown when idle', sp('ActionBtn').visible);

  vm.stopAll();
  console.log('\\n================ v3 RESULTS ================');
  let f = 0;
  for (const [s, n, e] of R) { if (s === 'FAIL') f++;
    console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`); }
  console.log(`\\n${R.length - f}/${R.length} passed`);
  process.exit(f ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.message); process.exit(2); });
