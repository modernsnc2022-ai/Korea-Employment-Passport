const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const RULES_URL='data/id_e9_manufacturing_2026_rules.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
const CONTRACT_URL='data/slc_guardian_2026.json';
const WORKPLACE_URL='data/workplace_reality_v1.json';
const WORKPLACE_WORKER_EVIDENCE_URL='data/workplace_worker_evidence_v1.json';
const DOCUMENT_PACKS_URL='data/document_packs_2026.json';
const EXACT_ANSWERS_URL='data/exact_answer_rules_v1.json';
const DOCUMENT_EXAMPLES_URL='data/document_examples_v1.json';
const FRESHNESS_URL='data/freshness_policy_v1.json';
const BROKER_QUESTION_URL='data/broker_question_catalog_v1.json';
const FORM_WIZARDS_URL='data/form_wizards_2026.json';
const FORM_LINEAGE_URL='data/form_lineage_2026.json';
const SOURCE_REVIEW_STATUS_URL='data/source_review_status.json';
const OFFICIAL_HELP_URL='data/official_help_channels_v1.json';
const DEPARTURE_CALLS_URL='data/departure_calls_2026.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps',contract:'kep.contract',workplace:'kep.workplace',ledger:'kep.costLedger',payroll:'kep.payroll',fieldQuestions:'kep.unresolvedFieldQuestions',rejections:'kep.rejectionCases',betaChecks:'kep.betaZeroBrokerChecks',betaTesterId:'kep.betaTesterId',betaWorkerExperienceYear:'kep.betaWorkerExperienceYear',scopeSelections:'kep.scopeSelections',formWizard:'kep.formWizard',wizardReviewed:'kep.formWizardReviewed',quickSetup:'kep.quickSetupDone'};
let route=null,rules=null,contractRules=null,workplaceRules=null,workplaceWorkerEvidence=null,documentPacks=null,documentExamples=null,exactAnswers=null,freshnessPolicy=null,brokerQuestions=null,formWizards=null,formLineage=null,sourceReviewStatus=null,officialHelp=null,departureCalls=null,i18n={},activeStage=null,deferredInstall=null;
let consistencyRisk={stageId:null,hasMismatch:false};

const $=(id)=>document.getElementById(id);
const BETA_SCOPED_KEYS=new Set([KEYS.gaps,KEYS.fieldQuestions,KEYS.rejections,KEYS.betaChecks,KEYS.betaWorkerExperienceYear]);
function activeBetaTesterIdForStorage(){
  try{return canonicalBetaTesterId(JSON.parse(localStorage.getItem(KEYS.betaTesterId)||'""'))}catch{return ''}
}
function storageKeyFor(key){
  if(!BETA_SCOPED_KEYS.has(key))return key;
  const testerId=activeBetaTesterIdForStorage();
  return testerId?key+'.'+testerId:key;
}
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(storageKeyFor(key)))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(storageKeyFor(key),JSON.stringify(value));
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stageTitle=(stage)=>i18n[stage.id]?.title||stage.title;
const stageAction=(stage)=>i18n[stage.id]?.action||stage.action;
const stageWarning=(stage)=>i18n[stage.id]?.warning||stage.warning;

const SAFE_BACKUP_FIELDS=['done','docs','scopeSelections','formWizard','wizardReviewed','quickSetup'];

function routeBackupKey(){
  if(!route)return 'unknown';
  return [route.country,route.visa,route.sector,route.cycle].join('-');
}

function makeProgressBackup(){
  return {
    kind:'kep-progress-backup',
    schemaVersion:1,
    routeKey:routeBackupKey(),
    exportedAt:new Date().toISOString(),
    progress:{
      done:read(KEYS.done,[]),
      docs:read(KEYS.docs,[]),
      scopeSelections:read(KEYS.scopeSelections,{}),
      formWizard:read(KEYS.formWizard,{}),
      wizardReviewed:read(KEYS.wizardReviewed,[]),
      quickSetup:read(KEYS.quickSetup,false)
    }
  };
}

function safeRestoreProgress(payload){
  if(!payload||payload.kind!=='kep-progress-backup'||payload.schemaVersion!==1){
    throw new Error('File ini bukan backup progres Korea Employment Passport yang didukung.');
  }
  if(payload.routeKey!==routeBackupKey()){
    throw new Error('Backup ini berasal dari rute yang berbeda: '+String(payload.routeKey||'unknown'));
  }
  const progress=payload.progress||{};
  const stageIds=new Set((route?.stages||[]).map(stage=>stage.id));
  const docIds=new Set((documentPacks?.packs||[]).flatMap(pack=>(pack.items||[]).map(item=>item.id)));
  const formIds=new Set((formWizards?.forms||[]).map(form=>form.id));

  const done=Array.isArray(progress.done)?progress.done.filter(id=>stageIds.has(id)):[];
  const docs=Array.isArray(progress.docs)?progress.docs.filter(id=>docIds.has(id)):[];
  const scopes={};
  if(progress.scopeSelections&&typeof progress.scopeSelections==='object'&&!Array.isArray(progress.scopeSelections)){
    for(const [stageId,value] of Object.entries(progress.scopeSelections)){
      if(stageIds.has(stageId)&&typeof value==='string')scopes[stageId]=value;
    }
  }
  const wizard={};
  if(progress.formWizard&&typeof progress.formWizard==='object'&&!Array.isArray(progress.formWizard)){
    if(formIds.has(progress.formWizard.formId)){
      wizard.formId=progress.formWizard.formId;
      const form=(formWizards?.forms||[]).find(item=>item.id===wizard.formId);
      const index=Number(progress.formWizard.index||0);
      wizard.index=Math.max(0,Math.min(Number.isFinite(index)?index:0,form?.fields?.length||0));
    }
  }

  const validReviewedKeys=new Set();
  (formWizards?.forms||[]).forEach(form=>{
    const scopesForForm=Array.isArray(form.scopeKeys)&&form.scopeKeys.length
      ?form.scopeKeys
      :form.scopeKey?[form.scopeKey]:['default'];
    (form.stages||[]).forEach(stageId=>{
      if(!stageIds.has(stageId))return;
      (form.fields||[]).forEach(field=>{
        if(!field?.id||!field.validator)return;
        scopesForForm.forEach(scope=>validReviewedKeys.add([stageId,scope,form.id,field.id].join('|')));
      });
    });
  });
  const wizardReviewed=Array.isArray(progress.wizardReviewed)
    ?[...new Set(progress.wizardReviewed.filter(key=>typeof key==='string'&&validReviewedKeys.has(key)))]
    :[];

  write(KEYS.done,done);
  write(KEYS.docs,docs);
  write(KEYS.scopeSelections,scopes);
  write(KEYS.formWizard,wizard);
  write(KEYS.wizardReviewed,wizardReviewed);
  write(KEYS.quickSetup,Boolean(progress.quickSetup));
}

$('backupProgressBtn').addEventListener('click',()=>{
  const out=$('backupProgressResult');
  try{
    const payload=makeProgressBackup();
    const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    const date=new Date().toISOString().slice(0,10);
    link.href=url;
    link.download='korea-employment-passport-progress-'+date+'.json';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    out.hidden=false;
    out.className='result safe';
    out.textContent='Backup progres dibuat. Simpan file ini di tempat yang Anda percaya.';
  }catch(error){
    out.hidden=false;
    out.className='result risk';
    out.textContent='Backup gagal: '+error.message;
  }
});

$('restoreProgressBtn').addEventListener('click',()=>$('restoreProgressFile').click());
$('restoreProgressFile').addEventListener('change',async(event)=>{
  const out=$('backupProgressResult');
  const file=event.target.files?.[0];
  if(!file)return;
  try{
    if(file.size>1024*1024)throw new Error('File backup terlalu besar.');
    const payload=JSON.parse(await file.text());
    safeRestoreProgress(payload);
    out.hidden=false;
    out.className='result safe';
    out.textContent='Progres berhasil dipulihkan. Halaman akan dimuat ulang.';
    setTimeout(()=>location.reload(),500);
  }catch(error){
    out.hidden=false;
    out.className='result risk';
    out.textContent='Backup tidak dapat dipulihkan: '+error.message;
  }finally{
    event.target.value='';
  }
});


const QUICK_MILESTONES=[
  {label:'Pendaftaran resmi sudah saya kirim',nextStage:'exam_fee'},
  {label:'Biaya ujian EPS-TOPIK sudah saya bayar',nextStage:'biometric'},
  {label:'Biometrik sudah selesai',nextStage:'document_verify'},
  {label:'Verifikasi dokumen sudah selesai',nextStage:'exam_card'},
  {label:'Saya sudah ikut EPS-TOPIK',nextStage:'skill_competency'},
  {label:'Saya sudah lulus seleksi akhir',nextStage:'psychology_pre_job'},
  {label:'Lamaran kerja online sudah terkirim',nextStage:'roster'},
  {label:'Saya sudah dipilih perusahaan Korea',nextStage:'slc'},
  {label:'SLC sudah terbit / saya terima',nextStage:'post_slc_requirements'},
  {label:'Berkas visa sudah selesai',nextStage:'predeparture_training'},
  {label:'Saya sudah berangkat dan tiba di Korea',nextStage:'korea_entry_training'},
  {label:'Saya sudah diserahkan ke perusahaan',nextStage:'residence_registration'},
];

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
  korea_entry_training:[],
  employer_handover:['workplace'],
  residence_registration:['documents'],
  eps_insurance_check:[],
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
      const allJourney=$('allJourneyDetails');
      if(allJourney)allJourney.open=true;
      document.querySelector('[data-phase-group="'+phase.id+'"]')?.scrollIntoView({behavior:'smooth',block:'start'});
    });
    wrap.appendChild(button);
  });
}

function renderContextTools(stage){
  const box=$('contextTools');
  if(!stage){box.hidden=true;box.innerHTML='';box.open=false;return}
  const toolsForStage=STAGE_TOOLS[stage.id]||[];
  if(!toolsForStage.length){box.hidden=true;box.innerHTML='';box.open=false;return}
  box.hidden=false;
  box.open=false;
  const toolButtons=toolsForStage.map(key=>{
    const meta=TOOL_META[key];
    return `<button type="button" class="context-tool" data-tool-view="${meta.view}"><strong>${escapeHtml(meta.label)}</strong><small>${escapeHtml(meta.desc)}</small></button>`;
  }).join('');
  box.innerHTML=`
    <summary>Perlu bantuan tambahan untuk langkah ini?</summary>
    <div class="context-tools-body">
      <div class="context-tool-grid">${toolButtons}</div>
    </div>`;
  box.querySelectorAll('[data-tool-view]').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.toolView)));
}

async function fetchJsonRequired(url,attempts=3){
  let lastError=null;
  for(let attempt=1;attempt<=attempts;attempt+=1){
    try{
      const response=await fetch(url,{cache:'no-store'});
      if(!response.ok)throw new Error('HTTP '+response.status);
      return await response.json();
    }catch(error){
      lastError=error;
      if(attempt<attempts)await new Promise(resolve=>setTimeout(resolve,200*attempt));
    }
  }
  throw new Error('required data unavailable: '+url+' — '+String(lastError?.message||lastError||'unknown error'));
}

async function fetchJsonOptional(url,fallback,label){
  try{
    const response=await fetch(url,{cache:'no-store'});
    if(!response.ok)throw new Error('HTTP '+response.status);
    return await response.json();
  }catch(err){
    console.warn('Optional data unavailable:',label||url,err);
    return fallback;
  }
}

