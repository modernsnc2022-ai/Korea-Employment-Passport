const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const RULES_URL='data/id_e9_manufacturing_2026_rules.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps'};
let route=null,rules=null,activeStage=null,deferredInstall=null;

const $=(id)=>document.getElementById(id);
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

async function boot(){
  try{
    const [routeRes,rulesRes]=await Promise.all([
      fetch(ROUTE_URL,{cache:'no-store'}),
      fetch(RULES_URL,{cache:'no-store'})
    ]);
    if(!routeRes.ok||!rulesRes.ok) throw new Error('verified data unavailable');
    route=await routeRes.json();
    rules=await rulesRes.json();
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufacturing · 2026 · pack ${route.packVersion} · verified ${route.lastVerified}`;
    renderCycleStatus();
    renderJourney();
    renderEligibility();
    renderDocuments();
    renderGapStage();
    renderGaps();
    updateProgress();
  }catch(err){
    $('routeMeta').textContent='Unable to load verified route. Reconnect and retry.';
    console.error(err);
  }
}

function renderCycleStatus(){
  const box=$('cycleStatus');
  box.hidden=false;
  if(rules.registration.status==='closed'){
    box.innerHTML=`<strong>2026 general manufacturing registration is closed.</strong> ${escapeHtml(rules.registration.statusMessage)} <a href="${rules.source.url}" target="_blank" rel="noopener">Official notice ↗</a>`;
  }else{
    box.textContent=rules.registration.statusMessage||'Check the latest official recruitment notice.';
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
  renderJourney();
  updateProgress();
});

function updateProgress(){
  if(!route)return;
  const done=new Set(read(KEYS.done,[]));
  const count=route.stages.filter(s=>done.has(s.id)).length;
  const pct=route.stages.length?Math.round(count/route.stages.length*100):0;
  $('progressBar').style.width=pct+'%';
  $('progressText').textContent=`${count} / ${route.stages.length} · ${pct}%`;
}

function renderEligibility(){
  const wrap=$('eligibilityForm');
  wrap.innerHTML='';
  rules.eligibility.forEach(rule=>{
    const row=document.createElement('div');
    row.className='elig-row';
    const info=document.createElement('div');
    info.innerHTML=`<strong>${escapeHtml(rule.label)}</strong>`;
    let input;
    if(rule.type==='date_range'){
      input=document.createElement('input');
      input.type='date'; input.id='elig_'+rule.id;
      info.innerHTML+=`<div class="hint">2026 accepted birth dates: ${rule.min} to ${rule.max}</div>`;
    }else if(rule.type==='number_max'){
      input=document.createElement('input');
      input.type='number'; input.min='0'; input.step='0.1'; input.placeholder='0'; input.id='elig_'+rule.id;
      info.innerHTML+=`<div class="hint">Maximum under the 2026 rule: ${rule.max} years</div>`;
    }else{
      input=document.createElement('select');
      input.id='elig_'+rule.id;
      input.innerHTML='<option value="">Pilih</option><option value="yes">Ya, memenuhi</option><option value="no">Tidak / tidak yakin</option>';
    }
    row.append(info,input);
    wrap.appendChild(row);
  });
}

$('checkEligibilityBtn').addEventListener('click',()=>{
  const failures=[],unknown=[];
  rules.eligibility.forEach(rule=>{
    const el=$('elig_'+rule.id);
    const value=el?.value||'';
    if(!value){unknown.push(rule.label);return}
    if(rule.type==='date_range'){
      if(value<rule.min||value>rule.max)failures.push(rule.fail||rule.label);
    }else if(rule.type==='number_max'){
      if(Number(value)>Number(rule.max))failures.push(rule.fail||rule.label);
    }else if(value!=='yes'){
      failures.push(rule.label);
    }
  });
  const out=$('eligibilityResult');
  out.hidden=false;out.className='result';
  if(unknown.length){
    out.classList.add('warn');
    out.innerHTML=`<strong>Incomplete self-check.</strong> Answer all items before using the result. Nothing from this checker is saved.`;
    return;
  }
  if(failures.length){
    out.classList.add('risk');
    out.innerHTML='<strong>Does not match one or more 2026 general manufacturing criteria:</strong><br>'+failures.map(x=>'• '+escapeHtml(x)).join('<br>')+'<br><br>This is not an official decision. Check the official notice.';
  }else{
    out.classList.add('safe');
    out.innerHTML='<strong>Matches the listed 2026 general manufacturing criteria in this self-check.</strong><br>The 2026 registration is already closed, so this result is for preparation only. Wait for the next official KP2MI/HRD Korea recruitment notice because future criteria can change.';
  }
});

function renderDocuments(){
  const checked=new Set(read(KEYS.docs,[]));
  $('docList').innerHTML='';
  rules.documents.forEach(doc=>{
    const article=document.createElement('article');
    const optional=doc.required?'Required in 2026 notice':'If available / conditional';
    article.innerHTML=`<input type="checkbox" ${checked.has(doc.id)?'checked':''} aria-label="${escapeHtml(doc.title)}"><div><h3>${escapeHtml(doc.title)} · ${escapeHtml(doc.format)}</h3><p>${escapeHtml(optional)} · max ${rules.maxFileSizeMb} MB. ${escapeHtml(doc.note)}</p></div>`;
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
  if(payee==='broker'||/guarantee|jamin|job|kerja pasti|slc pasti|penempatan pasti/.test(purpose)){
    out.classList.add('risk');
    out.innerHTML='<strong>High risk.</strong> A private payment cannot be treated as an official EPS employer-selection guarantee. Verify the purpose and official source before paying.';
    return;
  }
  const known=rules.fees.find(f=>f.amountIdr===amount);
  if(known){
    const expectedBank=/bni/i.test(known.payee);
    const payeeMatches=expectedBank?payee==='bank':payee==='official';
    out.classList.add(payeeMatches?'safe':'warn');
    out.innerHTML=`<strong>Exact match in the verified 2026 general-route snapshot:</strong> Rp${known.amountIdr.toLocaleString('id-ID')} for ${escapeHtml(known.purpose)}. Official payment path: ${escapeHtml(known.payee)}. The 2026 registration is closed; do not reuse this amount for a future cycle without a new official notice.`;
    return;
  }
  out.classList.add('warn');
  out.innerHTML='<strong>No exact match in this route’s verified official fee snapshot.</strong> Do not pay yet. Verify amount, payee, purpose, stage and the latest official source.';
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

boot();