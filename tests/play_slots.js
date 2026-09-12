// THE GOLD ROOM (slots): a second, independent implementation of the payline
// rule, played against the real VM.
//
// Nothing here is transcribed from src/build.py. The evaluator below is written
// from the contract prose and from build/tables7.json - the numbers the solver
// published and the art was drawn from - so a bug in the block logic has
// nowhere to hide: both sides would have to be wrong in the same direction.
//
// Three things make slots harder to verify than the other games, and each has
// its own section here:
//
//   * The weighting lives in the reel STRIP, not in the draw. A biased rand()
//     would produce the same symbol frequencies and pass any payout test, so
//     every spin's nine cells are reconstructed from slStops and the published
//     strips and compared cell for cell. The +27 window index is wrong only for
//     stops 1-2 and only on the top row, which no payout assertion would see.
//   * The top rungs are unreachable by spinning. WILD x3 on one line is 6 in
//     27000 and the ladder's top fifth of the return sits up there
//     (PITFALLS 12), so the paytable is driven through the real VM by writing
//     slGrid directly and firing the `slotsEval` hook: all 729 triples on the
//     middle row, all 729 on a diagonal, one screen per distinct total, the
//     leading-wild cases, and the 90x maximum the solver prints.
//   * A win is drawn by DIMMING the losers, so the result is as much in the
//     ghost effect and the costume of nine clones as it is in slUnits
//     (CLAUDE.md: verify the display, not just the variable). The grid is read
//     back off the Reel clones and compared to the list.
//
//   node tests/play_slots.js <sb3> [spins]
const fs = require('fs'), path = require('path'), VM = require('scratch-vm');
const BUILD = path.join(__dirname, '..', 'build');
const T7 = JSON.parse(fs.readFileSync(path.join(BUILD, 'tables7.json')));
const G = JSON.parse(fs.readFileSync(path.join(BUILD, 'geom7.json')));
const vm = new VM();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const stage = () => vm.runtime.getTargetForStage();
const gv = n => { const s = stage();
  for (const id in s.variables) if (s.variables[id].name === n) return s.variables[id].value;
  throw new Error('no var ' + n); };
const num = n => Number(gv(n));
const setv = (n, v) => { stage().lookupVariableByNameAndType(n).value = v; };
const lst = n => { const l = stage().lookupVariableByNameAndType(n, 'list');
  if (!l) throw new Error('no list ' + n);
  return l; };
const gls = n => lst(n).value.map(Number);
const sls = (n, v) => { lst(n).value = v.slice(); };
const sp = n => vm.runtime.targets.find(t => !t.isStage && t.sprite.name === n && t.isOriginal);
const cl = n => vm.runtime.targets.filter(t => !t.isStage && t.sprite.name === n && !t.isOriginal);
const lv = (t, n) => { for (const id in t.variables) if (t.variables[id].name === n) return t.variables[id].value; };
const click = t => vm.runtime.startHats('event_whenthisspriteclicked', null, t);
async function until(p, l, m = 3000) {
  for (let i = 0; i < m; i++) { if (p()) return true; await sleep(12); }
  throw new Error('timeout ' + l);
}
const settled = () => num('roundOn') === 0 && num('busy') === 0 && num('msgId') === 1;
const J = v => JSON.stringify(v);

// Checks are collected with the phase they belong to and printed in that
// order, because the phases cannot run in it: the paytable walk has to happen
// on a machine that has not spun yet, and the frame-by-frame atomicity run has
// to stop the 30fps interval that every display assertion depends on.
const R = [];
const check = (o, n, c, e = '') => R.push([o, c ? 'PASS' : 'FAIL', n, e]);

// ===================================================================
// THE RULES - an independent implementation, from the contract prose
// ===================================================================
const LEN = T7.stripLen;                  // 30 stops per reel
const REELS = T7.reels;                   // 3
const ROWS = T7.rows;                     // 3
const CELLS = REELS * ROWS;               // 9
const WILD = T7.wild;                     // 9
const NLINES = T7.lines.length / REELS;   // 5
const PAY3 = T7.pay3, PAY2 = T7.pay2;
const NAME = i => T7.names[i - 1];

// "cell = (col - 1) * 3 + row, row 1 is the top row" - 1-based cell ids, held
// here in a 0-based array, so cell id k is grid[k - 1].
const cellId = (col, row) => (col - 1) * ROWS + row;

// "reel c position p is index (c-1)*30 + p", 1-based into slStrip
const stripAt = (c, p) => T7.strips[(c - 1) * LEN + (p - 1)];

// "Column c drawn on stop s shows, in row r:
//    slGrid[(c-1)*3 + r] = slStrip[(c-1)*30 + ((s + r + 27) mod 30) + 1]"
function gridFromStops(stops) {
  const g = new Array(CELLS);
  for (let c = 1; c <= REELS; c++)
    for (let r = 1; r <= ROWS; r++)
      g[cellId(c, r) - 1] = stripAt(c, ((stops[c - 1] + r + 27) % LEN) + 1);
  return g;
}

// "A line pays on its leading run from reel 1 only. WILD substitutes for every
//  symbol. The line's symbol is the first non-wild cell scanning left to right;
//  if all three are wild the symbol is WILD. The run is 3 when reels 2 and 3
//  both match-or-wild, 2 when only reel 2 does, 1 otherwise. A run of 3 pays
//  slPay3[symbol], a run of 2 pays slPay2[symbol], a run of 1 pays nothing."
function lineEval(cells) {
  let base = WILD;
  for (const s of cells) if (s !== WILD) { base = s; break; }
  const fits = s => s === base || s === WILD;
  const run = fits(cells[1]) ? (fits(cells[2]) ? 3 : 2) : 1;
  const pay = run === 3 ? PAY3[base - 1] : (run === 2 ? PAY2[base - 1] : 0);
  return { base, run, pay };
}