async function boot(){
  try{
    [
      route,
      rules,
      i18n,
      contractRules,
      workplaceRules,
      workplaceWorkerEvidence,
      documentPacks,
      exactAnswers,
      documentExamples,
      freshnessPolicy,
      brokerQuestions,
      formWizards,
      formLineage,
      sourceReviewStatus,
      officialHelp,
      departureCalls
    ]=await Promise.all([
      fetchJsonRequired(ROUTE_URL),
      fetchJsonRequired(RULES_URL),
      fetchJsonRequired(I18N_URL),
      fetchJsonRequired(CONTRACT_URL),
      fetchJsonRequired(WORKPLACE_URL),
      fetchJsonOptional(
        WORKPLACE_WORKER_EVIDENCE_URL,
        {version:'unavailable',status:'unavailable',records:[],displayPolicy:{}},
        'verified worker evidence registry'
      ),
      fetchJsonRequired(DOCUMENT_PACKS_URL),
      fetchJsonRequired(EXACT_ANSWERS_URL),
      fetchJsonRequired(DOCUMENT_EXAMPLES_URL),
      fetchJsonRequired(FRESHNESS_URL),
      fetchJsonRequired(BROKER_QUESTION_URL),
      fetchJsonRequired(FORM_WIZARDS_URL),
      fetchJsonRequired(FORM_LINEAGE_URL),
      fetchJsonOptional(
        SOURCE_REVIEW_STATUS_URL,
        {
          state:'fetch_warning',
          autoPublishRules:false,
          configured:0,
          checked:0,
          reviewRequiredUrls:[],
          reviewRequiredSourceIds:[],
          fetchFailureUrls:['source_review_status'],
          fetchFailureSourceIds:['source_review_status']
        },
        'official source review status'
      ),
      fetchJsonOptional(
        OFFICIAL_HELP_URL,
        {version:'unavailable',verifiedAt:null,channels:[],stageMap:{}},
        'official help channels'
      ),
      fetchJsonOptional(
        DEPARTURE_CALLS_URL,
        {version:'unavailable',coverageStatus:'unavailable',complete:false,calls:[]},
        'departure call registry'
      )
    ]);
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufaktur · 2026 · paket ${route.packVersion} · diperiksa ${route.lastVerified}`;
    renderCycleStatus();
    renderFreshnessStatus();
    renderBqcStatus();
    renderQuickStart();
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
    hydrateBetaTesterIdFromUrl();
    renderBetaModeBanner();
    renderBetaValidation();
    renderRejectionStage();
    renderRejections();
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

function renderFreshnessStatus(){
  const box=$('freshnessStatus');
  if(!freshnessPolicy||!route){box.hidden=true;return}
  box.hidden=false;
  box.className='freshness-status';
  const state=sourceReviewStatus?.state||'clean';
  const trustPanel=document.querySelector('.trust-panel');

  if(state==='review_required'){
    box.classList.add('review-required');
    if(trustPanel)trustPanel.open=true;
    const count=(sourceReviewStatus.reviewRequiredUrls||[]).length;
    box.innerHTML=`
      <span class="freshness-pill">PERUBAHAN SUMBER RESMI TERDETEKSI</span>
      <span><strong>${count} sumber perlu ditinjau.</strong> Jawaban/formulir yang bergantung pada sumber tersebut sementara tidak dianggap “jawaban pasti”.</span>
      <span>Aturan tidak diubah otomatis sampai review selesai.</span>`;
    return;
  }

  if(state==='fetch_warning'){
    box.classList.add('fetch-warning');
    const count=(sourceReviewStatus.fetchFailureUrls||[]).length;
    box.innerHTML=`
      <span class="freshness-pill">PEMERIKSAAN SUMBER BELUM LENGKAP</span>
      <span><strong>${count} sumber resmi sementara tidak dapat diperiksa.</strong> Aturan tidak diubah otomatis.</span>
      <span>Data rute terakhir diverifikasi: <strong>${escapeHtml(route.lastVerified||'-')}</strong></span>`;
    return;
  }

  const cadenceLabel=freshnessPolicy.monitorCadence==='every 6 hours'?'SETIAP 6 JAM':String(freshnessPolicy.monitorCadence||'').toUpperCase();
  box.innerHTML=`
    <span class="freshness-pill">SUMBER RESMI DIPANTAU ${escapeHtml(cadenceLabel)}</span>
    <span><strong>Tidak ada perubahan resmi yang belum direview.</strong> Aturan hanya berubah setelah verifikasi.</span>
    <span>Data rute terakhir diverifikasi: <strong>${escapeHtml(route.lastVerified||'-')}</strong></span>`;
}

function normalizeSourceUrl(url){
  return String(url||'')
    .trim()
    .replace(/^http:/i,'https:')
    .replace('://www.','://')
    .replace(/\/$/,'');
}

function sourceNeedsReview(url){
  if(!url||!sourceReviewStatus)return false;
  const target=normalizeSourceUrl(url);
  return (sourceReviewStatus.reviewRequiredUrls||[])
    .some(item=>normalizeSourceUrl(item)===target);
}

function sourceHasFetchWarning(url){
  if(!url||!sourceReviewStatus)return false;
  const target=normalizeSourceUrl(url);
  return (sourceReviewStatus.fetchFailureUrls||[])
    .some(item=>normalizeSourceUrl(item)===target);
}

function selectedScope(stageId){
  return read(KEYS.scopeSelections,{})[stageId]||'';
}

function exactAnswerById(answerId){
  return (exactAnswers?.answers||[]).find(item=>item.id===answerId)||null;
}

function exactAnswerApplies(item,stageId){
  if(!item?.stages?.includes(stageId))return false;
  if(sourceNeedsReview(item.sourceUrl))return false;
  if(item.scopeType!=='cohort')return true;
  const selected=selectedScope(stageId);
  if(Array.isArray(item.scopeKeys)&&item.scopeKeys.length)return item.scopeKeys.includes(selected);
  return selected===item.scopeKey;
}

function exactAnswerIdSet(stageId){
  return new Set((exactAnswers?.answers||[]).filter(item=>exactAnswerApplies(item,stageId)).map(item=>item.id));
}

function wizardSourceUrl(form,stageId){
  if(!form)return '';
  const targetStage=stageId||(form.stages||[])[0]||'visa_docs';
  const scope=selectedScope(targetStage);
  return (scope&&form.sourceUrlsByScope?.[scope])||form.sourceUrl||'';
}

function wizardGuidanceUrl(form,stageId){
  if(!form)return '';
  const targetStage=stageId||(form.stages||[])[0]||'visa_docs';
  const scope=selectedScope(targetStage);
  return (scope&&form.guidanceUrlsByScope?.[scope])||form.guidanceUrl||'';
}

function wizardFormApplies(form,stageId){
  if(!form?.stages?.includes(stageId))return false;
  if(sourceNeedsReview(wizardSourceUrl(form,stageId))||sourceNeedsReview(wizardGuidanceUrl(form,stageId)))return false;
  const selected=selectedScope(stageId);
  if(Array.isArray(form.scopeKeys)&&form.scopeKeys.length)return form.scopeKeys.includes(selected);
  if(form.scopeType!=='cohort')return true;
  return selected===form.scopeKey;
}
function wizardFormVerified(form){
  return String(form?.verificationStatus||'').startsWith('verified_');
}
function wizardFieldRefSet(stageId){
  const refs=new Set();
  (formWizards?.forms||[])
    .filter(form=>wizardFormApplies(form,stageId)&&wizardFormVerified(form))
    .forEach(form=>{
      (form.fields||[]).forEach(field=>refs.add(form.id+':'+field.id));
    });
  return refs;
}

function brokerQuestionApplies(item,stageId){
  if(item?.stageId!==stageId)return false;
  const selected=selectedScope(stageId);
  if(Array.isArray(item.scopeKeys)&&item.scopeKeys.length)return item.scopeKeys.includes(selected);
  if(!item.scopeKey)return true;
  return selected===item.scopeKey;
}
function bqcQuestionsForStage(stageId){
  const answerIds=exactAnswerIdSet(stageId);
  const wizardRefs=wizardFieldRefSet(stageId);
  const base=(brokerQuestions?.questions||[])
    .filter(item=>brokerQuestionApplies(item,stageId))
    .map(item=>{
      const candidates=[...new Set([item.answerId,...(item.answerIds||[])].filter(Boolean))];
      const resolvedByExact=candidates.some(id=>answerIds.has(id));
      const requiredWizardRefs=[...new Set([item.wizardRef,...(item.wizardRefs||[])].filter(Boolean))];
      const resolvedByWizard=requiredWizardRefs.length>0&&requiredWizardRefs.every(ref=>wizardRefs.has(ref));
      return {...item,resolved:resolvedByExact||resolvedByWizard};
    });
  const local=read(KEYS.fieldQuestions,[])
    .filter(item=>item.stageId===stageId)
    .map(item=>({
      id:item.key,
      stageId,
      question:item.question,
      severity:'high',
      category:'user_discovered',
      answerId:null,
      resolved:false,
      blocksZeroBrokerReady:true,
      discoveredBy:'user'
    }));
  const seen=new Set();
  return [...base,...local].filter(item=>{
    const key=normalizeSearch(item.question);
    if(seen.has(key))return false;
    seen.add(key);
    return true;
  });
}

function bqcStageStats(stageId){
  const items=bqcQuestionsForStage(stageId);
  const answered=items.filter(item=>item.resolved).length;
  const blockers=items.filter(item=>!item.resolved&&item.blocksZeroBrokerReady).length;
  const pct=items.length?Math.round(answered/items.length*100):0;
  return {items,answered,total:items.length,blockers,pct,ready:items.length>0&&blockers===0&&answered===items.length};
}

function renderBqcStatus(){
  const box=$('bqcStatus');
  if(!brokerQuestions||!route){box.hidden=true;return}
  const stageIds=route.stages.map(stage=>stage.id);
  const all=stageIds.flatMap(id=>bqcQuestionsForStage(id));
  const answered=all.filter(item=>item.resolved).length;
  const blockers=all.filter(item=>!item.resolved&&item.blocksZeroBrokerReady).length;
  const pct=all.length?Math.round(answered/all.length*100):0;
  box.hidden=false;
  box.innerHTML=`
    <div><strong>Kelengkapan jawaban</strong><small>${answered}/${all.length} pertanyaan kecil sudah punya jawaban pasti</small></div>
    <div class="bqc-meter"><span style="width:${pct}%"></span></div>
    <div class="bqc-value">${pct}% · ${blockers} belum pasti</div>`;
}

function renderStageBqc(stage){
  const section=$('stageBqcSection');
  if(!brokerQuestions){section.hidden=true;return}
  const stats=bqcStageStats(stage.id);
  section.hidden=false;
  $('stageBqcText').textContent=`${stats.answered}/${stats.total} sudah pasti · ${stats.blockers} belum pasti`;
  $('stageBqcBar').style.width=stats.pct+'%';
  const badge=$('stageBqcBadge');
  badge.className='bqc-badge'+(stats.ready?' ready':'');
  badge.textContent=stats.ready?'SUDAH LENGKAP':'MASIH ADA YANG BELUM PASTI';

  const unresolved=stats.items.filter(item=>!item.resolved);
  $('stageBqcQuestions').innerHTML=unresolved.length
    ? unresolved.slice(0,6).map(item=>`<div class="stage-bqc-question ${item.severity==='high'?'high':''}"><strong>${item.severity==='high'?'Harus dijawab sebelum dianggap siap':'Perlu jawaban'}</strong>${escapeHtml(item.question)}</div>`).join('')+
      (unresolved.length>6?`<div class="stage-bqc-question">+${unresolved.length-6} pertanyaan lain belum terverifikasi</div>`:'')
    : '<div class="stage-bqc-question"><strong>Semua pertanyaan yang ditemukan sudah punya jawaban terverifikasi.</strong></div>';
}

function refreshProgressViews(){
  renderJourney();
  renderCurrentStageSelector();
  renderPhaseNav();
  renderNextAction();
  renderDocuments();
  updateProgress();
}

function applyCurrentStage(stageId,finishQuickSetup=true){
  if(!route)return;
  const index=route.stages.findIndex(stage=>stage.id===stageId);
  if(index<0)return;
  write(KEYS.done,route.stages.slice(0,index).map(stage=>stage.id));
  if(finishQuickSetup)write(KEYS.quickSetup,true);
  refreshProgressViews();
  renderQuickStart();
}

function renderQuickStart(){
  const box=$('quickStart');
  const select=$('lastMilestoneSelect');
  if(!box||!route)return;
  const hasProgress=read(KEYS.done,[]).length>0;
  const finished=read(KEYS.quickSetup,false);
  if(hasProgress||finished){
    box.hidden=true;
    document.body.classList.remove('setup-mode');
    return;
  }
  document.body.classList.add('setup-mode');
  box.hidden=false;
  select.innerHTML='<option value="">Pilih hal terakhir yang sudah selesai</option>'+
    QUICK_MILESTONES.map(item=>'<option value="'+escapeHtml(item.nextStage)+'">'+escapeHtml(item.label)+'</option>').join('');
}

$('setMilestoneBtn').addEventListener('click',()=>{
  const stageId=$('lastMilestoneSelect').value;
  if(!stageId)return;
  applyCurrentStage(stageId,true);
  document.querySelector('.flow-dashboard')?.scrollIntoView({behavior:'smooth',block:'start'});
});

document.querySelectorAll('[data-quick-stage]').forEach(button=>button.addEventListener('click',()=>{
  const stageId=button.dataset.quickStage;
  if(!stageId)return;
  applyCurrentStage(stageId,true);
  document.querySelector('.flow-dashboard')?.scrollIntoView({behavior:'smooth',block:'start'});
}));

$('startFromBeginningBtn').addEventListener('click',()=>{
  write(KEYS.done,[]);
  write(KEYS.quickSetup,true);
  refreshProgressViews();
  renderQuickStart();
  document.querySelector('.flow-dashboard')?.scrollIntoView({behavior:'smooth',block:'start'});
});

function renderCurrentStageSelector(){
  const select=$('currentStageSelect');
  select.innerHTML='<option value="">Pilih tahap paling awal yang belum selesai</option>';
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
  const stage=route.stages[Number(value)];
  if(!stage)return;
  applyCurrentStage(stage.id,true);
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

function scopePrefixForStage(stageId){
  return {
    visa_docs:'visa_',
    predeparture_training:'opp_',
    mcu3_departure:'departure_',
    departure:'departure_'
  }[stageId]||'';
}

function scopePromptForStage(stageId){
  return {
    visa_docs:'Tanggal panggilan MCU II / visa saya',
    predeparture_training:'Jadwal OPP saya',
    mcu3_departure:'Tanggal keberangkatan saya',
    departure:'Tanggal keberangkatan saya'
  }[stageId]||'Pengumuman yang memuat nama saya';
}

function scopeOptionAllowed(stageId,key){
  const prefix=scopePrefixForStage(stageId);
  return !prefix||String(key||'').startsWith(prefix);
}

function departureRegistryFallback(stageId){
  if(!['mcu3_departure','departure'].includes(stageId))return null;
  if(departureCalls?.coverageStatus!=='partial_verified')return null;
  return {
    url:departureCalls.indexUrl||'https://kp2mi.go.id/gtog-korea/info',
    message:'Daftar panggilan keberangkatan 2026 di aplikasi belum lengkap. Jika tanggal Anda tidak ada, jangan memakai aturan tanggal lain — cari panggilan nama Anda di indeks resmi KP2MI.'
  };
}

function saveScopeSelection(stageId,value){
  const state=read(KEYS.scopeSelections,{});
  const apply=(id)=>{
    if(value)state[id]=value;
    else delete state[id];
  };
  apply(stageId);
  if(String(value||'').startsWith('departure_')){
    apply('mcu3_departure');
    apply('departure');
  }
  write(KEYS.scopeSelections,state);
}

function scopeOptionsForStage(stageId){
  const rows=[];
  (exactAnswers?.answers||[])
    .filter(item=>item.stages?.includes(stageId)&&item.scopeType==='cohort'&&item.scopeKey)
    .forEach(item=>rows.push({
      key:item.scopeKey,
      label:item.scopeLabel||item.scopeKey,
      sourceUrl:item.sourceUrl||''
    }));
  (documentPacks?.packs||[])
    .filter(pack=>pack.appliesTo?.includes(stageId)&&pack.scopeType==='cohort'&&pack.scopeKey)
    .forEach(pack=>rows.push({
      key:pack.scopeKey,
      label:pack.scopeLabel||pack.scopeKey,
      sourceUrl:pack.sourceUrl||''
    }));
  (departureCalls?.calls||[])
    .filter(call=>call.stages?.includes(stageId)&&call.key)
    .forEach(call=>rows.push({
      key:call.key,
      label:call.label||call.key,
      sourceUrl:call.sourceUrl||''
    }));
  const map=new Map();
  rows.forEach(item=>{
    const prev=map.get(item.key)||{};
    map.set(item.key,{
      key:item.key,
      label:item.label||prev.label||item.key,
      sourceUrl:item.sourceUrl||prev.sourceUrl||''
    });
  });
  return [...map.values()].filter(item=>scopeOptionAllowed(stageId,item.key));
}

function renderScopePicker(stage){
  const section=$('scopePickerSection');
  const select=$('scopePicker');
  const sourceLink=$('scopePickerSource');
  if(!exactAnswers?.answers?.length){section.hidden=true;select.innerHTML='';sourceLink.hidden=true;return}
  const scoped=scopeOptionsForStage(stage.id);
  if(!scoped.length){
    section.hidden=true;
    select.innerHTML='';
    sourceLink.hidden=true;
    return;
  }
  section.hidden=false;
  $('scopePickerLabel').textContent=scopePromptForStage(stage.id);
  const fallback=departureRegistryFallback(stage.id);
  select.innerHTML='<option value="">'+(fallback?'Tanggal saya belum ada / belum tahu':'Belum tahu')+'</option>'+scoped.map(item=>`<option value="${escapeHtml(item.key)}">${escapeHtml(item.label)}</option>`).join('');
  select.value=selectedScope(stage.id);
  const chosen=scoped.find(item=>item.key===select.value);
  const note=section.querySelector('small');
  if(chosen?.sourceUrl){
    sourceLink.hidden=false;
    sourceLink.href=chosen.sourceUrl;
    sourceLink.textContent='Periksa nama saya di pengumuman resmi ↗';
    if(note)note.textContent='Pilih hanya jika nama Anda benar-benar ada di pengumuman tersebut. Jika belum tahu, biarkan pilihan kosong.';
  }else if(fallback?.url){
    sourceLink.hidden=false;
    sourceLink.href=fallback.url;
    sourceLink.textContent='Cari panggilan lain di indeks resmi KP2MI ↗';
    if(note)note.textContent=fallback.message;
  }else{
    sourceLink.hidden=true;
    sourceLink.href='#';
    sourceLink.textContent='Periksa nama saya di pengumuman resmi ↗';
    if(note)note.textContent='Pilih hanya jika nama Anda benar-benar ada di pengumuman tersebut. Jika belum tahu, biarkan “Belum tahu”.';
  }
}

$('scopePicker').addEventListener('change',()=>{
  if(!activeStage)return;
  const value=$('scopePicker').value;
  saveScopeSelection(activeStage.id,value);
  renderStageBqc(activeStage);
  renderExactAnswers(activeStage);
  renderPreSubmitGate(activeStage);
  renderDocuments();
  renderBqcStatus();
});

function exactScopeLabel(item){
  if(item.scopeType==='cohort')return item.scopeLabel||'Khusus pengumuman tertentu';
  if(item.scopeType==='current_rule')return 'Aturan resmi yang sedang berlaku';
  if(item.scopeType==='route_2026')return 'Rute Indonesia E-9 2026';
  return 'Periksa cakupan sumber';
}

function exactVerificationLabel(item){
  const v=String(item.verificationStatus||'');
  if(v==='waiting_official_notice')return 'Menunggu pengumuman resmi · jangan menebak';
  if(v==='call_specific_follow_notice'||v==='flight_call_specific')return 'Ikuti pengumuman yang memuat nama Anda';
  if(v==='institution_specific_follow_notice')return 'Ikuti petunjuk lembaga resmi Anda';
  if(v==='official_process_no_universal_deadline')return 'Tidak ada batas waktu universal pada prosedur resmi';
  if(v==='official_channel_confirmed')return 'Kanal resmi sudah dikonfirmasi';
  if(v==='official_rights_guidance')return 'Panduan hak resmi';
  if(v==='verified_with_current_process_check')return 'Terverifikasi · proses terbaru juga dicek';
  if(v==='verified_official_pdf')return 'Terverifikasi dari PDF resmi';
  if(v.startsWith('verified_current'))return 'Terverifikasi · aturan aktif';
  if(v.startsWith('verified_across'))return 'Terverifikasi · konsisten di beberapa pengumuman 2026';
  if(v.startsWith('verified'))return 'Terverifikasi';
  if(v.startsWith('cohort_specific'))return 'Terverifikasi · khusus pengumuman tertentu';
  return 'Sumber resmi sudah ditautkan · cek cakupan';
}

function renderExactAnswers(stage){
  const section=$('exactAnswerSection');
  const list=$('exactAnswerList');
  if(!exactAnswers?.answers?.length){
    section.hidden=true;
    list.innerHTML='';
    return;
  }

  const answers=exactAnswers.answers.filter(item=>exactAnswerApplies(item,stage.id));
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
        <div class="exact-line"><strong>Berlaku untuk:</strong>${escapeHtml(exactScopeLabel(item))}</div>
        <div class="exact-line"><strong>Status:</strong>${escapeHtml(exactVerificationLabel(item))} · diperiksa ${escapeHtml(item.verifiedAt||'')}</div>
        <a class="source" href="${item.sourceUrl}" target="_blank" rel="noopener">Lihat dasar resmi ↗</a>
        <button type="button" class="exact-more" data-exact-more="${escapeHtml(item.id)}">Masih bingung? Tanya lebih spesifik</button>
      </div>
    </details>`;
  }).join('');
  list.querySelectorAll('[data-exact-more]').forEach(button=>button.addEventListener('click',()=>{
    const item=answers.find(row=>row.id===button.dataset.exactMore);
    if(!item)return;
    if($('stageDialog')?.open)$('stageDialog').close();
    const input=$('brokerLikeQuestion');
    input.value=item.question+' — ';
    document.querySelector('.micro-help')?.scrollIntoView({behavior:'smooth',block:'center'});
    setTimeout(()=>input.focus(),250);
  }));
}

