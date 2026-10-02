const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const RULES_URL='data/id_e9_manufacturing_2026_rules.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
const CONTRACT_URL='data/slc_guardian_2026.json';
const WORKPLACE_URL='data/workplace_reality_v1.json';
const DOCUMENT_PACKS_URL='data/document_packs_2026.json';
const EXACT_ANSWERS_URL='data/exact_answer_rules_v1.json';
const DOCUMENT_EXAMPLES_URL='data/document_examples_v1.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps',contract:'kep.contract',workplace:'kep.workplace',ledger:'kep.costLedger',payroll:'kep.payroll',fieldQuestions:'kep.unresolvedFieldQuestions'};
let route=null,rules=null,contractRules=null,workplaceRules=null,documentPacks=null,documentExamples=null,exactAnswers=null,i18n={},activeStage=null,deferredInstall=null;

const $=(id)=>document.getElementById(id);
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stageTitle=(stage)=>i18n[stage.id]?.title||stage.title;
const stageAction=(stage)=>i18n[stage.id]?.action||stage.action;
const stageWarning=(stage)=>i18n[stage.id]?.warning||stage.warning;

const PHASES=[
  {
    id:'prepare',
    label:'Persiapan & pendaftaran',
    short:'Persiapan',
    stages:['eligibility','registration','exam_fee','biometric','document_verify','exam_card']
  },
  {
    id:'test',
    label:'Ujian & seleksi',
    short:'Ujian',
    stages:['eps_topik','skill_competency','final_selection','psychology_pre_job','mcu1']
  },
  {
    id:'matching',
    label:'Lamaran & pemilihan perusahaan',
    short:'Lamaran',
    stages:['job_application','roster','employer_selection']
  },
  {
    id:'contract_departure',
    label:'SLC, visa & keberangkatan',
    short:'SLC & berangkat',
    stages:['slc','post_slc_requirements','visa_docs','predeparture_training','mcu3_departure','departure']
  },
  {
    id:'korea',
    label:'Masuk Korea & bekerja',
    short:'Di Korea',
    stages:['korea_entry_training','employer_handover','residence_registration','eps_insurance_check','first_payroll_check','labor_support_ready','employment_maintenance']
  }
];

const TOOL_META={
  eligibility:{view:'eligibility',label:'Cek kelayakan',desc:'Periksa syarat rute resmi'},
  documents:{view:'documents',label:'Periksa dokumen',desc:'Format, ukuran dan checklist'},
  fees:{view:'fees',label:'Cek biaya',desc:'Nominal, penerima dan catatan'},
  contract:{view:'contract',label:'Periksa SLC',desc:'Kontrak dan gaji pertama'},
  workplace:{view:'workplace',label:'Cek tempat kerja',desc:'Perusahaan, lokasi dan asrama'},
  payroll:{view:'payroll',label:'Periksa gaji pertama',desc:'Slip gaji, transfer dan potongan'},
  gaps:{view:'gaps',label:'Broker Guardian',desc:'Pesan, biaya dan celah bantuan'}
};

const STAGE_TOOLS={
  eligibility:['eligibility','documents'],
  registration:['documents','fees'],
  exam_fee:['fees'],
  biometric:['documents'],
  document_verify:['documents'],
  exam_card:['documents'],
  eps_topik:[],
  skill_competency:[],
  final_selection:[],
  psychology_pre_job:['fees','documents'],
  mcu1:['fees','documents'],
  job_application:['documents'],
  roster:['gaps'],
  employer_selection:['gaps'],
  slc:['contract','workplace'],
  post_slc_requirements:['documents','fees'],
  visa_docs:['documents','fees'],
  predeparture_training:['documents','fees'],
  mcu3_departure:['documents','fees'],
  departure:['documents','fees'],
  korea_entry_training:['documents'],
  employer_handover:['workplace'],
  residence_registration:['documents'],
  eps_insurance_check:['fees'],
  first_payroll_check:['payroll'],
  labor_support_ready:['gaps'],
  employment_maintenance:['gaps']
};

function currentStage(){
  if(!route)return null;
  const done=new Set(read(KEYS.done,[]));
  return route.stages.find(stage=>!done.has(stage.id))||null;
}

function phaseForStage(stageId){
  return PHASES.find(phase=>phase.stages.includes(stageId))||PHASES[0];
}

function phaseStats(phase,done){
  const existing=phase.stages.filter(id=>route.stages.some(stage=>stage.id===id));
  const complete=existing.filter(id=>done.has(id)).length;
  return {total:existing.length,complete};
}

function renderPhaseNav(){
  if(!route)return;
  const done=new Set(read(KEYS.done,[]));
  const current=currentStage();
  const currentPhase=phaseForStage(current?.id||route.stages.at(-1)?.id);
  const wrap=$('phaseNav');
  wrap.innerHTML='';
  PHASES.forEach((phase,index)=>{
    const stats=phaseStats(phase,done);
    const button=document.createElement('button');
    button.type='button';
    button.className='phase-btn'+(phase.id===currentPhase.id?' active':'')+(stats.total>0&&stats.complete===stats.total?' done':'');
    button.innerHTML=`
      <span class="phase-num">${stats.total>0&&stats.complete===stats.total?'✓':index+1}</span>
      <span class="phase-copy"><strong>${escapeHtml(phase.short)}</strong><small>${escapeHtml(phase.label)}</small></span>
      <span class="phase-count">${stats.complete}/${stats.total}</span>`;
    button.addEventListener('click',()=>{
      switchView('journey',false);
      document.querySelector('[data-phase-group="'+phase.id+'"]')?.scrollIntoView({behavior:'smooth',block:'start'});
    });
    wrap.appendChild(button);
  });
}

function renderContextTools(stage){
  const box=$('contextTools');
  if(!stage){box.hidden=true;box.innerHTML='';return}
  const toolsForStage=STAGE_TOOLS[stage.id]||[];
  box.hidden=false;
  const toolButtons=toolsForStage.map(key=>{
    const meta=TOOL_META[key];
    return `<button type="button" class="context-tool" data-tool-view="${meta.view}"><strong>${escapeHtml(meta.label)}</strong><small>${escapeHtml(meta.desc)}</small></button>`;
  }).join('');
  box.innerHTML=`
    <div class="context-tools-head">
      <strong>Alat untuk tahap ini</strong>
      <small>${toolsForStage.length?'Buka hanya yang diperlukan':'Tidak ada alat tambahan'}</small>
    </div>
    <div class="context-tool-grid">
      ${toolButtons||'<div class="context-tool"><strong>Ikuti sumber resmi</strong><small>Buka tahap untuk instruksi dan tautan resmi.</small></div>'}
    </div>`;
  box.querySelectorAll('[data-tool-view]').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.toolView)));
}

