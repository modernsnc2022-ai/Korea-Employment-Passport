const PROGRAM_URL='data/beta_program_v1.json';
const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
const RECRUITMENT_SOURCES_URL='data/beta_recruitment_sources_v1.json';
let betaProgram=null,betaRoute=null,betaI18n={};
let betaRecruitmentSourceCodes=new Set(['website']);
let betaRecruitmentDefaultCode='website';

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

function recruitmentSourceCode(){
  const raw=String(new URLSearchParams(location.search).get('src')||'website').trim().toLowerCase();
  return betaRecruitmentSourceCodes.has(raw)?raw:betaRecruitmentDefaultCode;
}

function selectedApplicantStageTitle(){
  const select=$('applicantStage');
  return select?.selectedOptions?.[0]?.textContent?.trim()||'';
}

function renderApplicantCycleOptions(){
  const select=$('applicantCycle');
  if(!select||!betaRoute)return;
  const cycle=Number(betaRoute.cycle)||2026;
  const years=[cycle,cycle-1,cycle-2];
  select.innerHTML='<option value="">Pilih tahun proses EPS</option>';
  years.forEach(year=>{
    const option=document.createElement('option');
    option.value=String(year);
    option.textContent=String(year);
    select.appendChild(option);
  });
  const unknown=document.createElement('option');
  unknown.value='unknown';
  unknown.textContent='Tidak yakin';
  select.appendChild(unknown);
}

function workerValidatorText(){
  return [
    'KOREA EMPLOYMENT PASSPORT — E-9 WORKER VALIDATOR INTEREST',
    '',
    'Recruitment source code: '+recruitmentSourceCode(),
    'Currently working in Korea with E-9: YES',
    'Completed Indonesia G-to-G Korea / EPS process: YES',
    'Experience-validation participation agreement: YES',
    '',
    'I am registering my interest in the separate 20-person retrospective validation panel.',
    'I understand that sending this interest does not activate worker-panel access yet.',
    'I will compare app guidance with my real process experience and report mismatches after approval.',
    'I will not send passport/KTP/ARC images, identity numbers, exact home/dorm addresses, or other sensitive identity documents.'
  ].join('\n');
}

function workerInterestOpen(){
  return betaProgram?.retrospectivePanel?.intakeStatus==='open';
}

function workerPanelOpen(){
  const release=betaProgram?.releaseDecision||{};
  return betaProgram?.retrospectivePanel?.status==='open'
    && release.retrospectivePanel==='approved_manual'
    && Boolean(String(release.retrospectiveApprovedAt||'').trim());
}

function gmailComposeUrl(to,subject,body){
  const params=new URLSearchParams({
    view:'cm',
    fs:'1',
    to:String(to||''),
    su:String(subject||''),
    body:String(body||'')
  });
  return 'https://mail.google.com/mail/?'+params.toString();
}

function directIntakeEndpoint(){
  return String(betaProgram?.application?.directIntake?.endpoint||'').trim();
}

function directIntakeEnabled(){
  const endpoint=directIntakeEndpoint();
  if(!endpoint)return false;
  try{return new URL(endpoint).protocol==='https:'}catch{return false}
}

function applicantFormComplete(){
  return Boolean($('activeProcess').checked&&$('feedbackAgreement').checked&&$('applicantStage').value&&$('applicantCycle').value);
}

function validContactEmail(value){
  const email=String(value||'').trim();
  return email.length<=254&&/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
}

function directApplicantPayload(){
  return {
    kind:'active_applicant',
    contactEmail:String($('applicantContactEmail').value||'').trim(),
    stageId:$('applicantStage').value,
    stageTitle:selectedApplicantStageTitle(),
    cycle:$('applicantCycle').value,
    sourceCode:recruitmentSourceCode(),
    activeProcess:$('activeProcess').checked===true,
    feedbackAgreement:$('feedbackAgreement').checked===true,
    website:String($('intakeWebsite').value||'')
  };
}