const PRE_SUBMIT_STAGES=new Set([
  'registration','document_verify','job_application','visa_docs','predeparture_training','residence_registration'
]);

function renderPreSubmitGate(stage){
  const section=$('preSubmitSection');
  const result=$('preSubmitResult');
  if(!PRE_SUBMIT_STAGES.has(stage.id)){
    section.hidden=true;
    result.hidden=true;
    result.innerHTML='';
    return;
  }
  section.hidden=false;
  result.hidden=true;
  result.innerHTML='';
}

function evaluatePreSubmit(stage){
  const issues=[];
  const stats=bqcStageStats(stage.id);
  const unresolvedHigh=stats.items.filter(item=>!item.resolved&&item.blocksZeroBrokerReady);
  if(unresolvedHigh.length){
    issues.push(...unresolvedHigh.slice(0,8).map(item=>'Belum ada jawaban pasti: '+item.question));
    if(unresolvedHigh.length>8)issues.push('+'+(unresolvedHigh.length-8)+' pertanyaan blocker lain belum terverifikasi.');
  }

  if(consistencyRisk.hasMismatch&&consistencyRisk.stageId===stage.id){
    issues.push('Data antar dokumen yang Anda bandingkan masih tidak konsisten.');
  }

  const wizardStats=wizardReviewStats(stage.id);
  if(wizardStats.total&&wizardStats.missing){
    issues.push('Panduan formulir belum selesai: '+wizardStats.missing+' dari '+wizardStats.total+' kolom belum Anda cek.');
  }

  const availableScopes=scopeOptionsForStage(stage.id);
  if(availableScopes.length&&!selectedScope(stage.id)){
    issues.push('Pilih dulu pengumuman yang benar-benar memuat nama Anda. Aturan tanggal/gelombang tidak boleh ditebak.');
  }

  const pack=documentPackForStage(stage.id);
  if(!pack){
    issues.push('Belum ada checklist dokumen resmi yang dikunci untuk tahap ini.');
  }else if(['awaiting_sector_notice','source_guided','scope_required','review_required'].includes(pack.status)){
    issues.push('Checklist dokumen tahap ini belum cukup spesifik untuk pengumuman yang berlaku bagi Anda.');
  }else{
    const checked=new Set(read(KEYS.docs,[]));
    const missing=(pack.items||[]).filter(item=>item.required&&!checked.has(item.id));
    missing.forEach(item=>issues.push('Dokumen wajib belum ditandai siap: '+item.title));
  }

  return {issues,ready:issues.length===0};
}

$('preSubmitBtn').addEventListener('click',()=>{
  if(!activeStage)return;
  const result=$('preSubmitResult');
  const check=evaluatePreSubmit(activeStage);
  result.hidden=false;
  result.className='result '+(check.ready?'safe':'risk');
  if(check.ready){
    result.innerHTML='<strong>SIAP MENURUT PEMERIKSAAN APLIKASI.</strong><p>Tidak ada hal penting yang belum pasti dari aturan dan checklist yang saat ini sudah terverifikasi. Tetap cocokkan dengan pengumuman resmi yang memuat nama Anda sebelum menekan tombol submit.</p>';
  }else{
    result.innerHTML='<strong>JANGAN SUBMIT DULU.</strong><p>Ada hal yang belum cukup aman untuk dilewati:</p><ul class="pre-submit-list">'+check.issues.map(x=>'<li>'+escapeHtml(x)+'</li>').join('')+'</ul>';
  }
});

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
  renderScopePicker(stage);
  renderStageBqc(stage);
  renderPreSubmitGate(stage);
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
  doneBtn.textContent=isDone
    ?'Batalkan tahap ini & setelahnya'
    :canComplete
      ?(PRE_SUBMIT_STAGES.has(stage.id)?'Periksa & lanjut':'Tandai selesai & lanjut')
      :'Selesaikan tahap sebelumnya dulu';
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
    if(PRE_SUBMIT_STAGES.has(activeStage.id)){
      const check=evaluatePreSubmit(activeStage);
      if(!check.ready){
        const result=$('preSubmitResult');
        $('preSubmitSection').hidden=false;
        result.hidden=false;
        result.className='result risk';
        result.innerHTML='<strong>JANGAN LANJUT DULU.</strong><p>Selesaikan ini terlebih dahulu:</p><ul class="pre-submit-list">'+check.issues.map(x=>'<li>'+escapeHtml(x)+'</li>').join('')+'</ul>';
        $('preSubmitSection').scrollIntoView({behavior:'smooth',block:'center'});
        return;
      }
    }
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


function renderQuickQuestionChips(stage){
  const wrap=$('quickQuestionChips');
  if(!wrap||!stage||!brokerQuestions){
    if(wrap){wrap.hidden=true;wrap.innerHTML='';}
    return;
  }
  const candidates=bqcQuestionsForStage(stage.id)
    .filter(item=>item.resolved)
    .sort((a,b)=>{
      const aw=a.severity==='high'?0:a.severity==='medium'?1:2;
      const bw=b.severity==='high'?0:b.severity==='medium'?1:2;
      return aw-bw;
    })
    .slice(0,4);

  if(!candidates.length){
    wrap.hidden=true;
    wrap.innerHTML='';
    return;
  }

  wrap.hidden=false;
  wrap.innerHTML=candidates.map(item=>
    '<button type="button" class="quick-question-chip" data-quick-question="'+escapeHtml(item.question)+'">'+escapeHtml(item.question)+'</button>'
  ).join('');

  wrap.querySelectorAll('[data-quick-question]').forEach(btn=>btn.addEventListener('click',()=>{
    $('brokerLikeQuestion').value=btn.dataset.quickQuestion||'';
    answerBrokerLikeQuestion();
    $('brokerLikeQuestionResult').scrollIntoView({behavior:'smooth',block:'nearest'});
  }));
}

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
    const scoped=scopeOptionsForStage(next.id);
    const needsScope=scoped.length>0&&!selectedScope(next.id);
    const toolKeys=STAGE_TOOLS[next.id]||[];
    const firstTool=toolKeys.length?TOOL_META[toolKeys[0]]:null;
    const normalAction=firstTool
      ? `<button class="primary" data-go="${firstTool.view}">${escapeHtml(firstTool.label)}</button><button class="secondary" data-stage="${escapeHtml(next.id)}">Lihat instruksi tahap</button>`
      : `<button class="primary" data-stage="${escapeHtml(next.id)}">Buka langkah ini</button>`;
    const scopeAction=needsScope
      ? `<div class="next-scope"><label>${escapeHtml(scopePromptForStage(next.id))}<select data-next-scope><option value="">Pilih tanggal</option>${scoped.map(item=>`<option value="${escapeHtml(item.key)}">${escapeHtml(item.label)}</option>`).join('')}</select></label><small>Pilih hanya jadwal yang memang memuat nama Anda.</small></div><button class="secondary" data-stage="${escapeHtml(next.id)}">Saya belum tahu → lihat petunjuk</button>`
      : normalAction;
    box.innerHTML=`<small>LANGKAH BERIKUTNYA</small><h2>${escapeHtml(stageTitle(next))}</h2><p>${escapeHtml(stageAction(next))}</p>${scopeAction}`;
    renderContextTools(next);
  }else{
    box.innerHTML='<small>RUTE SELESAI</small><h2>Semua tahap yang dilacak sudah ditandai selesai</h2><p>Periksa kembali Celah Calo sebelum menganggap rute ini benar-benar tanpa calo.</p><button class="primary" data-go="gaps">Periksa Celah Calo</button>';
    renderContextTools(null);
  }

  box.querySelector('[data-next-scope]')?.addEventListener('change',e=>{
    const value=e.currentTarget.value;
    if(!value)return;
    saveScopeSelection(next.id,value);
    renderNextAction();
    renderDocuments();
    renderBqcStatus();
  });
  box.querySelectorAll('[data-go]').forEach(btn=>btn.addEventListener('click',e=>switchView(e.currentTarget.dataset.go)));
  box.querySelectorAll('[data-stage]').forEach(btn=>btn.addEventListener('click',e=>{
    const stage=route.stages.find(s=>s.id===e.currentTarget.dataset.stage);
    if(stage)openStage(stage);
  }));
  renderQuickQuestionChips(next||null);
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



async function detectFileSignature(file){
  const bytes=new Uint8Array(await file.slice(0,8).arrayBuffer());
  const isPdf=bytes.length>=5&&String.fromCharCode(...bytes.slice(0,5))==='%PDF-';
  const isJpeg=bytes.length>=3&&bytes[0]===0xFF&&bytes[1]===0xD8&&bytes[2]===0xFF;
  if(isPdf)return 'PDF';
  if(isJpeg)return 'JPG';
  return 'UNKNOWN';
}

function normalizeSearch(value){
  return String(value||'')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[^a-z0-9\s]/g,' ')
    .replace(/\s+/g,' ')
    .trim();
}

const SEARCH_STOP_WORDS=new Set([
  'apa','apakah','saya','anda','kamu','yang','dan','atau','untuk','dari','dengan','ini','itu',
  'harus','boleh','bisa','kalau','jika','bagaimana','gimana','berapa','kapan','dimana','mana',
  'pilih','memilih','tombol','tolong','mohon','pakai','gunakan'
]);

function meaningfulSearchTokens(normalizedQuery){
  return String(normalizedQuery||'').split(' ').filter(token=>token.length>1&&!SEARCH_STOP_WORDS.has(token));
}

function fieldAnswerHtml(item){
  const dont=(item.doNotDo||[]).map(text=>'• '+escapeHtml(text)).join('<br>');
  return `<article class="field-match">
    <strong>${escapeHtml(item.question)}</strong>
    <div class="write-this">${escapeHtml(item.answer)}</div>
    <div class="exact-body">
      <div class="exact-line write"><strong>Tulis / lakukan seperti ini:</strong>${escapeHtml(item.writeExactly)}</div>
      <div class="exact-line"><strong>Mengapa:</strong>${escapeHtml(item.why)}</div>
      <div class="exact-line"><strong>Berlaku untuk:</strong>${escapeHtml(exactScopeLabel(item))}</div>
      ${dont?'<div class="exact-line block"><strong>Jangan:</strong>'+dont+'</div>':''}
      <a class="source" href="${item.sourceUrl}" target="_blank" rel="noopener">Dasar resmi ↗</a>
    </div>
  </article>`;
}

function wizardFieldSearchRows(query,stageId){
  if(!formWizards?.forms?.length)return [];
  const q=normalizeSearch(query);
  if(!q)return [];
  const tokens=meaningfulSearchTokens(q);
  const rows=[];
  for(const form of formWizards.forms){
    if(stageId){
      if(!wizardFormApplies(form,stageId))continue;
    }else{
      if(form.scopeType==='cohort'||(form.scopeKeys||[]).length)continue;
      if(sourceNeedsReview(form.sourceUrl)||sourceNeedsReview(form.guidanceUrl))continue;
    }
    const scope=stageId?selectedScope(stageId):'';
    const scopeInfo=stageId?scopeOptionsForStage(stageId).find(item=>item.key===scope):null;
    const sourceUrl=stageId
      ?(wizardGuidanceUrl(form,stageId)||wizardSourceUrl(form,stageId))
      :(form.guidanceUrl||form.sourceUrl);
    for(const field of form.fields||[]){
      const hay=normalizeSearch([form.title,field.label,field.instruction,field.example,field.dont||''].join(' '));
      let score=0;
      if(hay.includes(q))score+=24;
      tokens.forEach(token=>{if(hay.includes(token))score+=2});
      if(score>0){
        rows.push({
          item:{
            id:'wizard:'+form.id+':'+field.id,
            question:form.title+' — '+field.label,
            answer:field.instruction,
            writeExactly:field.instruction,
            why:'Berdasarkan petunjuk resmi untuk formulir dan pengumuman yang dipilih.',
            doNotDo:field.dont?[field.dont]:[],
            sourceUrl,
            verifiedAt:form.verifiedAt||formWizards.verifiedAt||'2026-10-02',
            verificationStatus:form.verificationStatus||'verified_form_guidance',
            scopeType:scope?'cohort':'route_2026',
            scopeKey:scope||undefined,
            scopeLabel:scopeInfo?.label||undefined
          },
          score
        });
      }
    }
  }
  return rows;
}

