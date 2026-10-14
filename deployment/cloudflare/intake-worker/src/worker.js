/**
 * KEP private Indonesian E-9 applicant-interest intake.
 * No production URL is configured in the public KEP beta application.
 * D1 UNIQUE(email_hmac) serializes duplicate submissions; no client IP stored.
 */
const CONTENT_HEADERS={
  'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'no-store',
  'X-Content-Type-Options':'nosniff',
  'Referrer-Policy':'no-referrer',
  'X-Robots-Tag':'noindex, nofollow'
};
const ROUTE='/v1/beta/applicant';
const RETENTION_MS=90*24*60*60*1000;
const MAX_BYTES=4096;
const STAGES=new Set([
  'eligibility','registration','exam_fee','biometric','document_verify','exam_card',
  'eps_topik','skill_competency','final_selection','psychology_pre_job','mcu1',
  'job_application','roster','employer_selection','slc','post_slc_requirements',
  'visa_docs','predeparture_training','mcu3_departure','departure','korea_entry_training',
  'employer_handover','residence_registration','eps_insurance_check','first_payroll_check',
  'labor_support_ready','employment_maintenance'
]);
const ALLOWED_KEYS=new Set([
  'kind','contactEmail','stageId','stageTitle','cycle','sourceCode',
  'activeProcess','feedbackAgreement','website','turnstileToken'
]);
const HEX='0123456789abcdef';

