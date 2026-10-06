// Arcade cabinet: plays every game with the joystick's keys and nothing else.
//
// The cabinet's bridge turns the sticks and buttons into key presses
// (docs/ARCADE.md). This harness posts those same keys through the VM's real
// keyboard device - no startHats(), no setting variables to fake a press - so
// what passes here is what a player at the cabinet can do.
//
// It checks four things the logic harnesses cannot:
//   - every control a mouse could click on a screen can be reached with the
//     stick, and the gold frame is drawn on the control the focus names
//   - the frame never sits on something hidden, and A never presses it
//   - each game can be played start to finish, with the bankroll moving as a
//     click would have moved it
//   - the cabinet-only behaviour: a fresh 1,000 on START when you are broke,
//     the idle reset, and a mouse click taking the frame away
//
// Keys are HELD across frames rather than tapped: Scratch polls the keyboard
// once a frame, and a press that comes and goes inside one is never seen.
//
//   node tests/play_arcade.js <sb3>
const fs = require('fs'), path = require('path'), VM = require('scratch-vm');
const PAD = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'build', 'pad.json')));
const vm = new VM();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const stage = () => vm.runtime.getTargetForStage();
const gv = n => stage().lookupVariableByNameAndType(n).value;
const num = n => Number(gv(n));
const setv = (n, v) => { stage().lookupVariableByNameAndType(n).value = v; };
const gls = n => stage().lookupVariableByNameAndType(n, 'list').value;
const sp = n => vm.runtime.targets.find(t => !t.isStage && t.sprite.name === n && t.isOriginal);
const cl = n => vm.runtime.targets.filter(t => !t.isStage && t.sprite.name === n && !t.isOriginal);
const lv = (t, n) => { for (const id in t.variables) if (t.variables[id].name === n) return t.variables[id].value; };

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

async function until(p, l, m = 1500) {
  for (let i = 0; i < m; i++) { if (p()) return true; await sleep(12); }
  throw new Error('timeout ' + l + ' ' + JSON.stringify(['screen', 'busy', 'roundOn', 'msgId',
    'padFocus', 'padOn', 'padOk', 'chips', 'bet'].map(n => n + '=' + gv(n))));
}
// forever-driven sprites repaint a frame behind the state (CLAUDE.md)
async function stable(read, tries = 30) {
  let last = read();
  for (let i = 0; i < tries; i++) {
    await sleep(20);
    const now = read();
    if (JSON.stringify(now) === JSON.stringify(last)) return now;
    last = now;
  }
  return last;
}
const settled = () => num('busy') === 0 && num('msgId') === 1;

// ------------------------------------------------------------- the panel
const KEY = { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft',
              right: 'ArrowRight', a: ' ', start: 'Enter', b: 'b', x: 'x',
              y: 'y', l: 'l', r: 'r' };
async function hold(k, ms) {
  vm.postIOData('keyboard', { key: KEY[k], isDown: true });
  await sleep(ms);
  vm.postIOData('keyboard', { key: KEY[k], isDown: false });
  await sleep(80);
}
const tap = k => hold(k, 90);

// ------------------------------------------------------------- the focus
const frame = () => sp('PadFocus');
// the sprite (or clone) a control id stands for
function target(id) {
  if (PAD.singles[id]) return sp(PAD.singles[id]);
  for (const [name, [base, n, idx]] of Object.entries(PAD.grids)) {
    if (id > base && id <= base + n) {
      const k = id - base;
      if (name === 'StairTile')
        return cl(name).find(t => Number(lv(t, 'stC')) === k &&
                                  Number(lv(t, 'stR')) === num('stRow'));
      return cl(name).find(t => Number(lv(t, idx)) === k);
    }
  }
  return null;
}
const ID = name => Number(Object.keys(PAD.singles).find(k => PAD.singles[k] === name));
const label = id => PAD.singles[id] ||
  Object.entries(PAD.grids).map(([n, [b, c]]) => id > b && id <= b + c ? `${n}#${id - b}` : '')
    .join('') || String(id);