function findScopedAnswerChoices(query,stageId){
  if(!stageId||!exactAnswers?.answers?.length||selectedScope(stageId))return [];
  const q=normalizeSearch(query);
  if(!q)return [];
  const tokens=meaningfulSearchTokens(q);
  const scopeMeta=new Map(scopeOptionsForStage(stageId).map(item=>[item.key,item]));
  const scopes=new Map();

  exactAnswers.answers
    .filter(item=>item.stages?.includes(stageId)&&item.scopeType==='cohort')
    .forEach(item=>{
      const hay=normalizeSearch([item.question,item.answer,item.writeExactly,item.why,...(item.doNotDo||[])].join(' '));
      let score=0;
      if(hay.includes(q))score+=20;
      tokens.forEach(token=>{if(hay.includes(token))score+=2});
      if(score<8)return;

      const keys=Array.isArray(item.scopeKeys)&&item.scopeKeys.length
        ?item.scopeKeys
        :(item.scopeKey?[item.scopeKey]:[]);
      keys.forEach(key=>{
        const meta=scopeMeta.get(key);
        const candidate={
          ...item,
          scopeKey:key,
          scopeLabel:meta?.label||item.scopeLabel||key,
          sourceUrl:meta?.sourceUrl||item.sourceUrl
        };
        const current=scopes.get(key);
        if(!current||score>current.score)scopes.set(key,{item:candidate,score});
      });
    });

  return [...scopes.values()]
    .sort((a,b)=>b.score-a.score)
    .slice(0,5)
    .map(row=>row.item);
}

function renderScopeChoiceForQuestion(query,out,onChosen){
  const stage=currentStage();
  const choices=findScopedAnswerChoices(query,stage?.id);
  if(!choices.length)return false;
  out.className='result warn';
  out.hidden=false;
  out.innerHTML='<strong>Satu hal dulu: nama Anda ada di pengumuman yang mana?</strong><p>Pilih pengumuman yang benar. Setelah itu jawaban akan menyesuaikan otomatis.</p><div class="scope-choice-list">'+choices.map(item=>
    '<div class="scope-choice-row"><button type="button" class="scope-choice" data-scope="'+escapeHtml(item.scopeKey)+'">'+escapeHtml(item.scopeLabel||'Pengumuman ini')+'</button>'+
    (item.sourceUrl?'<a class="scope-check-link" href="'+item.sourceUrl+'" target="_blank" rel="noopener">Cek nama saya ↗</a>':'')+
    '</div>'
  ).join('')+'</div><small class="muted">Kalau tidak yakin, jangan pilih sembarang. Buka pengumuman resmi dan pastikan nama Anda ada di sana.</small>';
  out.querySelectorAll('[data-scope]').forEach(btn=>btn.addEventListener('click',()=>{
    const state=read(KEYS.scopeSelections,{});
    state[stage.id]=btn.dataset.scope;
    write(KEYS.scopeSelections,state);
    renderScopePicker(stage);
    renderBqcStatus();
    renderDocuments();
    if(activeStage?.id===stage.id){
      renderStageBqc(activeStage);
      renderExactAnswers(activeStage);
      renderPreSubmitGate(activeStage);
    }
    onChosen?.();
  }));
  return true;
}

function findExactFieldAnswers(query){
  const q=normalizeSearch(query);
  if(!q)return [];
  const tokens=meaningfulSearchTokens(q);
  const current=currentStage();
  const stageId=current?.id||null;
  const exactRows=(exactAnswers?.answers||[])
    .filter(item=>!stageId||exactAnswerApplies(item,stageId))
    .map(item=>{
      const hay=normalizeSearch([item.question,item.answer,item.writeExactly,item.why,...(item.doNotDo||[])].join(' '));
      let lexicalScore=0;
      if(hay.includes(q))lexicalScore+=20;
      tokens.forEach(token=>{if(hay.includes(token))lexicalScore+=2});
      if(lexicalScore===0)return {item,score:0};
      const stageBoost=current&&item.stages?.includes(current.id)?12:0;
      return {item,score:lexicalScore+stageBoost};
    })
    .filter(row=>row.score>0);
  const wizardRows=wizardFieldSearchRows(query,stageId);
  const seen=new Set();
  return [...exactRows,...wizardRows]
    .sort((a,b)=>b.score-a.score)
    .filter(row=>{
      const key=normalizeSearch(row.item.question);
      if(seen.has(key))return false;
      seen.add(key);
      return true;
    })
    .slice(0,5)
    .map(row=>row.item);
}


function saveUnresolvedQuestion(query,origin='micro_help'){
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
      status:'needs_official_verification',
      origin
    });
    write(KEYS.fieldQuestions,list);
    renderUnresolvedFieldQuestions();
    renderBqcStatus();
    if(activeStage?.id===stage?.id)renderStageBqc(activeStage);
  }
  return key;
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
  const helpHtml=officialHelpFallbackHtml(currentStage()?.id);
  out.innerHTML=`<strong>Belum ada jawaban terverifikasi untuk “${escapeHtml(query)}”.</strong>
    <p>Jangan isi berdasarkan tebakan, aturan lama, atau jawaban sektor lain. Simpan pertanyaan ini untuk diverifikasi sebelum submit.</p>
    <button id="saveUnresolvedFieldBtn" class="secondary" type="button">Simpan pertanyaan yang belum terjawab</button>${helpHtml}`;

  const saveUnresolvedBtn=out.querySelector('#saveUnresolvedFieldBtn');
  saveUnresolvedBtn?.addEventListener('click',()=>{
    saveUnresolvedQuestion(query,'field_copilot');
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


function officialHelpChannel(channelId){
  return (officialHelp?.channels||[]).find(item=>item.id===channelId)||null;
}

function officialHelpCard(channel){
  if(!channel)return '';
  const calls=(channel.phones||[]).map(phone=>
    '<a class="official-help-link" href="'+escapeHtml(phone.href)+'">'+escapeHtml(phone.label)+': '+escapeHtml(phone.display)+'</a>'
  ).join('');
  const whatsapp=channel.whatsapp
    ? '<a class="official-help-link" href="'+escapeHtml(channel.whatsapp.href)+'" target="_blank" rel="noopener">WhatsApp: '+escapeHtml(channel.whatsapp.display)+'</a>'
    : '';
  const email=channel.email
    ? '<a class="official-help-link" href="'+escapeHtml(channel.email.href)+'">Email: '+escapeHtml(channel.email.display)+'</a>'
    : '';
  const hours=channel.hours?'<small>'+escapeHtml(channel.hours)+'</small>':'';
  return '<div class="official-help-card"><strong>'+escapeHtml(channel.name)+'</strong><span>'+escapeHtml(channel.label||'')+'</span>'+calls+whatsapp+email+hours+'<a class="official-help-source" href="'+escapeHtml(channel.sourceUrl)+'" target="_blank" rel="noopener">Sumber kontak resmi ↗</a></div>';
}

function officialHelpFallbackHtml(stageId){
  const ids=officialHelp?.stageMap?.[stageId]||[];
  const channels=ids.map(officialHelpChannel).filter(Boolean);
  if(!channels.length)return '';
  const first=officialHelpCard(channels[0]);
  const more=channels.slice(1).map(officialHelpCard).join('');
  return '<div class="official-help-fallback"><strong>Kalau perlu bicara dengan petugas:</strong>'+first+
    (more?'<details><summary>Pilihan resmi lain</summary>'+more+'</details>':'')+
    '<p>Gunakan jalur resmi di atas, bukan calo, untuk pertanyaan yang belum bisa dipastikan aplikasi.</p></div>';
}

function answerBrokerLikeQuestion(){
  const query=$('brokerLikeQuestion').value.trim();
  const out=$('brokerLikeQuestionResult');
  out.hidden=false;
  out.className='result';

  if(!query){
    out.classList.add('warn');
    out.textContent='Tulis pertanyaan kecil yang membuat Anda ragu.';
    return;
  }

  if(renderScopeChoiceForQuestion(query,out,answerBrokerLikeQuestion))return;
  const matches=findExactFieldAnswers(query);
  if(matches.length){
    out.classList.add('safe');
    out.innerHTML='<strong>Jawaban terverifikasi ditemukan.</strong><div class="field-match-list">'+matches.map(fieldAnswerHtml).join('')+'</div>';
    return;
  }

  out.classList.add('warn');
  const helpHtml=officialHelpFallbackHtml(currentStage()?.id);
  out.innerHTML=`<strong>Belum ada jawaban resmi yang cukup spesifik untuk “${escapeHtml(query)}”.</strong>
    <p>Jangan menebak dan jangan submit dulu. Simpan pertanyaan ini agar diverifikasi terhadap form/pengumuman resmi yang tepat.</p>
    <button id="saveBrokerLikeQuestionBtn" class="secondary" type="button">Simpan sebagai pertanyaan wajib diverifikasi</button>${helpHtml}`;

  const saveBtn=out.querySelector('#saveBrokerLikeQuestionBtn');
  saveBtn?.addEventListener('click',()=>{
    saveUnresolvedQuestion(query,'global_broker_like_help');
    saveBtn.disabled=true;
    saveBtn.textContent='Tersimpan — jangan submit sampai ada jawaban resmi';
  });
}

$('brokerLikeQuestionBtn').addEventListener('click',answerBrokerLikeQuestion);
$('brokerLikeQuestion').addEventListener('keydown',(event)=>{
  if(event.key==='Enter'){
    event.preventDefault();
    answerBrokerLikeQuestion();
  }
});


const CONSISTENCY_GROUPS=[
  {label:'Nama',ids:['consNamePassport','consNameSlc','consNameKtp','consNameBank'],normalizer:'name'},
  {label:'Tanggal lahir',ids:['consDobPassport','consDobKtp','consDobSlc'],normalizer:'date'},
  {label:'Nomor paspor',ids:['consPassportMain','consPassportSkck','consPassportVisa'],normalizer:'id'},
  {label:'NIK',ids:['consNikKtp','consNikVisa','consNikOther'],normalizer:'id'},
  {label:'ID CPMI',ids:['consCpmiCall','consCpmiChecklist','consCpmiPower'],normalizer:'id'},
  {label:'Nomor rekening BNI',ids:['consBankBook','consBankChecklist','consBankPower'],normalizer:'digits'},
  {label:'Nomor HP',ids:['consPhoneSisko','consPhoneVisa','consPhonePlacement'],normalizer:'phone'},
  {label:'Email',ids:['consEmailSisko','consEmailVisa','consEmailPlacement'],normalizer:'email'}
];

function normalizeConsistencyValue(value,type){
  const text=String(value||'').trim();
  if(!text)return '';
  if(type==='name'){
    return text.normalize('NFKC').replace(/\s+/g,' ').toUpperCase();
  }
  if(type==='id'){
    return text.normalize('NFKC').replace(/[\s-]+/g,'').toUpperCase();
  }
  if(type==='digits'){
    return text.normalize('NFKC').replace(/[^0-9]/g,'');
  }
  if(type==='phone'){
    let digits=text.normalize('NFKC').replace(/[^0-9]/g,'');
    if(digits.startsWith('0062'))digits='0'+digits.slice(4);
    else if(digits.startsWith('62'))digits='0'+digits.slice(2);
    return digits;
  }
  if(type==='email'){
    return text.normalize('NFKC').replace(/\s+/g,'').toLowerCase();
  }
  if(type==='date'){
    const raw=text.replace(/[.\-]/g,'/').replace(/\s+/g,'');
    let m=raw.match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/);
    if(m)return [m[1],String(Number(m[2])).padStart(2,'0'),String(Number(m[3])).padStart(2,'0')].join('-');
    m=raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if(m)return [m[3],String(Number(m[2])).padStart(2,'0'),String(Number(m[1])).padStart(2,'0')].join('-');
    return raw.toUpperCase();
  }
  return text;
}

function evaluateConsistency(){
  const checked=[];
  const mismatches=[];
  const formatWarnings=[];

  CONSISTENCY_GROUPS.forEach(group=>{
    const values=group.ids
      .map(id=>({id,value:$(id)?.value?.trim()||''}))
      .filter(row=>row.value!=='');
    if(values.length<2)return;

    checked.push(group.label);
    const normalized=values.map(row=>normalizeConsistencyValue(row.value,group.normalizer));
    if(new Set(normalized).size>1){
      mismatches.push(group.label);
    }

    if(group.label==='Tanggal lahir'){
      values.forEach(row=>{
        const v=normalizeConsistencyValue(row.value,'date');
        const m=v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if(!m){
          formatWarnings.push('Tanggal lahir harus menggunakan tanggal yang jelas dan valid.');
          return;
        }
        const y=Number(m[1]),mo=Number(m[2]),d=Number(m[3]);
        const dt=new Date(Date.UTC(y,mo-1,d));
        if(dt.getUTCFullYear()!==y||dt.getUTCMonth()!==mo-1||dt.getUTCDate()!==d){
          formatWarnings.push('Tanggal lahir tidak valid. Periksa tahun, bulan, dan hari.');
        }
      });
    }
    if(group.label==='NIK'){
      values.forEach(row=>{
        const v=normalizeConsistencyValue(row.value,'id');
        if(!/^\d{16}$/.test(v))formatWarnings.push('NIK harus 16 digit.');
      });
    }
    if(group.label==='Nomor paspor'){
      values.forEach(row=>{
        const v=normalizeConsistencyValue(row.value,'id');
        if(!/^[A-Z0-9]{5,12}$/.test(v))formatWarnings.push('Periksa format nomor paspor; gunakan nomor terbaru tanpa spasi/simbol.');
      });
    }
    if(group.label==='ID CPMI'){
      values.forEach(row=>{
        const v=normalizeConsistencyValue(row.value,'id');
        if(!/^ID\d+$/.test(v))formatWarnings.push('ID CPMI harus mengikuti format ID + angka dari pengumuman resmi.');
      });
    }
    if(group.label==='Nomor rekening BNI'){
      values.forEach(row=>{
        const raw=String(row.value||'').trim().replace(/[\s-]/g,'');
        if(!/^\d+$/.test(raw))formatWarnings.push('Nomor rekening BNI harus berupa angka.');
      });
    }
    if(group.label==='Nomor HP'){
      values.forEach(row=>{
        const v=normalizeConsistencyValue(row.value,'phone');
        if(v.length<8||v.length>16)formatWarnings.push('Periksa nomor HP; setelah normalisasi harus 8–16 digit.');
      });
    }
    if(group.label==='Email'){
      values.forEach(row=>{
        const v=normalizeConsistencyValue(row.value,'email');
        if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v))formatWarnings.push('Format email belum valid.');
      });
    }
  });

  return {checked,mismatches,formatWarnings:[...new Set(formatWarnings)]};
}

$('checkConsistencyBtn').addEventListener('click',()=>{
  const out=$('consistencyResult');
  const result=evaluateConsistency();
  const stage=currentStage();

  out.hidden=false;
  if(!result.checked.length){
    out.className='result warn';
    out.innerHTML='<strong>Belum cukup data untuk dibandingkan.</strong><p>Isi minimal dua sumber untuk satu kelompok, misalnya nama di Paspor dan nama di SLC.</p>';
    consistencyRisk={stageId:stage?.id||null,hasMismatch:false};
    return;
  }

  const issues=[...result.mismatches.map(x=>'Tidak sama: '+x),...result.formatWarnings];
  if(issues.length){
    out.className='result risk';
    out.innerHTML='<strong>JANGAN SUBMIT DULU.</strong><p>Ada perbedaan yang perlu dijelaskan atau diperbaiki:</p><ul class="pre-submit-list">'+issues.map(x=>'<li>'+escapeHtml(x)+'</li>').join('')+'</ul><p>Periksa dokumen sumber dan aturan resmi sebelum mengubah data.</p>';
    consistencyRisk={stageId:stage?.id||null,hasMismatch:true};
  }else{
    out.className='result safe';
    out.innerHTML='<strong>Data yang dibandingkan konsisten.</strong><p>'+escapeHtml(result.checked.join(', '))+' tidak menunjukkan perbedaan setelah normalisasi dasar.</p>';
    consistencyRisk={stageId:stage?.id||null,hasMismatch:false};
  }
});

