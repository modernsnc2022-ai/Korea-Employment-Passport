const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps'};
let route=null,activeStage=null,deferredInstall=null;

const $=(id)=>document.getElementById(id);
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));

const documents=[
  {id:'identity',title:'Identity data matches everywhere',detail:'Compare spelling, date of birth and other identity fields before any official submission.'},
  {id:'photo',title:'Photo matches current notice',detail:'Check current background, framing, dimensions and file requirements before upload.'},
  {id:'education',title:'Education proof is readable',detail:'Use the exact education document required by the current recruitment notice.'},
  {id:'scan',title:'Documents are scanned clearly',detail:'Avoid cropped pages, glare, blur and unreadable text. Use scans where the official notice requires scans.'},
  {id:'current_notice',title:'Current-cycle checklist rechecked',detail:'Do not rely on an old LPK checklist. Recheck the current KP2MI / HRD Korea notice for this stage.'}
];

async function boot(){
  try{
    const res=await fetch(ROUTE_URL,{cache:'no-store'});
    if(!res.ok)throw new Error('route '+res.status);
    route=await res.json();
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufacturing · 2026 · pack ${route.packVersion} · verified ${route.lastVerified}`;
    renderJourney();renderDocuments();renderGapStage();renderGaps();updateProgress();
  }catch(err){
    $('routeMeta').textContent='Unable to load verified route. Reconnect and retry.';
    console.error(err);
  }
}

function renderJourney(){
  const done=new Set(read(KEYS.done,[]));
  $('stageList').innerHTML='';
  route.stages.forEach((stage,index)=>{
    const card=document.createElement('article');
    card.className='stage'+(done.has(stage.id)?' done':'');
    card.innerHTML=`
      <div class="step-no">${done.has(stage.id)?'✓':index+1}</div>
      <div><h3>${escapeHtml(stage.title)}</h3><p>${escapeHtml(stage.authority)}</p></div>
      <span class="status">${done.has(stage.id)?'Completed':'Open'}</span>`;
    card.addEventListener('click',()=>openStage(stage));
    $('stageList').appendChild(card);
  });
}

function openStage(stage){
  activeStage=stage;
  $('stageKind').textContent=stage.kind.replaceAll('_',' ');
  $('stageTitle').textContent=stage.title;
  $('stageAuthority').textContent=stage.authority;
  $('stageAction').textContent=stage.action;
  $('stageSource').href=stage.sourceUrl;
  const warn=$('stageWarning');
  if(stage.warning){warn.hidden=false;warn.textContent='⚠ '+stage.warning}else{warn.hidden=true;warn.textContent=''}
  const done=new Set(read(KEYS.done,[]));
  $('stageDoneBtn').textContent=done.has(stage.id)?'Mark not complete':'Mark complete';
  $('stageDialog').showModal();
}

$('stageDoneBtn').addEventListener('click',(event)=>{
  event.preventDefault();
  if(!activeStage)return;
  const done=new Set(read(KEYS.done,[]));
  done.has(activeStage.id)?done.delete(activeStage.id):done.add(activeStage.id);
  write(KEYS.done,[...done]);
  $('stageDialog').close();
  renderJourney();updateProgress();
});

function updateProgress(){
  if(!route)return;
  const done=new Set(read(KEYS.done,[]));
  const count=route.stages.filter(s=>done.has(s.id)).length;
  const pct=route.stages.length?Math.round(count/route.stages.length*100):0;
  $('progressBar').style.width=pct+'%';
  $('progressText').textContent=`${count} / ${route.stages.length} · ${pct}%`;
}

function renderDocuments(){
  const checked=new Set(read(KEYS.docs,[]));
  $('docList').innerHTML='';
  documents.forEach(doc=>{
    const article=document.createElement('article');
    article.innerHTML=`<input type="checkbox" ${checked.has(doc.id)?'checked':''} aria-label="${escapeHtml(doc.title)}"><div><h3>${escapeHtml(doc.title)}</h3><p>${escapeHtml(doc.detail)}</p></div>`;
    article.querySelector('input').addEventListener('change',(e)=>{
      const state=new Set(read(KEYS.docs,[]));
      e.target.checked?state.add(doc.id):state.delete(doc.id);
      write(KEYS.docs,[...state]);
    });
    $('docList').appendChild(article);
  });
}
$('resetDocs').addEventListener('click',()=>{write(KEYS.docs,[]);renderDocuments()});

$('checkFeeBtn').addEventListener('click',()=>{
  const amount=Number(($('feeAmount').value||'').replace(/[^0-9]/g,''));
  const payee=$('feePayee').value;
  const purpose=$('feePurpose').value.trim().toLowerCase();
  const out=$('feeResult');out.hidden=false;out.className='result';
  if(!amount||!payee){out.classList.add('warn');out.textContent='Enter both the amount and who asked you to pay.';return}
  if(payee==='broker'||/guarantee|jamin|job|kerja pasti|slc pasti/.test(purpose)){
    out.classList.add('risk');
    out.innerHTML='<strong>High risk.</strong> Do not treat a private payment as an official EPS fee or employer-selection guarantee. Verify the purpose and official source before paying.';
    return;
  }
  if(amount===350000){
    out.classList.add(payee==='official'?'safe':'warn');
    out.innerHTML='<strong>Known rule snapshot:</strong> Rp350,000 matches the 2026 psychology-test fee found in the KP2MI/HIMPSI rule. It is valid only with the correct stage and official/approved payee. Recheck the current notice before payment.';
    return;
  }
  if(amount===1260000){
    out.classList.add(payee==='bank'?'safe':'warn');
    out.innerHTML='<strong>Known rule snapshot:</strong> Rp1,260,000 matches the visa + KVAC administration amount used for relevant 2026 cohorts. Verify the current cohort notice and designated payment channel.';
    return;
  }
  if(amount>=1500000&&amount<1600000){
    out.classList.add('warn');
    out.innerHTML='<strong>Possible confusion:</strong> this range may correspond to a required bank balance rather than a fee. Do not transfer it to a person or broker. Verify the current official notice.';
    return;
  }
  out.classList.add('warn');
  out.innerHTML='<strong>No exact match in the current verified snapshot.</strong> Do not pay yet. Verify amount, payee, purpose, stage and the latest official source.';
});

function renderGapStage(){
  $('gapStage').innerHTML='';
  route.stages.forEach(s=>{
    const o=document.createElement('option');o.value=s.id;o.textContent=s.title;$('gapStage').appendChild(o);
  });
}
$('saveGapBtn').addEventListener('click',()=>{
  const task=$('gapTask').value.trim();if(!task)return;
  const gaps=read(KEYS.gaps,[]);
  gaps.push({id:Date.now(),stage:$('gapStage').value,task,helper:$('gapHelper').value,createdAt:new Date().toISOString()});
  write(KEYS.gaps,gaps);$('gapTask').value='';renderGaps();
});
function renderGaps(){
  const gaps=read(KEYS.gaps,[]);$('gapList').innerHTML='';
  if(!gaps.length){$('gapList').innerHTML='<div class="gap-item"><p>No Broker Gaps recorded on this device yet.</p></div>';return}
  gaps.forEach(g=>{
    const stage=route?.stages.find(s=>s.id===g.stage)?.title||g.stage;
    const el=document.createElement('article');el.className='gap-item';
    el.innerHTML=`<h3>${escapeHtml(stage)}</h3><p>${escapeHtml(g.task)}</p><p><strong>Helper:</strong> ${escapeHtml(g.helper)}</p><div class="gap-actions"><button>Delete</button></div>`;
    el.querySelector('button').addEventListener('click',()=>{write(KEYS.gaps,read(KEYS.gaps,[]).filter(x=>x.id!==g.id));renderGaps()});
    $('gapList').appendChild(el);
  });
}
$('emailGapsBtn').addEventListener('click',()=>{
  const gaps=read(KEYS.gaps,[]);if(!gaps.length)return;
  const lines=gaps.map((g,i)=>`${i+1}. [${g.stage}] ${g.task} — ${g.helper}`).join('\n');
  const subject=encodeURIComponent('[KEP Beta] Broker Gap report');
  const body=encodeURIComponent('Broker Gaps from my device:\n\n'+lines+'\n\nNo sensitive document is attached.');
  location.href='mailto:modernsnc2022@gmail.com?subject='+subject+'&body='+body;
});

document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b===btn));
  document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===btn.dataset.view));
}));

window.addEventListener('beforeinstallprompt',(e)=>{e.preventDefault();deferredInstall=e;$('installBtn').hidden=false});
$('installBtn').addEventListener('click',async()=>{if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;$('installBtn').hidden=true});
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(console.error));

function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]))}
boot();