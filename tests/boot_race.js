// Opens every game BEFORE the clone groups have finished spawning.
//
// This is the only check that catches a sprite left visible on a screen it does
// not belong to. The play_*.js harnesses all wait for the clone count to settle
// before they touch anything, so none of them can see this class of bug - and
// three sprites shipped with it. StairTile, RSpot and Bucket spawned one clone
// per frame, and for those ~0.8s the ORIGINAL sprite carried a non-zero index.
// A refresh arriving in that window passed their `idx > 0` guard and showed the
// original, which the end of the spawn loop then excluded from every later
// refresh by resetting the index to 0. Nothing hid it again: a stray stairs
// tile sat on top of the lobby, and of every other game, until the green flag.
//
// It is driven a FRAME AT A TIME rather than on a timer, for two reasons.
// Headless there is no renderer, so RenderedTarget never calls
// requestRedraw(), the sequencer's `!redrawRequested` condition never breaks
// its loop, and it keeps running passes until WORK_TIME - spawning several
// clones per frame and shrinking the very window this test exists to cover.
// Pinning currentStepTime tiny forces exactly one pass per step, which is what
// a real player's browser does, and makes the coverage independent of how fast
// the machine running the suite happens to be.
//
//   node tests/boot_race.js <sb3>
const fs = require('fs'), VM = require('scratch-vm');

const R = [];
const check = (n, c, e = '') => R.push([c ? 'PASS' : 'FAIL', n, e]);

// lobby tile index -> [label, sprite forming the board, tiles it should show]
const BOARDS = [
  [1, 'Slots',     'Reel',       9],   // 3x3 grid, one clone per cell
  [2, 'Plinko',    'Bucket',    13],   // 12 rows -> 13 buckets
  [5, 'Roulette',  'RSpot',     49],
  [6, 'Stairs',    'StairTile', 27],   // MEDIUM: 9 rows x 3 tiles
  [6, 'Stairs',    'StairMult',  9],
  [7, 'Duck Road', 'DuckMult',  12],
];
// nothing in here may be left visible once we are back in the lobby
const WATCH = ['Bucket', 'RSpot', 'StairTile', 'StairMult', 'DuckMult',
               'DuckCar', 'MineTile', 'Card', 'Reel', 'Spark', 'AvOrb',
               'Coin', 'CoinPip', 'DiceMark', 'DiceThresh', 'DiceBandL'];

function step(vm, n) {
  for (let i = 0; i < n; i++) {
    // WORK_TIME is 0.75 * currentStepTime; tiny means one pass per frame
    vm.runtime.currentStepTime = 0.001;
    vm.runtime._step();
  }
}

(async () => {
  const sb3 = fs.readFileSync(process.argv[2]);
  // 49 RSpot clones is the longest spawn, so anything up to ~55 frames could
  // once have raced it. MenuTile spawns one tile per frame too, so a tile
  // cannot be clicked before it exists - those frames are skipped, not failed.
  const FRAMES = [];
  for (let f = 1; f <= 56; f++) FRAMES.push(f);

  const leaked = [], short = [], never = [];
  let trials = 0;

  for (const [tileIdx, name, sprite, want] of BOARDS) {
    const vm = new VM();
    await vm.loadProject(sb3);
    const orig = n => vm.runtime.targets.find(t => !t.isStage && t.sprite.name === n && t.isOriginal);
    const cl = n => vm.runtime.targets.filter(t => !t.isStage && t.sprite.name === n && !t.isOriginal);
    const lv = (t, n) => { for (const id in t.variables) if (t.variables[id].name === n) return t.variables[id].value; };
    const gv = n => { const s = vm.runtime.getTargetForStage();
      for (const id in s.variables) if (s.variables[id].name === n) return s.variables[id].value; };
    const click = t => vm.runtime.startHats('event_whenthisspriteclicked', null, t);

    for (const f of FRAMES) {
      vm.greenFlag();                       // stopAll() first: clones cleared
      step(vm, f);
      const tile = cl('MenuTile').find(t => Number(lv(t, 'mIdx')) === tileIdx);
      if (!tile) continue;                  // the tile is not on screen yet
      trials++;
      click(tile);
      step(vm, 40);
      if (Number(gv('screen')) === 0) { never.push(`${name}@f${f}`); continue; }
      const shown = cl(sprite).filter(t => t.visible).length;
      if (shown !== want) short.push(`${name}@f${f}: ${shown}/${want} ${sprite}`);

      click(orig('BackBtn'));
      step(vm, 40);
      for (const n of WATCH) {
        const o = orig(n);
        if (o && o.visible) leaked.push(`${name}@f${f}: ${n} original`);
      }
      const stray = WATCH.filter(n => cl(n).some(t => t.visible));
      if (stray.length) leaked.push(`${name}@f${f}: ${stray.join(',')} clones`);
    }
  }

  check('boot race: no sprite is left visible in the lobby', leaked.length === 0,
        leaked.length ? `${leaked.length} of ${trials}: ` + leaked.slice(0, 3).join(' | ') : `${trials} trials clean`);
  check('boot race: every board is complete however early it is opened',
        short.length === 0,
        short.length ? `${short.length} of ${trials}: ` + short.slice(0, 3).join(' | ') : '');
  check('boot race: the game opens at every frame it can be clicked',
        never.length === 0, never.slice(0, 3).join(' | '));

  console.log('\n============== BOOT RACE ==============');
  for (const [s, n, e] of R) console.log(`${s}  ${n}${e ? '   [' + e + ']' : ''}`);
  const bad = R.filter(x => x[0] === 'FAIL').length;
  console.log(`\n${R.length - bad}/${R.length} passed  (${trials} click frames across ${BOARDS.length} boards)`);
  process.exit(bad ? 1 : 0);
})().catch(e => { console.log('HARNESS ERROR:', e.stack); process.exit(2); });