async function submitDirectApplicant(){
  const response=await fetch(directIntakeEndpoint(),{
    method:'POST',
    mode:'cors',
    credentials:'omit',
    cache:'no-store',
    headers:{'Content-Type':'application/json','Accept':'application/json'},
    body:JSON.stringify(directApplicantPayload())
  });
  let payload={};
  try{payload=await response.json()}catch{}
  if(!response.ok)throw new Error(String(payload?.error||'HTTP '+response.status));
  return payload;
}

function applicationText(){
  const stage=$('applicantStage').value;
  const stageTitle=selectedApplicantStageTitle();
  const cycle=$('applicantCycle').value;
  return [
    'KOREA EMPLOYMENT PASSPORT — TESTER INTEREST',
    '',
    'Current route stage ID: '+stage,
    'Current stage title: '+stageTitle,
    'EPS process cycle: '+cycle,
    'Recruitment source code: '+recruitmentSourceCode(),
    'Official G-to-G / EPS E-9 process: YES',
    'Feedback participation agreement: YES',
    '',
    'I am registering my interest as a beta tester.',
    'I understand that sending this application does not activate beta access yet.',
    'I understand that the initial validation target is around 30 testers, not an automatic rejection cap.',
    'I understand that beta access does not guarantee a job, employer selection, SLC, visa, or departure.',
    'I will not attach passport/KTP/ARC images or sensitive identity numbers.',
    '',
    'The team may review and approve eligible testers after seeing the application volume.'
  ].join('\n');
}

function sourceAttributedBetaUrl(worker=false){
  const url=new URL('beta.html',location.href);
  url.searchParams.set('src',recruitmentSourceCode());
  url.hash=worker?'worker-panel':'';
  return url.toString();
}

function communityApplicantInviteText(){
  return [
    'Korea Employment Passport (KEP) membuka pendaftaran minat beta gratis untuk WNI yang benar-benar sedang menjalani proses resmi G-to-G Korea / EPS E-9.',
    '',
    'Target validasi awal sekitar 30 pelamar aktif. Peserta yang disetujui mendapat akses gratis 6 bulan sejak akun beta diaktifkan dan diminta memberi feedback dari proses nyata.',
    '',
    'KEP adalah proyek independen, bukan layanan pemerintah atau agen penempatan. Tidak ada jaminan kelulusan, pekerjaan, employer selection, SLC, visa, atau keberangkatan.',
    '',
    'Daftar minat:',
    sourceAttributedBetaUrl(false)
  ].join('\n');
}

function communityWorkerInviteText(){
  return [
    'Korea Employment Passport (KEP) membuka pendaftaran minat untuk panel validasi sekitar 20 pekerja Indonesia yang saat ini bekerja di Korea dengan status E-9 dan sebelumnya melalui Indonesia G-to-G Korea / EPS.',
    '',
    'Mengirim minat belum mengaktifkan akses panel. Peserta akan direview terlebih dahulu. Pendaftaran awal tidak meminta foto paspor/KTP/ARC, nomor identitas, nomor telepon, atau alamat rumah/asrama.',
    '',
    'KEP adalah proyek independen dan tidak menjanjikan pekerjaan, SLC, visa, atau keberangkatan.',
    '',
    'Daftar minat panel pekerja E-9:',
    sourceAttributedBetaUrl(true)
  ].join('\n');
}

