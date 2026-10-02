const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const RULES_URL='data/id_e9_manufacturing_2026_rules.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
const CONTRACT_URL='data/slc_guardian_2026.json';
const WORKPLACE_URL='data/workplace_reality_v1.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps',contract:'kep.contract',workplace:'kep.workplace',ledger:'kep.costLedger',payroll:'kep.payroll'};
let route=null,rules=null,contractRules=null,workplaceRules=null,i18n={},activeStage=null,deferredInstall=null;

const $=(id)=>document.getElementById(id);
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stageTitle=(stage)=>i18n[stage.id]?.title||stage.title;
const stageAction=(stage)=>i18n[stage.id]?.action||stage.action;
const stageWarning=(stage)=>i18n[stage.id]?.warning||stage.warning;

async function boot(){
  try{
    const [routeRes,rulesRes,i18nRes,contractRes,workplaceRes]=await Promise.all([
      fetch(ROUTE_URL,{cache:'no-store'}),
      fetch(RULES_URL,{cache:'no-store'}),
      fetch(I18N_URL,{cache:'no-store'}),
      fetch(CONTRACT_URL,{cache:'no-store'}),
      fetch(WORKPLACE_URL,{cache:'no-store'})
    ]);
    if(!routeRes.ok||!rulesRes.ok||!i18nRes.ok||!contractRes.ok||!workplaceRes.ok) throw new Error('verified data unavailable');
    route=await routeRes.json();
    rules=await rulesRes.json();
    i18n=await i18nRes.json();
    contractRules=await contractRes.json();
    workplaceRules=await workplaceRes.json();
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufaktur · 2026 · paket ${route.packVersion} · diperiksa ${route.lastVerified}`;
    renderCycleStatus();
    renderJourney();
    renderCurrentStageSelector();
    renderNextAction();
    renderEligibility();
    renderDocuments();
    renderCostLedger();
    renderContract();
    renderPayroll();
    renderWorkplace();
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
    if(next.id==='slc'){
      box.innerHTML=`<small>LANGKAH BERIKUTNYA</small><h2>${escapeHtml(stageTitle(next))}</h2><p>${escapeHtml(stageAction(next))}</p><button class="primary" data-go="contract">Periksa SLC saya</button>`;
    }else{
      box.innerHTML=`<small>LANGKAH BERIKUTNYA</small><h2>${escapeHtml(stageTitle(next))}</h2><p>${escapeHtml(stageAction(next))}</p><button class="primary" data-stage="${escapeHtml(next.id)}">Buka langkah ini</button>`;
    }
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

function readImageRatio(file){
  return new Promise((resolve,reject)=>{
    const url=URL.createObjectURL(file);
    const img=new Image();
    img.onload=()=>{const ratio=img.width/img.height;URL.revokeObjectURL(url);resolve(ratio)};
    img.onerror=()=>{URL.revokeObjectURL(url);reject(new Error('image read failed'))};
    img.src=url;
  });
}

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
    article.querySelector('.doc-file').addEventListener('change',async(e)=>{
      const file=e.target.files?.[0];
      const status=article.querySelector('.file-status');
      if(!file){status.textContent='No file checked yet';status.className='file-status';return}
      const errors=[];
      if(file.size>rules.maxFileSizeMb*1024*1024)errors.push('larger than '+rules.maxFileSizeMb+' MB');
      const lower=file.name.toLowerCase();
      if(doc.format==='PDF'&&!lower.endsWith('.pdf'))errors.push('expected PDF');
      if(doc.format==='JPG'&&!/\.jpe?g$/.test(lower))errors.push('format harus JPG/JPEG');
      if(doc.id==='photo'&&!errors.length){
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