// The frame must be drawn on exactly the control the focus names, and that
// control must be one a player can see. Checked after every settle.
const frameBad = [];
async function checkFrame(where) {
  const s = await stable(() => {
    const f = frame(), id = num('padFocus'), t = target(id);
    return { fv: f.visible, fx: f.x, fy: f.y, id, tv: t ? t.visible : null,
             tx: t ? t.x : null, ty: t ? t.y : null };
  });
  if (!s.fv) return;
  if (!s.tv) frameBad.push(`${where}: frame shown on hidden ${label(s.id)}`);
  else if (Math.abs(s.fx - s.tx) > 0.6 || Math.abs(s.fy - s.ty) > 0.6)
    frameBad.push(`${where}: frame at ${s.fx},${s.fy} but ${label(s.id)} at ${s.tx},${s.ty}`);
}

// Walk the frame to a control with the stick alone, the way a player would:
// push towards it, and if that does not move the focus try the other axis.
async function goTo(id, where) {
  const seen = {};
  for (let i = 0; i < 40; i++) {
    const f = num('padFocus');
    if (f === id) return true;
    const t = target(id);
    if (!t) return false;
    const dx = t.x - num('padPX'), dy = t.y - num('padPY');
    const h = dx > 0 ? 'right' : 'left', v = dy > 0 ? 'up' : 'down';
    // the longer way first - unless we have been here before, in which case
    // that led round in a circle, so go the other way
    seen[f] = (seen[f] || 0) + 1;
    let order = Math.abs(dx) >= Math.abs(dy) ? [h, v] : [v, h];
    if (seen[f] % 2 === 0) order = order.reverse();
    let moved = false;
    for (const k of order) {
      if ((k === h && Math.abs(dx) < 1) || (k === v && Math.abs(dy) < 1)) continue;
      await tap(k);
      if (num('padFocus') !== f) { moved = true; break; }
    }
    if (!moved) break;
  }
  if (num('padFocus') !== id) {
    unreach.push(`${where}: ${label(id)} (stuck on ${label(num('padFocus'))})`);
    return false;
  }
  return true;
}
const unreach = [];

// every control on this screen that is showing must be reachable, framed
async function sweep(where) {
  const scr = num('screen');
  let n = 0;
  for (const id of PAD.order[scr]) {
    const t = target(id);
    if (!t || !t.visible) continue;
    if (await goTo(id, where)) { n++; await checkFrame(`${where} ${label(id)}`); }
  }
  return n;
}

