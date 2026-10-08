const READINESS_URL='data/country_readiness_dashboard_2026.json';
const SOURCES_URL='data/beta_recruitment_sources_v1.json';
const APPLICATION_TO='modernsnc2022@gmail.com';
let allowedSources=new Set(['global_beta_website']);
let defaultSource='global_beta_website';

const $=(id)=>document.getElementById(id);

function sourceCode(){
  const raw=String(new URLSearchParams(location.search).get('src')||defaultSource).trim().toLowerCase();
  return allowedSources.has(raw)?raw:defaultSource;
}

async function loadSources(){
  try{
    const response=await fetch(SOURCES_URL,{cache:'no-store'});
    const data=await response.json();
    allowedSources=new Set(data.codes||[]);
  }catch{}
}

async function loadCountries(){
  const select=$('countryCode');
  try{
    const response=await fetch(READINESS_URL,{cache:'no-store'});
    const data=await response.json();
    const rows=(data.rows||[])
      .filter(row=>row.country!=='ID' && row.routeId && row.packState==='research_hold')
      .sort((a,b)=>String(a.countryName).localeCompare(String(b.countryName)));
    select.innerHTML='<option value="">Select sending country</option>';
    rows.forEach(row=>{
      const option=document.createElement('option');
      option.value=row.country;
      option.textContent=row.countryName;
      option.dataset.routeId=row.routeId;
      select.appendChild(option);
    });
  }catch{
    select.innerHTML='<option value="">Country list unavailable — try again later</option>';
  }
}

function selectedCountryName(){
  return $('countryCode').selectedOptions?.[0]?.textContent?.trim()||'';
}

function selectedRouteId(){
  return $('countryCode').selectedOptions?.[0]?.dataset?.routeId||'';
}

function selectedStageTitle(){
  return $('stageCategory').selectedOptions?.[0]?.textContent?.trim()||'';
}

function applicationText(){
  return [
    'KOREA EMPLOYMENT PASSPORT — GLOBAL TESTER INTEREST',
    '',
    'Country code: '+$('countryCode').value,
    'Country name: '+selectedCountryName(),
    'Country Pack route ID: '+selectedRouteId(),
    'Current stage category: '+$('stageCategory').value,
    'Current stage description: '+selectedStageTitle(),
    'EPS process cycle: '+$('processCycle').value,
    'Recruitment source code: '+sourceCode(),
    'Official G-to-G / EPS E-9 process: YES',
    'Feedback participation agreement: YES',
    '',
    'I am registering my interest as a KEP country-route validator / beta tester.',
    'I understand that this registration does not activate beta access automatically.',
    'I understand that my country pack may still be under research validation and that KEP will not guess unverified country-specific rules.',
    'I understand that KEP does not guarantee a job, employer selection, SLC, visa, or departure.',
    'I will not attach passport, national ID, ARC, identity numbers, home address, or identity-document images.'
  ].join('\n');
}

function subject(){
  return '[KEP Global Beta Interest] '+selectedCountryName()+' EPS applicant';
}

function gmailCompose(){
  const params=new URLSearchParams({view:'cm',fs:'1',to:APPLICATION_TO,su:subject(),body:applicationText()});
  return 'https://mail.google.com/mail/?'+params.toString();
}

async function copyText(text){
  if(navigator.clipboard?.writeText){
    try{await navigator.clipboard.writeText(text);return true}catch{}
  }
  const area=document.createElement('textarea');
  area.value=text;area.style.position='fixed';area.style.opacity='0';
  document.body.appendChild(area);area.select();
  let ok=false;try{ok=document.execCommand('copy')}catch{}
  area.remove();return ok;
}

function complete(){
  return Boolean(
    $('countryCode').value &&
    $('stageCategory').value &&
    $('processCycle').value &&
    $('officialProcess').checked &&
    $('feedbackAgreement').checked
  );
}

function warn(message){
  const out=$('result');
  out.hidden=false;out.className='result warn';out.textContent=message;
}

$('globalBetaForm').addEventListener('submit',(event)=>{
  event.preventDefault();
  if(!complete())return warn('Complete the country, stage, cycle, and both confirmations first.');
  const mailto='mailto:'+encodeURIComponent(APPLICATION_TO)+'?subject='+encodeURIComponent(subject())+'&body='+encodeURIComponent(applicationText());
  location.href=mailto;
});

$('gmailBtn').addEventListener('click',()=>{
  if(!complete())return warn('Complete the country, stage, cycle, and both confirmations first.');
  window.open(gmailCompose(),'_blank','noopener');
});

$('copyBtn').addEventListener('click',async()=>{
  if(!complete())return warn('Complete the country, stage, cycle, and both confirmations first.');
  const ok=await copyText(applicationText());
  const out=$('result');
  out.hidden=false;out.className='result '+(ok?'ok':'warn');
  out.textContent=ok?'Application copied. Email it to '+APPLICATION_TO+'.':'Could not copy automatically. Please use Send by email or Open Gmail.';
});

Promise.all([loadSources(),loadCountries()]);
