const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const RULES_URL='data/id_e9_manufacturing_2026_rules.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps'};
let route=null,rules=null,i18n={},activeStage=null,deferredInstall=null;

const $=(id)=>document.getElementById(id);
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stageTitle=(stage)=>i18n[stage.id]?.title||stage.title;
const stageAction=(stage)=>i18n[stage.id]?.action||stage.action;
const stageWarning=(stage)=>i18n[stage.id]?.warning||stage.warning;

async function boot(){
  try{
    const [routeRes,rulesRes,i18nRes]=await Promise.all([
      fetch(ROUTE_URL,{cache:'no-store'}),
      fetch(RULES_URL,{cache:'no-store'}),
      fetch(I18N_URL,{cache:'no-store'})
    ]);
    if(!routeRes.ok||!rulesRes.ok||!i18nRes.ok) throw new Error('verified data unavailable');
    route=await routeRes.json();
    rules=await rulesRes.json();
    i18n=await i18nRes.json();
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufaktur · 2026 · paket ${route.packVersion} · diperiksa ${route.lastVerified}`;
    renderCycleStatus();
    renderJourney();
    renderCurrentStageSelector();
    renderNextAction();
    renderEligibility();
    renderDocuments();
    renderGapStage();
    renderGaps();
    updateProgress();
  }catch(err){
    $('routeMeta').textContent='Data rute terverifikasi tidak dapat dimuat. Sambungkan internet dan coba lagi.';
    console.error(err);
  }
}

function renderCycleStatus(){
  const box=$('cycleStatus');
  box.hidden=false;
  if(rules.registration.status==='closed'){
    box.innerHTML=`<strong>Pendaftaran umum manufaktur 2026 sudah ditutup.</strong> ${escapeHtml(rules.registration.statusMessage)} <a href="${rules.source.url}" target="_blank" rel="noopener">Pengumuman resmi ↗</a>`;
  }else{
    box.textContent=rules.registration.statusMessage||'Periksa pengumuman rekrutmen resmi terbaru.';
  }
}

function renderCurrentStageSelector(){
  const select=$('currentStageSelect');
  select.innerHTML='<option value="">Pilih tahap sekarang</option>';
  route.stages.forEach((stage,index)=>{
    const option=document.createElement('option');
    option.value=String(index);
    option.textContent=(index+1)+'. '+stageTitle(stage);
    select.appendChild(option);
  });
}

$('setCurrentStageBtn').addEventListener('click',()=>{
  const value=$('currentStageSelect').value;
  if(value==='')return;
  const index=Number(value);
  const done=route.stages.slice(0,index).map(s=>s.id);
  write(KEYS.done,done);
  renderJourney();
  renderNextAction();
  updateProgress();
});

function renderJourney(){
  const done=new Set(read(KEYS.done,[]));
  $('stageList').innerHTML='';
  route.stages.forEach((stage,index)=>{
    const card=document.createElement('article');
    card.className='stage'+(done.has(stage.id)?' done':'');
    card.innerHTML=`
      <div class="step-no">${done.has(stage.id)?'✓':index+1}</div>
      <div><h3>${escapeHtml(stageTitle(stage))}</h3><p>${escapeHtml(stage.authority)}</p></div>
      <span class="status">${done.has(stage.id)?'Selesai':'Belum selesai'}</span>`;
    card.addEventListener('click',()=>openStage(stage));
    $('stageList').appendChild(card);
  });
}

function openStage(stage){
  activeStage=stage;
  $('stageKind').textContent=stage.kind.replaceAll('_',' ');
  $('stageTitle').textContent=stageTitle(stage);
  $('stageAuthority').textContent=stage.authority;
  $('stageAction').textContent=stageAction(stage);
  $('stageSource').href=stage.sourceUrl;
  const warn=$('stageWarning');
  const warning=stageWarning(stage);
  if(warning){warn.hidden=false;warn.textContent='⚠ '+warning}else{warn.hidden=true;warn.textContent=''}
  const done=new Set(read(KEYS.done,[]));
  $('stageDoneBtn').textContent=done.has(stage.id)?'Batalkan tanda selesai':'Tandai selesai';
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
  renderNextAction();
  updateProgress();
});

function renderNextAction(){
  if(!route||!rules)return;
  const done=new Set(read(KEYS.done,[]));
  const next=route.stages.find(s=>!done.has(s.id));
  const box=$('nextAction');
  box.hidden=false;

  if(done.size===0&&rules.registration.status==='closed'){
    box.innerHTML='<small>LANGKAH BERIKUTNYA</small><h2>Persiapkan siklus rekrutmen resmi berikutnya</h2><p>Pendaftaran umum manufaktur 2026 sudah ditutup. Periksa kelayakan dan kualitas dokumen sekarang; jangan membayar atau mendaftar melalui calo untuk siklus berikutnya.</p><button class="primary" data-go="eligibility">Buka Cek Kelayakan</button>';
  }else if(next){
    box.innerHTML=`<small>LANGKAH BERIKUTNYA</small><h2>${escapeHtml(stageTitle(next))}</h2><p>${escapeHtml(stageAction(next))}</p><button class="primary" data-stage="${escapeHtml(next.id)}">Buka langkah ini</button>`;
  }else{
    box.innerHTML='<small>RUTE SELESAI</small><h2>Semua tahap yang dilacak sudah ditandai selesai</h2><p>Periksa kembali Celah Calo sebelum menganggap rute ini benar-benar tanpa calo.</p><button class="primary" data-go="gaps">Periksa Celah Calo</button>';
  }

  box.querySelector('[data-go]')?.addEventListener('click',e=>switchView(e.currentTarget.dataset.go));
  box.querySelector('[data-stage]')?.addEventListener('click',e=>{
    const stage=route.stages.find(s=>s.id===e.currentTarget.dataset.stage);
    if(stage)openStage(stage);
  });
}

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
      info.innerHTML+=`<div class="hint">Rentang tanggal lahir 2026: ${rule.min} sampai ${rule.max}</div>`;
    }else if(rule.type==='number_max'){
      input=document.createElement('input');
      input.type='number'; input.min='0'; input.step='0.1'; input.placeholder='0'; input.id='elig_'+rule.id;
      info.innerHTML+=`<div class="hint">Maksimum menurut aturan 2026: ${rule.max} tahun</div>`;
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
    out.innerHTML=`<strong>Pemeriksaan belum lengkap.</strong> Jawab semua item terlebih dahulu. Jawaban pada pemeriksaan ini tidak disimpan.`;
    return;
  }
  if(failures.length){
    out.classList.add('risk');
    out.innerHTML='<strong>Ada satu atau lebih kriteria manufaktur umum 2026 yang tidak terpenuhi:</strong><br>'+failures.map(x=>'• '+escapeHtml(x)).join('<br>')+'<br><br>Ini bukan keputusan resmi. Periksa pengumuman resmi.';
  }else{
    out.classList.add('safe');
    out.innerHTML='<strong>Sesuai dengan kriteria manufaktur umum 2026 yang tercantum pada pemeriksaan ini.</strong><br>Pendaftaran 2026 sudah ditutup, jadi hasil ini hanya untuk persiapan. Tunggu pengumuman resmi KP2MI/HRD Korea berikutnya karena persyaratan dapat berubah.';
  }
});

function renderDocuments(){
  const checked=new Set(read(KEYS.docs,[]));
  $('docList').innerHTML='';
  rules.documents.forEach(doc=>{
    const article=document.createElement('article');
    const optional=doc.required?'Wajib pada pengumuman 2026':'Jika tersedia / bersyarat';
    const accept=doc.format==='PDF'?'.pdf':'image/jpeg,.jpg,.jpeg';
    article.innerHTML=`<input class="doc-check" type="checkbox" ${checked.has(doc.id)?'checked':''} aria-label="${escapeHtml(doc.title)}"><div><h3>${escapeHtml(doc.title)} · ${escapeHtml(doc.format)}</h3><p>${escapeHtml(optional)} · maks. ${rules.maxFileSizeMb} MB. ${escapeHtml(doc.note)}</p><div class="doc-tools"><input class="doc-file" type="file" accept="${accept}"><span class="file-status">Belum ada file yang diperiksa</span></div></div>`;
    article.querySelector('.doc-check').addEventListener('change',(e)=>{
      const state=new Set(read(KEYS.docs,[]));
      e.target.checked?state.add(doc.id):state.delete(doc.id);
      write(KEYS.docs,[...state]);
    });
    article.querySelector('.doc-file').addEventListener('change',(e)=>{
      const file=e.target.files?.[0];
      const status=article.querySelector('.file-status');
      if(!file){status.textContent='No file checked yet';status.className='file-status';return}
      const errors=[];
      if(file.size>rules.maxFileSizeMb*1024*1024)errors.push('larger than '+rules.maxFileSizeMb+' MB');
      const lower=file.name.toLowerCase();
      if(doc.format==='PDF'&&!lower.endsWith('.pdf'))errors.push('expected PDF');
      if(doc.format==='JPG'&&!/\.jpe?g$/.test(lower))errors.push('expected JPG/JPEG');
      status.className='file-status '+(errors.length?'bad':'ok');
      status.textContent=errors.length?'Check failed: '+errors.join('; '):'Format/size check passed · '+(file.size/1024/1024).toFixed(2)+' MB';
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
  if(!amount||!payee){out.classList.add('warn');out.textContent='Masukkan nominal dan siapa yang meminta pembayaran.';return}
  if(payee==='broker'||/guarantee|jamin|job|kerja pasti|slc pasti|penempatan pasti/.test(purpose)){
    out.classList.add('risk');
    out.innerHTML='<strong>Risiko tinggi.</strong> Pembayaran kepada calo/individu tidak dapat dianggap sebagai jaminan resmi pemilihan perusahaan EPS. Periksa tujuan dan sumber resmi sebelum membayar.';
    return;
  }
  const known=rules.fees.find(f=>f.amountIdr===amount);
  if(known){
    if(known.kind==='minimum_balance'){
      out.classList.add(payee==='bank'?'safe':'risk');
      out.innerHTML=`<strong>Ini bukan biaya.</strong> Rp${known.amountIdr.toLocaleString('id-ID')} adalah jumlah saldo minimum yang harus tersedia di rekening BNI milik pemohon untuk proses visa 2026. Jangan menyerahkan jumlah ini kepada calo atau individu. <a href="${known.sourceUrl}" target="_blank" rel="noopener">Sumber resmi ↗</a>`;
      return;
    }
    const payeeMatches=payee===known.payeeCategory;
    out.classList.add(payeeMatches?'safe':'warn');
    out.innerHTML=`<strong>Nominal cocok dengan data resmi 2026:</strong> Rp${known.amountIdr.toLocaleString('id-ID')} — ${escapeHtml(known.purpose)}. Jalur pembayaran: ${escapeHtml(known.payee)}. ${payeeMatches?'Penerima yang Anda pilih cocok dengan kategori resmi.':'Nominal cocok, tetapi kategori penerima tidak cocok; jangan bayar sebelum diverifikasi.'} <a href="${known.sourceUrl}" target="_blank" rel="noopener">Sumber resmi ↗</a>`;
    return;
  }
  out.classList.add('warn');
  out.innerHTML='<strong>Nominal ini tidak cocok dengan daftar biaya resmi yang sudah diverifikasi untuk rute ini.</strong> Jangan bayar dulu. Periksa nominal, penerima, tujuan, tahap, dan sumber resmi terbaru.';
});

function renderGapStage(){
  $('gapStage').innerHTML='';
  route.stages.forEach(s=>{
    const o=document.createElement('option');o.value=s.id;o.textContent=stageTitle(s);$('gapStage').appendChild(o);
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
  if(!gaps.length){$('gapList').innerHTML='<div class="gap-item"><p>Belum ada Celah Calo yang dicatat pada perangkat ini.</p></div>';return}
  gaps.forEach(g=>{
    const found=route?.stages.find(s=>s.id===g.stage);
    const stage=found?stageTitle(found):g.stage;
    const el=document.createElement('article');el.className='gap-item';
    el.innerHTML=`<h3>${escapeHtml(stage)}</h3><p>${escapeHtml(g.task)}</p><p><strong>Pembantu:</strong> ${escapeHtml(g.helper)}</p><div class="gap-actions"><button>Hapus</button></div>`;
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

function switchView(viewId){
  document.querySelectorAll('.tab').forEach(b=>b.classList.toggle('active',b.dataset.view===viewId));
  document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===viewId));
  document.getElementById(viewId)?.scrollIntoView({behavior:'smooth',block:'start'});
}
document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.view)));

window.addEventListener('beforeinstallprompt',(e)=>{e.preventDefault();deferredInstall=e;$('installBtn').hidden=false});
$('installBtn').addEventListener('click',async()=>{if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;$('installBtn').hidden=true});
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(console.error));

boot();