$('clearConsistencyBtn').addEventListener('click',()=>{
  document.querySelectorAll('.consistency-check input').forEach(input=>{input.value=''});
  const out=$('consistencyResult');
  out.hidden=true;
  out.className='result';
  out.innerHTML='';
  consistencyRisk={stageId:null,hasMismatch:false};
});

document.querySelectorAll('.consistency-check input').forEach(input=>input.addEventListener('input',()=>{
  const out=$('consistencyResult');
  if(!out.hidden){
    out.hidden=true;
    out.className='result';
    out.innerHTML='';
  }
  consistencyRisk={stageId:null,hasMismatch:false};
}));

function renderDocumentExamples(stageId){
  const section=$('documentExampleSection');
  const list=$('documentExampleList');
  if(!documentExamples?.samples?.length){
    section.hidden=true;
    list.innerHTML='';
    return;
  }

  const samples=documentExamples.samples.filter(sample=>{
    if(!sample.stages?.includes(stageId))return false;
    if(sourceNeedsReview(sample.sourceUrl))return false;
    if((sample.officialFiles||[]).some(file=>sourceNeedsReview(file.url)))return false;
    if(sample.scopeType!=='cohort')return true;
    return selectedScope(stageId)===sample.scopeKey;
  });
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
    const officialFiles=(sample.officialFiles||[]).map(file=>`<a class="example-file-link" href="${file.url}" target="_blank" rel="noopener">${escapeHtml(file.label)} ↗</a>`).join('');
    return `<details class="example-card" ${index===0?'open':''}>
      <summary><span>${escapeHtml(sample.title)}</span><span>Contoh</span></summary>
      <div class="example-banner">${escapeHtml(documentExamples.policy?.banner||'DATA CONTOH — JANGAN DISALIN')}</div>
      <div class="example-body">
        <div class="example-table">${rows}</div>
        ${checks?'<ul class="example-checks">'+checks+'</ul>':''}
        <p class="example-note">${escapeHtml(documentExamples.policy?.note||'Ganti semua data contoh dengan data Anda sendiri.')}</p>
        ${officialFiles?'<div class="example-files"><strong>Bandingkan dengan file resmi:</strong>'+officialFiles+'</div>':''}
        <a class="source" href="${sample.sourceUrl}" target="_blank" rel="noopener">Dasar resmi contoh ↗</a>
      </div>
    </details>`;
  }).join('');
}


function formsForStage(stageId){
  return (formWizards?.forms||[]).filter(form=>wizardFormApplies(form,stageId));
}

function wizardReviewKey(form,field,stageId){
  const scope=selectedScope(stageId)||'default';
  return [stageId,scope,form.id,field.id].join('|');
}

function reviewedWizardSet(){
  return new Set(read(KEYS.wizardReviewed,[]));
}

function markWizardFieldReviewed(form,field,stageId){
  if(!form||!field||!stageId)return;
  const state=reviewedWizardSet();
  state.add(wizardReviewKey(form,field,stageId));
  write(KEYS.wizardReviewed,[...state]);
}

function isWizardFieldReviewed(form,field,stageId){
  return reviewedWizardSet().has(wizardReviewKey(form,field,stageId));
}

function wizardReviewStats(stageId){
  const forms=formsForStage(stageId).filter(form=>wizardFormVerified(form));
  const reviewed=reviewedWizardSet();
  let total=0,done=0;
  forms.forEach(form=>{
    (form.fields||[]).forEach(field=>{
      if(!field.validator)return;
      total+=1;
      if(reviewed.has(wizardReviewKey(form,field,stageId)))done+=1;
    });
  });
  return {total,done,missing:Math.max(0,total-done)};
}

function validateWizardValue(value,validator){
  const raw=String(value??'');
  const text=raw.trim();
  const type=validator?.type;
  if(!type)return {ok:null,message:'Tidak ada pemeriksaan otomatis untuk kolom ini.'};

  if(type==='blank'){
    return text===''?{ok:true,message:'Benar — kolom ini dibiarkan kosong.'}:{ok:false,message:'Kolom ini harus dikosongkan.'};
  }
  if(type==='exact_ci'){
    const expected=String(validator.expected||'').trim();
    return text.toUpperCase()===expected.toUpperCase()
      ?{ok:true,message:'Benar — nilainya sesuai petunjuk.'}
      :{ok:false,message:'Tulis persis: '+expected};
  }
  if(type==='contains_ci'){
    const expected=String(validator.expected||'').trim();
    return text.toUpperCase().includes(expected.toUpperCase())
      ?{ok:true,message:'Benar — nilai memuat '+expected+'.'}
      :{ok:false,message:'Nilai harus memuat '+expected+'.'};
  }
  if(type==='date_yyyy_mm_dd'){
    const m=text.match(/^(\d{4})\/(\d{2})\/(\d{2})$/);
    if(!m)return {ok:false,message:'Gunakan format YYYY/MM/DD, contoh 1995/04/17.'};
    const y=Number(m[1]),mo=Number(m[2]),d=Number(m[3]);
    const dt=new Date(Date.UTC(y,mo-1,d));
    const valid=dt.getUTCFullYear()===y&&dt.getUTCMonth()===mo-1&&dt.getUTCDate()===d;
    return valid?{ok:true,message:'Format tanggal valid.'}:{ok:false,message:'Tanggal tidak valid. Periksa tahun, bulan, dan hari.'};
  }
  if(type==='email'){
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)
      ?{ok:true,message:'Format email valid.'}
      :{ok:false,message:'Format email belum valid.'};
  }
  if(type==='nik16'){
    return /^\d{16}$/.test(text)
      ?{ok:true,message:'Format NIK 16 digit valid.'}
      :{ok:false,message:'NIK harus 16 digit angka.'};
  }
  if(type==='phone'){
    const digits=text.replace(/[^0-9]/g,'');
    return digits.length>=8&&digits.length<=16
      ?{ok:true,message:'Format dasar nomor telepon terlihat valid.'}
      :{ok:false,message:'Periksa nomor telepon; gunakan nomor aktif dengan 8–16 digit.'};
  }
  if(type==='passport'){
    return /^[A-Za-z0-9]{5,12}$/.test(text)
      ?{ok:true,message:'Format dasar nomor paspor terlihat valid.'}
      :{ok:false,message:'Gunakan nomor paspor terbaru tanpa spasi/simbol tambahan.'};
  }
  if(type==='uppercase_nonempty'){
    if(!text)return {ok:false,message:'Kolom ini tidak boleh kosong.'};
    return text===text.toUpperCase()
      ?{ok:true,message:'Terisi dan huruf kapital.'}
      :{ok:false,message:'Gunakan huruf kapital sesuai petunjuk formulir.'};
  }
  if(type==='relationship_en'){
    const allowed=['FATHER','MOTHER','HUSBAND','WIFE','SISTER','BROTHER'];
    return allowed.includes(text.toUpperCase())
      ?{ok:true,message:'Hubungan ditulis dalam bahasa Inggris.'}
      :{ok:false,message:'Gunakan salah satu: '+allowed.join(', ')+'.'};
  }
  if(type==='cpmi_id'){
    return /^ID\d+$/i.test(text)
      ?{ok:true,message:'Format ID CPMI terlihat valid.'}
      :{ok:false,message:'ID CPMI harus mengikuti format ID + angka dari pengumuman/name tag.'};
  }
  if(type==='digits'){
    return /^\d+$/.test(text)
      ?{ok:true,message:'Format angka valid.'}
      :{ok:false,message:'Gunakan angka saja, tanpa spasi atau tanda baca.'};
  }
  if(type==='nonempty'){
    return text?{ok:true,message:'Kolom sudah terisi.'}:{ok:false,message:'Kolom ini tidak boleh kosong.'};
  }
  return {ok:null,message:'Jenis pemeriksaan belum didukung.'};
}

function resetWizardValueCheck(field){
  const wrap=$('formFieldCheck');
  const input=$('formFieldValue');
  const checkBtn=$('formFieldCheckBtn');
  const confirmBtn=$('formFieldConfirmBtn');
  const summary=wrap.querySelector('summary');
  const note=wrap.querySelector('.wizard-check-body small');
  const result=$('formFieldCheckResult');
  input.value='';
  result.hidden=true;
  result.className='result';
  result.textContent='';
  wrap.open=false;
  wrap.hidden=!field?.validator;

  const manual=field?.validator?.type==='manual_confirm';
  input.hidden=manual;
  checkBtn.hidden=manual;
  confirmBtn.hidden=!manual;
  if(summary)summary.textContent=manual?'Konfirmasi saya sudah melakukan ini':'Cek apakah isian saya sudah benar';
  if(note)note.textContent=manual
    ?'Konfirmasi ini hanya disimpan selama layar ini terbuka dan tidak mengirim data ke server.'
    :'Nilai ini tidak disimpan ke localStorage dan tidak dikirim ke server.';

  if(field?.validator&&!manual){
    input.placeholder=field.validator.type==='blank'
      ?'Biarkan kosong lalu tekan “Periksa nilai”'
      :'Tempel nilai yang Anda tulis — tidak disimpan';
  }
}


function formLineageStatus(form){
  if(!formLineage?.forms?.length||!form)return null;
  const lineageId=form.lineageFormId||form.id;
  const row=formLineage.forms.find(item=>item.formId===lineageId);
  if(!row)return null;

  if(row.stableAcrossComparedIssues){
    return {
      kind:'stable',
      text:'Versi formulir ini sama pada panggilan resmi yang sudah dibandingkan.'
    };
  }

  const stageId=(form.stages||[])[0]||'visa_docs';
  const scope=selectedScope(stageId);
  const legacyScopes=new Set(['visa_may26_2026','visa_jun19_2026']);

  if(lineageId==='debit_power'){
    if(form.id==='debit_power_legacy'||legacyScopes.has(scope)){
      return {
        kind:'legacy',
        text:'Gunakan versi lama yang dilampirkan pada panggilan Mei/Juni 2026; jangan campur dengan versi Agustus.'
      };
    }
    return {
      kind:'updated',
      text:'Formulir ini berubah pada Agustus 2026. Gunakan lampiran dari pengumuman yang memuat nama Anda.'
    };
  }

  return {
    kind:'updated',
    text:'Versi formulir pernah berubah. Gunakan lampiran dari pengumuman yang memuat nama Anda.'
  };
}

function renderFormWizardCard(form,index){
  const card=$('formWizardCard');
  const intro=$('formWizardIntro');
  if(!form){
    card.hidden=true;
    intro.innerHTML='';
    resetWizardValueCheck(null);
    return;
  }

  const lineage=formLineageStatus(form);
  const lineageHtml=lineage?'<div class="wizard-version '+lineage.kind+'">'+escapeHtml(lineage.text)+'</div>':'';
  intro.innerHTML='<strong>'+escapeHtml(form.title)+'</strong>'+lineageHtml+
    '<ul>'+((form.intro||[]).map(item=>'<li>'+escapeHtml(item)+'</li>').join(''))+'</ul>'+
    (form.attention?'<div class="wizard-attention"><strong>Perhatian:</strong> '+escapeHtml(form.attention)+'</div>':'')+
    '<p class="muted">'+escapeHtml(formWizards?.policy?.scopeNote||'')+'</p>'+
    '<div class="wizard-source-links"><a href="'+escapeHtml(wizardSourceUrl(form))+'" target="_blank" rel="noopener">Buka formulir resmi ↗</a><a href="'+escapeHtml(wizardGuidanceUrl(form))+'" target="_blank" rel="noopener">Buka petunjuk resmi ↗</a></div>';

  const stage=currentStage()||route?.stages?.at(-1);
  const stageForms=stage?formsForStage(stage.id):[form];
  const foundFormIndex=stageForms.findIndex(item=>item.id===form.id);
  const formIndex=foundFormIndex>=0?foundFormIndex:0;
  const total=form.fields.length;
  const safeIndex=Math.max(0,Math.min(index,total));
  const state={formId:form.id,index:safeIndex};
  write(KEYS.formWizard,state);

  card.hidden=false;
  if(safeIndex>=total){
    const stageId=stage?.id||(form.stages||[])[0]||'';
    const stats=stageId?wizardReviewStats(stageId):{total:0,done:0,missing:0};
    $('formWizardProgress').textContent='Panduan selesai · '+stats.done+'/'+stats.total+' kolom dicek';
    $('formWizardLabel').textContent='Periksa kembali formulir Anda';
    $('formWizardInstruction').textContent='Bandingkan semua kolom dengan formulir asli dan pengumuman yang memuat nama Anda sebelum menyerahkan dokumen.';
    $('formWizardExample').textContent='Jangan submit hanya karena semua langkah sudah dibaca.';
    $('formWizardDont').innerHTML='<strong>Terakhir:</strong> Periksa nama, tanggal, nomor paspor, NIK, alamat, tanda tangan, materai, dan kolom yang memang harus kosong.';
    $('formWizardPrev').disabled=false;
    const nextForm=stageForms[formIndex+1]||null;
    $('formWizardNext').hidden=!nextForm;
    $('formWizardNext').dataset.nextForm=nextForm?.id||'';
    if(nextForm)$('formWizardNext').textContent='Lanjut ke formulir berikutnya →';
    resetWizardValueCheck(null);
    return;
  }

  const field=form.fields[safeIndex];
  resetWizardValueCheck(field);
  const stageId=stage?.id||(form.stages||[])[0]||'';
  const reviewed=isWizardFieldReviewed(form,field,stageId);
  $('formWizardProgress').textContent='Kolom '+(safeIndex+1)+' dari '+total+(reviewed?' · ✓ sudah dicek':'');
  $('formWizardLabel').textContent=field.label;
  $('formWizardInstruction').textContent=field.instruction;
  $('formWizardExample').textContent=field.example||'';
  $('formWizardDont').innerHTML=field.dont?'<strong>Jangan:</strong> '+escapeHtml(field.dont):'';
  const prevForm=stageForms[formIndex-1]||null;
  $('formWizardPrev').disabled=safeIndex===0&&!prevForm;
  $('formWizardPrev').dataset.prevForm=safeIndex===0&&prevForm?prevForm.id:'';
  $('formWizardNext').hidden=false;
  $('formWizardNext').dataset.nextForm='';
  $('formWizardNext').textContent=safeIndex===total-1?'Selesai formulir →':'Berikutnya →';
}

function renderFormWizard(stage){
  const section=$('formWizardSection');
  const select=$('formWizardSelect');
  if(!formWizards||!stage){section.hidden=true;return}
  const forms=formsForStage(stage.id);
  if(!forms.length){
    section.hidden=true;
    select.innerHTML='';
    $('formWizardCard').hidden=true;
    return;
  }

  section.hidden=false;
  const saved=read(KEYS.formWizard,{});
  const selected=forms.some(form=>form.id===saved.formId)?saved.formId:forms[0].id;
  select.innerHTML=forms.map(form=>'<option value="'+escapeHtml(form.id)+'">'+escapeHtml(form.title)+'</option>').join('');
  select.value=selected;
  const form=forms.find(item=>item.id===selected);
  renderFormWizardCard(form,saved.formId===selected?Number(saved.index||0):0);
}