async function shareText(text){
  if(navigator.share){
    try{
      await navigator.share({text});
      return {ok:true,mode:'share'};
    }catch(error){
      if(error?.name==='AbortError')return {ok:false,mode:'cancel'};
    }
  }
  const ok=await copyText(text);
  return {ok,mode:'copy'};
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

  const release=program.releaseDecision||{};
  const accessOpen=program.status==='open'
    && release.publicBeta==='approved_manual'
    && Boolean(String(release.approvedAt||'').trim());
  const intakeOpen=program.application?.intakeStatus==='open';
  $('closedPanel').hidden=accessOpen;
  $('applicationPanel').hidden=!intakeOpen;
  const workerOpen=program.retrospectivePanel?.status==='open'
    && release.retrospectivePanel==='approved_manual'
    && Boolean(String(release.retrospectiveApprovedAt||'').trim());
  const workerIntakeOpen=program.retrospectivePanel?.intakeStatus==='open';
  $('workerPanelClosed').hidden=workerOpen;
  $('workerValidatorForm').hidden=!workerIntakeOpen;
  const shareSource=recruitmentSourceCode();
  $('communitySharePanel').hidden=shareSource==='website';
  $('communityShareSource').textContent=shareSource;
  const direct=directIntakeEnabled();
  $('directIntakeFields').hidden=!direct;
  $('applicantContactEmail').required=direct;
  $('betaApplicationSubmitBtn').textContent=direct?'Kirim pendaftaran':'Kirim lewat aplikasi email';
  $('applicationSendHelp').textContent=direct
    ?'Pendaftaran dikirim langsung di halaman ini. Jika pengiriman langsung gagal, gunakan “Buka Gmail” atau “Salin teks pendaftaran” sebagai cadangan.'
    :'Jika tombol email tidak membuka aplikasi, gunakan “Buka Gmail”. Jika Gmail juga tidak tersedia, salin teks lalu kirim manual ke alamat yang ditampilkan setelah menyalin.';
  const pill=$('betaStatusPill');
  pill.textContent=accessOpen
    ?'AKSES BETA OPEN'
    :intakeOpen
      ?'PENDAFTARAN OPEN · AKSES MENUNGGU'
      :'BELUM DIBUKA';
  pill.className='status-pill '+(intakeOpen||accessOpen?'open':'hold');
}

$('betaApplicationForm').addEventListener('submit',async(event)=>{
  event.preventDefault();
  const out=$('applicationResult');
  if(!betaProgram||betaProgram.application?.intakeStatus!=='open'){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran minat beta belum dibuka.';return;
  }
  if(!applicantFormComplete()){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi tahap, tahun proses EPS, dan kedua persetujuan terlebih dahulu.';return;
  }
  if(directIntakeEnabled()){
    if(!validContactEmail($('applicantContactEmail').value)){
      out.hidden=false;out.className='result warn';out.textContent='Masukkan alamat email yang valid untuk menerima keputusan beta.';return;
    }
    const button=$('betaApplicationSubmitBtn');
    button.disabled=true;
    const previous=button.textContent;
    button.textContent='Mengirim…';
    try{
      const result=await submitDirectApplicant();
      out.hidden=false;out.className='result';
      out.textContent='Pendaftaran diterima langsung. Simpan kode referensi: '+String(result.submissionId||'diterima')+'. Tim akan meninjau pendaftaran tanpa meminta dokumen identitas.';
      $('betaApplicationForm').reset();
    }catch{
      out.hidden=false;out.className='result warn';
      out.textContent='Pengiriman langsung belum berhasil. Data belum dianggap terkirim. Gunakan “Buka Gmail” atau “Salin teks pendaftaran” sebagai cadangan.';
    }finally{
      button.disabled=false;
      button.textContent=previous;
    }
    return;
  }
  const email=betaProgram.application?.email||'modernsnc2022@gmail.com';
  const subject=encodeURIComponent('[KEP Beta Interest] Active EPS applicant');
  const body=encodeURIComponent(applicationText());
  location.href='mailto:'+encodeURIComponent(email)+'?subject='+subject+'&body='+body;
});

