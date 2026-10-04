const PROGRAM_URL='data/beta_program_v1.json';
const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
let betaProgram=null,betaRoute=null,betaI18n={};

const $=(id)=>document.getElementById(id);
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

const STAGE_GROUPS=[
  {label:'Persiapan & pendaftaran',ids:['eligibility','registration','exam_fee','biometric','document_verify','exam_card']},
  {label:'Ujian & seleksi',ids:['eps_topik','skill_competency','final_selection','psychology_pre_job','mcu1']},
  {label:'Lamaran kerja & kontrak',ids:['job_application','roster','employer_selection','slc','post_slc_requirements']},
  {label:'Visa & keberangkatan',ids:['visa_docs','predeparture_training','mcu3_departure','departure']},
  {label:'Setelah tiba di Korea',ids:['korea_entry_training','employer_handover','residence_registration','eps_insurance_check','first_payroll_check','labor_support_ready','employment_maintenance']}
];

function renderApplicantStageOptions(){
  const select=$('applicantStage');
  if(!select||!betaRoute)return;
  const byId=Object.fromEntries((betaRoute.stages||[]).map(stage=>[stage.id,stage]));
  select.innerHTML='<option value="">Pilih tahap resmi saat ini</option>';
  STAGE_GROUPS.forEach(group=>{
    const optgroup=document.createElement('optgroup');
    optgroup.label=group.label;
    group.ids.forEach(id=>{
      const stage=byId[id];
      if(!stage)return;
      const option=document.createElement('option');
      option.value=id;
      option.textContent=betaI18n[id]?.title||stage.title||id;
      optgroup.appendChild(option);
    });
    select.appendChild(optgroup);
  });
}

function selectedApplicantStageTitle(){
  const select=$('applicantStage');
  return select?.selectedOptions?.[0]?.textContent?.trim()||'';
}

function workerValidatorText(){
  return [
    'KOREA EMPLOYMENT PASSPORT — E-9 WORKER VALIDATOR',
    '',
    'Currently working in Korea with E-9: YES',
    'Completed Indonesia G-to-G Korea / EPS process: YES',
    'Experience-validation participation agreement: YES',
    '',
    'I am interested in joining the separate 20-person retrospective validation panel.',
    'I will compare app guidance with my real process experience and report mismatches.',
    'I will not send passport/KTP/ARC images, identity numbers, exact home/dorm addresses, or other sensitive identity documents.'
  ].join('\n');
}

function workerPanelOpen(){
  return betaProgram?.retrospectivePanel?.status==='open';
}

function applicationText(){
  const stage=$('applicantStage').value;
  const stageTitle=selectedApplicantStageTitle();
  return [
    'KOREA EMPLOYMENT PASSPORT — BETA APPLICATION',
    '',
    'Current route stage ID: '+stage,
    'Current stage title: '+stageTitle,
    'Official G-to-G / EPS E-9 process: YES',
    'Feedback participation agreement: YES',
    '',
    'I am applying for the limited public beta.',
    'I understand that beta access does not guarantee a job, employer selection, SLC, visa, or departure.',
    'I will not attach passport/KTP/ARC images or sensitive identity numbers.',
    '',
    'Queue order should use the received timestamp of this application email.'
  ].join('\n');
}

async function copyText(text){
  if(navigator.clipboard?.writeText){
    try{await navigator.clipboard.writeText(text);return true}catch{}
  }
  const area=document.createElement('textarea');
  area.value=text;area.setAttribute('readonly','');area.style.position='fixed';area.style.opacity='0';
  document.body.appendChild(area);area.select();
  let ok=false;try{ok=document.execCommand('copy')}catch{}
  area.remove();return ok;
}

function renderProgram(program){
  betaProgram=program;
  const beta=program.publicBeta||{};
  $('eligibilityList').innerHTML=(beta.eligibility||[]).map(x=>'<li>'+escapeHtml(x)+'</li>').join('');
  $('feedbackList').innerHTML=(beta.feedback||[]).map(x=>'<li>'+escapeHtml(x)+'</li>').join('');
  $('noGuaranteeList').innerHTML=(beta.noGuarantee||[]).map(x=>'<span>'+escapeHtml(x)+'</span>').join('');

  const open=program.status==='open';
  $('closedPanel').hidden=open;
  $('applicationPanel').hidden=!open;
  const workerOpen=program.retrospectivePanel?.status==='open';
  $('workerPanelClosed').hidden=workerOpen;
  $('workerValidatorForm').hidden=!workerOpen;
  const pill=$('betaStatusPill');
  pill.textContent=open?'OPEN · '+beta.slots+' PESERTA':'BELUM DIBUKA';
  pill.className='status-pill '+(open?'open':'hold');
}