function origins(env){
  return String(env.ALLOWED_ORIGINS||'')
    .split(',').map(s=>s.trim()).filter(s=>{
      try{
        const u=new URL(s);
        return u.protocol==='https:'&&u.origin===s&&!u.username&&!u.password;
      }catch{return false;}
    });
}
function cors(origin,env){
  return origins(env).includes(origin)?{
    'Access-Control-Allow-Origin':origin,
    'Access-Control-Allow-Methods':'POST,OPTIONS',
    'Access-Control-Allow-Headers':'Content-Type,Accept',
    'Access-Control-Max-Age':'600',
    'Vary':'Origin'
  }:{};
}
function result(body,status=200,extra={}){
  return new Response(JSON.stringify(body),{status,headers:{...CONTENT_HEADERS,...extra}});
}
function isEmail(email){
  return email.length>=6&&email.length<=254
    &&/^[^\s@<>()[\]{}:,;\\"]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+$/i.test(email);
}
function allowedSource(value){
  return typeof value==='string'&&/^[a-z0-9_]{2,96}$/.test(value);
}
function validate(input){
  if(!input||typeof input!=='object'||Array.isArray(input))return null;
  if(Object.keys(input).some(k=>!ALLOWED_KEYS.has(k)))return null;
  if(input.kind!=='active_applicant'||input.activeProcess!==true||input.feedbackAgreement!==true)return null;
  if(typeof input.website!=='string'||input.website.length>120)return null;
  if(input.website.trim())return {bot:true};
  if(typeof input.contactEmail!=='string')return null;
  const email=input.contactEmail.trim().toLowerCase();
  if(!isEmail(email))return null;
  if(!STAGES.has(input.stageId))return null;
  // stageTitle comes from the public UI but is untrusted/free text; the
  // canonical stage ID is sufficient for the private review queue.
  if(typeof input.stageTitle!=='string'||input.stageTitle.length>180)return null;
  if(!['2026','2025','2024','unknown'].includes(input.cycle))return null;
  if(!allowedSource(input.sourceCode))return null;
  if(typeof input.turnstileToken!=='string'||input.turnstileToken.length<10
    ||input.turnstileToken.length>2048)return null;
  return {
    email,stageId:input.stageId,cycle:input.cycle,sourceCode:input.sourceCode,
    token:input.turnstileToken
  };
}
function ready(env){
  return env.INTAKE_ENABLED==='true'
    && Boolean(env.KEP_BETA_DB?.prepare)
    && typeof env.INTAKE_HMAC_SECRET==='string'
    && env.INTAKE_HMAC_SECRET.length>=32
    && typeof env.TURNSTILE_SECRET==='string'
    && env.TURNSTILE_SECRET.length>=16
    && origins(env).length>0;
}
async function emailKey(email,secret){
  const key=await crypto.subtle.importKey(
    'raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},
    false,['sign']
  );
  const sig=new Uint8Array(await crypto.subtle.sign(
    'HMAC',key,new TextEncoder().encode('kep:beta:v1:'+email)
  ));
  return Array.from(sig,v=>HEX[v>>4]+HEX[v&15]).join('');
}
async function confirmTurnstile(token,origin,secret,fetcher){
  const params=new URLSearchParams({secret,response:token});
  // Intentionally DO NOT send remoteip, log tokens, or save a challenge token.
  const r=await fetcher('https://challenges.cloudflare.com/turnstile/v0/siteverify',{
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:params.toString()
  });
  if(!r.ok)return false;
  const data=await r.json();
  const host=new URL(origin).hostname.toLowerCase();
  return data?.success===true&&typeof data.hostname==='string'
    &&data.hostname.toLowerCase()===host;
}
async function application(request,env,origin,fetcher){
  const c=cors(origin,env);
  if(!ready(env))return result({ok:false,error:'intake_unavailable'},503,c);
  if(!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json')){
    return result({ok:false,error:'json_required'},415,c);
  }
  if(Number(request.headers.get('Content-Length')||0)>MAX_BYTES){
    return result({ok:false,error:'too_large'},413,c);
  }
  let raw='';
  try{raw=await request.text();}catch{return result({ok:false,error:'bad_request'},400,c);}
  if(new TextEncoder().encode(raw).length>MAX_BYTES)return result({ok:false,error:'too_large'},413,c);
  let body;
  try{body=JSON.parse(raw);}catch{return result({ok:false,error:'bad_json'},400,c);}
  const data=validate(body);
  if(!data)return result({ok:false,error:'invalid_application'},400,c);
  if(data.bot)return result({ok:false,error:'submission_not_confirmed'},202,c);
  let verified=false;
  try{verified=await confirmTurnstile(data.token,origin,env.TURNSTILE_SECRET,fetcher);}
  catch{verified=false;}
  if(!verified)return result({ok:false,error:'challenge_required'},403,c);

  const now=Date.now(),expiry=now+RETENTION_MS;
  const hash=await emailKey(data.email,env.INTAKE_HMAC_SECRET);
  const receipt='KEP-I-'+crypto.randomUUID().replace(/-/g,'').toUpperCase();
  // SQLite UNIQUE constraint makes duplicates safe even under concurrent
  // requests; old unexpired submissions retain their original receipt.
  // Expired records may be replaced on next submission without waiting for Cron.
  const statement=env.KEP_BETA_DB.prepare(
    'INSERT INTO beta_applications '+
    '(email_hmac,submission_id,contact_email,stage_id,route_cycle,source_code,received_at_ms,expires_at_ms) '+
    'VALUES (?,?,?,?,?,?,?,?) '+
    'ON CONFLICT(email_hmac) DO UPDATE SET '+
    'submission_id=excluded.submission_id,contact_email=excluded.contact_email,'+
    'stage_id=excluded.stage_id,route_cycle=excluded.route_cycle,'+
    'source_code=excluded.source_code,received_at_ms=excluded.received_at_ms,'+
    'expires_at_ms=excluded.expires_at_ms '+
    'WHERE beta_applications.expires_at_ms<=excluded.received_at_ms '+
    'RETURNING submission_id'
  );
  try{
    const inserted=await statement.bind(hash,receipt,data.email,data.stageId,
      data.cycle,data.sourceCode,now,expiry).first();
    if(inserted?.submission_id){
      return result({ok:true,submissionId:inserted.submission_id},201,c);
    }
    const existing=await env.KEP_BETA_DB.prepare(
      'SELECT submission_id FROM beta_applications WHERE email_hmac=? AND expires_at_ms>?'
    ).bind(hash,now).first();
    if(existing?.submission_id){
      return result({ok:true,submissionId:existing.submission_id,duplicate:true},200,c);
    }
    // A competing update/delete race must never fabricate an acknowledgement.
    return result({ok:false,error:'retry_later'},503,c);
  }catch{
    // Never return D1 error strings, email or other applicant data.
    return result({ok:false,error:'storage_unavailable'},503,c);
  }
}
async function cleanup(env){
  if(!env.KEP_BETA_DB?.prepare)return;
  // Runs daily; expiration is also checked before any duplicate response.
  await env.KEP_BETA_DB.prepare(
    'DELETE FROM beta_applications WHERE expires_at_ms<=?'
  ).bind(Date.now()).run();
}
const worker={
  async fetch(request,env){
    const url=new URL(request.url);
    const origin=request.headers.get('Origin')||'';
    const c=cors(origin,env);
    if(request.method==='GET'&&url.pathname==='/health'){
      return result({ok:true,service:'kep-beta-intake',acceptingApplications:ready(env)},200);
    }
    if(request.method==='OPTIONS'&&url.pathname===ROUTE){
      return Object.keys(c).length
        ?new Response(null,{status:204,headers:c})
        :result({ok:false,error:'origin_not_allowed'},403);
    }
    if(request.method!=='POST'||url.pathname!==ROUTE){
      return result({ok:false,error:'not_found'},404,c);
    }
    if(!origin||!Object.keys(c).length){
      return result({ok:false,error:'origin_not_allowed'},403);
    }
    return application(request,env,origin,fetch);
  },
  async scheduled(_event,env){
    await cleanup(env);
  }
};
export {validate,ready,emailKey,confirmTurnstile};
export default worker;
