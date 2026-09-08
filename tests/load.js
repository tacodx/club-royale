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