$('betaApplicationForm').addEventListener('submit',(event)=>{
  event.preventDefault();
  const out=$('applicationResult');
  if(!betaProgram||betaProgram.status!=='open'){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran beta belum dibuka.';return;
  }
  if(!$('activeProcess').checked||!$('feedbackAgreement').checked||!$('applicantStage').value){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi tahap dan kedua persetujuan terlebih dahulu.';return;
  }
  const email=betaProgram.application?.email||'modernsnc2022@gmail.com';
  const subject=encodeURIComponent('[KEP Beta Application] Active EPS applicant');
  const body=encodeURIComponent(applicationText());
  location.href='mailto:'+encodeURIComponent(email)+'?subject='+subject+'&body='+body;
});

$('workerValidatorForm').addEventListener('submit',(event)=>{
  event.preventDefault();
  const out=$('workerValidatorResult');
  if(!workerPanelOpen()){
    out.hidden=false;out.className='result warn';out.textContent='Panel validator E-9 belum dibuka.';return;
  }
  if(!$('workerInKorea').checked||!$('workerUsedG2G').checked||!$('workerFeedbackAgreement').checked){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi ketiga konfirmasi terlebih dahulu.';return;
  }
  const email=betaProgram.retrospectivePanel?.application?.email||'modernsnc2022@gmail.com';
  const subject=encodeURIComponent('[KEP E-9 Worker Validator] Retrospective panel');
  const body=encodeURIComponent(workerValidatorText());
  location.href='mailto:'+encodeURIComponent(email)+'?subject='+subject+'&body='+body;
});

$('copyWorkerValidatorBtn').addEventListener('click',async()=>{
  const out=$('workerValidatorResult');
  if(!workerPanelOpen()){
    out.hidden=false;out.className='result warn';out.textContent='Panel validator E-9 belum dibuka.';return;
  }
  if(!$('workerInKorea').checked||!$('workerUsedG2G').checked||!$('workerFeedbackAgreement').checked){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi ketiga konfirmasi terlebih dahulu.';return;
  }
  const ok=await copyText(workerValidatorText());
  out.hidden=false;out.className='result'+(ok?'':' warn');
  out.textContent=ok
    ?'Teks minat validator sudah disalin. Kirim ke '+(betaProgram.retrospectivePanel?.application?.email||'modernsnc2022@gmail.com')+'.'
    :'Browser tidak mengizinkan salin otomatis. Gunakan tombol email.';
});

$('copyApplicationBtn').addEventListener('click',async()=>{
  const out=$('applicationResult');
  if(!betaProgram||betaProgram.status!=='open'){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran beta belum dibuka.';return;
  }
  if(!$('activeProcess').checked||!$('feedbackAgreement').checked||!$('applicantStage').value){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi tahap dan kedua persetujuan terlebih dahulu.';return;
  }
  const ok=await copyText(applicationText());
  out.hidden=false;out.className='result'+(ok?'':' warn');
  out.textContent=ok
    ?'Teks aplikasi sudah disalin. Kirim ke '+(betaProgram.application?.email||'modernsnc2022@gmail.com')+'.'
    :'Browser tidak mengizinkan salin otomatis. Gunakan tombol email.';
});

Promise.all([
  fetch(PROGRAM_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('program HTTP '+response.status);return response.json()}),
  fetch(ROUTE_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('route HTTP '+response.status);return response.json()}),
  fetch(I18N_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('i18n HTTP '+response.status);return response.json()})
])
  .then(([program,route,i18n])=>{
    betaRoute=route;
    betaI18n=i18n||{};
    renderApplicantStageOptions();
    renderProgram(program);
  })
  .catch(()=>{
    $('betaStatusPill').textContent='STATUS TIDAK TERSEDIA';
    $('betaStatusPill').className='status-pill hold';
    $('closedPanel').hidden=false;
    $('applicationPanel').hidden=true;
    $('closedPanel').querySelector('p').textContent='Status beta tidak dapat diverifikasi. Jangan mengirim aplikasi sampai halaman ini kembali normal.';
  });