// a published list of lit cell ids -> the 0/1 vector the VM keeps in slHot
const hotVector = ids => { const v = new Array(CELLS).fill(0);
  for (const id of ids) v[id - 1] = 1; return v; };

// the cell ids line L reads, in reel order: "(L-1)*3 + reel"
const lineCells = L => [0, 1, 2].map(k => T7.lines[(L - 1) * REELS + k]);

// "slHot marks cells 1..run of every line that paid"
function evalGrid(grid) {
  const lineWin = [], hot = new Array(CELLS).fill(0);
  let units = 0;
  for (let L = 1; L <= NLINES; L++) {
    const ids = lineCells(L);
    const e = lineEval(ids.map(ci => grid[ci - 1]));
    lineWin.push(e.pay);
    units += e.pay;
    if (e.pay > 0) for (let k = 0; k < e.run; k++) hot[ids[k] - 1] = 1;
  }
  return { lineWin, hot, units, mult: units / NLINES };
}

// ===================================================================
// display helpers
// ===================================================================
// A Reel clone's costume names the symbol it shows. build.py aliases the art
// file `sym7` to a costume called `s7` and validate.py only ever checks the
// short spelling, so read the id out of the digits rather than betting on
// which of the two names shipped.
const symOfCostume = t => {
  const n = t.getCostumes()[t.currentCostume].name;
  const m = /(\d+)/.exec(n);
  return m ? Number(m[1]) : NaN;
};