$('formWizardSelect').addEventListener('change',()=>{
  const stage=currentStage()||route?.stages?.at(-1);
  if(!stage)return;
  const form=formsForStage(stage.id).find(item=>item.id===$('formWizardSelect').value);
  if(form)renderFormWizardCard(form,0);
});

$('formWizardPrev').addEventListener('click',()=>{
  const prevFormId=$('formWizardPrev').dataset.prevForm||'';
  const stage=currentStage()||route?.stages?.at(-1);
  if(prevFormId&&stage){
    const prevForm=formsForStage(stage.id).find(item=>item.id===prevFormId);
    if(prevForm){
      $('formWizardSelect').value=prevForm.id;
      renderFormWizardCard(prevForm,Math.max(0,prevForm.fields.length-1));
      $('formWizardCard').scrollIntoView({behavior:'smooth',block:'start'});
      return;
    }
  }
  const state=read(KEYS.formWizard,{});
  const form=(formWizards?.forms||[]).find(item=>item.id===state.formId);
  if(!form)return;
  renderFormWizardCard(form,Math.max(0,Number(state.index||0)-1));
});

$('formWizardNext').addEventListener('click',()=>{
  const nextFormId=$('formWizardNext').dataset.nextForm||'';
  const stage=currentStage()||route?.stages?.at(-1);
  if(nextFormId&&stage){
    const nextForm=formsForStage(stage.id).find(item=>item.id===nextFormId);
    if(nextForm){
      $('formWizardSelect').value=nextForm.id;
      renderFormWizardCard(nextForm,0);
      $('formWizardCard').scrollIntoView({behavior:'smooth',block:'start'});
      return;
    }
  }
  const state=read(KEYS.formWizard,{});
  const form=(formWizards?.forms||[]).find(item=>item.id===state.formId);
  if(!form)return;
  const index=Number(state.index||0);
  const field=form.fields?.[index];
  if(field&&stage)markWizardFieldReviewed(form,field,stage.id);
  renderFormWizardCard(form,Math.min(form.fields.length,index+1));
});


function checkCurrentWizardValue(){
  const state=read(KEYS.formWizard,{});
  const form=(formWizards?.forms||[]).find(item=>item.id===state.formId);
  if(!form)return;
  const field=form.fields?.[Number(state.index||0)];
  if(!field?.validator)return;

  const input=$('formFieldValue');
  const out=$('formFieldCheckResult');
  const checked=validateWizardValue(input.value,field.validator);
  out.hidden=false;
  out.className='result '+(checked.ok===true?'safe':checked.ok===false?'risk':'warn');
  out.textContent=checked.message;
  if(checked.ok===true){
    const stage=currentStage()||route?.stages?.at(-1);
    if(stage)markWizardFieldReviewed(form,field,stage.id);
    renderFormWizardCard(form,Number(state.index||0));
  }
}

let formFieldCheckTimer=null;
$('formFieldCheckBtn').addEventListener('click',checkCurrentWizardValue);
$('formFieldConfirmBtn').addEventListener('click',()=>{
  const state=read(KEYS.formWizard,{});
  const form=(formWizards?.forms||[]).find(item=>item.id===state.formId);
  const field=form?.fields?.[Number(state.index||0)];
  const out=$('formFieldCheckResult');
  if(field?.validator?.type!=='manual_confirm')return;
  out.hidden=false;
  out.className='result safe';
  out.textContent='Dikonfirmasi — Anda sudah memeriksa langkah ini langsung pada formulir asli sesuai petunjuk.';
  const stage=currentStage()||route?.stages?.at(-1);
  if(stage)markWizardFieldReviewed(form,field,stage.id);
  renderFormWizardCard(form,Number(state.index||0));
});
$('formFieldValue').addEventListener('input',()=>{
  clearTimeout(formFieldCheckTimer);
  const state=read(KEYS.formWizard,{});
  const form=(formWizards?.forms||[]).find(item=>item.id===state.formId);
  const field=form?.fields?.[Number(state.index||0)];
  const out=$('formFieldCheckResult');
  if(!field?.validator||field.validator.type==='blank'||!$('formFieldValue').value.trim()){
    out.hidden=true;
    return;
  }
  formFieldCheckTimer=setTimeout(checkCurrentWizardValue,250);
});
$('formFieldValue').addEventListener('keydown',(event)=>{
  if(event.key==='Enter'){
    event.preventDefault();
    checkCurrentWizardValue();
  }
});

function safeDocumentPack(pack){
  if(!pack)return null;
  if(sourceNeedsReview(pack.sourceUrl)){
    return {
      ...pack,
      status:'review_required',
      title:'Panduan tahap ini sedang ditinjau',
      message:'Sumber resmi untuk tahap ini berubah. Jangan gunakan rincian lama, angka lama, atau checklist lama sampai review selesai. Buka sumber resmi terbaru atau gunakan kanal bantuan resmi.',
      items:[]
    };
  }
  return pack;
}

function documentPackForStage(stageId){
  if(!documentPacks?.packs?.length)return null;
  const selected=selectedScope(stageId);
  if(selected){
    const scoped=documentPacks.packs
      .filter(pack=>pack.appliesTo?.includes(stageId)&&pack.scopeKey===selected)
      .sort((a,b)=>(a.appliesTo?.length||999)-(b.appliesTo?.length||999))[0];
    if(scoped)return safeDocumentPack(scoped);
  }
  const unscoped=documentPacks.packs
    .filter(pack=>pack.appliesTo?.includes(stageId)&&!pack.scopeKey)
    .sort((a,b)=>(a.appliesTo?.length||999)-(b.appliesTo?.length||999));
  return safeDocumentPack(unscoped[0]||null);
}

function renderDocumentScopePicker(stage){
  const wrap=$('docScopeWrap');
  const select=$('docScopeSelect');
  const sourceLink=$('docScopeSource');
  const options=scopeOptionsForStage(stage.id);
  if(!options.length){
    wrap.hidden=true;
    select.innerHTML='';
    sourceLink.hidden=true;
    return;
  }
  wrap.hidden=false;
  select.innerHTML='<option value="">Belum pilih / pengumuman lain</option>'+options.map(item=>`<option value="${escapeHtml(item.key)}">${escapeHtml(item.label)}</option>`).join('');
  select.value=selectedScope(stage.id);
  const chosen=options.find(item=>item.key===select.value);
  const fallback=departureRegistryFallback(stage.id);
  if(chosen?.sourceUrl){
    sourceLink.hidden=false;
    sourceLink.href=chosen.sourceUrl;
    sourceLink.textContent='Buka pengumuman yang dipilih ↗';
  }else if(fallback?.url){
    sourceLink.hidden=false;
    sourceLink.href=fallback.url;
    sourceLink.textContent='Tanggal tidak ada? Cari di indeks resmi KP2MI ↗';
  }else{
    sourceLink.hidden=true;
    sourceLink.href='#';
  }
}

$('docScopeSelect').addEventListener('change',()=>{
  const stage=currentStage()||route?.stages?.at(-1);
  if(!stage)return;
  const value=$('docScopeSelect').value;
  saveScopeSelection(stage.id,value);
  renderDocuments();
  renderBqcStatus();
  if(activeStage?.id===stage.id){
    renderScopePicker(activeStage);
    renderStageBqc(activeStage);
    renderExactAnswers(activeStage);
    renderPreSubmitGate(activeStage);
  }
});

function renderDocuments(){
  if(!documentPacks||!route)return;
  const checked=new Set(read(KEYS.docs,[]));
  const stage=currentStage()||route.stages.at(-1);
  const pack=documentPackForStage(stage?.id);
  renderDocumentScopePicker(stage);
  renderFormWizard(stage);
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
    verified_practice:'Checklist bukti kerja',
    verified_current_immigration:'Terverifikasi dari Kementerian Kehakiman Korea',
    review_required:'Sumber resmi berubah — review diperlukan',
    scope_required:'Pilih pengumuman yang memuat nama Anda terlebih dahulu',
    verified_notice_2026_05_26:'Terverifikasi untuk panggilan 26 Mei 2026',
    verified_notice_2026_06_19:'Terverifikasi untuk panggilan 19 Juni 2026',
    verified_notice_2026_09_08:'Terverifikasi untuk panggilan 8 September 2026',
    verified_across_multiple_2026_calls:'Terverifikasi silang dari beberapa panggilan OPP 2026',
    verified_across_multiple_2026_notices:'Terverifikasi silang dari beberapa pengumuman 2026'
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
    if(pack.status==='review_required'){
      list.innerHTML='<article><div><h3>Jangan submit berdasarkan checklist lama</h3><p>Sumber resmi untuk tahap ini berubah dan sedang ditinjau. Checklist lama sengaja disembunyikan sampai review selesai.</p></div></article>';
    }else{
      list.innerHTML='<article><div><h3>Jangan gunakan daftar dari tahap/sector lain</h3><p>Checklist sengaja dikosongkan sampai sumber yang sesuai dengan rute ini terverifikasi. Ini mencegah dokumen lama atau sektor lain dianggap sebagai persyaratan resmi.</p></div></article>';
    }
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
        if(file.size===0)errors.push('file kosong');
        if(maxSize&&file.size>maxSize*1024*1024)errors.push('ukuran lebih dari '+maxSize+' MB');
        const lower=file.name.toLowerCase();
        if(doc.format==='PDF'&&!lower.endsWith('.pdf'))errors.push('nama file harus berakhiran .pdf');
        if(doc.format==='JPG'&&!/\.jpe?g$/.test(lower))errors.push('nama file harus berakhiran .jpg/.jpeg');
        try{
          const signature=await detectFileSignature(file);
          if(doc.format==='PDF'&&signature!=='PDF')errors.push('isi file bukan PDF asli');
          if(doc.format==='JPG'&&signature!=='JPG')errors.push('isi file bukan JPEG asli');
        }catch{
          errors.push('format internal file tidak dapat dibaca');
        }
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
        status.textContent=errors.length?'Periksa ulang: '+errors.join('; '):'Format asli/ukuran lolos pemeriksaan · '+(file.size/1024/1024).toFixed(2)+' MB';
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

function workplaceEvidenceMeta(check){
  const meta=workplaceRules?.evidenceTypes?.[check?.evidenceType]||{};
  return {
    label:meta.label||'Bukti belum diklasifikasikan',
    group:check?.coverageGroup||meta.group||'worker'
  };
}

function renderWorkplaceEvidencePolicy(){
  const box=$('workplaceEvidencePolicy');
  if(!box||!workplaceRules)return;
  const policy=workplaceRules.workerEvidencePolicy||{};
  const points=Array.isArray(policy.points)?policy.points:[];
  box.innerHTML=
    '<div class="workplace-policy-head"><span class="evidence-badge public">BISA DIMULAI TANPA TESTIMONI</span><strong>Mulai dari bukti publik dan SLC</strong></div>'+
    '<p>Nama perusahaan, alamat, kegiatan usaha, akses transportasi, dan fasilitas sekitar dapat diperiksa lebih dulu. Bukti pengalaman pekerja dipisahkan dan tidak boleh diasumsikan benar sebelum diverifikasi.</p>'+
    (points.length?'<details><summary>'+escapeHtml(policy.title||'Aturan bukti pekerja')+'</summary><ul>'+points.map(point=>'<li>'+escapeHtml(point)+'</li>').join('')+'</ul></details>':'');
}

function renderWorkplaceOfficialLookups(){
  const box=$('workplaceOfficialLookups');
  if(!box||!workplaceRules)return;
  const rows=Array.isArray(workplaceRules.officialLookups)?workplaceRules.officialLookups:[];
  if(!rows.length){box.hidden=true;box.innerHTML='';return}
  box.hidden=false;
  box.innerHTML='<div class="workplace-official-head"><strong>Pemeriksaan lewat sumber resmi Korea</strong><span>BUKTI TAMBAHAN</span></div>'+
    '<div class="workplace-official-grid">'+rows.map(item=>
      '<article>'+
        '<div class="workplace-check-meta"><span class="evidence-badge public">'+escapeHtml(item.access==='public'?'PUBLIK':'LOGIN RESMI')+'</span></div>'+
        '<strong>'+escapeHtml(item.title)+'</strong>'+
        '<small>'+escapeHtml(item.authority||'')+'</small>'+
        '<p>'+escapeHtml(item.use||'')+'</p>'+
        '<p class="lookup-caution">'+escapeHtml(item.caution||'')+'</p>'+
        '<a class="secondary link-button" href="'+escapeHtml(item.url)+'" target="_blank" rel="noopener">Buka sumber resmi ↗</a>'+
      '</article>'
    ).join('')+'</div>';
}

function normalizeWorkerEvidenceCompany(value){
  return String(value||'')
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[^a-z0-9가-힣\s]/g,' ')
    .replace(/\s+/g,' ')
    .trim();
}

function workerEvidenceForCompany(company){
  const target=normalizeWorkerEvidenceCompany(company);
  if(!target||!workplaceWorkerEvidence?.records?.length)return [];
  return workplaceWorkerEvidence.records.filter(row=>{
    const names=[row.companyName,...(row.companyAliases||[])];
    return names.some(name=>normalizeWorkerEvidenceCompany(name)===target);
  });
}

function renderWorkplaceWorkerEvidence(){
  const box=$('workplaceWorkerEvidence');
  if(!box)return;
  const company=$('wpCompany')?.value?.trim()||'';
  const policy=workplaceWorkerEvidence?.displayPolicy||{};
  if(!company){
    box.innerHTML='<div class="workplace-worker-head"><strong>Bukti pengalaman pekerja terverifikasi</strong><span>BETA</span></div><p>Masukkan nama perusahaan dari SLC untuk mencari bukti pengalaman pekerja yang sudah melalui verifikasi privasi.</p>';
    return;
  }

  const matches=workerEvidenceForCompany(company);
  if(!matches.length){
    box.innerHTML='<div class="workplace-worker-head"><strong>Bukti pengalaman pekerja terverifikasi</strong><span>BELUM ADA KECOCOKAN</span></div>'+
      '<p><strong>Belum ada bukti pekerja terverifikasi yang dipublikasikan untuk perusahaan ini.</strong></p>'+
      '<p>'+escapeHtml(policy.noEvidenceMeaning||'Tidak adanya data di sini bukan penilaian negatif terhadap perusahaan.')+'</p>';
    return;
  }

  box.innerHTML='<div class="workplace-worker-head"><strong>Bukti pengalaman pekerja terverifikasi</strong><span>'+matches.length+' CATATAN</span></div>'+
    matches.map(row=>{
      const facts=(row.facts||[]).map(fact=>
        '<li><strong>'+escapeHtml(fact.topic)+'</strong><span>'+escapeHtml(fact.summary)+'</span></li>'
      ).join('');
      const media=(row.media||[]).map(item=>
        '<a href="'+escapeHtml(item.url)+'" target="_blank" rel="noopener">Lihat '+escapeHtml(item.type)+' terverifikasi ↗</a>'
      ).join('');
      const verificationLabel={
        single_verified_worker:'1 pekerja terverifikasi',
        multi_verified_workers:'Beberapa pekerja terverifikasi',
        worker_plus_public_record:'Pekerja + sumber publik'
      }[row.verificationStatus]||'Terverifikasi';
      const experienceYear=String(row.experienceYear||'');
      const cycle=String(route?.cycle||'');
      const experienceLabel=experienceYear==='unknown'
        ?'Tahun pengalaman tidak pasti · retrospektif'
        :experienceYear===cycle
          ?'Pengalaman EPS '+experienceYear+' · siklus saat ini'
          :'Pengalaman EPS '+experienceYear+' · retrospektif';
      return '<article class="worker-evidence-card">'+
        '<div class="workplace-check-meta"><span class="evidence-badge worker">'+escapeHtml(verificationLabel)+'</span><span class="verify-state verified">Diverifikasi '+escapeHtml(row.verifiedAt||'')+'</span></div>'+
        '<strong>'+escapeHtml(row.companyName||company)+'</strong>'+
        '<small>'+escapeHtml(experienceLabel)+'</small>'+
        '<ul>'+facts+'</ul>'+
        (media?'<div class="worker-evidence-media">'+media+'</div>':'')+
        '<small>Ringkasan ini hanya berlaku pada pengalaman yang diverifikasi dan bukan jaminan kondisi semua pekerja.</small>'+
      '</article>';
    }).join('');
}

