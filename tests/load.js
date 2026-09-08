const fs = require('fs');
const VM = require('scratch-vm');
const vm = new VM();
const buf = fs.readFileSync(process.argv[2]);

vm.loadProject(buf).then(() => {
  const t = vm.runtime.targets;
  console.log("LOADED OK");
  console.log("targets:", t.length);
  let blocks = 0, scripts = 0;
  for (const tg of t) {
    const ids = Object.keys(tg.blocks._blocks);
    blocks += ids.length;
    scripts += tg.blocks._scripts.length;
  }
  console.log("blocks:", blocks, " top-level scripts:", scripts);

  // Every opcode we emit must be one scratch-vm actually implements. It skips
  // unknown opcodes silently - no warning, no error, the block simply never
  // runs - so a one-character typo is invisible in play and in every logic
  // test. `looks_goto_front_back` (the real opcode has no underscores) killed
  // all 20 go-to-layer blocks in the project from v1 to v3.5.
  const unknown = {};
  for (const tg of t) {
    for (const id of Object.keys(tg.blocks._blocks)) {
      const blk = tg.blocks._blocks[id];
      // shadows are the little input slots (numbers, text, dropdown menus).
      // They carry values, are never executed, and have no opcode function.
      if (blk.shadow) continue;
      const op = blk.opcode;
      if (typeof vm.runtime.getOpcodeFunction(op) === 'function') continue;
      if (vm.runtime.getIsHat(op)) continue;
      if (op.startsWith('procedures_') || op.startsWith('argument_')) continue;
      unknown[op] = (unknown[op] || 0) + 1;
    }
  }
  const bad = Object.keys(unknown);
  if (bad.length) {
    console.log("UNIMPLEMENTED OPCODES:",
      bad.map(o => `${o} x${unknown[o]}`).join(", "));
    console.log("These blocks are silently skipped by scratch-vm and never run.");
    process.exit(1);
  }
  console.log("opcodes: all implemented");
  console.log("costumes:", t.reduce((a,x)=>a+x.getCostumes().length,0));
  // list sprites + hat counts
  for (const tg of t) {
    const hats = tg.blocks._scripts
      .map(id => tg.blocks._blocks[id].opcode)
      .reduce((m,o)=>{m[o]=(m[o]||0)+1;return m;},{});
    console.log("  -", tg.getName(), JSON.stringify(hats));
  }
  process.exit(0);
}).catch(e => {
  console.log("LOAD FAILED:", e && e.message ? e.message : e);
  console.log(e && e.stack ? e.stack.split("\n").slice(0,6).join("\n") : "");
  process.exit(1);
});