async function boot(){
  try{
    const [routeRes,rulesRes,i18nRes,contractRes,workplaceRes,documentPacksRes,exactAnswersRes,documentExamplesRes]=await Promise.all([
      fetch(ROUTE_URL,{cache:'no-store'}),
      fetch(RULES_URL,{cache:'no-store'}),
      fetch(I18N_URL,{cache:'no-store'}),
      fetch(CONTRACT_URL,{cache:'no-store'}),
      fetch(WORKPLACE_URL,{cache:'no-store'}),
      fetch(DOCUMENT_PACKS_URL,{cache:'no-store'}),
      fetch(EXACT_ANSWERS_URL,{cache:'no-store'}),
      fetch(DOCUMENT_EXAMPLES_URL,{cache:'no-store'})
    ]);
    if(!routeRes.ok||!rulesRes.ok||!i18nRes.ok||!contractRes.ok||!workplaceRes.ok||!documentPacksRes.ok||!exactAnswersRes.ok||!documentExamplesRes.ok) throw new Error('verified data unavailable');
    route=await routeRes.json();
    rules=await rulesRes.json();
    i18n=await i18nRes.json();
    contractRules=await contractRes.json();
    workplaceRules=await workplaceRes.json();
    documentPacks=await documentPacksRes.json();
    exactAnswers=await exactAnswersRes.json();
    documentExamples=await documentExamplesRes.json();
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufaktur · 2026 · paket ${route.packVersion} · diperiksa ${route.lastVerified}`;
    renderCycleStatus();
    renderJourney();
    renderCurrentStageSelector();
    renderPhaseNav();
    renderNextAction();
    renderEligibility();
    renderDocuments();
    renderCostLedger();
    renderContract();
    renderPayroll();
    renderWorkplace();
    renderGapStage();
    renderGaps();
    renderUnresolvedFieldQuestions();
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
  const current=currentStage();
  const index=current?route.stages.findIndex(stage=>stage.id===current.id):-1;
  if(index>=0)select.value=String(index);
}

$('setCurrentStageBtn').addEventListener('click',()=>{
  const value=$('currentStageSelect').value;
  if(value==='')return;
  const index=Number(value);
  const done=route.stages.slice(0,index).map(s=>s.id);
  write(KEYS.done,done);
  renderJourney();
  renderPhaseNav();
  renderNextAction();
  renderDocuments();
  updateProgress();
});

function renderJourney(){
  const done=new Set(read(KEYS.done,[]));
  const current=currentStage();
  const currentPhase=phaseForStage(current?.id||route.stages.at(-1)?.id);
  const wrap=$('stageList');
  wrap.innerHTML='';

  PHASES.forEach((phase,phaseIndex)=>{
    const stages=phase.stages.map(id=>route.stages.find(stage=>stage.id===id)).filter(Boolean);
    if(!stages.length)return;
    const stats=phaseStats(phase,done);
    const group=document.createElement('section');
    const isCurrent=phase.id===currentPhase.id;
    const isDone=stats.complete===stats.total;
    group.className='phase-group'+(isCurrent?' current':'')+(isDone?' done':'');
    group.dataset.phaseGroup=phase.id;

    const details=document.createElement('details');
    details.open=isCurrent;
    const summary=document.createElement('summary');
    summary.innerHTML=`
      <span class="phase-summary-main">
        <span class="phase-num">${isDone?'✓':phaseIndex+1}</span>
        <span><strong>${escapeHtml(phase.label)}</strong><small>${stats.total} tahap</small></span>
      </span>
      <span class="phase-summary-status">${isDone?'Selesai':isCurrent?'Sedang berjalan':stats.complete+'/'+stats.total}</span>`;
    details.appendChild(summary);

    const list=document.createElement('div');
    list.className='phase-stage-list';
    stages.forEach(stage=>{
      const index=route.stages.findIndex(item=>item.id===stage.id);
      const isStageDone=done.has(stage.id);
      const isStageCurrent=current?.id===stage.id;
      const card=document.createElement('article');
      card.className='stage'+(isStageDone?' done':'')+(isStageCurrent?' current':'');
      card.innerHTML=`
        <div class="step-no">${isStageDone?'✓':index+1}</div>
        <div><h3>${escapeHtml(stageTitle(stage))}</h3><p>${escapeHtml(stage.authority)}</p></div>
        <span class="status">${isStageDone?'Selesai':isStageCurrent?'Sekarang':'Berikutnya'}</span>`;
      card.addEventListener('click',()=>openStage(stage));
      list.appendChild(card);
    });
    details.appendChild(list);
    group.appendChild(details);
    wrap.appendChild(group);
  });
}

function renderExactAnswers(stage){
  const section=$('exactAnswerSection');
  const list=$('exactAnswerList');
  if(!exactAnswers?.answers?.length){
    section.hidden=true;
    list.innerHTML='';
    return;
  }

  const answers=exactAnswers.answers.filter(item=>item.stages?.includes(stage.id));
  if(!answers.length){
    section.hidden=true;
    list.innerHTML='';
    return;
  }

  section.hidden=false;
  list.innerHTML=answers.map((item,index)=>{
    const blocks=(item.doNotDo||[]).map(text=>'• '+escapeHtml(text)).join('<br>');
    return `<details class="exact-card" ${index===0?'open':''}>
      <summary>${escapeHtml(item.question)}</summary>
      <div class="exact-body">
        <div class="exact-line answer"><strong>Jawaban:</strong>${escapeHtml(item.answer)}</div>
        <div class="exact-line write"><strong>Tulis / lakukan seperti ini:</strong>${escapeHtml(item.writeExactly)}</div>
        <div class="exact-line"><strong>Mengapa:</strong>${escapeHtml(item.why)}</div>
        ${blocks?'<div class="exact-line block"><strong>Jangan:</strong>'+blocks+'</div>':''}
        <div class="exact-line"><strong>Status:</strong>${item.verificationStatus==='verified'?'Terverifikasi':'Perlu cek ulang cohort'} · diperiksa ${escapeHtml(item.verifiedAt||'')}</div>
        <a class="source" href="${item.sourceUrl}" target="_blank" rel="noopener">Lihat dasar resmi ↗</a>
      </div>
    </details>`;
  }).join('');
}

function openStage(stage){
  activeStage=stage;
  const index=route.stages.findIndex(item=>item.id===stage.id);
  const phase=phaseForStage(stage.id);
  const done=new Set(read(KEYS.done,[]));
  const firstIncompleteIndex=route.stages.findIndex(item=>!done.has(item.id));
  const isDone=done.has(stage.id);
  const canComplete=isDone||firstIncompleteIndex===-1||index<=firstIncompleteIndex;
  const next=route.stages[index+1]||null;

  $('stageKind').textContent='Tahap '+(index+1)+' dari '+route.stages.length+' · '+phase.short;
  $('stageTitle').textContent=stageTitle(stage);
  $('stageAuthority').textContent=stage.authority;
  $('stageAction').textContent=stageAction(stage);
  $('stageSource').href=stage.sourceUrl;
  const officialAction=$('stageOfficialAction');
  if(stage.officialActionUrl){
    officialAction.hidden=false;
    officialAction.href=stage.officialActionUrl;
    officialAction.textContent=(stage.officialActionLabel||'Buka layanan resmi')+' ↗';
  }else{
    officialAction.hidden=true;
    officialAction.href='#';
    officialAction.textContent='Buka layanan resmi ↗';
  }
  renderExactAnswers(stage);
  const warn=$('stageWarning');
  const warning=stageWarning(stage);
  if(warning){warn.hidden=false;warn.textContent='⚠ '+warning}else{warn.hidden=true;warn.textContent=''}

  const hint=$('stageNextHint');
  if(isDone){
    hint.innerHTML='<strong>Sudah selesai.</strong> Jika dibatalkan, tahap ini dan semua tahap setelahnya akan dibuka kembali agar urutan tetap konsisten.';
  }else if(!canComplete){
    const current=route.stages[firstIncompleteIndex];
    hint.innerHTML='<strong>Belum dapat ditandai selesai.</strong> Selesaikan tahap sekarang terlebih dahulu: '+escapeHtml(stageTitle(current))+'.';
  }else if(next){
    hint.innerHTML='<strong>Setelah tahap ini:</strong> '+escapeHtml(stageTitle(next));
  }else{
    hint.innerHTML='<strong>Ini tahap terakhir.</strong> Setelah selesai, periksa kembali apakah masih ada Celah Calo.';
  }

  const doneBtn=$('stageDoneBtn');
  doneBtn.disabled=!canComplete;
  doneBtn.textContent=isDone?'Batalkan tahap ini & setelahnya':canComplete?'Tandai selesai & lanjut':'Selesaikan tahap sebelumnya dulu';
  $('stageDialog').showModal();
}

$('stageDoneBtn').addEventListener('click',(event)=>{
  event.preventDefault();
  if(!activeStage)return;
  const done=new Set(read(KEYS.done,[]));
  const index=route.stages.findIndex(stage=>stage.id===activeStage.id);
  const firstIncompleteIndex=route.stages.findIndex(stage=>!done.has(stage.id));

  if(done.has(activeStage.id)){
    route.stages.slice(index).forEach(stage=>done.delete(stage.id));
  }else{
    if(firstIncompleteIndex!==-1&&index!==firstIncompleteIndex)return;
    done.add(activeStage.id);
  }

  write(KEYS.done,[...done]);
  $('stageDialog').close();
  renderJourney();
  renderPhaseNav();
  renderNextAction();
  renderDocuments();
  renderCurrentStageSelector();
  updateProgress();
  switchView('journey',false);
  document.querySelector('.flow-dashboard')?.scrollIntoView({behavior:'smooth',block:'start'});
});

function renderNextAction(){
  if(!route||!rules)return;
  const done=new Set(read(KEYS.done,[]));
  const next=route.stages.find(s=>!done.has(s.id));
  const box=$('nextAction');
  box.hidden=false;

  if(done.size===0&&rules.registration.status==='closed'){
    box.innerHTML='<small>LANGKAH BERIKUTNYA</small><h2>Persiapkan siklus rekrutmen resmi berikutnya</h2><p>Pendaftaran umum manufaktur 2026 sudah ditutup. Mulai dari cek kelayakan, lalu siapkan dokumen sesuai pengumuman siklus berikutnya.</p><button class="primary" data-go="eligibility">Mulai dari Cek Kelayakan</button>';
    renderContextTools(route.stages[0]);
  }else if(next){
    const toolKeys=STAGE_TOOLS[next.id]||[];
    const firstTool=toolKeys.length?TOOL_META[toolKeys[0]]:null;
    const actionButton=firstTool
      ? `<button class="primary" data-go="${firstTool.view}">${escapeHtml(firstTool.label)}</button><button class="secondary" data-stage="${escapeHtml(next.id)}">Lihat instruksi tahap</button>`
      : `<button class="primary" data-stage="${escapeHtml(next.id)}">Buka langkah ini</button>`;
    box.innerHTML=`<small>LANGKAH BERIKUTNYA</small><h2>${escapeHtml(stageTitle(next))}</h2><p>${escapeHtml(stageAction(next))}</p>${actionButton}`;
    renderContextTools(next);
  }else{
    box.innerHTML='<small>RUTE SELESAI</small><h2>Semua tahap yang dilacak sudah ditandai selesai</h2><p>Periksa kembali Celah Calo sebelum menganggap rute ini benar-benar tanpa calo.</p><button class="primary" data-go="gaps">Periksa Celah Calo</button>';
    renderContextTools(null);
  }

  box.querySelectorAll('[data-go]').forEach(btn=>btn.addEventListener('click',e=>switchView(e.currentTarget.dataset.go)));
  box.querySelectorAll('[data-stage]').forEach(btn=>btn.addEventListener('click',e=>{
    const stage=route.stages.find(s=>s.id===e.currentTarget.dataset.stage);
    if(stage)openStage(stage);
  }));
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

function readImageRatio(file){
  return new Promise((resolve,reject)=>{
    const url=URL.createObjectURL(file);
    const img=new Image();
    img.onload=()=>{const ratio=img.width/img.height;URL.revokeObjectURL(url);resolve(ratio)};
    img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('image read failed'))};
    img.src=url;
  });
}


function normalizeSearch(value){
  return String(value||'')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[^a-z0-9\s]/g,' ')
    .replace(/\s+/g,' ')
    .trim();
}

function fieldAnswerHtml(item){
  const dont=(item.doNotDo||[]).map(text=>'• '+escapeHtml(text)).join('<br>');
  return `<article class="field-match">
    <strong>${escapeHtml(item.question)}</strong>
    <div class="write-this">${escapeHtml(item.answer)}</div>
    <div class="exact-body">
      <div class="exact-line write"><strong>Tulis / lakukan seperti ini:</strong>${escapeHtml(item.writeExactly)}</div>
      <div class="exact-line"><strong>Mengapa:</strong>${escapeHtml(item.why)}</div>
      ${dont?'<div class="exact-line block"><strong>Jangan:</strong>'+dont+'</div>':''}
      <a class="source" href="${item.sourceUrl}" target="_blank" rel="noopener">Dasar resmi ↗</a>
    </div>
  </article>`;
}

function findExactFieldAnswers(query){
  if(!exactAnswers?.answers?.length)return [];
  const q=normalizeSearch(query);
  if(!q)return [];
  const tokens=q.split(' ').filter(token=>token.length>1);
  const current=currentStage();
  return exactAnswers.answers
    .map(item=>{
      const hay=normalizeSearch([item.question,item.answer,item.writeExactly,item.why,...(item.doNotDo||[])].join(' '));
      let score=0;
      if(current&&item.stages?.includes(current.id))score+=10;
      if(hay.includes(q))score+=20;
      tokens.forEach(token=>{if(hay.includes(token))score+=2});
      return {item,score};
    })
    .filter(row=>row.score>0)
    .sort((a,b)=>b.score-a.score)
    .slice(0,5)
    .map(row=>row.item);
}

$('fieldHelpBtn').addEventListener('click',()=>{
  const query=$('fieldHelpQuery').value.trim();
  const out=$('fieldHelpResult');
  out.hidden=false;
  out.className='result';
  if(!query){
    out.classList.add('warn');
    out.textContent='Ketik nama kolom atau hal yang membingungkan terlebih dahulu.';
    return;
  }

  const matches=findExactFieldAnswers(query);
  if(matches.length){
    out.classList.add('safe');
    out.innerHTML='<strong>Jawaban terverifikasi ditemukan.</strong><div class="field-match-list">'+matches.map(fieldAnswerHtml).join('')+'</div>';
    return;
  }

  out.classList.add('warn');
  out.innerHTML=`<strong>Belum ada jawaban terverifikasi untuk “${escapeHtml(query)}”.</strong>
    <p>Jangan isi berdasarkan tebakan, aturan lama, atau jawaban sektor lain. Simpan pertanyaan ini untuk diverifikasi sebelum submit.</p>
    <button id="saveUnresolvedFieldBtn" class="secondary" type="button">Simpan pertanyaan yang belum terjawab</button>`;

  const saveUnresolvedBtn=out.querySelector('#saveUnresolvedFieldBtn');
  saveUnresolvedBtn?.addEventListener('click',()=>{
    const stage=currentStage();
    const list=read(KEYS.fieldQuestions,[]);
    const key=normalizeSearch(query)+'|'+(stage?.id||'unknown');
    if(!list.some(item=>item.key===key)){
      list.unshift({
        key,
        question:query,
        stageId:stage?.id||'unknown',
        stageTitle:stage?stageTitle(stage):'Unknown',
        createdAt:new Date().toISOString(),
        status:'needs_official_verification'
      });
      write(KEYS.fieldQuestions,list);
      renderUnresolvedFieldQuestions();
    }
    saveUnresolvedBtn.disabled=true;
    saveUnresolvedBtn.textContent='Tersimpan — jangan submit sampai terverifikasi';
  });
});

$('fieldHelpQuery').addEventListener('keydown',(event)=>{
  if(event.key==='Enter'){
    event.preventDefault();
    $('fieldHelpBtn').click();
  }
});

function renderDocumentExamples(stageId){
  const section=$('documentExampleSection');
  const list=$('documentExampleList');
  if(!documentExamples?.samples?.length){
    section.hidden=true;
    list.innerHTML='';
    return;
  }

  const samples=documentExamples.samples.filter(sample=>sample.stages?.includes(stageId));
  if(!samples.length){
    section.hidden=true;
    list.innerHTML='';
    return;
  }

  section.hidden=false;
  list.innerHTML=samples.map((sample,index)=>{
    const rows=(sample.rows||[]).map(([label,value])=>`
      <div class="example-row"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value)}</span></div>`
    ).join('');
    const checks=(sample.checks||[]).map(item=>'<li>'+escapeHtml(item)+'</li>').join('');
    return `<details class="example-card" ${index===0?'open':''}>
      <summary><span>${escapeHtml(sample.title)}</span><span>Contoh</span></summary>
      <div class="example-banner">${escapeHtml(documentExamples.policy?.banner||'DATA CONTOH — JANGAN DISALIN')}</div>
      <div class="example-body">
        <div class="example-table">${rows}</div>
        ${checks?'<ul class="example-checks">'+checks+'</ul>':''}
        <p class="example-note">${escapeHtml(documentExamples.policy?.note||'Ganti semua data contoh dengan data Anda sendiri.')}</p>
        <a class="source" href="${sample.sourceUrl}" target="_blank" rel="noopener">Dasar resmi contoh ↗</a>
      </div>
    </details>`;
  }).join('');
}

function documentPackForStage(stageId){
  if(!documentPacks?.packs?.length)return null;
  return documentPacks.packs.find(pack=>pack.appliesTo?.includes(stageId))||null;
}

function renderDocuments(){
  if(!documentPacks||!route)return;
  const checked=new Set(read(KEYS.docs,[]));
  const stage=currentStage()||route.stages.at(-1);
  const pack=documentPackForStage(stage?.id);
  renderDocumentExamples(stage?.id);
  const context=$('docStageContext');
  const list=$('docList');
  list.innerHTML='';

  if(!pack){
    context.innerHTML=`<strong>Belum ada paket dokumen untuk tahap ini.</strong><p class="muted">Buka sumber resmi tahap ${escapeHtml(stageTitle(stage))} dan jangan gunakan checklist dari tahap lain.</p><a class="source" href="${stage.sourceUrl}" target="_blank" rel="noopener">Buka sumber resmi ↗</a>`;
    return;
  }

  const statusLabel={
    verified:'Terverifikasi untuk pendaftaran 2026',
    verified_general_2026:'Terverifikasi pada proses reguler 2026',
    verified_call_2026:'Berdasarkan panggilan keberangkatan 2026',
    awaiting_sector_notice:'Menunggu pengumuman manufaktur yang sesuai',
    source_guided:'Sumber resmi saja — rincian belum dikunci',
    verified_practice:'Checklist bukti kerja'
  }[pack.status]||pack.status;

  context.innerHTML=`
    <div class="doc-context-head">
      <div><small>TAHAP SEKARANG</small><strong>${escapeHtml(stageTitle(stage))}</strong></div>
      <span class="doc-status">${escapeHtml(statusLabel)}</span>
    </div>
    <h3>${escapeHtml(pack.title)}</h3>
    <p>${escapeHtml(pack.message||'')}</p>
    <a class="source" href="${pack.sourceUrl}" target="_blank" rel="noopener">Buka sumber resmi paket ini ↗</a>`;

  if(!pack.items?.length){
    list.innerHTML='<article><div><h3>Jangan gunakan daftar dari tahap/sector lain</h3><p>Checklist sengaja dikosongkan sampai sumber yang sesuai dengan rute ini terverifikasi. Ini mencegah dokumen lama atau sektor lain dianggap sebagai persyaratan resmi.</p></div></article>';
    return;
  }

  pack.items.forEach(doc=>{
    const article=document.createElement('article');
    const optional=doc.required?'Wajib / perlu disiapkan':'Jika tersedia / bersyarat';
    const formatLabel=doc.format?' · '+doc.format:'';
    const maxSize=pack.maxFileSizeMb||null;
    const sizeLabel=maxSize?' · maks. '+maxSize+' MB':'';
    const fileTools=doc.validation==='file'
      ? `<div class="doc-tools"><input class="doc-file" type="file" accept="${doc.format==='PDF'?'.pdf':'image/jpeg,.jpg,.jpeg'}"><span class="file-status">Belum ada file yang diperiksa</span></div>`
      : '';

    article.innerHTML=`<input class="doc-check" type="checkbox" ${checked.has(doc.id)?'checked':''} aria-label="${escapeHtml(doc.title)}"><div><h3>${escapeHtml(doc.title)}${formatLabel}</h3><p>${escapeHtml(optional)}${sizeLabel}. ${escapeHtml(doc.note||'')}</p>${fileTools}</div>`;

    article.querySelector('.doc-check').addEventListener('change',(e)=>{
      const state=new Set(read(KEYS.docs,[]));
      e.target.checked?state.add(doc.id):state.delete(doc.id);
      write(KEYS.docs,[...state]);
    });

    const fileInput=article.querySelector('.doc-file');
    if(fileInput){
      fileInput.addEventListener('change',async(e)=>{
        const file=e.target.files?.[0];
        const status=article.querySelector('.file-status');
        if(!file){status.textContent='Belum ada file yang diperiksa';status.className='file-status';return}
        const errors=[];
        if(maxSize&&file.size>maxSize*1024*1024)errors.push('ukuran lebih dari '+maxSize+' MB');
        const lower=file.name.toLowerCase();
        if(doc.format==='PDF'&&!lower.endsWith('.pdf'))errors.push('format harus PDF');
        if(doc.format==='JPG'&&!/\.jpe?g$/.test(lower))errors.push('format harus JPG/JPEG');
        if(/photo/i.test(doc.id)&&!errors.length){
          try{
            const ratio=await readImageRatio(file);
            const target=3.5/4.5;
            if(Math.abs(ratio-target)>0.04)errors.push('rasio foto tidak mendekati 3.5 × 4.5');
          }catch{
            errors.push('dimensi foto tidak dapat dibaca');
          }
        }
        status.className='file-status '+(errors.length?'bad':'ok');
        status.textContent=errors.length?'Periksa ulang: '+errors.join('; '):'Format/ukuran lolos pemeriksaan · '+(file.size/1024/1024).toFixed(2)+' MB';
      });
    }
    list.appendChild(article);
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
    const scopeNote=known.conditional&&known.scope?' <strong>Berlaku bersyarat:</strong> '+escapeHtml(known.scope)+'.':'';
    out.innerHTML=`<strong>Nominal cocok dengan data resmi 2026:</strong> Rp${known.amountIdr.toLocaleString('id-ID')} — ${escapeHtml(known.purpose)}. Jalur pembayaran: ${escapeHtml(known.payee)}. ${payeeMatches?'Penerima yang Anda pilih cocok dengan kategori resmi.':'Nominal cocok, tetapi kategori penerima tidak cocok; jangan bayar sebelum diverifikasi.'}${scopeNote} <a href="${known.sourceUrl}" target="_blank" rel="noopener">Sumber resmi ↗</a>`;
    return;
  }
  out.classList.add('warn');
  out.innerHTML='<strong>Nominal ini tidak cocok dengan daftar biaya resmi yang sudah diverifikasi untuk rute ini.</strong> Jangan bayar dulu. Periksa nominal, penerima, tujuan, tahap, dan sumber resmi terbaru.';
});



function classifyLedgerEntry(entry){
  const known=rules.fees.find(f=>f.amountIdr===entry.amount);
  if(known?.kind==='minimum_balance')return {kind:'balance',label:'Saldo minimum, bukan biaya',known};
  if(known){
    const payeeMatches=entry.payee===known.payeeCategory;
    return {kind:payeeMatches?'official':'mismatch',label:payeeMatches?'Cocok dengan biaya resmi':'Nominal resmi, penerima tidak cocok',known};
  }
  if(entry.payee==='broker'||entry.payee==='lpk')return {kind:'private',label:'Biaya privat / belum terverifikasi'};
  return {kind:'unknown',label:'Belum ditemukan pada daftar resmi'};
}

function renderCostLedger(){
  if(!rules)return;
  $('knownCostList').innerHTML=rules.fees.map(f=>{
    const label=f.kind==='minimum_balance'?'Saldo minimum — bukan biaya':'Biaya resmi';
    const scope=f.conditional&&f.scope?'<p><strong>Bersyarat:</strong> '+escapeHtml(f.scope)+'</p>':'';
    return `<article class="cost-item"><h3>Rp${f.amountIdr.toLocaleString('id-ID')} · ${escapeHtml(label)}</h3><p>${escapeHtml(f.purpose)}</p><p>${escapeHtml(f.payee)}</p>${scope}<p><a href="${f.sourceUrl}" target="_blank" rel="noopener">Sumber resmi ↗</a></p></article>`;
  }).join('');

  const entries=read(KEYS.ledger,[]);
  let official=0,privateUnknown=0,balance=0;
  $('ledgerList').innerHTML='';
  if(!entries.length)$('ledgerList').innerHTML='<div class="gap-item"><p>Belum ada pembayaran yang dicatat.</p></div>';

  entries.forEach(entry=>{
    const classification=classifyLedgerEntry(entry);
    if(classification.kind==='official')official+=entry.amount;
    else if(classification.kind==='balance')balance+=entry.amount;
    else privateUnknown+=entry.amount;

    const item=document.createElement('article');
    item.className='gap-item';
    item.innerHTML=`<h3>Rp${entry.amount.toLocaleString('id-ID')} · ${escapeHtml(entry.purpose||'Tanpa keterangan')}</h3><p><strong>Status:</strong> ${escapeHtml(classification.label)}</p><p><strong>Penerima:</strong> ${escapeHtml(entry.payee)}</p><p class="muted">${new Date(entry.createdAt).toLocaleDateString('id-ID')}</p><div class="gap-actions"><button>Hapus</button></div>`;
    item.querySelector('button').addEventListener('click',()=>{
      write(KEYS.ledger,read(KEYS.ledger,[]).filter(x=>x.id!==entry.id));
      renderCostLedger();
    });
    $('ledgerList').appendChild(item);
  });

  $('costSummary').innerHTML=`
    <article><strong>Rp${official.toLocaleString('id-ID')}</strong><span>cocok dengan biaya resmi</span></article>
    <article><strong>Rp${privateUnknown.toLocaleString('id-ID')}</strong><span>privat / tidak terjelaskan</span></article>
    <article><strong>Rp${balance.toLocaleString('id-ID')}</strong><span>saldo minimum, bukan pengeluaran</span></article>`;
}

$('addLedgerBtn').addEventListener('click',()=>{
  const amount=Number(($('ledgerAmount').value||'').replace(/[^0-9]/g,''));
  const purpose=$('ledgerPurpose').value.trim();
  const payee=$('ledgerPayee').value;
  if(!amount||!payee)return;
  const entries=read(KEYS.ledger,[]);
  entries.unshift({id:Date.now(),amount,purpose,payee,createdAt:new Date().toISOString()});
  write(KEYS.ledger,entries);
  $('ledgerAmount').value='';
  $('ledgerPurpose').value='';
  $('ledgerPayee').value='';
  renderCostLedger();
}
);

function renderContract(){
  if(!contractRules)return;
  const saved=read(KEYS.contract,{});
  const wrap=$('contractForm');
  wrap.innerHTML='';
  contractRules.fields.forEach(field=>{
    const label=document.createElement('label');
    if(['enterpriseName','enterpriseLocation','workplace','jobDescription','holidays'].includes(field.id)) label.className='wide';
    label.append(document.createTextNode(field.label));
    let input;
    if(field.type==='select'){
      input=document.createElement('select');
      input.innerHTML='<option value="">Pilih</option>'+field.options.map(o=>`<option>${escapeHtml(o)}</option>`).join('');
    }else{
      input=document.createElement('input');
      input.type=field.type==='number'?'number':field.type==='time'?'time':'text';
      if(field.type==='number')input.min='0';
    }
    input.id='contract_'+field.id;
    input.value=saved[field.id]??'';
    input.addEventListener('change',saveContractLocally);
    label.appendChild(input);
    wrap.appendChild(label);
  });
  $('contractNotes').innerHTML=contractRules.notes.map(n=>'<li>'+escapeHtml(n)+'</li>').join('');
  $('contractSource').href=contractRules.source.law;
}


function extractSlcValue(text, patterns){
  for(const pattern of patterns){
    const match=text.match(pattern);
    if(match?.[1])return match[1].trim().replace(/[|]+$/,'').trim();
  }
  return '';
}

$('parseSlcBtn').addEventListener('click',()=>{
  const text=$('slcText').value||'';
  const out=$('parseSlcResult');
  out.hidden=false;
  out.className='result';
  if(!text.trim()){
    out.classList.add('warn');
    out.textContent='Tempel teks SLC terlebih dahulu.';
    return;
  }

  const extracted={
    enterpriseName:extractSlcValue(text,[
      /(?:업체명|Name of the enterprise)\s*[:：-]?\s*([^\n\r]{2,80}?)(?=\s*(?:전화번호|Phone number|소재지|Location of the enterprise|$))/i
    ]),
    enterpriseLocation:extractSlcValue(text,[
      /(?:소재지|Location of the enterprise)\s*[:：-]?\s*([^\n\r]{4,140}?)(?=\s*(?:성명|Name of the employer|근로자|Employee|$))/i
    ]),
    workplace:extractSlcValue(text,[
      /(?:근로장소|Place of employment)\s*[:：-]?\s*([^\n\r]{3,140})/i
    ]),
    industry:extractSlcValue(text,[
      /(?:업종|Industry)\s*[:：-]?\s*([^\n\r]{2,80})/i
    ]),
    jobDescription:extractSlcValue(text,[
      /(?:직무내용|Job description)\s*[:：-]?\s*([^\n\r]{2,140})/i
    ]),
    contractMonths:extractSlcValue(text,[
      /(?:신규\s*또는\s*재입국자|Newcomer|Re-entering employee)[\s\S]{0,80}?(\d{1,2})\s*(?:개월|month)/i
    ]),
    monthlyWage:(extractSlcValue(text,[
      /(?:월\s*통상임금|Monthly Normal wages?)[\s\S]{0,100}?([\d,]{5,})\s*(?:원|won)/i
    ])||'').replace(/,/g,''),
    basePay:(extractSlcValue(text,[
      /(?:기본급|Basic pay)[\s\S]{0,100}?([\d,]{5,})\s*(?:원|won)/i
    ])||'').replace(/,/g,''),
    payDate:extractSlcValue(text,[
      /매월\s*(\d{1,2})\s*일/i,
      /Every\s+(\d{1,2})(?:st|nd|rd|th)?\s+day/i
    ]),
    breakMinutes:extractSlcValue(text,[
      /(?:휴게시간|Recess hours?)[\s\S]{0,80}?(\d{1,3})\s*(?:분|minutes?)/i
    ])
  };

  const time=text.match(/(?:근로시간|Working hours?)[\s\S]{0,160}?(\d{1,2}:\d{2})\s*(?:부터|~|-|to)\s*(\d{1,2}:\d{2})/i);
  if(time){extracted.workStart=time[1];extracted.workEnd=time[2]}

  if(/통장\s*입금|direct\s+deposit|bank\s+transfer/i.test(text))extracted.paymentMethod='Transfer ke rekening pekerja';
  else if(/직접\s*지급|in\s+person/i.test(text))extracted.paymentMethod='Tunai langsung';

  let count=0;
  Object.entries(extracted).forEach(([key,value])=>{
    if(!value)return;
    const el=$('contract_'+key);
    if(el){el.value=value;count++}
  });
  saveContractLocally();
  out.classList.add(count?'safe':'warn');
  out.innerHTML=count
    ? '<strong>'+count+' kolom berhasil diisi otomatis.</strong> Periksa setiap nilai terhadap SLC asli sebelum menggunakan hasil pemeriksaan.'
    : '<strong>Belum ada kolom yang dapat diekstrak dengan aman.</strong> Isi kolom secara manual atau gunakan teks OCR yang lebih jelas.';
});

function saveContractLocally(){
  const data={};
  contractRules.fields.forEach(field=>{data[field.id]=$('contract_'+field.id)?.value??''});
  write(KEYS.contract,data);
  return data;
}

function contractWorkingHours(data){
  if(!data.workStart||!data.workEnd)return null;
  const [sh,sm]=data.workStart.split(':').map(Number);
  const [eh,em]=data.workEnd.split(':').map(Number);
  let minutes=(eh*60+em)-(sh*60+sm);
  if(minutes<0)minutes+=24*60;
  minutes-=Number(data.breakMinutes||0);
  return Math.max(0,minutes/60);
}

$('checkContractBtn').addEventListener('click',()=>{
  if(!contractRules)return;
  const data=saveContractLocally();
  const risks=[],warnings=[],ok=[];
  contractRules.fields.filter(f=>f.required).forEach(field=>{
    if(!String(data[field.id]??'').trim())warnings.push('Belum diisi: '+field.label);
  });

  const monthly=Number(data.monthlyWage||0);
  const base=Number(data.basePay||0);
  const min=contractRules.minimumWage2026.monthly209h;
  if(monthly>0&&monthly<min){
    risks.push('Upah normal bulanan '+monthly.toLocaleString('ko-KR')+' won berada di bawah acuan minimum 2026 sebesar '+min.toLocaleString('ko-KR')+' won untuk skenario 209 jam/bulan. Jam kerja aktual harus diperiksa sebelum mengambil kesimpulan.');
  }else if(monthly>=min){
    ok.push('Upah normal bulanan tidak berada di bawah acuan 2026 untuk 209 jam/bulan.');
  }
  if(base>0&&monthly>0&&base>monthly)warnings.push('Gaji pokok lebih besar daripada upah normal bulanan. Periksa kembali angka yang dimasukkan.');

  const hours=contractWorkingHours(data);
  if(hours!==null){
    if(hours>8)warnings.push('Jam kerja bersih yang dimasukkan sekitar '+hours.toFixed(1)+' jam/hari. Periksa pembagian jam normal, lembur, dan waktu istirahat pada SLC.');
    else ok.push('Jam kerja bersih yang dimasukkan sekitar '+hours.toFixed(1)+' jam/hari.');
  }

  if(data.paymentMethod==='Lainnya')warnings.push('Cara pembayaran tidak jelas sebagai transfer ke rekening pekerja atau pembayaran langsung. Pastikan tertulis dengan jelas.');
  if(data.roomProvided==='Ya'&&!String(data.roomCost??'').trim())warnings.push('Akomodasi disediakan tetapi biaya yang ditanggung pekerja belum diisi. Pastikan apakah gratis atau ada potongan.');
  if(data.mealsProvided==='Ya'&&!String(data.mealCost??'').trim())warnings.push('Makan disediakan tetapi biaya yang ditanggung pekerja belum diisi. Pastikan apakah gratis atau ada potongan.');
  if(data.enterpriseName&&data.workplace&&!data.enterpriseLocation)warnings.push('Nama perusahaan ada, tetapi alamat perusahaan belum diisi.');
  if(!risks.length&&!warnings.length)ok.push('Tidak ada celah dasar yang terdeteksi dari kolom yang diperiksa.');

  const out=$('contractResult');
  out.hidden=false;
  out.className='result '+(risks.length?'risk':warnings.length?'warn':'safe');
  const items=[
    ...risks.map(x=>'<div class="contract-flag risk"><strong>Perlu perhatian:</strong> '+escapeHtml(x)+'</div>'),
    ...warnings.map(x=>'<div class="contract-flag warn"><strong>Periksa:</strong> '+escapeHtml(x)+'</div>'),
    ...ok.map(x=>'<div class="contract-flag"><strong>OK:</strong> '+escapeHtml(x)+'</div>')
  ].join('');
  out.innerHTML='<strong>Hasil pemeriksaan SLC</strong><div class="contract-flags">'+items+'</div><p class="muted">Ini pemeriksaan awal, bukan keputusan hukum atau keputusan resmi HRD Korea/KP2MI.</p>';
});

$('openWorkplaceBtn').addEventListener('click',()=>{
  renderWorkplace();
  switchView('workplace');
});

$('resetContractBtn').addEventListener('click',()=>{
  localStorage.removeItem(KEYS.contract);
  renderContract();
  $('contractResult').hidden=true;
});



function renderPayroll(){
  const saved=read(KEYS.payroll,{});
  const fields=['payrollFullPeriod','payrollGross','payrollDeposit','payrollDeductions','payrollExplained','payrollHours','payrollMinimumBase'];
  fields.forEach(id=>{ if($(id)) $(id).value=saved[id]??''; });
}

function savePayroll(){
  const data={};
  ['payrollFullPeriod','payrollGross','payrollDeposit','payrollDeductions','payrollExplained','payrollHours','payrollMinimumBase'].forEach(id=>{
    data[id]=$(id)?.value??'';
  });
  write(KEYS.payroll,data);
  return data;
}

$('checkPayrollBtn').addEventListener('click',()=>{
  const data=savePayroll();
  const contract=read(KEYS.contract,{});
  const gross=Number((data.payrollGross||'').replace(/[^0-9.]/g,''))||0;
  const deposit=Number((data.payrollDeposit||'').replace(/[^0-9.]/g,''))||0;
  const deductions=Number((data.payrollDeductions||'').replace(/[^0-9.]/g,''))||0;
  const explained=Number((data.payrollExplained||'').replace(/[^0-9.]/g,''))||0;
  const hours=Number((data.payrollHours||'').replace(/[^0-9.]/g,''))||0;
  const minBase=Number((data.payrollMinimumBase||'').replace(/[^0-9.]/g,''))||0;
  const contracted=Number(contract.monthlyWage||0);
  const minHourly=contractRules.minimumWage2026.hourly;
  const risks=[],warnings=[],ok=[];

  if(!gross||!deposit)warnings.push('Masukkan gaji bruto dan jumlah yang benar-benar masuk rekening.');
  if(data.payrollFullPeriod==='yes'&&contracted>0&&gross>0){
    if(gross<contracted)risks.push('Gaji bruto periode penuh lebih rendah daripada upah normal bulanan pada SLC ('+contracted.toLocaleString('ko-KR')+' won). Periksa slip, absensi, dan alasan potongan.');
    else ok.push('Gaji bruto tidak lebih rendah daripada upah normal bulanan pada SLC.');
  }
  if(gross>0&&deposit>0&&deductions>=0){
    const expected=Math.max(0,gross-deductions);
    if(Math.abs(expected-deposit)>1000)warnings.push('Gaji bruto - total potongan tidak sama dengan jumlah yang masuk rekening. Selisih sekitar '+Math.abs(expected-deposit).toLocaleString('ko-KR')+' won perlu dijelaskan.');
    else ok.push('Gaji bruto, potongan, dan jumlah masuk rekening konsisten secara aritmetika.');
  }
  const unexplained=Math.max(0,deductions-explained);
  if(unexplained>0)warnings.push('Ada sekitar '+unexplained.toLocaleString('ko-KR')+' won potongan yang belum Anda pahami atau belum dijelaskan.');
  if(hours>0&&minBase>0){
    const implied=minBase/hours;
    if(implied<minHourly)risks.push('Upah per jam tersirat sekitar '+Math.round(implied).toLocaleString('ko-KR')+' won, di bawah upah minimum 2026 '+minHourly.toLocaleString('ko-KR')+' won. Komponen upah dan jam yang masuk perhitungan harus dikonfirmasi.');
    else ok.push('Upah per jam tersirat dari angka yang Anda masukkan tidak berada di bawah acuan minimum 2026.');
  }
  if(!risks.length&&!warnings.length)ok.push('Tidak ada ketidaksesuaian dasar yang terdeteksi dari angka yang dimasukkan.');

  const out=$('payrollResult');
  out.hidden=false;
  out.className='result '+(risks.length?'risk':warnings.length?'warn':'safe');
  out.innerHTML='<strong>Hasil pemeriksaan slip gaji</strong><div class="contract-flags">'+[
    ...risks.map(x=>'<div class="contract-flag risk"><strong>Perlu perhatian:</strong> '+escapeHtml(x)+'</div>'),
    ...warnings.map(x=>'<div class="contract-flag warn"><strong>Periksa:</strong> '+escapeHtml(x)+'</div>'),
    ...ok.map(x=>'<div class="contract-flag"><strong>OK:</strong> '+escapeHtml(x)+'</div>')
  ].join('')+'</div><p class="muted">Jika ada kekurangan upah atau potongan yang tidak dapat dijelaskan, simpan SLC, slip gaji, mutasi rekening, dan catatan jam kerja lalu gunakan jalur resmi 1350/Labor Portal.</p>';
});

['payrollFullPeriod','payrollGross','payrollDeposit','payrollDeductions','payrollExplained','payrollHours','payrollMinimumBase'].forEach(id=>{
  $(id)?.addEventListener('change',savePayroll);
});

function renderWorkplace(){
  if(!workplaceRules)return;
  const saved=read(KEYS.workplace,{checks:[]});
  const contract=read(KEYS.contract,{});
  $('wpCompany').value=saved.company||contract.enterpriseName||'';
  $('wpAddress').value=saved.address||contract.workplace||contract.enterpriseLocation||'';
  $('wpDorm').value=saved.dorm||'';
  updateMapLinks();

  const selected=new Set(saved.checks||[]);
  const wrap=$('realityChecks');
  wrap.innerHTML='';
  workplaceRules.checks.forEach(check=>{
    const article=document.createElement('article');
    article.innerHTML=`<input type="checkbox" ${selected.has(check.id)?'checked':''}><div><h3>${escapeHtml(check.title)}</h3><p>${escapeHtml(check.detail)}</p></div>`;
    article.querySelector('input').addEventListener('change',saveWorkplace);
    wrap.appendChild(article);
  });

  ['wpCompany','wpAddress','wpDorm'].forEach(id=>{
    const el=$(id);
    el.oninput=()=>{saveWorkplace();updateMapLinks()};
  });
  updateCoverage();
}

function saveWorkplace(){
  const checked=[];
  [...$('realityChecks').querySelectorAll('article')].forEach((article,index)=>{
    if(article.querySelector('input')?.checked)checked.push(workplaceRules.checks[index].id);
  });
  const data={company:$('wpCompany').value.trim(),address:$('wpAddress').value.trim(),dorm:$('wpDorm').value.trim(),checks:checked};
  write(KEYS.workplace,data);
  updateCoverage();
  return data;
}

function updateMapLinks(){
  const query=[$('wpCompany').value.trim(),$('wpAddress').value.trim()].filter(Boolean).join(' ');
  const q=encodeURIComponent(query||'Korea');
  $('naverMapLink').href='https://map.naver.com/p/search/'+q;
  $('kakaoMapLink').href='https://map.kakao.com/?q='+q;
  $('googleMapLink').href='https://www.google.com/maps/search/?api=1&query='+q;
}

function updateCoverage(){
  if(!workplaceRules)return;
  const state=read(KEYS.workplace,{checks:[]});
  const count=(state.checks||[]).length;
  const total=workplaceRules.checks.length;
  const pct=total?Math.round(count/total*100):0;
  $('coverageText').textContent=pct+'%';
  $('coverageBar').style.width=pct+'%';
}

$('requestScoutBtn').addEventListener('click',()=>{
  const data=saveWorkplace();
  if(!data.company&&!data.address)return;
  const checked=new Set(data.checks||[]);
  const missing=workplaceRules.checks.filter(c=>!checked.has(c.id)).map(c=>'• '+c.title).join('\n');
  const subject=encodeURIComponent('[KEP Beta] Workplace Reality Check request');
  const body=encodeURIComponent(
    'Halo Korea Employment Passport Beta,\n\n'+
    'Saya ingin meminta pemeriksaan lapangan / reality check untuk:\n'+
    'Perusahaan: '+(data.company||'-')+'\n'+
    'Alamat kerja: '+(data.address||'-')+'\n'+
    'Info asrama: '+(data.dorm||'-')+'\n\n'+
    'Yang belum terverifikasi:\n'+(missing||'Semua checklist sudah ditandai.')+'\n\n'+
    'Saya memahami pemeriksaan harus dilakukan secara legal: tanpa masuk area privat tanpa izin, tanpa merekam rahasia dagang, dan tanpa mengirim dokumen pribadi sensitif.'
  );
  location.href='mailto:modernsnc2022@gmail.com?subject='+subject+'&body='+body;
});


$('analyzeBrokerBtn').addEventListener('click',()=>{
  const text=($('brokerText').value||'').trim();
  const out=$('brokerResult');
  out.hidden=false;
  out.className='result';
  if(!text){
    out.classList.add('warn');
    out.textContent='Tempel pesan atau teks tagihan terlebih dahulu.';
    return;
  }

  const lower=text.toLowerCase();
  const signals=[];
  const strong=[
    [/(dijamin|jaminan|pasti).{0,30}(kerja|slc|berangkat|perusahaan|dipilih)/i,'Janji hasil/penempatan yang dijamin'],
    [/(jalur\s*(cepat|khusus)|orang\s*dalam|koneksi\s*khusus|prioritas\s*khusus)/i,'Klaim jalur khusus atau koneksi orang dalam'],
    [/(tanpa|tidak perlu).{0,25}(ujian|eps-?topik|skill\s*test|proses\s*resmi)/i,'Klaim dapat melewati proses resmi'],
    [/(rekening\s*pribadi|transfer.{0,35}atas\s*nama\s*(pribadi|perorangan))/i,'Permintaan pembayaran ke rekening pribadi'],
    [/(jangan\s*(bilang|cerita)|rahasia|diam-diam)/i,'Permintaan merahasiakan proses atau pembayaran']
  ];
  const medium=[
    [/(hari\s*ini|sekarang\s*juga|segera\s*bayar|slot\s*terbatas)/i,'Tekanan waktu untuk segera membayar'],
    [/(fee\s*(job|penempatan)|biaya\s*(jaminan|penempatan)|uang\s*pelicin)/i,'Biaya penempatan/jaminan yang perlu diverifikasi'],
    [/(cepat|percepat).{0,25}(slc|berangkat|dipilih|perusahaan)/i,'Janji mempercepat hasil resmi']
  ];
  strong.forEach(([re,label])=>{if(re.test(lower))signals.push({level:'risk',label})});
  medium.forEach(([re,label])=>{if(re.test(lower))signals.push({level:'warn',label})});

  const amounts=[];
  const re=/\bRp\s*([0-9][0-9.,\s]{2,})/gi;
  let m;
  while((m=re.exec(text))!==null){
    const amount=Number(m[1].replace(/[^0-9]/g,''));
    if(amount>0&&!amounts.includes(amount))amounts.push(amount);
  }

  const amountFindings=amounts.map(amount=>{
    const known=rules.fees.find(f=>f.amountIdr===amount);
    if(!known)return {level:'warn',text:'Rp'+amount.toLocaleString('id-ID')+' tidak cocok dengan daftar nominal resmi yang sudah diverifikasi untuk rute ini.'};
    if(known.kind==='minimum_balance')return {level:'warn',text:'Rp'+amount.toLocaleString('id-ID')+' cocok dengan saldo minimum BNI, bukan biaya yang harus diberikan kepada seseorang.'};
    const scope=known.conditional&&known.scope?' Berlaku hanya pada kondisi: '+known.scope+'.':'';
    return {level:'ok',text:'Rp'+amount.toLocaleString('id-ID')+' sama dengan nominal resmi: '+known.purpose+'. Kesamaan nominal saja tidak membuktikan penerima pembayaran benar.'+scope};
  });

  const hasRisk=signals.some(s=>s.level==='risk');
  const hasWarn=signals.some(s=>s.level==='warn')||amountFindings.some(s=>s.level==='warn');
  out.classList.add(hasRisk?'risk':hasWarn?'warn':'safe');

  const signalHtml=signals.length
    ? signals.map(s=>'<div class="contract-flag '+(s.level==='risk'?'risk':'warn')+'"><strong>'+(s.level==='risk'?'Risiko tinggi':'Periksa')+':</strong> '+escapeHtml(s.label)+'</div>').join('')
    : '<div class="contract-flag"><strong>Tidak ada pola janji berisiko yang terdeteksi secara otomatis.</strong></div>';
  const amountHtml=amountFindings.map(f=>'<div class="contract-flag '+(f.level==='warn'?'warn':'')+'">'+escapeHtml(f.text)+'</div>').join('');

  out.innerHTML='<strong>Hasil Broker Guardian</strong><div class="contract-flags">'+signalHtml+amountHtml+'</div><p class="muted">Deteksi ini bukan bukti bahwa seseorang melakukan penipuan. Verifikasi proses, penerima, tujuan, dan nominal terhadap sumber resmi sebelum membayar.</p>';
});

function renderUnresolvedFieldQuestions(){
  const list=read(KEYS.fieldQuestions,[]);
  const wrap=$('unresolvedFieldList');
  wrap.innerHTML='';
  if(!list.length){
    wrap.innerHTML='<div class="gap-item"><p>Belum ada pertanyaan field yang menunggu verifikasi.</p></div>';
    return;
  }

  list.forEach(item=>{
    const article=document.createElement('article');
    article.className='gap-item';
    article.innerHTML=`
      <h3>${escapeHtml(item.question)}</h3>
      <p><strong>Tahap:</strong> ${escapeHtml(item.stageTitle||item.stageId)}</p>
      <p><strong>Status:</strong> Jangan submit berdasarkan tebakan — perlu verifikasi resmi.</p>
      <div class="gap-actions"><button type="button">Hapus</button></div>`;
    article.querySelector('button').addEventListener('click',()=>{
      write(KEYS.fieldQuestions,read(KEYS.fieldQuestions,[]).filter(row=>row.key!==item.key));
      renderUnresolvedFieldQuestions();
    });
    wrap.appendChild(article);
  });
}

$('emailFieldQuestionsBtn').addEventListener('click',()=>{
  const list=read(KEYS.fieldQuestions,[]);
  if(!list.length)return;
  const lines=list.map((item,index)=>`${index+1}. [${item.stageTitle||item.stageId}] ${item.question}`).join('\n');
  const subject=encodeURIComponent('[KEP Beta] Exact field questions needing verification');
  const body=encodeURIComponent(
    'Pertanyaan field yang belum punya jawaban terverifikasi:\n\n'+
    lines+
    '\n\nMohon verifikasi berdasarkan form/pengumuman resmi yang sesuai. Jangan jawab berdasarkan tebakan atau sektor/siklus lain.'
  );
  location.href='mailto:modernsnc2022@gmail.com?subject='+subject+'&body='+body;
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

function switchView(viewId,scroll=true){
  const utilityOwner={
    eligibility:'journey',
    contract:'journey',
    workplace:'journey',
    payroll:'journey'
  }[viewId]||viewId;

  document.querySelectorAll('.utility-tab').forEach(btn=>{
    btn.classList.toggle('active',btn.dataset.view===utilityOwner);
  });
  document.querySelectorAll('.view').forEach(view=>{
    view.classList.toggle('active',view.id===viewId);
  });
  if(scroll)document.getElementById(viewId)?.scrollIntoView({behavior:'smooth',block:'start'});
}
document.querySelectorAll('.utility-tab').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.view)));
document.querySelectorAll('.process-return').forEach(btn=>btn.addEventListener('click',()=>{
  switchView('journey');
  const current=currentStage();
  const phase=phaseForStage(current?.id||route?.stages?.[0]?.id);
  document.querySelector('[data-phase-group="'+phase.id+'"]')?.scrollIntoView({behavior:'smooth',block:'start'});
}));

window.addEventListener('beforeinstallprompt',(e)=>{e.preventDefault();deferredInstall=e;$('installBtn').hidden=false});
$('installBtn').addEventListener('click',async()=>{if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;$('installBtn').hidden=true});
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(console.error));

boot();