function renderWorkplace(){
  if(!workplaceRules)return;
  const saved=read(KEYS.workplace,{checks:[]});
  const contract=read(KEYS.contract,{});
  $('wpCompany').value=saved.company||contract.enterpriseName||'';
  $('wpAddress').value=saved.address||contract.workplace||contract.enterpriseLocation||'';
  $('wpDorm').value=saved.dorm||'';
  updateMapLinks();
  renderWorkplaceEvidencePolicy();
  renderWorkplaceOfficialLookups();
  renderWorkplaceWorkerEvidence();

  const selected=new Set(saved.checks||[]);
  const wrap=$('realityChecks');
  wrap.innerHTML='';
  workplaceRules.checks.forEach(check=>{
    const checked=selected.has(check.id);
    const meta=workplaceEvidenceMeta(check);
    const article=document.createElement('article');
    article.dataset.evidenceGroup=meta.group;
    article.innerHTML=`<input type="checkbox" ${checked?'checked':''} aria-label="${escapeHtml(check.title)}"><div><div class="workplace-check-meta"><span class="evidence-badge ${meta.group==='public'?'public':'worker'}">${escapeHtml(meta.label)}</span><span class="verify-state ${checked?'verified':'unverified'}">${checked?'Sudah diperiksa':'Belum diverifikasi'}</span></div><h3>${escapeHtml(check.title)}</h3><p>${escapeHtml(check.detail)}</p></div>`;
    const input=article.querySelector('input');
    const status=article.querySelector('.verify-state');
    input.addEventListener('change',()=>{
      saveWorkplace();
      status.textContent=input.checked?'Sudah diperiksa':'Belum diverifikasi';
      status.className='verify-state '+(input.checked?'verified':'unverified');
    });
    wrap.appendChild(article);
  });

  ['wpCompany','wpAddress','wpDorm'].forEach(id=>{
    const el=$(id);
    el.oninput=()=>{saveWorkplace();updateMapLinks();if(id==='wpCompany')renderWorkplaceWorkerEvidence()};
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
  const selected=new Set(state.checks||[]);
  const count=selected.size;
  const total=workplaceRules.checks.length;
  const pct=total?Math.round(count/total*100):0;
  $('coverageText').textContent=pct+'%';
  $('coverageBar').style.width=pct+'%';

  const publicChecks=workplaceRules.checks.filter(check=>workplaceEvidenceMeta(check).group==='public');
  const workerChecks=workplaceRules.checks.filter(check=>workplaceEvidenceMeta(check).group==='worker');
  const publicCount=publicChecks.filter(check=>selected.has(check.id)).length;
  const workerCount=workerChecks.filter(check=>selected.has(check.id)).length;
  const detail=$('workplaceCoverageDetail');
  if(detail){
    detail.innerHTML=
      '<span><strong>Bukti publik/kontrak:</strong> '+publicCount+'/'+publicChecks.length+'</span>'+
      '<span><strong>Bukti pengalaman pekerja:</strong> '+workerCount+'/'+workerChecks.length+'</span>'+
      (workerCount<workerChecks.length?'<small>Bagian pekerja yang belum ada bukti tetap ditandai belum diverifikasi; itu tidak menghapus hasil pemeriksaan publik.</small>':'');
  }
}

function buildScoutRequestBody(data,missing){
  return (
    'Halo Korea Employment Passport Beta,\n\n'+
    'Saya ingin meminta pemeriksaan lapangan / reality check untuk:\n'+
    'Perusahaan: '+(data.company||'-')+'\n'+
    'Alamat kerja: '+(data.address||'-')+'\n\n'+
    'Yang belum terverifikasi:\n'+(missing||'Semua checklist sudah ditandai.')+'\n\n'+
    'Catatan privasi: informasi/alamat asrama tidak disertakan dalam permintaan ini.\n'+
    'Saya memahami pemeriksaan harus dilakukan secara legal: tanpa masuk area privat tanpa izin, tanpa merekam rahasia dagang, dan tanpa mengirim dokumen pribadi sensitif.'
  );
}

$('requestScoutBtn').addEventListener('click',()=>{
  const data=saveWorkplace();
  if(!data.company&&!data.address)return;
  const checked=new Set(data.checks||[]);
  const missing=workplaceRules.checks.filter(c=>!checked.has(c.id)).map(c=>'• '+c.title).join('\n');
  const subject=encodeURIComponent('[KEP Beta] Workplace Reality Check request');
  const body=encodeURIComponent(buildScoutRequestBody(data,missing));
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

const BETA_FEEDBACK_REDACTION_RULES=[
  {label:'email',pattern:/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi},
  {label:'document_id',pattern:/\b[A-Z]{1,3}[-\s]?\d{6,12}\b/gi},
  {label:'phone',pattern:/(?<!\w)(?:\+?82|\+?62|0)[\s.-]?(?:\d[\s.-]?){8,13}(?!\w)/g},
  {label:'long_number',pattern:/\b\d[\d\s.-]{8,}\d\b/g}
];

function sanitizeBetaFeedback(text){
  let value=String(text||'');
  let redacted=false;
  BETA_FEEDBACK_REDACTION_RULES.forEach(rule=>{
    value=value.replace(rule.pattern,()=>{
      redacted=true;
      return '[DIHAPUS:'+rule.label+']';
    });
  });
  return {text:value,redacted};
}

function sanitizedBetaFeedbackText(rawBody){
  const safe=sanitizeBetaFeedback(rawBody);
  const notice=safe.redacted
    ?'Catatan privasi: pola yang tampak seperti email, nomor telepon, nomor dokumen, atau nomor panjang telah dihapus otomatis. Pemeriksaan otomatis tidak dapat menjamin nama, alamat, atau semua data pribadi terdeteksi; baca sekali lagi sebelum membagikan.\n\n'
    :'Catatan privasi: tidak ada pola nomor/email yang terdeteksi otomatis. Pemeriksaan otomatis tidak dapat menjamin nama, alamat, atau semua data pribadi terdeteksi; baca sekali lagi sebelum membagikan.\n\n';
  return notice+safe.text;
}

function encodeSanitizedBetaBody(rawBody){
  return encodeURIComponent(sanitizedBetaFeedbackText(rawBody));
}

async function copyTextSafely(text){
  if(navigator.clipboard?.writeText){
    try{
      await navigator.clipboard.writeText(text);
      return true;
    }catch{}
  }
  const area=document.createElement('textarea');
  area.value=text;
  area.setAttribute('readonly','');
  area.style.position='fixed';
  area.style.opacity='0';
  document.body.appendChild(area);
  area.select();
  let copied=false;
  try{copied=document.execCommand('copy')}catch{}
  area.remove();
  return copied;
}

function canonicalBetaTesterId(value){
  const normalized=String(value||'').trim().toUpperCase();
  const match=/^KEP-(\d{4})$/.exec(normalized);
  if(!match)return '';
  const number=Number(match[1]);
  return number>=1&&number<=50?normalized:'';
}

function betaTesterIdState(){
  return canonicalBetaTesterId(read(KEYS.betaTesterId,''));
}

function betaTesterRole(testerId=betaTesterIdState()){
  const match=/^KEP-(\d{4})$/.exec(String(testerId||''));
  if(!match)return '';
  const number=Number(match[1]);
  if(number>=1&&number<=30)return 'active_applicant';
  if(number>=31&&number<=50)return 'e9_worker_validator';
  return '';
}

function hydrateBetaTesterIdFromUrl(){
  const fromUrl=canonicalBetaTesterId(new URLSearchParams(location.search).get('beta'));
  if(fromUrl)write(KEYS.betaTesterId,fromUrl);
}

function renderBetaModeBanner(){
  const banner=$('betaModeBanner');
  if(!banner)return;
  const testerId=betaTesterIdState();
  if(!testerId){
    banner.hidden=true;
    banner.innerHTML='';
    return;
  }
  banner.hidden=false;
  const role=betaTesterRole(testerId);
  if(role==='e9_worker_validator'){
    banner.innerHTML=
      `<strong>Panel validator E-9 ${escapeHtml(testerId)}</strong>`+
      '<span><b>1</b> Pilih tahap yang benar-benar pernah Anda jalani</span>'+
      '<span><b>2</b> Bandingkan panduan dengan pengalaman nyata; jika tidak ingat, pilih “belum dijalani/tidak dapat dinilai”</span>'+
      '<span><b>3</b> Jangan masukkan nama, nomor identitas, telepon, email, atau alamat asrama pribadi</span>';
  }else{
    banner.innerHTML=
      `<strong>Mode beta ${escapeHtml(testerId)}</strong>`+
      '<span><b>1</b> Gunakan aplikasi seperti biasa pada tahap Anda</span>'+
      '<span><b>2</b> Nilai hanya tahap yang benar-benar Anda alami</span>'+
      '<span><b>3</b> Jangan masukkan nama, nomor identitas, telepon, atau email</span>';
  }
}

function betaChecksState(){
  const value=read(KEYS.betaChecks,{});
  return value&&typeof value==='object'&&!Array.isArray(value)?value:{};
}

function betaValidationStats(){
  const checks=betaChecksState();
  const rows=(route?.stages||[])
    .map(stage=>checks[stage.id]?{stage,...checks[stage.id]}:null)
    .filter(Boolean);
  const evaluatedRows=rows.filter(row=>['no_private_help','private_help_needed'].includes(row.status));
  const passed=evaluatedRows.filter(row=>row.status==='no_private_help').length;
  const failed=evaluatedRows.filter(row=>row.status==='private_help_needed').length;
  const notExperienced=rows.filter(row=>row.status==='not_experienced').length;
  const testerId=betaTesterIdState();
  const testerRole=betaTesterRole(testerId);
  const workerExperienceYear=testerRole==='e9_worker_validator'
    ?String(read(KEYS.betaWorkerExperienceYear,'')||'')
    :'';
  const currentCycle=String(route?.cycle||'');
  const currentRouteEligible=testerRole!=='e9_worker_validator'||workerExperienceYear===currentCycle;
  const checkpointComplete=Boolean(route?.stages?.length)&&evaluatedRows.length===route.stages.length&&failed===0;
  return {
    rows,
    evaluatedRows,
    recorded:rows.length,
    tested:evaluatedRows.length,
    passed,
    failed,
    notExperienced,
    total:(route?.stages||[]).length,
    testerRole,
    workerExperienceYear,
    currentCycle,
    currentRouteEligible,
    retrospectiveOnly:testerRole==='e9_worker_validator'&&!currentRouteEligible,
    checkpointComplete,
    routePass:checkpointComplete&&currentRouteEligible
  };
}

function renderBetaValidation(){
  const select=$('betaCheckStage');
  const summary=$('betaValidationSummary');
  const list=$('betaValidationList');
  const testerInput=$('betaTesterId');
  const testerStatus=$('betaTesterIdStatus');
  if(!select||!summary||!list||!route)return;
  const testerId=betaTesterIdState();
  const role=betaTesterRole(testerId);
  if(testerInput)testerInput.value=testerId;
  const workerYearWrap=$('betaWorkerExperienceWrap');
  const workerYearSelect=$('betaWorkerExperienceYear');
  const workerYearStatus=$('betaWorkerExperienceStatus');
  if(workerYearWrap&&workerYearSelect){
    const isWorker=role==='e9_worker_validator';
    workerYearWrap.hidden=!isWorker;
    if(isWorker){
      const options=Array.from({length:23},(_,index)=>String(2026-index));
      workerYearSelect.innerHTML='<option value="">Pilih tahun pengalaman</option>'+
        options.map(year=>'<option value="'+year+'">'+year+'</option>').join('')+
        '<option value="unknown">Tidak ingat pasti</option>';
      const savedYear=String(read(KEYS.betaWorkerExperienceYear,'')||'');
      workerYearSelect.value=options.includes(savedYear)||savedYear==='unknown'?savedYear:'';
      if(workerYearStatus){
        workerYearStatus.textContent=workerYearSelect.value
          ?'Tahun pengalaman tersimpan untuk ID beta ini.'
          :'Pilih tahun pengalaman sebelum menyimpan penilaian tahap.';
      }
    }
  }
  if(testerStatus){
    testerStatus.textContent=testerId
      ?role==='e9_worker_validator'
        ?`ID validator E-9 tersimpan: ${testerId}. Nilai hanya pengalaman yang benar-benar Anda ingat; kode ini bukan identitas pribadi.`
        :`ID beta tersimpan: ${testerId}. Kode ini bukan nama atau nomor identitas.`
      :'Gunakan hanya kode KEP yang diberikan tim beta. Jangan masukkan nama, email, atau nomor telepon.';
  }
  const previous=select.value;
  select.innerHTML='';
  route.stages.forEach(stage=>{
    const option=document.createElement('option');
    option.value=stage.id;
    option.textContent=stageTitle(stage);
    select.appendChild(option);
  });
  const preferred=previous||currentStage()?.id||route.stages[0]?.id;
  if(preferred&&route.stages.some(stage=>stage.id===preferred))select.value=preferred;

  const stats=betaValidationStats();
  summary.hidden=false;
  summary.className='result '+(stats.failed?'warn':stats.routePass?'safe':'');
  const retrospectiveNote=stats.retrospectiveOnly
    ?`<br><strong>Validasi retrospektif ${escapeHtml(stats.workerExperienceYear==='unknown'?'tahun tidak pasti':stats.workerExperienceYear)}:</strong> hasil ini dipakai untuk menemukan perbedaan/celah pengalaman, bukan sebagai bukti PASS rute ${escapeHtml(stats.currentCycle)}.`
    :'';
  summary.innerHTML=`<strong>Checkpoint beta: ${stats.tested}/${stats.total} tahap benar-benar dinilai.</strong><br>`+
    `Tanpa bantuan swasta: ${stats.passed} · Masih butuh bantuan swasta: ${stats.failed} · Belum dijalani/tidak dapat dinilai: ${stats.notExperienced}. `+
    (stats.routePass
      ?'<strong>Checkpoint perangkat ini lengkap: 27/27 tanpa bantuan swasta.</strong> Ini bukti beta perangkat ini, bukan PASS final produk.'
      :stats.retrospectiveOnly&&stats.checkpointComplete
        ?`Checkpoint pengalaman ini lengkap tanpa bantuan swasta, tetapi tidak dihitung sebagai PASS rute ${escapeHtml(stats.currentCycle)} karena tahun pengalaman berbeda/tidak pasti.`
        :stats.failed
          ?'Rute belum PASS. Catat tugas yang masih membutuhkan bantuan pada Celah Calo di bawah.'
          :'Belum cukup untuk menyatakan rute PASS; hanya tahap yang benar-benar dijalani boleh dihitung sebagai bukti.')+
    retrospectiveNote;

  list.innerHTML='';
  stats.rows.forEach(row=>{
    const article=document.createElement('article');
    article.className='gap-item';
    const outcome=row.status==='no_private_help'
      ?'✓ Selesai tanpa bantuan swasta'
      :row.status==='private_help_needed'
        ?'⚠ Masih membutuhkan bantuan swasta'
        :'— Belum menjalani / tidak bisa menilai';
    article.innerHTML=`<h3>${escapeHtml(stageTitle(row.stage))}</h3><p>${outcome}</p>`;
    list.appendChild(article);
  });
}

$('saveBetaTesterIdBtn').addEventListener('click',()=>{
  const input=$('betaTesterId');
  const status=$('betaTesterIdStatus');
  const raw=String(input?.value||'').trim();
  if(!raw){
    localStorage.removeItem(KEYS.betaTesterId);
    renderBetaModeBanner();
    renderBetaValidation();
    renderRejections();
    renderGaps();
    renderUnresolvedFieldQuestions();
    return;
  }
  const testerId=canonicalBetaTesterId(raw);
  if(!testerId){
    if(status)status.textContent='ID beta tidak valid. Gunakan kode KEP-0001 sampai KEP-0050.';
    return;
  }
  write(KEYS.betaTesterId,testerId);
  renderBetaModeBanner();
  renderBetaValidation();
  renderRejections();
  renderGaps();
  renderUnresolvedFieldQuestions();
});

$('betaWorkerExperienceYear').addEventListener('change',()=>{
  const value=String($('betaWorkerExperienceYear').value||'');
  const allowed=value==='unknown'||/^(?:200[4-9]|201\d|202[0-6])$/.test(value);
  if(!allowed&&value!=='')return;
  write(KEYS.betaWorkerExperienceYear,value);
  const status=$('betaWorkerExperienceStatus');
  if(status)status.textContent=value
    ?'Tahun pengalaman tersimpan untuk ID beta ini.'
    :'Pilih tahun pengalaman sebelum menyimpan penilaian tahap.';
});

$('saveBetaCheckBtn').addEventListener('click',()=>{
  const stageId=$('betaCheckStage').value;
  const status=$('betaCheckOutcome').value;
  if(!stageId||!['no_private_help','private_help_needed','not_experienced'].includes(status))return;
  if(betaTesterRole()==='e9_worker_validator'&&!String(read(KEYS.betaWorkerExperienceYear,'')||'')){
    const yearStatus=$('betaWorkerExperienceStatus');
    if(yearStatus)yearStatus.textContent='Pilih tahun pengalaman (atau “Tidak ingat pasti”) sebelum menyimpan hasil tahap.';
    return;
  }
  const checks=betaChecksState();
  checks[stageId]={stageId,status,updatedAt:new Date().toISOString()};
  write(KEYS.betaChecks,checks);
  renderBetaValidation();
  if(status==='private_help_needed'&&$('gapStage'))$('gapStage').value=stageId;
});

function buildBetaFeedbackBundle(){
  const fieldQuestions=read(KEYS.fieldQuestions,[]);
  const rejections=read(KEYS.rejections,[]);
  const gaps=read(KEYS.gaps,[]);
  const sections=[];

  if(fieldQuestions.length){
    sections.push(
      'PERTANYAAN YANG BELUM TERVERIFIKASI\n'+
      fieldQuestions.map((item,index)=>`${index+1}. [${item.stageTitle||item.stageId}] ${item.question}`).join('\n')
    );
  }
  if(rejections.length){
    sections.push(
      'KASUS PENOLAKAN\n'+
      rejections.map((item,index)=>
        `${index+1}. [${item.stageTitle||item.stageId}] ${item.field||'kolom/dokumen'}\n`+
        `   Penolakan: ${item.reason}\n`+
        `   Perbaikan: ${item.fix||'belum diketahui'}`
      ).join('\n')
    );
  }
  if(gaps.length){
    sections.push(
      'CELAH CALO / PERANTARA\n'+
      gaps.map((item,index)=>{
        const stage=route?.stages.find(row=>row.id===item.stage);
        return `${index+1}. [${stage?stageTitle(stage):item.stage}] ${item.task} — ${item.helper}`;
      }).join('\n')
    );
  }

  const betaStats=betaValidationStats();
  if(betaStats.recorded){
    sections.unshift(
      'CHECKPOINT ZERO-BROKER\n'+
      `Tahap benar-benar dinilai: ${betaStats.tested}/${betaStats.total}; tanpa bantuan swasta: ${betaStats.passed}; masih butuh bantuan swasta: ${betaStats.failed}; belum dijalani/tidak dapat dinilai: ${betaStats.notExperienced}; checkpoint lengkap tanpa bantuan swasta: ${betaStats.routePass?'YA':'BELUM'}; eligible bukti rute ${betaStats.currentCycle}: ${betaStats.currentRouteEligible?'YA':'TIDAK (retrospektif)'}\n`+
      betaStats.rows.map((row,index)=>{
        const statusText=row.status==='no_private_help'
          ?'PASS tanpa bantuan swasta'
          :row.status==='private_help_needed'
            ?'FAIL masih membutuhkan bantuan swasta'
            :'BELUM DIJALANI / TIDAK DINILAI';
        return `${index+1}. [${stageTitle(row.stage)}] ${statusText}`;
      }).join('\n')
    );
  }

  const findingCount=fieldQuestions.length+rejections.length+gaps.length;
  const checkpointCount=betaStats.recorded;
  const count=findingCount+checkpointCount;
  const done=read(KEYS.done,[]);
  const current=currentStage();
  const testerId=betaTesterIdState();
  const testerRole=betaTesterRole(testerId);
  const workerExperienceYear=testerRole==='e9_worker_validator'
    ?String(read(KEYS.betaWorkerExperienceYear,'')||'')
    :'';
  const routeLabel=route?[route.country,route.visa,route.sector,route.cycle].filter(Boolean).join(' → '):'route belum dimuat';
  const sessionSummary=[
    'RINGKASAN SESI — PERIKSA & HAPUS IDENTITAS SEBELUM KIRIM',
    ...(testerId?['ID beta anonim: '+testerId]:[]),
    ...(testerId?['Peran beta: '+(testerRole==='e9_worker_validator'?'validator E-9 retrospektif':'pelamar aktif')]:[]),
    ...(testerRole==='e9_worker_validator'?['Tahun pengalaman/proses EPS: '+(workerExperienceYear||'belum dicatat')]:[]),
    'Rute: '+routeLabel,
    'Tahap sekarang: '+(current?stageTitle(current):'semua tahap selesai'),
    'Tahap selesai: '+done.length+'/'+(route?.stages?.length||0),
    'Temuan: '+fieldQuestions.length+' pertanyaan, '+rejections.length+' penolakan, '+gaps.length+' Celah Calo',
    'Checkpoint zero-broker: '+betaStats.tested+'/'+betaStats.total+' benar-benar dinilai; '+betaStats.passed+' PASS; '+betaStats.failed+' FAIL; '+betaStats.notExperienced+' belum dijalani/tidak dinilai'
  ].join('\n');
  return {
    count,
    findingCount,
    checkpointCount,
    testerId,
    rawBody:
      'Temuan beta Korea Employment Passport dari perangkat ini:\n\n'+
      sessionSummary+'\n\n'+
      sections.join('\n\n')+
      '\n\nMohon verifikasi terhadap sumber resmi sebelum mengubah aturan. Jangan lampirkan dokumen atau nomor identitas sensitif.'
  };
}

function betaFeedbackBundleMailto(bundle=buildBetaFeedbackBundle()){
  const testerPrefix=bundle.testerId?`[${bundle.testerId}] `:'';
  const subject=encodeURIComponent(`${testerPrefix}[KEP Beta] Combined feedback — ${bundle.findingCount} temuan, ${bundle.checkpointCount} checkpoint`);
  const body=encodeSanitizedBetaBody(bundle.rawBody);
  return 'mailto:modernsnc2022@gmail.com?subject='+subject+'&body='+body;
}

function betaFeedbackBundleOrWarn(){
  const out=$('betaFeedbackBundleResult');
  const bundle=buildBetaFeedbackBundle();
  if(!bundle.count){
    out.hidden=false;
    out.className='result warn';
    out.textContent='Belum ada checkpoint beta, pertanyaan, kasus penolakan, atau Celah Calo yang tersimpan di perangkat ini.';
    return null;
  }
  return {out,bundle};
}

$('copyAllBetaFeedbackBtn').addEventListener('click',async()=>{
  const state=betaFeedbackBundleOrWarn();
  if(!state)return;
  const copied=await copyTextSafely(sanitizedBetaFeedbackText(state.bundle.rawBody));
  state.out.hidden=false;
  state.out.className='result '+(copied?'safe':'warn');
  state.out.textContent=copied
    ?'Laporan beta anonim sudah disalin. Tempelkan ke WhatsApp, Telegram, atau kanal beta yang disepakati.'
    :'Browser tidak mengizinkan salin otomatis. Gunakan tombol email atau izinkan akses clipboard lalu coba lagi.';
});

$('emailAllBetaFeedbackBtn').addEventListener('click',()=>{
  const state=betaFeedbackBundleOrWarn();
  if(!state)return;
  state.out.hidden=true;
  location.href=betaFeedbackBundleMailto(state.bundle);
});

$('emailFieldQuestionsBtn').addEventListener('click',()=>{
  const list=read(KEYS.fieldQuestions,[]);
  if(!list.length)return;
  const lines=list.map((item,index)=>`${index+1}. [${item.stageTitle||item.stageId}] ${item.question}`).join('\n');
  const subject=encodeURIComponent('[KEP Beta] Exact field questions needing verification');
  const body=encodeSanitizedBetaBody(
    'Pertanyaan field yang belum punya jawaban terverifikasi:\n\n'+
    lines+
    '\n\nMohon verifikasi berdasarkan form/pengumuman resmi yang sesuai. Jangan jawab berdasarkan tebakan atau sektor/siklus lain.'
  );
  location.href='mailto:modernsnc2022@gmail.com?subject='+subject+'&body='+body;
});

function renderRejectionStage(){
  const select=$('rejectStage');
  if(!select||!route)return;
  select.innerHTML='';
  route.stages.forEach(stage=>{
    const option=document.createElement('option');
    option.value=stage.id;
    option.textContent=stageTitle(stage);
    select.appendChild(option);
  });
  const current=currentStage();
  if(current)select.value=current.id;
}

function renderRejections(){
  const wrap=$('rejectList');
  if(!wrap)return;
  const items=read(KEYS.rejections,[]);
  wrap.innerHTML='';
  if(!items.length){
    wrap.innerHTML='<div class="gap-item"><p>Belum ada kasus penolakan yang disimpan.</p></div>';
    return;
  }
  items.forEach(item=>{
    const article=document.createElement('article');
    article.className='gap-item';
    article.innerHTML=`
      <h3>${escapeHtml(item.field||'Alasan penolakan')}</h3>
      <p><strong>Tahap:</strong> ${escapeHtml(item.stageTitle||item.stageId)}</p>
      <p><strong>Penolakan:</strong> ${escapeHtml(item.reason)}</p>
      ${item.fix?'<p><strong>Perbaikan:</strong> '+escapeHtml(item.fix)+'</p>':''}
      <div class="gap-actions"><button type="button">Hapus</button></div>`;
    article.querySelector('button').addEventListener('click',()=>{
      write(KEYS.rejections,read(KEYS.rejections,[]).filter(row=>row.id!==item.id));
      renderRejections();
    });
    wrap.appendChild(article);
  });
}

$('saveRejectBtn').addEventListener('click',()=>{
  const stageId=$('rejectStage').value;
  const stage=route?.stages.find(item=>item.id===stageId);
  const field=$('rejectField').value.trim();
  const reason=$('rejectReason').value.trim();
  const fix=$('rejectFix').value.trim();
  const out=$('rejectSuggest');
  if(!stageId||!reason){
    out.hidden=false;
    out.className='result warn';
    out.textContent='Pilih tahap dan masukkan alasan penolakan.';
    return;
  }

  const items=read(KEYS.rejections,[]);
  const id=Date.now();
  items.unshift({
    id,stageId,stageTitle:stage?stageTitle(stage):stageId,
    field,reason,fix,createdAt:new Date().toISOString()
  });
  write(KEYS.rejections,items);
  renderRejections();

  const query=[field,reason].filter(Boolean).join(' ');
  const matches=findExactFieldAnswers(query);
  out.hidden=false;
  if(matches.length){
    out.className='result safe';
    out.innerHTML='<strong>Ada aturan yang mungkin sudah relevan.</strong><div class="field-match-list">'+matches.slice(0,3).map(fieldAnswerHtml).join('')+'</div>';
  }else{
    out.className='result warn';
    out.innerHTML='<strong>Belum ada aturan pasti yang cocok.</strong><p>Kasus ini ditandai sebagai celah baru. Jangan mengulangi submit dengan tebakan yang sama sampai penyebabnya diverifikasi.</p>';
    const question='Kasus penolakan — '+(field||'kolom/dokumen')+': '+reason;
    const currentBefore=currentStage();
    if(stage){
      const list=read(KEYS.fieldQuestions,[]);
      const key=normalizeSearch(question)+'|'+stage.id;
      if(!list.some(row=>row.key===key)){
        list.unshift({
          key,question,stageId:stage.id,stageTitle:stageTitle(stage),
          createdAt:new Date().toISOString(),
          status:'needs_official_verification',
          origin:'rejection_lab'
        });
        write(KEYS.fieldQuestions,list);
        renderUnresolvedFieldQuestions();
        renderBqcStatus();
        if(activeStage?.id===stage.id)renderStageBqc(activeStage);
      }
    }
  }

  $('rejectField').value='';
  $('rejectReason').value='';
  $('rejectFix').value='';
});

$('emailRejectsBtn').addEventListener('click',()=>{
  const items=read(KEYS.rejections,[]);
  if(!items.length)return;
  const bodyLines=items.map((item,index)=>
    (index+1)+'. ['+(item.stageTitle||item.stageId)+']\n'+
    'Field/Document: '+(item.field||'-')+'\n'+
    'Rejection: '+item.reason+'\n'+
    'Fix: '+(item.fix||'belum diketahui')
  ).join('\n\n');
  const subject=encodeURIComponent('[KEP Beta] Rejection cases for rule update');
  const body=encodeSanitizedBetaBody(
    'Kasus penolakan untuk diverifikasi dan dijadikan aturan pencegahan:\n\n'+
    bodyLines+
    '\n\nData sensitif (nomor paspor/KTP/ARC) tidak boleh disertakan.'
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
  const body=encodeSanitizedBetaBody('Broker Gaps from my device:\n\n'+lines+'\n\nNo sensitive document is attached.');
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
  const allJourney=$('allJourneyDetails');
  if(allJourney)allJourney.open=true;
  const current=currentStage();
  const phase=phaseForStage(current?.id||route?.stages?.[0]?.id);
  document.querySelector('[data-phase-group="'+phase.id+'"]')?.scrollIntoView({behavior:'smooth',block:'start'});
}));

window.addEventListener('beforeinstallprompt',(e)=>{e.preventDefault();deferredInstall=e;$('installBtn').hidden=false});
$('installBtn').addEventListener('click',async()=>{if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;$('installBtn').hidden=true});
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(console.error));

boot();