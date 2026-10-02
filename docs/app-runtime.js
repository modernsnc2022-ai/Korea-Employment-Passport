const ROUTE_URL='data/id_e9_manufacturing_2026.json';
const RULES_URL='data/id_e9_manufacturing_2026_rules.json';
const I18N_URL='data/id_e9_manufacturing_2026_id.json';
const CONTRACT_URL='data/slc_guardian_2026.json';
const KEYS={done:'kep.doneStages',docs:'kep.docs',gaps:'kep.brokerGaps',contract:'kep.contract'};
let route=null,rules=null,contractRules=null,i18n={},activeStage=null,deferredInstall=null;

const $=(id)=>document.getElementById(id);
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,value)=>localStorage.setItem(key,JSON.stringify(value));
const escapeHtml=(value)=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const stageTitle=(stage)=>i18n[stage.id]?.title||stage.title;
const stageAction=(stage)=>i18n[stage.id]?.action||stage.action;
const stageWarning=(stage)=>i18n[stage.id]?.warning||stage.warning;

async function boot(){
  try{
    const [routeRes,rulesRes,i18nRes,contractRes]=await Promise.all([
      fetch(ROUTE_URL,{cache:'no-store'}),
      fetch(RULES_URL,{cache:'no-store'}),
      fetch(I18N_URL,{cache:'no-store'}),
      fetch(CONTRACT_URL,{cache:'no-store'})
    ]);
    if(!routeRes.ok||!rulesRes.ok||!i18nRes.ok||!contractRes.ok) throw new Error('verified data unavailable');
    route=await routeRes.json();
    rules=await rulesRes.json();
    i18n=await i18nRes.json();
    contractRules=await contractRes.json();
    $('routeTitle').textContent='Indonesia → Korea';
    $('routeMeta').textContent=`E-9 · Manufaktur · 2026 · paket ${route.packVersion} · diperiksa ${route.lastVerified}`;
    renderCycleStatus();
    renderJourney();
    renderCurrentStageSelector();
    renderNextAction();
    renderEligibility();
    renderDocuments();
    renderContract();
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

$('resetContractBtn').addEventListener('click',()=>{
  localStorage.removeItem(KEYS.contract);
  renderContract();
  $('contractResult').hidden=true;
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