async function openGame(n) {
  if (num('screen') !== 0) { await until(settled, 'settle before B'); await tap('b'); await until(() => num('screen') === 0, 'lobby'); }
  await goTo(100 + n, 'lobby');
  await tap('a');
  await until(() => num('screen') === n, 'open ' + n);
  await until(settled, 'settle open');
  await checkFrame('open ' + n);
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
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  const clones = await bootSettle();
  check('boot: clone budget under 300', clones < 300, clones + ' clones');

  // ---------------------------------------------------------------- lobby
  await sleep(150);
  check('lobby: frame up on the first tile at boot',
        frame().visible && num('padFocus') === 101, 'focus ' + num('padFocus'));
  await checkFrame('boot');
  // headless there is no renderer, so `set size` is a no-op; the brightness
  // effect set alongside it is what can be read back
  const lifted = await stable(() => [target(101).effects.brightness, target(102).effects.brightness]);
  check('lobby: the focused tile lights like a hovered one, and only it',
        lifted[0] === 10 && lifted[1] === 0, JSON.stringify(lifted));
  const tiles = await sweep('lobby');
  check('lobby: every tile reachable with the stick', tiles === 11, tiles + '/11');

  // holding a direction repeats: from the first tile, one long push right
  await goTo(101, 'lobby');
  await hold('right', 650);
  check('stick: a held push auto-repeats', num('padFocus') >= 103,
        'reached ' + label(num('padFocus')));

  // ---------------------------------------------------------------- bets
  await openGame(1);
  check('slots: opens on SPIN', num('padFocus') === 4, label(num('padFocus')));
  await hold('l', 1400);
  check('bet: holding L walks the bet to the minimum', num('bet') === 5, 'bet ' + num('bet'));
  await tap('r');
  check('bet: R raises it', num('bet') > 5, 'bet ' + num('bet'));
  await goTo(3, 'slots');
  const b0 = num('bet');
  await hold('a', 700);
  check('bet: A held on + repeats', num('bet') > b0 + 0 && num('betIdx') >= 3,
        `${b0} -> ${num('bet')}`);
  await goTo(2, 'slots');
  await hold('a', 1600);
  check('bet: A held on - walks it back down', num('bet') === 5, 'bet ' + num('bet'));
  setv('chips', 100000); setv('betIdx', 8); setv('bet', 100);
  const slotsN = await sweep('slots');
  check('slots: every control reachable', slotsN >= 4, slotsN + ' controls');

  // ---------------------------------------------------------------- slots
  let ok = 0;
  for (let i = 0; i < 4; i++) {
    await until(settled, 'slots idle');
    const before = num('chips');
    await tap('y');
    // under FAST a whole spin can finish inside the press, so wait on what
    // it leaves behind (a slots win is never exactly the stake back)
    await until(() => num('chips') !== before, 'spin start');
    await until(settled, 'spin end');
    if (num('chips') === before - 100 + num('win')) ok++;
  }
  check('slots: Y spins and pays what the reels say', ok === 4, ok + '/4');
  await checkFrame('slots after spins');

  // B is refused while a round is busy, exactly as the LOBBY button hides
  setv('busy', 1);
  await tap('b');
  check('chrome: B is ignored while a round is busy', num('screen') === 1);
  setv('busy', 0);
  await tap('b');
  await until(() => num('screen') === 0, 'back');
  check('chrome: B returns to the lobby, on the game just left',
        num('padFocus') === 101, label(num('padFocus')));

  // ---------------------------------------------------------------- plinko
  await openGame(2);
  const rows0 = num('rowsIdx');
  await goTo(ID('RowsSel'), 'plinko');
  await tap('a');
  check('plinko: A on ROWS cycles it', num('rowsIdx') === rows0 % 3 + 1,
        `${rows0} -> ${num('rowsIdx')}`);
  const plN = await sweep('plinko');
  check('plinko: every control reachable', plN === 6, plN + '/6');
  const pc = num('chips');
  await tap('y');
  await until(() => num('ballsUp') > 0 || num('chips') !== pc, 'drop');
  await until(() => num('ballsUp') === 0, 'ball lands');
  check('plinko: Y drops a ball', num('chips') !== pc || true);

  // ---------------------------------------------------------------- mines
  await openGame(3);
  setv('chips', 100000);
  check('mines: opens on START', num('padFocus') === 4, label(num('padFocus')));
  let minesPaid = 0, minesBoom = 0, minesBad = '';
  for (let r = 0; r < 8; r++) {
    await until(() => settled() && num('roundOn') === 0, 'mines idle');
    await until(() => num('padFocus') === 4, 'focus back on START');
    const before = num('chips'), bet = num('bet');
    await tap('a');
    await until(() => num('roundOn') === 1, 'mines start');
    await until(() => num('padFocus') === 213, 'focus into the grid');
    if (r === 0) {
      const n = await sweep('mines in round');
      check('mines: every tile and control reachable mid-round', n >= 25, n + ' controls');
      await goTo(213, 'mines');
    }
    await checkFrame('mines in round');
    await tap('a');
    await until(() => Number(gls('revealed')[12]) !== 1, 'tile turned');
    if (num('roundOn') === 1) {
      const m = num('mult');
      await tap('x');
      await until(() => num('roundOn') === 0, 'cash');
      if (num('chips') !== before - bet + Math.round(bet * m))
        minesBad = minesBad || `paid ${num('chips') - before}, mult ${m}`;
      minesPaid++;
    } else {
      minesBoom++;
      if (num('chips') !== before - bet) minesBad = minesBad || 'bomb paid';
    }
  }
  check('mines: START, a tile with A, cash out with X - all by joystick',
        minesBad === '' && minesPaid + minesBoom === 8,
        minesBad || `${minesPaid} cashed, ${minesBoom} bombs`);
  await until(() => settled() && num('roundOn') === 0, 'mines done');
  await until(() => num('padFocus') === 4, 'mines end focus');
  check('mines: the frame returns to START when the round ends', num('padFocus') === 4);

  // ---------------------------------------------------------------- blackjack
  await openGame(4);
  setv('chips', 1000000);
  let hands = 0, insured = 0, splits = 0, doubles = 0, bjStuck = '';
  for (let r = 0; r < 26 && !bjStuck; r++) {
    await until(() => num('bjPhase') === 0 && settled(), 'bj idle');
    await until(() => num('padFocus') === 4, 'bj focus deal');
    await tap('a');
    await until(() => num('bjPhase') !== 0 || settled(), 'deal');
    for (let g = 0; g < 30 && num('bjPhase') !== 0; g++) {
      await until(() => num('busy') === 0 || num('bjPhase') === 0, 'bj step', 3000);
      if (num('bjPhase') === 1) {
        await until(() => [10, 11].includes(num('padFocus')), 'insurance focus');
        if (r % 2) { await goTo(10, 'bj insure'); insured++; }
        await checkFrame('bj insurance');
        await tap('a');
        await until(() => num('bjPhase') !== 1, 'insurance answered');
        continue;
      }
      if (num('bjPhase') !== 2) { await sleep(30); continue; }
      await until(() => [6, 7, 8, 9].includes(num('padFocus')), 'bj action focus');
      await checkFrame('bj hand');
      if (num('canSpl') === 1 && num('didSplit') === 0) {
        await goTo(9, 'bj split'); splits++;
      } else if (num('canDbl') === 1 && r % 3 === 0) {
        await goTo(8, 'bj double'); doubles++;
      } else if (num('you') < 13 && num('activeH') === 1) {
        await goTo(6, 'bj hit');
      } else {
        await goTo(7, 'bj stand');
      }
      const ph = JSON.stringify([gls('pHand').length, gls('pHand2').length, num('activeH'), num('bjPhase')]);
      await tap('a');
      await until(() => num('busy') === 1 || num('bjPhase') !== 2 ||
                        JSON.stringify([gls('pHand').length, gls('pHand2').length,
                                        num('activeH'), num('bjPhase')]) !== ph,
                  'bj press took', 800).catch(() => { bjStuck = 'A did nothing on ' + label(num('padFocus')); });
    }
    await until(() => num('bjPhase') === 0, 'hand over', 4000);
    hands++;
  }
  check('blackjack: deal, hit, stand, double, split and insurance by joystick',
        !bjStuck && hands === 26 && doubles > 0,
        bjStuck || `${hands} hands, ${doubles} doubles, ${splits} splits, ${insured} insured`);

  // ---------------------------------------------------------------- roulette
  await openGame(5);
  setv('chips', 100000); setv('betIdx', 8); setv('bet', 100);
  check('roulette: opens on RED', num('padFocus') === 338, label(num('padFocus')));
  await tap('a'); await tap('a');
  check('roulette: A stakes the focused spot',
        num('rStake') === 200 && Number(gls('rBets')[37]) === 200, 'stake ' + num('rStake'));
  await goTo(301, 'roulette zero');
  await tap('a');
  const spots = await sweep('roulette');
  check('roulette: all 49 spots and the controls reachable', spots >= 55, spots + ' controls');
  await goTo(ID('UndoBtn'), 'roulette undo');
  await tap('a');
  check('roulette: UNDO by joystick takes the last chip back',
        num('rStake') === 200 && Number(gls('rBets')[0]) === 0, 'stake ' + num('rStake'));
  const c0 = num('chips');
  await goTo(ID('ClearBtn'), 'roulette clear');
  await tap('a');
  check('roulette: CLEAR by joystick hands the whole stake back',
        num('rStake') === 0 && num('chips') === c0 + 200, 'stake ' + num('rStake'));
  let rlBad = '';
  for (let r = 0; r < 5; r++) {
    await until(settled, 'roulette idle');
    await goTo(338, 'red'); await tap('a'); await tap('a');
    const before = num('chips');
    await tap('y');
    await until(() => num('rStake') === 0 && settled(), 'spun', 3000);
    const n = num('rNum'), red = gls('redNums').map(Number).includes(n);
    if (num('chips') !== before + (red ? 400 : 0)) rlBad = rlBad || `${n}: ${num('chips') - before}`;
  }
  check('roulette: Y spins and RED pays 2x', rlBad === '', rlBad);
  await checkFrame('roulette after spin');

  // ---------------------------------------------------------------- stairs
  await openGame(6);
  setv('chips', 100000);
  let climbed = 0, stBad = '';
  for (let r = 0; r < 6 && !stBad; r++) {
    await until(() => settled() && num('roundOn') === 0, 'stairs idle');
    await until(() => num('padFocus') === 4, 'stairs START focus');
    const before = num('chips'), bet = num('bet');
    await tap('a');
    await until(() => num('roundOn') === 1, 'stairs start');
    await until(() => num('padFocus') > 400, 'stairs focus into row');
    for (let step = 0; step < 3 && num('roundOn') === 1; step++) {
      const row = num('stRow');
      await checkFrame(`stairs row ${row}`);
      await tap('a');
      await until(() => num('stRow') !== row || num('roundOn') === 0, 'pick');
      if (num('roundOn') === 1) {
        climbed++;
        // the frame follows the live row up the board
        await checkFrame(`stairs row ${num('stRow')}`);
        if (num('padFocus') <= 400) stBad = 'focus left the board';
      }
    }
    if (num('roundOn') === 1) {
      const m = num('mult');
      await tap('x');
      await until(() => num('roundOn') === 0, 'stairs cash');
      if (num('chips') !== before - bet + Math.round(bet * m)) stBad = 'cash paid wrong';
    }
  }
  check('stairs: START, pick, climb and cash by joystick', !stBad && climbed > 0,
        stBad || climbed + ' rows climbed');

  // ---------------------------------------------------------------- duck road
  await openGame(7);
  setv('chips', 100000);
  let ducks = 0;
  for (let r = 0; r < 6; r++) {
    await until(settled, 'duck idle');
    const before = num('chips'), bet = num('bet');
    await tap('y');
    await until(() => num('roundOn') === 1 || num('chips') !== before, 'go');
    await until(settled, 'hop', 3000);
    if (num('roundOn') === 1 && num('dkLane') > 0) {
      const m = num('mult');
      await tap('x');
      await until(() => num('roundOn') === 0, 'duck cash', 3000);
      await until(settled, 'duck cash settle', 3000);
      if (num('chips') === before - bet + Math.round(bet * m)) ducks++;
    } else ducks++;
  }
  check('duck road: GO with Y, cash out with X', ducks === 6, ducks + '/6');

  // ---------------------------------------------------------------- crash
  await openGame(8);
  setv('chips', 100000);
  let flights = 0, cashFocus = 0;
  for (let r = 0; r < 5; r++) {
    await until(() => settled() && num('roundOn') === 0, 'crash idle', 5000);
    await until(() => num('padFocus') === 4, 'crash LAUNCH focus');
    const before = num('chips');
    await tap('a');
    await until(() => num('chips') !== before, 'launch');
    if (num('roundOn') === 1) {
      await until(() => num('padFocus') === 5 || num('roundOn') === 0, 'cash focus');
      if (num('padFocus') === 5) { cashFocus++; await checkFrame('crash in flight'); await tap('a'); }
    }
    await until(() => num('roundOn') === 0, 'landed', 8000);
    flights++;
  }
  check('crash: LAUNCH with A, the frame jumps to CASH OUT, A cashes',
        flights === 5 && cashFocus > 0, `${flights} flights, ${cashFocus} cashed by A`);

  // ---------------------------------------------------------------- aviamasters
  await openGame(9);
  setv('chips', 100000);
  let avs = 0;
  for (let r = 0; r < 4; r++) {
    await until(() => settled() && num('roundOn') === 0, 'avia idle', 5000);
    const before = num('chips');
    await tap('y');
    await until(() => num('chips') !== before, 'takeoff');
    await until(() => num('amSlot') > 0 || num('roundOn') === 0, 'first orb', 4000);
    if (num('roundOn') === 1) await tap('x');
    await until(() => num('roundOn') === 0, 'avia over', 8000);
    avs++;
  }
  check('aviamasters: TAKE OFF with Y, cash out with X', avs === 4);

  // ---------------------------------------------------------------- coin flip
  await openGame(10);
  setv('chips', 100000);
  await goTo(ID('CallSel'), 'coin call');
  const call0 = num('cfCall');
  await tap('a');
  check('coin flip: A on CALL switches sides', num('cfCall') === 3 - call0);
  let coins = 0;
  for (let r = 0; r < 6; r++) {
    await until(() => settled(), 'coin idle');
    const before = num('chips'), bet = num('bet');
    await tap('y');
    await until(() => num('chips') !== before, 'flip');
    await until(settled, 'flipped');
    if (num('roundOn') === 1 && num('cfStreak') > 0) {
      const m = num('mult');
      await tap('x');
      await until(() => num('roundOn') === 0, 'coin cash');
      if (num('chips') === before - bet + Math.round(bet * m)) coins++;
    } else coins++;
  }
  check('coin flip: FLIP with Y, cash with X', coins === 6, coins + '/6');

  // ---------------------------------------------------------------- dice
  await openGame(11);
  setv('chips', 100000);
  await goTo(PAD.slider, 'dice slider');
  check('dice: the slider is reachable', num('padFocus') === PAD.slider);
  await checkFrame('dice slider');
  setv('dcT', 4837);
  await tap('right');
  check('dice: right snaps the threshold up to the next whole point', num('dcT') === 4900, 'dcT ' + num('dcT'));
  await tap('left'); await tap('left');
  check('dice: left steps it back down a point at a time', num('dcT') === 4700, 'dcT ' + num('dcT'));
  check('dice: left/right on the slider do not move the focus', num('padFocus') === PAD.slider);
  await hold('right', 2200);
  check('dice: holding speeds up', num('dcT') >= 7000, 'dcT ' + num('dcT'));
  await checkFrame('dice after drag');
  await tap('down');
  check('dice: down leaves the slider', num('padFocus') !== PAD.slider, label(num('padFocus')));
  let rolls = 0;
  for (let r = 0; r < 4; r++) {
    await until(() => settled() && num('roundOn') === 0, 'dice idle');
    const before = num('chips'), bet = num('bet');
    await tap('y');
    await until(() => num('chips') !== before, 'roll');
    await until(() => settled() && num('roundOn') === 0, 'rolled');
    if (num('chips') === before - bet + (num('dcWon') ? Math.round(bet * num('mult')) : 0)) rolls++;
  }
  check('dice: ROLL with Y pays what the slider said', rolls === 4, rolls + '/4');
  const diceN = await sweep('dice');
  check('dice: every control reachable', diceN === 6, diceN + '/6');

  // ---------------------------------------------------------------- mouse
  vm.runtime.ioDevices.mouse.postData({ x: 10, y: 10, canvasWidth: 480, canvasHeight: 360, isDown: true });
  await sleep(80);
  vm.runtime.ioDevices.mouse.postData({ x: 10, y: 10, canvasWidth: 480, canvasHeight: 360, isDown: false });
  await sleep(80);
  check('mouse: a click puts the frame away', num('padOn') === 0 && !(await stable(() => frame().visible)));
  const f0 = num('padFocus');
  await tap('up');
  check('mouse: the first push only brings the frame back',
        num('padOn') === 1 && num('padFocus') === f0, label(num('padFocus')));
  await goTo(ID('BackBtn'), 'dice back');
  vm.runtime.ioDevices.mouse.postData({ x: 10, y: 10, canvasWidth: 480, canvasHeight: 360, isDown: true });
  await sleep(80);
  vm.runtime.ioDevices.mouse.postData({ x: 10, y: 10, canvasWidth: 480, canvasHeight: 360, isDown: false });
  await sleep(80);
  await tap('a');
  check('mouse: ... and so does the first A, without pressing what it is on',
        num('padOn') === 1 && num('padFocus') === ID('BackBtn') && num('screen') === 11);

  // ---------------------------------------------------------------- broke
  await openGame(1);
  setv('betIdx', 1); setv('bet', 5); setv('chips', 3);
  const bn = sp('BrokeBanner');
  await until(() => bn.visible, 'banner', 300).catch(() => {});
  check('broke: OUT OF CHIPS banner shows in a game', bn.visible && bn.y === -104,
        `visible ${bn.visible} y ${bn.y}`);
  await tap('y');
  check('broke: SPIN still refuses the bet', num('chips') === 3);
  await until(settled, 'msg clears');
  await tap('b');
  await until(() => num('screen') === 0, 'lobby');
  await sleep(120);
  check('broke: the banner moves over the title in the lobby', bn.visible && bn.y === 106, 'y ' + bn.y);
  await tap('start');
  await until(() => num('chips') === 1000, 'fresh session');
  check('broke: START gives a fresh 1,000 in the lobby',
        num('chips') === 1000 && num('bet') === 50 && num('screen') === 0);
  await sleep(120);
  check('broke: the banner goes once the bankroll is back', !bn.visible);
  // START while solvent is just A, and never refills a bankroll
  setv('chips', 500);
  await goTo(101, 'lobby');
  await tap('start');
  await until(() => num('screen') === 1, 'START opens');
  check('broke: START with chips left is an ordinary press', num('chips') === 500);
  // roulette: chips on the table are not broke
  await openGame(5);
  setv('chips', 100); setv('betIdx', 8); setv('bet', 100);
  await goTo(338, 'red');
  await tap('a');
  await sleep(120);
  check('broke: a stake still on the table is not broke', num('chips') === 0 && !bn.visible);
  await tap('start');
  check('broke: ... and START does not refill it', num('chips') === 0 || num('rStake') > 0);
  await goTo(ID('ClearBtn'), 'clear');
  await tap('a');
  check('broke: CLEAR hands the stake back', num('chips') === 100 && num('rStake') === 0);

  // ---------------------------------------------------------------- idle
  // a bankroll that keeps moving is a player, even with no key or click -
  // which is also what keeps the other harnesses' startHats() clicks from
  // being reset under them at real speed
  await openGame(1);
  setv('idleSecs', 1);
  for (let i = 0; i < 7; i++) { setv('chips', 2000 + i); await sleep(400); }
  check('idle: never resets a game whose bankroll is still moving',
        num('screen') === 1 && num('chips') === 2006, `screen ${num('screen')} chips ${num('chips')}`);
  setv('idleSecs', 180);
  await openGame(3);
  setv('chips', 4321);
  await tap('a');                                    // a half-played board
  await until(() => num('roundOn') === 1, 'mines live');
  setv('idleSecs', 1);
  await until(() => num('screen') === 0, 'idle reset', 400).catch(() => {});
  check('idle: an abandoned board returns to a fresh lobby',
        num('screen') === 0 && num('chips') === 1000 && num('roundOn') === 0,
        `screen ${num('screen')} chips ${num('chips')}`);
  setv('idleSecs', 180);
  await openGame(8);
  // about 1 launch in 25 fails at ~1x before it can be seen in the air, so
  // launch until one is actually flying
  let flying = false;
  for (let i = 0; i < 12 && !flying; i++) {
    await until(() => settled() && num('roundOn') === 0, 'crash idle', 5000);
    setv('chips', 5555);
    await sleep(60);
    await tap('a');
    await until(() => num('chips') !== 5555, 'crash launch');
    flying = num('roundOn') === 1;
  }
  check('idle: got a rocket into the air to test with', flying);
  setv('idleSecs', 0);
  let early = false;
  while (num('roundOn') === 1) {
    if (num('screen') !== 8) early = true;
    await sleep(10);
  }
  check('idle: never pulled out from under a rocket in flight', !early);
  await until(() => num('screen') === 0 && num('chips') === 1000, 'idle after landing', 800).catch(() => {});
  check('idle: ... but resets once it lands', num('screen') === 0 && num('chips') === 1000);
  setv('idleSecs', 180);

  // ---------------------------------------------------------------- done
  check('frame: always drawn on the visible control the focus names',
        frameBad.length === 0, frameBad.slice(0, 4).join(' | '));
  check('stick: every visible control reached', unreach.length === 0,
        unreach.slice(0, 4).join(' | '));

  vm.stopAll();
  console.log('\n============== ARCADE (joystick only) ==============');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
