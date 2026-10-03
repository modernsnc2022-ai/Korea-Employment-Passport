const PROGRAM_URL='data/beta_program_v1.json';
let betaProgram=null;

const $=(id)=>document.getElementById(id);
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

function applicationText(){
  const stage=$('applicantStage').value;
  return [
    'KOREA EMPLOYMENT PASSPORT — BETA APPLICATION',
    '',
    'Current stage: '+stage,
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

fetch(PROGRAM_URL,{cache:'no-store'})
  .then(response=>{if(!response.ok)throw new Error('HTTP '+response.status);return response.json()})
  .then(renderProgram)
  .catch(()=>{
    $('betaStatusPill').textContent='STATUS TIDAK TERSEDIA';
    $('betaStatusPill').className='status-pill hold';
    $('closedPanel').hidden=false;
    $('applicationPanel').hidden=true;
    $('closedPanel').querySelector('p').textContent='Status beta tidak dapat diverifikasi. Jangan mengirim aplikasi sampai halaman ini kembali normal.';
  });
