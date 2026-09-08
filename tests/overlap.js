// Detects buttons whose centre is covered by another visible sprite.
// startHats() bypasses hit-testing, so logic tests cannot catch this.
const fs=require('fs'),VM=require('scratch-vm');const vm=new VM();
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const stage=()=>vm.runtime.getTargetForStage();
const gv=n=>{const s=stage();for(const id in s.variables) if(s.variables[id].name===n) return s.variables[id].value;};
const sp=n=>vm.runtime.targets.find(t=>!t.isStage&&t.sprite.name===n&&t.isOriginal);
const cl=n=>vm.runtime.targets.filter(t=>!t.isStage&&t.sprite.name===n&&!t.isOriginal);
const lv=(t,n)=>{for(const id in t.variables) if(t.variables[id].name===n) return t.variables[id].value;};
const click=t=>vm.runtime.startHats('event_whenthisspriteclicked',null,t);
async function until(p,l,m=800){for(let i=0;i<m;i++){if(p())return;await sleep(34);}throw new Error('timeout '+l);}

// stage-space bbox from costume metadata (bitmapResolution 2, centred rotation point)
function bbox(t){
  const c=t.getCostumes()[t.currentCostume];
  if(!c) return null;
  const br=c.bitmapResolution||1, k=(t.size||100)/100;
  const w=(c.rotationCenterX*2/br)*k, h=(c.rotationCenterY*2/br)*k;
  return {l:t.x-w/2,r:t.x+w/2,b:t.y-h/2,t:t.y+h/2};
}
// sprites whose artwork is deliberately transparent / decorative
const IGNORE=new Set(['Msg','Sfx','BJTable','RouletteCtrl','StairsCtrl','WheelPanel']);
function blockers(name){
  const b=sp(name); if(!b||!b.visible) return null;
  const out=[];
  for(const t of vm.runtime.targets){
    if(t.isStage||t===b||!t.visible) continue;
    if(IGNORE.has(t.sprite.name)) continue;
    const o=bbox(t); if(!o) continue;
    if(b.x>o.l&&b.x<o.r&&b.y>o.b&&b.y<o.t) out.push(t.sprite.name);
  }
  return out;
}
const BTNS=['ActionBtn','BackBtn','BetPlus','BetMinus','CashoutBtn','HitBtn',
  'StandBtn','DoubleBtn','SplitBtn','InsureBtn','NoInsBtn','ClearBtn','UndoBtn',
  'RowsSel','RiskSel','BombsSel','DiffSel'];
const faults=[];
function sweep(label){
  for(const n of BTNS){
    const b=blockers(n);
    if(b&&b.length) faults.push(`${label}: ${n} covered by ${[...new Set(b)].join(',')}`);
  }
}
(async()=>{
  await vm.loadProject(fs.readFileSync(process.argv[2]));
  vm.start(); vm.greenFlag(); await sleep(600);
  const tile=n=>cl('MenuTile').find(t=>Number(lv(t,'mIdx'))===n);
  const act=sp('ActionBtn');
  sweep('lobby');
  for(const [i,name] of [[1,'slots'],[2,'plinko'],[5,'roulette']]){
    click(tile(i)); await sleep(320); sweep(name+' idle');
  }
  // mines mid-round
  click(sp('BackBtn')); await sleep(260); click(tile(3)); await sleep(300);
  sweep('mines idle');
  stage().lookupVariableByNameAndType('chips').value=100000;
  click(act); await until(()=>Number(gv('roundOn'))===1,'mines start'); await sleep(200);
  sweep('mines in round');
  click(sp('BackBtn')); await sleep(400);
  // stairs mid-round
  click(tile(6)); await sleep(300); sweep('stairs idle');
  stage().lookupVariableByNameAndType('chips').value=100000;
  click(act); await until(()=>Number(gv('roundOn'))===1,'stairs start'); await sleep(200);
  sweep('stairs in round');
  click(sp('BackBtn')); await sleep(400);
  // blackjack: idle, mid-hand, and an insurance offer if one turns up
  click(tile(4)); await sleep(320); sweep('blackjack idle');
  for(let r=0;r<26;r++){
    await until(()=>Number(gv('bjPhase'))===0&&Number(gv('busy'))===0,'idle',500);
    stage().lookupVariableByNameAndType('chips').value=1000000;
    stage().lookupVariableByNameAndType('bet').value=100;
    click(act); await sleep(220);
    await until(()=>Number(gv('bjPhase'))!==0||Number(gv('busy'))===0,'phase',500);
    if(Number(gv('bjPhase'))===1){ sweep('blackjack insurance'); click(sp('NoInsBtn')); await sleep(200); }
    await until(()=>Number(gv('bjPhase'))===2||Number(gv('bjPhase'))===0,'act',600);
    if(Number(gv('bjPhase'))===2){
      sweep('blackjack in hand');
      if(Number(gv('canSpl'))===1){ click(sp('SplitBtn')); await sleep(400); sweep('blackjack split'); }
      let g=0;
      while(Number(gv('bjPhase'))===2&&g++<14){
        await until(()=>Number(gv('busy'))===0||Number(gv('bjPhase'))!==2,'idle2',500);
        if(Number(gv('bjPhase'))!==2) break;
        click(sp('StandBtn')); await sleep(200);
      }
    }
    await until(()=>Number(gv('bjPhase'))===0,'end',700);
  }
  vm.stopAll();
  console.log('\n=== OVERLAP SWEEP ===');
  const uniq=[...new Set(faults)];
  if(uniq.length===0) console.log('PASS  no button is covered by another visible sprite');
  else uniq.forEach(f=>console.log('FAIL  '+f));
  process.exit(uniq.length?1:0);
})().catch(e=>{console.log('HARNESS ERROR:',e.message);process.exit(2)});