$('gmailApplicationBtn').addEventListener('click',()=>{
  const out=$('applicationResult');
  if(!betaProgram||betaProgram.application?.intakeStatus!=='open'){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran minat beta belum dibuka.';return;
  }
  if(!applicantFormComplete()){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi tahap, tahun proses EPS, dan kedua persetujuan terlebih dahulu.';return;
  }
  const email=betaProgram.application?.email||'modernsnc2022@gmail.com';
  const url=gmailComposeUrl(email,'[KEP Beta Interest] Active EPS applicant',applicationText());
  const opened=window.open(url,'_blank','noopener,noreferrer');
  if(!opened){
    out.hidden=false;out.className='result warn';
    out.textContent='Browser memblokir jendela Gmail. Gunakan tombol aplikasi email atau salin teks pendaftaran.';
  }
});

$('shareCommunityApplicantInviteBtn').addEventListener('click',async()=>{
  const out=$('communityShareResult');
  const result=await shareText(communityApplicantInviteText());
  out.hidden=false;
  out.className='result'+(result.ok?'':' warn');
  out.textContent=result.mode==='share'
    ?'Menu berbagi dibuka untuk undangan pelamar aktif dengan kode kanal '+recruitmentSourceCode()+'.'
    :result.mode==='copy'&&result.ok
      ?'Browser tidak mendukung menu berbagi; undangan pelamar aktif sudah disalin.'
      :result.mode==='cancel'
        ?'Berbagi dibatalkan.'
        :'Browser tidak mengizinkan berbagi atau salin otomatis.';
});

$('shareCommunityWorkerInviteBtn').addEventListener('click',async()=>{
  const out=$('communityShareResult');
  const result=await shareText(communityWorkerInviteText());
  out.hidden=false;
  out.className='result'+(result.ok?'':' warn');
  out.textContent=result.mode==='share'
    ?'Menu berbagi dibuka untuk undangan pekerja E-9 dengan kode kanal '+recruitmentSourceCode()+'.'
    :result.mode==='copy'&&result.ok
      ?'Browser tidak mendukung menu berbagi; undangan pekerja E-9 sudah disalin.'
      :result.mode==='cancel'
        ?'Berbagi dibatalkan.'
        :'Browser tidak mengizinkan berbagi atau salin otomatis.';
});

$('copyCommunityApplicantInviteBtn').addEventListener('click',async()=>{
  const out=$('communityShareResult');
  const ok=await copyText(communityApplicantInviteText());
  out.hidden=false;out.className='result'+(ok?'':' warn');
  out.textContent=ok
    ?'Undangan pelamar aktif sudah disalin dengan kode kanal '+recruitmentSourceCode()+'.'
    :'Browser tidak mengizinkan salin otomatis.';
});

$('copyCommunityWorkerInviteBtn').addEventListener('click',async()=>{
  const out=$('communityShareResult');
  const ok=await copyText(communityWorkerInviteText());
  out.hidden=false;out.className='result'+(ok?'':' warn');
  out.textContent=ok
    ?'Undangan pekerja E-9 sudah disalin dengan kode kanal '+recruitmentSourceCode()+'.'
    :'Browser tidak mengizinkan salin otomatis.';
});

$('workerValidatorForm').addEventListener('submit',(event)=>{
  event.preventDefault();
  const out=$('workerValidatorResult');
  if(!workerInterestOpen()){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran minat panel validator E-9 belum dibuka.';return;
  }
  if(!$('workerInKorea').checked||!$('workerUsedG2G').checked||!$('workerFeedbackAgreement').checked){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi ketiga konfirmasi terlebih dahulu.';return;
  }
  const email=betaProgram.retrospectivePanel?.application?.email||'modernsnc2022@gmail.com';
  const subject=encodeURIComponent(betaProgram.retrospectivePanel?.application?.interestSubject||'[KEP E-9 Worker Validator Interest] Retrospective panel');
  const body=encodeURIComponent(workerValidatorText());
  location.href='mailto:'+encodeURIComponent(email)+'?subject='+subject+'&body='+body;
});