function readout(field) {
  return cl('Digit')
    .filter(t => Number(lv(t, 'dField')) === field && t.visible)
    .sort((a, b) => Number(lv(a, 'dSlot')) - Number(lv(b, 'dSlot')))
    .map(t => { const i = Number(t.getCostumes()[t.currentCostume].name.slice(1));
      // 13 is the blank. Anything else is a real glyph and must come back as
      // itself: mapping M and B to '' is how a bankroll readout would quietly
      // lose the magnitude suffix it is abbreviated with.
      return i <= 10 ? String(i - 1)
        : ({ 11: '.', 12: ',', 13: '', 14: 'x', 15: 'M', 16: 'B' })[i]; })
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

// the grid as the PLAYER sees it: nine clones, each carrying its own cIdx
const screenGrid = () => {
  const out = new Array(CELLS).fill(0);
  for (const t of cl('Reel')) {
    const i = Number(lv(t, 'cIdx'));
    if (i >= 1 && i <= CELLS) out[i - 1] = symOfCostume(t);
  }
  return out;
};

async function bootSettle(cap = 8000) {
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

// ------------------------------------------------------------ the hook
// `when I receive slotsEval -> if screen == 1 then sl_eval()`. The runtime
// upper-cases both the hat's stored field and the value passed here
// (blocks-runtime-cache.js), so the name goes in exactly as authored.
function fire(name) {
  const started = vm.runtime.startHats(
    'event_whenbroadcastreceived', { BROADCAST_OPTION: name });
  if (!started || started.length === 0)
    throw new Error(`broadcast "${name}" started no script - is the harness hook wired?`);
  return started.length;
}
// one frame, with WORK_TIME pinned tiny so a step is a step (PITFALLS 10b,
// the tests/boot_race.js idiom)
function step(n = 1) {
  for (let i = 0; i < n; i++) {
    vm.runtime.currentStepTime = 0.001;
    vm.runtime._step();
  }
}
// write a grid, evaluate it through the real VM, read back what it decided
function drive(grid) {
  sls('slGrid', grid);
  fire('slotsEval');
  step(1);
  return { lineWin: gls('slLineWin'), hot: gls('slHot'),
           units: num('slUnits'), mult: num('mult'), grid: gls('slGrid') };
}

// ------------------------------------------------------- chips write log
// Counting VALUE CHANGES would miss a credit of 0 on a losing spin and call
// that one write. What has to be true is that a round TOUCHES chips exactly
// twice - the debit and the credit - whatever those two numbers are.
let chipLog = [];
function watchChips() {
  const v = stage().lookupVariableByNameAndType('chips');
  let held = v.value;
  Object.defineProperty(v, 'value', {
    configurable: true,
    get() { return held; },
    set(x) { held = x; chipLog.push(Number(x)); }
  });
}

(async () => {
  const SPINS = Number(process.argv[3] || 60);
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag();
  const bootClones = await bootSettle();
  const STEP30 = vm.runtime.currentStepTime;

  // =================================================================
  // 1. CONSTANTS - what the VM ships against what the solver wrote
  // =================================================================
  const vmStrip = gls('slStrip'), vmPay3 = gls('slPay3'),
        vmPay2 = gls('slPay2'), vmLines = gls('slLines');
  // only ever printed on a failure, so it never narrates a mismatch that a
  // passing check did not have
  const firstDiff = (a, b) => a.length !== b.length
    ? `${a.length} entries, expected ${b.length}`
    : `first mismatch at index ${a.findIndex((v, i) => v !== b[i])}: `
      + `${a[a.findIndex((v, i) => v !== b[i])]} vs `
      + `${b[a.findIndex((v, i) => v !== b[i])]}`;
  const diffIf = (ok, a, b) => ok ? '' : firstDiff(a, b);
  check(1, 'table: slStrip is the solved strip, flattened',
        J(vmStrip) === J(T7.strips),
        diffIf(J(vmStrip) === J(T7.strips), vmStrip, T7.strips));
  check(1, 'table: slPay3 is the solved 3-of-a-kind ladder',
        J(vmPay3) === J(T7.pay3), diffIf(J(vmPay3) === J(T7.pay3), vmPay3, T7.pay3));
  check(1, 'table: slPay2 is the solved near-miss rung',
        J(vmPay2) === J(T7.pay2), diffIf(J(vmPay2) === J(T7.pay2), vmPay2, T7.pay2));
  check(1, 'table: slLines is the solved payline map',
        J(vmLines) === J(T7.lines), diffIf(J(vmLines) === J(T7.lines), vmLines, T7.lines));
  // A stale build/tables7.json would agree with a stale VM. Re-derive the
  // house edge from the published numbers alone: if it is not exactly 24/25,
  // nobody solved for what is about to be paid out.
  let unitsTotal = 0;
  const byTotal = new Map(), byLines = new Map();
  let topScreen = { units: -1 };
  for (let s0 = 1; s0 <= LEN; s0++)
    for (let s1 = 1; s1 <= LEN; s1++)
      for (let s2 = 1; s2 <= LEN; s2++) {
        const stops = [s0, s1, s2], grid = gridFromStops(stops);
        const e = evalGrid(grid);
        unitsTotal += e.units;
        if (!byTotal.has(e.units)) byTotal.set(e.units, { stops, grid });
        const paid = e.lineWin.filter(v => v > 0).length;
        if (!byLines.has(paid)) byLines.set(paid, { stops, grid });
        if (e.units > topScreen.units) topScreen = { units: e.units, stops, grid };
      }
  const SCREENS = LEN ** REELS;
  const [HN, HD] = T7.house;          // exact, as a fraction: no float compare
  check(1, `table: the shipped ladder returns exactly ${HN}/${HD}`,
        unitsTotal * HD === SCREENS * NLINES * HN,
        `${unitsTotal / (SCREENS * NLINES)} over ${SCREENS} screens, `
        + `solver published ${T7.rtp}`);
  // Not `=== [22,17,19]`: two different screens reach 450 units, so WHICH one
  // a walk finds is an artefact of its iteration order, not a property of the
  // table. Check the size of the top prize, and check that the screen the
  // solver PUBLISHED really is worth it.
  const pubTop = evalGrid(T7.maxGrid);
  check(1, 'table: the top prize is what the solver says it is',
        topScreen.units === T7.maxUnits && pubTop.units === T7.maxUnits
        && J(gridFromStops(T7.maxStops)) === J(T7.maxGrid)
        && J(pubTop.hot) === J(hotVector(T7.maxHot)),
        `walk found ${topScreen.units} at ${J(topScreen.stops)}; solver `
        + `published ${T7.maxUnits} at ${J(T7.maxStops)} worth ${pubTop.units}`);

  // =================================================================
  // 2a. LIST LENGTHS at boot
  // =================================================================
  const WANT_LEN = { slGrid: CELLS, slStops: REELS, slLineWin: NLINES, slHot: CELLS };
  const lens = () => { const o = {};
    for (const k in WANT_LEN) o[k] = gls(k).length;
    return o; };
  const bootLens = lens();
  check(2, 'lists: constant lengths at boot', J(bootLens) === J(WANT_LEN),
        `${J(bootLens)} vs ${J(WANT_LEN)}`);

  // ------------------------------------------------------------- nav
  const tile = n => cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === n);
  click(tile(1));
  await until(() => num('screen') === 1, 'nav slots');
  check(0, 'nav: the lobby opens the gold room', num('screen') === 1,
        'screen ' + num('screen'));
  await until(settled, 'idle after nav');

  const act = sp('ActionBtn');
  setv('chips', 100000000);
  setv('bet', 100);
  await sleep(140);

  // =================================================================
  // 4. THE DETERMINISTIC WALK - drive the whole paytable through the VM
  //    Run before the spin loop so the window-rule evidence below is
  //    gathered on a machine this section has not written slGrid on.
  // =================================================================
  const chipsBeforeWalk = num('chips');
  let walkBad = 0, walkFirst = '', walkN = 0;
  const walkFail = m => { walkBad++; walkFirst = walkFirst || m; };

  function compare(label, grid, got) {
    walkN++;
    const want = evalGrid(grid);
    if (J(got.grid) !== J(grid))
      return walkFail(`${label}: sl_eval moved slGrid to ${J(got.grid)}`);
    if (J(got.lineWin) !== J(want.lineWin))
      return walkFail(`${label}: slLineWin ${J(got.lineWin)}, expected `
                      + `${J(want.lineWin)}  grid ${J(grid)}`);
    if (got.units !== want.units)
      return walkFail(`${label}: slUnits ${got.units}, expected ${want.units}`
                      + `  grid ${J(grid)}`);
    if (J(got.hot) !== J(want.hot))
      return walkFail(`${label}: slHot ${J(got.hot)}, expected ${J(want.hot)}`
                      + `  grid ${J(grid)}`);
    if (got.mult !== want.mult)
      return walkFail(`${label}: mult ${got.mult}, expected ${want.mult}`
                      + `  grid ${J(grid)}`);
    if (got.lineWin.reduce((a, b) => a + b, 0) !== got.units)
      return walkFail(`${label}: slLineWin sums to `
                      + `${got.lineWin.reduce((a, b) => a + b, 0)} but slUnits `
                      + `says ${got.units}`);
    return want;
  }

  // Find the straight line and the down diagonal by SHAPE rather than by
  // index. A typed [2,5,8] / [1,5,9] would go red the day slLines is
  // reordered, which is a change to the published table and not a bug in the
  // game - the whole point of reading the map from tables7.json.
  const rowOf = ci => (ci - 1) % ROWS + 1;
  const shapeOf = L => lineCells(L).map(rowOf);
  const findLine = want => {
    for (let L = 1; L <= NLINES; L++)
      if (J(shapeOf(L)) === J(want)) return L;
    return 0;
  };
  const MID = findLine([2, 2, 2]);                 // straight across the middle
  const DIAG = findLine([1, 2, 3]);                // top left to bottom right
  const midCells = MID ? lineCells(MID) : [];
  const diagCells = DIAG ? lineCells(DIAG) : [];
  check(4, 'walk: the line map has a middle row and a down diagonal to drive',
        MID > 0 && DIAG > 0 && MID !== DIAG,
        `middle row is line ${MID} ${J(midCells)}, `
        + `down diagonal is line ${DIAG} ${J(diagCells)}`);

  // Filler for the six cells not under test. It has to pay nothing on the
  // other four lines FOR EVERY triple, including the ones that put a WILD in
  // the centre, because lines 4 and 5 both read cell 5 and lines 2 and 3 both
  // read a corner. A leading JACK with a QUEEN on reel 3 does it: the run can
  // never exceed two, and JACK does not pay from two. Argued here, asserted
  // below - the whole 729 is worthless if the filler quietly pays.
  // JACK on reel 1, KING on reel 2, QUEEN on reel 3: a leading JACK whose run
  // stops at one, and JACK does not pay from two either way.
  const FILLER = [3, 5, 4];
  const fillAround = cells => {
    const f = {};
    for (let ci = 1; ci <= CELLS; ci++)
      if (!cells.includes(ci)) f[ci] = FILLER[Math.floor((ci - 1) / ROWS)];
    return f;
  };
  const FILL_MID = fillAround(midCells);
  const FILL_DIAG = fillAround(diagCells);
  const build = (fill, cells, trip) => {
    const g = new Array(CELLS).fill(0);
    for (const k in fill) g[Number(k) - 1] = fill[k];
    cells.forEach((ci, i) => { g[ci - 1] = trip[i]; });
    return g;
  };
  let fillerBad = 0, fillerFirst = '';
  const fillerCheck = (label, under, want, trip) => {
    for (let L = 1; L <= NLINES; L++)
      if (L !== under && want.lineWin[L - 1] !== 0 && !fillerBad) {
        fillerBad++;
        fillerFirst = `${label} filler pays ${want.lineWin[L - 1]} on line ${L}`
                      + ` for ${trip.map(NAME).join('/')}`;
      }
  };

  // --- (a) all 729 triples on the middle row, (b) the same on a diagonal ---
  for (const [label, fill, cells, under] of
       [['middle-row', FILL_MID, midCells, MID],
        ['diagonal', FILL_DIAG, diagCells, DIAG]])
    for (let a = 1; a <= CELLS; a++)
      for (let b = 1; b <= CELLS; b++)
        for (let c = 1; c <= CELLS; c++) {
          const trip = [a, b, c];
          const grid = build(fill, cells, trip);
          fillerCheck(label, under, evalGrid(grid), trip);
          compare(`${label} ${trip.map(NAME).join(',')}`, grid, drive(grid));
        }
  check(4, 'walk: the filler pays nothing on the four lines not under test',
        fillerBad === 0, fillerBad ? fillerFirst : '1458 triples, both lines');

  // --- (c) multi-line screens: one per distinct total, one per line count ---
  // Enumerated from the strips rather than invented, so every total the machine
  // can ever pay goes through the VM once - including the 90x maximum, which is
  // 2 screens in 27000 and would never turn up by spinning (PITFALLS 12).
  for (const [total, s] of [...byTotal.entries()].sort((a, b) => a[0] - b[0]))
    compare(`total ${total}u (stops ${s.stops.join(',')})`, s.grid, drive(s.grid));
  for (const [n, s] of [...byLines.entries()].sort((a, b) => a[0] - b[0]))
    compare(`${n} paying lines (stops ${s.stops.join(',')})`, s.grid, drive(s.grid));
  check(4, 'walk: the screens driven through the VM span the whole table',
        byTotal.size > 1 && byLines.size > 1,
        `${byTotal.size} distinct totals, line counts ${J([...byLines.keys()].sort())}`);

  const topGot = drive(topScreen.grid);
  compare('MAX screen', topScreen.grid, topGot);
  const pubGot = drive(T7.maxGrid);
  compare('MAX screen (as published)', T7.maxGrid, pubGot);
  check(4, `walk: the ${T7.maxUnits / NLINES}x maximum pays `
           + `${T7.maxUnits} units through the real VM`,
        topGot.units === T7.maxUnits && topGot.mult === T7.maxUnits / NLINES
        && pubGot.units === T7.maxUnits,
        `stops ${J(T7.maxStops)} -> slUnits ${pubGot.units}, mult ${pubGot.mult}; `
        + `expected ${T7.maxUnits} and ${T7.maxUnits / NLINES}, `
        + `lines ${J(pubGot.lineWin)}`);

  // --- (d) leading wilds -------------------------------------------------
  // W W x resolves to reel 3, W x x to reel 2, W W W to WILD itself. The point
  // is that (WILD, run 2) is unreachable - a leading pair of wilds always takes
  // reel 3's symbol - so nothing but three wilds may ever pay slPay3[WILD].
  let wildBad = 0, wildFirst = '', wildN = 0;
  const wildFail = m => { wildBad++; wildFirst = wildFirst || m; };
  for (let x = 1; x <= CELLS; x++)
    for (const trip of [[WILD, WILD, x], [WILD, x, x], [WILD, x, WILD]]) {
      const grid = build(FILL_MID, midCells, trip);
      const want = evalGrid(grid);
      const got = drive(grid);
      wildN++;
      fillerCheck('wild', MID, want, trip);
      compare(`wild ${trip.map(NAME).join(',')}`, grid, got);
      // These interrogate what the VM PAID, not what lineEval() computed -
      // `base === WILD implies run === 3` is true by construction in our own
      // evaluator, so asserting it there proves nothing about the block logic.
      // A leading pair of wilds must take reel 3's symbol, so the line under
      // test pays exactly that symbol's rung:
      const lineUnits = got.lineWin[MID - 1];
      if (lineUnits !== want.lineWin[MID - 1])
        wildFail(`${trip.map(NAME).join(',')} paid ${lineUnits}u on line ${MID}, `
                 + `expected ${want.lineWin[MID - 1]}u`);
      if (x !== WILD && lineUnits === PAY2[WILD - 1] && PAY2[WILD - 1] > 0)
        wildFail(`${trip.map(NAME).join(',')} paid the (WILD, 2) rung, which `
                 + 'no spin can reach');
      if (got.units === PAY3[WILD - 1] && !trip.every(s => s === WILD))
        wildFail(`${trip.map(NAME).join(',')} paid the WILD x3 rung `
                 + `(${PAY3[WILD - 1]}u) without three wilds`);
    }
  const wildGrid = build(FILL_MID, midCells, [WILD, WILD, WILD]);
  const allWild = drive(wildGrid);
  compare('wild WILD,WILD,WILD', wildGrid, allWild);
  if (allWild.units !== PAY3[WILD - 1])
    wildFail(`three wilds paid ${allWild.units}u, expected ${PAY3[WILD - 1]}u`);
  check(4, 'walk: leading wilds take the next symbol; only three pay WILD',
        wildBad === 0, wildBad ? wildFirst : `${wildN + 1} wild screens`);

  // --- (e) sl_eval must stand on its own ---------------------------------
  // The hook exists so a test can write a grid and read a verdict. If it left
  // the previous spin's slHot or slLineWin standing where the new grid does not
  // win, every screen above was read off stale state and proved nothing.
  sls('slHot', new Array(CELLS).fill(1));
  sls('slLineWin', new Array(NLINES).fill(999));
  setv('slUnits', 999);
  const dirtyGrid = build(FILL_MID, midCells, [3, 4, 5]);   // JACK QUEEN KING
  const dirty = drive(dirtyGrid);
  check(4, 'walk: sl_eval overwrites the previous verdict, never adds to it',
        dirty.units === 0 && J(dirty.hot) === J(new Array(CELLS).fill(0))
          && J(dirty.lineWin) === J(new Array(NLINES).fill(0)),
        `units ${dirty.units} hot ${J(dirty.hot)} lineWin ${J(dirty.lineWin)}`);
  check(4, 'walk: every screen the VM evaluated matched the independent rule',
        walkBad === 0,
        walkBad ? `${walkBad} of ${walkN} wrong - ${walkFirst}`
                : `${walkN} screens driven through sl_eval`);
  check(4, 'walk: sl_eval never touches chips', num('chips') === chipsBeforeWalk,
        `${chipsBeforeWalk} -> ${num('chips')}`);
  vm.runtime.currentStepTime = STEP30;

  // =================================================================
  // 3, 5, 7, 8. THE SPIN LOOP - the window rule, the payout, the display
  // =================================================================
  await until(settled, 'settle before spinning');
  watchChips();
  setv('chips', 100000000);

  // fault buckets, counted here and reported in the order the phases were
  // specified rather than the order they could be run in:
  //   win   3: slGrid vs the published strips
  //   units 5: slUnits / slLineWin / slHot vs the independent rule
  //   pay   5: the chips delta        write 5: exactly two writes
  //   face  7: what the nine clones show   pos 7: where they stand
  //   ghost 7: which of them stay lit      read 8: the MULT plaque
  const F = {};
  const fail = (k, m) => { F[k] = (F[k] || 0) + 1; F[k + '1'] = F[k + '1'] || m; };

  const BETS = T7.betLevels.filter(b => b <= 500);
  const stopsSeen = new Set(), symsSeen = new Set();
  let wins = 0, biggest = 0;

  for (let r = 0; r < SPINS; r++) {
    await until(settled, 'settle ' + r);
    setv('bet', BETS[r % BETS.length]);
    await sleep(30);
    // read the level back rather than assuming it took: the bet plaque owns
    // `bet` and everything below is measured against what the VM actually holds
    const bet = num('bet');
    const before = num('chips');
    chipLog.length = 0;

    click(act);
    // A round writes chips twice; waiting on that rather than on `busy` cannot
    // miss a round that starts and finishes between two polls, which a FAST
    // build does routinely. The one-write escape hatch is so that a build that
    // skips the credit on a losing spin reports a FAIL below instead of hanging
    // the harness on a timeout.
    await until(() => chipLog.length >= 2 || (chipLog.length >= 1 && settled()),
                'round ' + r);
    await until(settled, 'settle after ' + r);
    await sleep(20);

    const stops = gls('slStops'), grid = gls('slGrid');
    stopsSeen.add(stops.join(','));
    grid.forEach(s => symsSeen.add(s));

    // --- 3. the window rule: nine cells out of three stops ---------------
    if (!stops.every(s => Number.isInteger(s) && s >= 1 && s <= LEN))
      fail('win', `spin ${r}: slStops ${J(stops)} outside 1..${LEN}`);
    const wantGrid = gridFromStops(stops);
    if (J(grid) !== J(wantGrid))
      fail('win', `spin ${r}: stops ${J(stops)} -> slGrid ${J(grid)}, but the `
                  + `published strips say ${J(wantGrid)}`);

    // --- 5. the payout ---------------------------------------------------
    const want = evalGrid(grid);
    if (num('slUnits') !== want.units)
      fail('units', `spin ${r}: slUnits ${num('slUnits')}, expected `
                    + `${want.units}  grid ${J(grid)}`);
    if (J(gls('slLineWin')) !== J(want.lineWin))
      fail('units', `spin ${r}: slLineWin ${J(gls('slLineWin'))}, expected `
                    + `${J(want.lineWin)}  grid ${J(grid)}`);
    if (J(gls('slHot')) !== J(want.hot))
      fail('units', `spin ${r}: slHot ${J(gls('slHot'))}, expected `
                    + `${J(want.hot)}  grid ${J(grid)}`);

    const won = bet * want.units / NLINES;
    if (!Number.isInteger(won))
      fail('pay', `spin ${r}: bet ${bet} x ${want.units}u / ${NLINES} is not a `
                  + 'whole number of chips');
    if (num('chips') - before !== won - bet)
      fail('pay', `spin ${r}: bet ${bet}, ${want.units}u, chips moved by `
                  + `${num('chips') - before}, expected ${won - bet}`);
    if (num('win') !== won)
      fail('pay', `spin ${r}: win ${num('win')}, expected ${won}`);
    if (chipLog.length !== 2)
      fail('write', `spin ${r}: chips written ${chipLog.length} times `
                    + `(${J(chipLog)}) - expected 2, the debit and the credit`);
    else if (chipLog[0] !== before - bet || chipLog[1] !== before - bet + won)
      fail('write', `spin ${r}: chips went ${before} -> ${J(chipLog)}, expected `
                    + `[${before - bet}, ${before - bet + won}]`);
    if (want.units > 0) { wins++; biggest = Math.max(biggest, want.units); }

    // --- 7. the display --------------------------------------------------
    if (num('slSpin') !== 0)
      fail('pos', `spin ${r}: settled with slSpin ${num('slSpin')}`);
    const shownGrid = await stable(() => J(screenGrid()));
    if (shownGrid !== J(grid))
      fail('face', `spin ${r}: the reels show ${shownGrid}, slGrid says ${J(grid)}`);
    const reels = cl('Reel');
    const idxs = reels.map(t => Number(lv(t, 'cIdx'))).sort((a, b) => a - b);
    if (J(idxs) !== J(Array.from({ length: CELLS }, (_, i) => i + 1)))
      fail('pos', `spin ${r}: the grid's cIdx values are ${J(idxs)}, expected 1..${CELLS}`);
    for (const t of reels) {
      const i = Number(lv(t, 'cIdx'));
      if (!(i >= 1 && i <= CELLS)) continue;
      const col = Math.floor((i - 1) / ROWS) + 1, row = (i - 1) % ROWS + 1;
      if (!t.visible)
        fail('pos', `spin ${r}: cell ${i} (col ${col} row ${row}) is not visible`);
      if (Math.abs(t.x - G.colX[col - 1]) > 0.51 ||
          Math.abs(t.y - G.rowY[row - 1]) > 0.51)
        fail('pos', `spin ${r}: cell ${i} stands at (${t.x}, ${t.y}), geom7 says `
                    + `(${G.colX[col - 1]}, ${G.rowY[row - 1]})`);
      // A win is drawn by dimming the LOSERS, so a losing spin dims nothing:
      // ghost is 0 when slUnits is 0 or the cell is hot, 62 otherwise.
      const wantGhost = (want.units === 0 || want.hot[i - 1] === 1) ? 0 : 62;
      const ghost = Number(t.effects.ghost || 0);
      if (Math.abs(ghost - wantGhost) > 1e-6)
        fail('ghost', `spin ${r}: cell ${i} ghost ${ghost}, expected ${wantGhost} `
                      + `(slUnits ${want.units}, slHot ${want.hot[i - 1]})`);
    }

    // --- 8. the MULT plaque ----------------------------------------------
    const wantTxt = want.units > 0 ? String(want.units / NLINES) : '';
    const shownTxt = await stable(() => readout(3));
    if (shownTxt !== wantTxt)
      fail('read', `spin ${r}: ${want.units}u -> plaque reads "${shownTxt}", `
                   + `expected "${wantTxt}"`);
    if (num('mult') !== want.units / NLINES)
      fail('read', `spin ${r}: mult ${num('mult')}, expected ${want.units / NLINES}`);
  }

  const fc = k => F[k] || 0, fm = k => F[k + '1'] || '';
  check(3, 'window: every cell is the strip position its stop points at',
        fc('win') === 0,
        fc('win') ? fm('win') : `${SPINS} spins, ${stopsSeen.size} distinct stop sets`);
  // No `|| SPINS < 20` escape hatch: a short run must ask for less coverage,
  // not report PASS on no evidence. 9 symbols over 5 spins is 45 cells, and
  // the rarest symbol sits on 1 stop in 30, so a floor rather than a pass.
  check(3, 'window: the spins land on real strip positions, not a private draw',
        symsSeen.size >= Math.min(T7.names.length, 3 + SPINS),
        `${symsSeen.size} of ${T7.names.length} symbols seen over ${SPINS} spins, `
        + `${stopsSeen.size} distinct stop sets`);
  check(5, 'pay: slUnits, slLineWin and slHot are what the payline rule says',
        fc('units') === 0,
        fc('units') ? fm('units')
                    : `${wins} winning spins of ${SPINS}, best ${biggest / NLINES}x`);
  check(5, 'pay: chips move by bet x slUnits / 5 exactly', fc('pay') === 0,
        fc('pay') ? fm('pay') : `bet levels ${J(BETS)}`);
  check(5, 'pay: chips are written exactly twice a round', fc('write') === 0,
        fc('write') ? fm('write') : 'the debit and the credit, never more');

  // =================================================================
  // 2b. LIST LENGTHS after the spins
  // =================================================================
  const afterLens = lens();
  check(2, `lists: still constant length after ${SPINS} spins and ${walkN} evals`,
        J(afterLens) === J(WANT_LEN), `${J(afterLens)} vs ${J(WANT_LEN)}`);

  // =================================================================
  // 5b. THE REELS ACTUALLY TURN, AND THEY STOP LEFT TO RIGHT
  // =================================================================
  // Nothing else in this file reads slSpin except "it is 0 once we settle",
  // which a build whose reels never move satisfies perfectly. Pinning all
  // three slSpin writes to 0 - so the grid snaps straight to its result -
  // passed every other assertion here. The contract says column c turns while
  // slSpin > 3 - c, so a guard written the other way round would stop the
  // reels right to left and nothing would notice.
  await until(settled, 'settle before the spin ladder');
  {
    vm.runtime.quit();                            // stop the 30fps interval
    vm.runtime.currentStepTime = 0.001;
    const seen = [];                 // the slSpin values, in the order they appear
    let earlyBad = 0, earlyFirst = '', rolled = false, prev = null, held = 0;
    click(act);
    for (let f = 0; f < 12000; f++) {
      step(1);
      await sleep(1);                              // real time, for the waits
      const sp_ = num('slSpin');
      if (sp_ !== prev) { seen.push(sp_); prev = sp_; held = 0; } else held++;
      if (num('busy') === 0 && seen.length > 1) break;
      const grid = gls('slGrid');
      // one frame of grace on a transition: the cells repaint from a forever
      // loop, so they are a frame behind the variable that steers them
      if (held < 1) continue;
      for (const t of cl('Reel')) {
        const i = Number(lv(t, 'cIdx'));
        if (!(i >= 1 && i <= CELLS)) continue;
        const col = Math.floor((i - 1) / ROWS) + 1;
        const shows = symOfCostume(t);
        if (sp_ > REELS - col) {                   // this column is still turning
          if (shows !== grid[i - 1]) rolled = true;
        } else if (shows !== grid[i - 1]) {        // it has stopped: it must be final
          earlyBad++;
          earlyFirst = earlyFirst || `slSpin ${sp_}: column ${col} (cell ${i}) `
            + `shows ${NAME(shows)}, but it has stopped and slGrid says `
            + `${NAME(grid[i - 1])}`;
        }
      }
    }
    vm.runtime.currentStepTime = STEP30;
    vm.start();
    await until(settled, 'settle after the spin ladder');
    // 3 -> 2 -> 1 -> 0: strictly falling, starting at REELS, ending at rest
    const ladder = seen.filter((v, k) => k === 0 || v !== seen[k - 1]);
    const falls = ladder.slice(ladder.indexOf(REELS));
    check(5, 'spin: slSpin counts the reels down 3, 2, 1, 0',
          ladder.includes(REELS) && ladder[ladder.length - 1] === 0
          && falls.every((v, k) => k === 0 || v === falls[k - 1] - 1),
          `slSpin went ${J(ladder)}`);
    check(5, 'spin: the reels really turn before they land', rolled,
          rolled ? `${ladder.length - 1} stops` :
          'no cell ever showed anything but its final symbol - the grid '
          + 'snapped straight to the result');
    check(5, 'spin: a reel that has stopped is showing its final symbol',
          earlyBad === 0,
          earlyBad ? `${earlyBad} frames, first: ${earlyFirst}` : 'left to right');
  }

  // =================================================================
  // 6. ATOMICITY - a frame at a time, from the click to the banner
  // =================================================================
  // Driven by hand with the step time pinned (PITFALLS 10b, the boot_race.js
  // idiom): headless the sequencer runs several passes per frame, which is
  // exactly what would hide a one-frame window in which SPIN is live over a
  // settled round. The 30fps interval has to stop for the duration or it would
  // step the VM behind this loop's back.
  await until(settled, 'settle before atomicity');
  {
    setv('bet', 100);
    await sleep(60);
    const bet = num('bet'), before = num('chips');
    chipLog.length = 0;
    vm.runtime.quit();                            // stop the 30fps interval

    let started = false, sawOn = false, ended = false;
    let busyBad = 0, gapBad = 0, fallBad = 0, msgBad = 0, payFrame = -1;
    let startFrame = -1, debitFrame = -1, endFrame = -1, frames = 0;
    const MAXF = 12000;
    click(act);
    for (let f = 0; f < MAXF; f++) {
      step(1);
      await sleep(1);                             // real time, for the waits
      const busy = num('busy'), on = num('roundOn'), msg = num('msgId');
      if (!started) {
        // the click broadcasts `action` and the handler's body runs on the next
        // sequencer pass, which may or may not fall inside this same _step()
        if (busy === 1 || on === 1 || chipLog.length > 0) {
          started = true; startFrame = f;
        } else if (f > 10) break;                 // the click did nothing
        else continue;
      }
      frames++;
      if (on === 1) sawOn = true;
      if (debitFrame < 0 && num('chips') === before - bet) debitFrame = f;
      // roundOn falls inside warped sl_pay, with busy still up
      if (sawOn && on === 0 && !ended) { ended = true; if (busy !== 1) fallBad++; }
      // sl_pay credits and clears roundOn inside one warped call, so by the
      // frame roundOn is seen down, the payout must already be in the log.
      // (The old check here - roundOn 0 and busy 0 before settlement - could
      // never fail without the busy check on the next line failing first.)
      if (ended && payFrame < 0) {
        payFrame = f;
        if (chipLog.length !== 2) gapBad++;
      }
      if (busy === 0) {
        endFrame = f;
        if (!ended) busyBad++;                    // busy dropped mid-round
        if (msg !== 1) msgBad++;
        break;
      }
      if (busy !== 1) busyBad++;
    }
    const w = evalGrid(gls('slGrid'));
    const won = bet * w.units / NLINES;
    check(6, 'atomic: the click opens a round', started && startFrame <= 2,
          started ? 'busy up on frame ' + startFrame : 'the round never started');
    // busy, roundOn and the debit are one non-yielding step, so no frame can
    // see any of them without the others
    check(6, 'atomic: the debit lands in the same frame as busy and roundOn',
          debitFrame === startFrame && sawOn,
          `busy up on frame ${startFrame}, debited on frame ${debitFrame}, `
          + `roundOn seen ${sawOn}`);
    check(6, 'atomic: busy is up on every frame from the click to the banner',
          busyBad === 0,
          busyBad ? `${busyBad} of ${frames} frames had busy = 0 mid-round`
                  : `${frames} frames`);
    check(6, 'atomic: the credit lands in the same step that clears roundOn',
          gapBad === 0 && payFrame >= 0,
          gapBad ? 'roundOn fell with the payout still pending'
                 : `paid and closed on frame ${payFrame}`);
    check(6, 'atomic: roundOn falls while busy is still up', fallBad === 0,
          fallBad ? 'SPIN was live over a settled round' : '');
    check(6, 'atomic: the round closes with roundOn 0, busy 0, msgId 1',
          endFrame >= 0 && msgBad === 0 && num('roundOn') === 0 &&
          num('busy') === 0 && num('msgId') === 1,
          `ended on frame ${endFrame}: roundOn ${num('roundOn')} `
          + `busy ${num('busy')} msgId ${num('msgId')}`);
    check(6, 'atomic: chips written exactly twice across the whole round',
          chipLog.length === 2 && chipLog[0] === before - bet &&
          chipLog[1] === before - bet + won,
          `${J(chipLog)} from ${before}, bet ${bet}, ${w.units}u -> ${won}`);
    vm.runtime.currentStepTime = STEP30;
    vm.start();
  }

  // --- the machine itself ------------------------------------------------
  // Every assertion above is about the nine plates. None of them notices if
  // the frame they sit in, or the paytable beside it, is missing: hiding
  // Paytable outright still scored a clean sweep. The panels ARE the screen.
  for (const [name, xy, size] of [['SlotFrame', G.frameXY, G.frame],
                                  ['Paytable', G.ptXY, G.pt]]) {
    const t = sp(name);
    if (!t) { fail('panel', `${name} is not in the project at all`); continue; }
    if (!t.visible) fail('panel', `${name} is hidden on the slots screen`);
    if (Math.abs(t.x - xy[0]) > 0.51 || Math.abs(t.y - xy[1]) > 0.51)
      fail('panel', `${name} stands at (${t.x}, ${t.y}), geom7 says `
                    + `(${xy[0]}, ${xy[1]})`);
    const c = t.getCostumes()[t.currentCostume];
    const br = c.bitmapResolution || 1;
    const w = c.rotationCenterX * 2 / br, h = c.rotationCenterY * 2 / br;
    if (Math.abs(w - size[0]) > 1 || Math.abs(h - size[1]) > 1)
      fail('panel', `${name} is ${w}x${h}, geom7 says ${size[0]}x${size[1]}`);
  }
  // and the plates have to sit INSIDE the frame, not merely on its lattice
  {
    const f = { l: G.frameXY[0] - G.frame[0] / 2, r: G.frameXY[0] + G.frame[0] / 2,
                b: G.frameXY[1] - G.frame[1] / 2, t: G.frameXY[1] + G.frame[1] / 2 };
    for (let col = 1; col <= REELS; col++)
      for (let row = 1; row <= ROWS; row++) {
        const x = G.colX[col - 1], y = G.rowY[row - 1], h = G.cell / 2;
        if (x - h < f.l || x + h > f.r || y - h < f.b || y + h > f.t)
          fail('panel', `cell (col ${col} row ${row}) at (${x}, ${y}) hangs off `
                        + `the frame ${J(f)}`);
      }
  }
  check(7, 'display: the frame and the paytable are on screen, where geom7 says',
        fc('panel') === 0,
        fc('panel') ? fm('panel')
                    : `frame ${J(G.frame)} at ${J(G.frameXY)}, `
                      + `paytable ${J(G.pt)} at ${J(G.ptXY)}`);

  // ------------------------------------------ 7 and 8, reported in order
  check(7, 'display: the nine reels show the grid that was paid',
        fc('face') === 0, fc('face') ? fm('face') : `${SPINS} spins`);
  check(7, 'display: every cell stands on its geom7 coordinate, once',
        fc('pos') === 0, fc('pos') ? fm('pos')
                                   : `colX ${J(G.colX)} rowY ${J(G.rowY)}`);
  check(7, 'display: the winning cells stay lit and the losers dim to 62',
        fc('ghost') === 0, fc('ghost') ? fm('ghost') : '');
  check(8, 'display: the MULT plaque matches slUnits / 5, and is blank on a loss',
        fc('read') === 0, fc('read') ? fm('read') : '');

  // =================================================================
  // 9. CLONE BUDGET
  // =================================================================
  await until(settled, 'settle before counting');
  const clones = vm.runtime.targets.filter(t => !t.isStage && !t.isOriginal).length;
  const reelClones = cl('Reel').length;
  check(9, 'clones: the whole project stays under 300', clones < 300,
        `${clones} clones (${bootClones} at boot)`);
  check(9, 'clones: the grid is exactly nine reels', reelClones === CELLS,
        reelClones + ' Reel clones');

  // ------------------------------------------------------------- report
  vm.stopAll();
  R.sort((a, b) => a[0] - b[0]);
  console.log('\n============== THE GOLD ROOM ==============');
  for (const [, s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[1] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