$('gmailWorkerValidatorBtn').addEventListener('click',()=>{
  const out=$('workerValidatorResult');
  if(!workerInterestOpen()){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran minat panel validator E-9 belum dibuka.';return;
  }
  if(!$('workerInKorea').checked||!$('workerUsedG2G').checked||!$('workerFeedbackAgreement').checked){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi ketiga konfirmasi terlebih dahulu.';return;
  }
  const email=betaProgram.retrospectivePanel?.application?.email||'modernsnc2022@gmail.com';
  const subject=betaProgram.retrospectivePanel?.application?.interestSubject||'[KEP E-9 Worker Validator Interest] Retrospective panel';
  const url=gmailComposeUrl(email,subject,workerValidatorText());
  const opened=window.open(url,'_blank','noopener,noreferrer');
  if(!opened){
    out.hidden=false;out.className='result warn';
    out.textContent='Browser memblokir jendela Gmail. Gunakan tombol aplikasi email atau salin teks validator.';
  }
});

$('copyWorkerValidatorBtn').addEventListener('click',async()=>{
  const out=$('workerValidatorResult');
  if(!workerInterestOpen()){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran minat panel validator E-9 belum dibuka.';return;
  }
  if(!$('workerInKorea').checked||!$('workerUsedG2G').checked||!$('workerFeedbackAgreement').checked){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi ketiga konfirmasi terlebih dahulu.';return;
  }
  const ok=await copyText(workerValidatorText());
  out.hidden=false;out.className='result'+(ok?'':' warn');
  out.textContent=ok
    ?'Teks minat validator sudah disalin. Kirim ke '+(betaProgram.retrospectivePanel?.application?.email||'modernsnc2022@gmail.com')+'. Mengirim minat belum mengaktifkan akses panel.'
    :'Browser tidak mengizinkan salin otomatis. Gunakan tombol email.';
});

$('copyApplicationBtn').addEventListener('click',async()=>{
  const out=$('applicationResult');
  if(!betaProgram||betaProgram.application?.intakeStatus!=='open'){
    out.hidden=false;out.className='result warn';out.textContent='Pendaftaran minat beta belum dibuka.';return;
  }
  if(!applicantFormComplete()){
    out.hidden=false;out.className='result warn';out.textContent='Lengkapi tahap, tahun proses EPS, dan kedua persetujuan terlebih dahulu.';return;
  }
  const ok=await copyText(applicationText());
  out.hidden=false;out.className='result'+(ok?'':' warn');
  out.textContent=ok
    ?'Teks pendaftaran minat sudah disalin. Kirim ke '+(betaProgram.application?.email||'modernsnc2022@gmail.com')+'. Akses beta akan disetujui kemudian.'
    :'Browser tidak mengizinkan salin otomatis. Gunakan tombol email.';
});

Promise.all([
  fetch(PROGRAM_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('program HTTP '+response.status);return response.json()}),
  fetch(ROUTE_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('route HTTP '+response.status);return response.json()}),
  fetch(I18N_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('i18n HTTP '+response.status);return response.json()}),
  fetch(RECRUITMENT_SOURCES_URL,{cache:'no-store'}).then(response=>{if(!response.ok)throw new Error('sources HTTP '+response.status);return response.json()})
])
  .then(([program,route,i18n,recruitmentSources])=>{
    betaRoute=route;
    betaI18n=i18n||{};
    betaRecruitmentSourceCodes=new Set(recruitmentSources?.codes||[]);
    betaRecruitmentDefaultCode=String(recruitmentSources?.defaultCode||'website');
    if(!betaRecruitmentSourceCodes.has(betaRecruitmentDefaultCode))throw new Error('invalid recruitment source default');
    renderApplicantStageOptions();
    renderApplicantCycleOptions();
    renderProgram(program);
  })
  .catch(()=>{
    $('betaStatusPill').textContent='STATUS TIDAK TERSEDIA';
    $('betaStatusPill').className='status-pill hold';
    $('closedPanel').hidden=false;
    $('applicationPanel').hidden=true;
    $('closedPanel').querySelector('p').textContent='Status beta tidak dapat diverifikasi. Jangan mengirim aplikasi sampai halaman ini kembali normal.';
  });
