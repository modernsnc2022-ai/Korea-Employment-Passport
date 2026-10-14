/**
 * Private KEP email ownership service. Accessible ONLY through the intake
 * Worker's Cloudflare service binding; no public route or workers.dev hostname.
 * No raw email address or OTP is persisted, returned, or logged.
 */
const JSON_HEADERS={'Content-Type':'application/json; charset=utf-8',
  'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
const CODE_TTL_MS=10*60*1000, RESEND_MS=60*1000, HOUR_MS=60*60*1000;
const SECRET_MIN=32, MAX_BYTES=512;
const encoder=new TextEncoder();

function answer(ok,status=200){return new Response(JSON.stringify({ok}),{
  status,headers:JSON_HEADERS
});}
function validEmail(value){
  return typeof value==='string'&&value.length>=6&&value.length<=254
    &&value===value.trim().toLowerCase()
    &&/^[^\s@<>()[\]{}:,;\\"]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+$/i.test(value);
}
function configured(env){
  return env.VERIFIER_ENABLED==='true'&&Boolean(env.OTP_DB?.prepare)
    &&typeof env.VERIFIER_CALL_SECRET==='string'
    &&env.VERIFIER_CALL_SECRET.length>=SECRET_MIN
    &&typeof env.OTP_HMAC_SECRET==='string'
    &&env.OTP_HMAC_SECRET.length>=SECRET_MIN
    &&typeof env.EMAIL_FROM==='string'
    &&/^[^\s@]+@(?:gdglobal\.kr|mail\.gdglobal\.kr)$/i.test(env.EMAIL_FROM)
    &&(env.EMAIL_DELIVERY_PROVIDER==='resend'
      ?typeof env.RESEND_API_KEY==='string'
        &&env.RESEND_API_KEY.startsWith('re_')
        &&env.RESEND_API_KEY.length>=20
      :(env.EMAIL_DELIVERY_PROVIDER===undefined
        ||env.EMAIL_DELIVERY_PROVIDER==='cloudflare')
        &&typeof env.EMAIL?.send==='function');
}
function secretEqual(a,b){
  const left=encoder.encode(String(a||'')),right=encoder.encode(String(b||''));
  if(left.length!==right.length)return false;
  let diff=0;
  for(let i=0;i<left.length;i++)diff|=left[i]^right[i];
  return diff===0;
}
async function digest(parts,secret){
  const key=await crypto.subtle.importKey('raw',encoder.encode(secret),
    {name:'HMAC',hash:'SHA-256'},false,['sign']);
  const data=encoder.encode(parts.join(':'));
  const bytes=new Uint8Array(await crypto.subtle.sign('HMAC',key,data));
  return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
}
function newCode(){
  const limit=Math.floor(0x100000000/100000000)*100000000;
  const bytes=new Uint32Array(1);
  do{crypto.getRandomValues(bytes);}while(bytes[0]>=limit);
  return String(bytes[0]%100000000).padStart(8,'0');
}
async function deliverOtp(env,email,code,codeHash){
  const message={
    to:email,from:env.EMAIL_FROM,
    subject:'KEP - Kode verifikasi email',
    text:'Kode verifikasi Korea Employment Passport Anda: '+code+
      '\nBerlaku selama 10 menit. Jangan bagikan kode ini.\n'+
      'Jika Anda tidak meminta kode, abaikan pesan ini.'
  };
  if(env.EMAIL_DELIVERY_PROVIDER==='resend'){
    // Free-capable transactional provider. Never expose the API key or OTP in logs.
    const response=await fetch('https://api.resend.com/emails',{
      method:'POST',
      headers:{Authorization:'Bearer '+env.RESEND_API_KEY,
        'Content-Type':'application/json',
        'Idempotency-Key':'kep-otp-'+codeHash},
      body:JSON.stringify(message)
    });
    if(!response.ok)throw new Error('email_provider_rejected');
    const accepted=await response.json();
    if(typeof accepted?.id!=='string'||accepted.id.length<1)
      throw new Error('email_provider_unconfirmed');
    return;
  }
  await env.EMAIL.send(message);
}
async function requestCode(email,env,now){
  const key=await digest(['kep','email','v1',email],env.OTP_HMAC_SECRET);
  const code=newCode();
  const codeHash=await digest(['kep','otp','v1',key,code],env.OTP_HMAC_SECRET);
  // SQLite UPSERT makes 60s/3-per-hour limits atomic across Worker instances.
  // Pending challenges cannot be used. A failed send remains rate-limited.
  const row=await env.OTP_DB.prepare(
    'INSERT INTO otp_verifications '+
    '(email_hmac,code_hmac,requested_at_ms,expires_at_ms,window_started_ms,requests_in_window,attempts,delivery_state,consumed_at_ms) '+
    'VALUES (?,?,?,?,?,1,0,\'pending\',NULL) '+
    'ON CONFLICT(email_hmac) DO UPDATE SET '+
    'code_hmac=excluded.code_hmac,requested_at_ms=excluded.requested_at_ms,'+
    'expires_at_ms=excluded.expires_at_ms,attempts=0,delivery_state=\'pending\',consumed_at_ms=NULL,'+
    'window_started_ms=CASE WHEN excluded.requested_at_ms-otp_verifications.window_started_ms>=3600000 '+
    'THEN excluded.requested_at_ms ELSE otp_verifications.window_started_ms END,'+
    'requests_in_window=CASE WHEN excluded.requested_at_ms-otp_verifications.window_started_ms>=3600000 '+
    'THEN 1 ELSE otp_verifications.requests_in_window+1 END '+
    'WHERE excluded.requested_at_ms-otp_verifications.requested_at_ms>=60000 '+
    'AND (excluded.requested_at_ms-otp_verifications.window_started_ms>=3600000 '+
    'OR otp_verifications.requests_in_window<3) RETURNING email_hmac'
  ).bind(key,codeHash,now,now+CODE_TTL_MS,now).first();
  if(!row)return answer(false,429);
  try{
    await deliverOtp(env,email,code,codeHash);
    const confirmed=await env.OTP_DB.prepare(
      "UPDATE otp_verifications SET delivery_state='sent' "+
      "WHERE email_hmac=? AND code_hmac=? AND delivery_state='pending' RETURNING email_hmac"
    ).bind(key,codeHash).first();
    return answer(Boolean(confirmed),confirmed?200:503);
  }catch{
    await env.OTP_DB.prepare(
      "UPDATE otp_verifications SET delivery_state='failed' "+
      "WHERE email_hmac=? AND code_hmac=? AND delivery_state='pending'"
    ).bind(key,codeHash).run().catch(()=>{});
    return answer(false,503);
  }
}
async function confirmCode(email,code,env,now){
  const key=await digest(['kep','email','v1',email],env.OTP_HMAC_SECRET);
  const codeHash=await digest(['kep','otp','v1',key,code],env.OTP_HMAC_SECRET);
  const used=await env.OTP_DB.prepare(
    'UPDATE otp_verifications SET consumed_at_ms=? '+
    "WHERE email_hmac=? AND code_hmac=? AND delivery_state='sent' "+
    'AND consumed_at_ms IS NULL AND expires_at_ms>? AND attempts<5 '+
    'RETURNING email_hmac'
  ).bind(now,key,codeHash,now).first();
  if(used)return answer(true);
  await env.OTP_DB.prepare(
    'UPDATE otp_verifications SET attempts=attempts+1 '+
    "WHERE email_hmac=? AND delivery_state='sent' "+
    'AND consumed_at_ms IS NULL AND expires_at_ms>? AND attempts<5'
  ).bind(key,now).run();
  return answer(false,403);
}
const worker={
  async fetch(request,env){
    if(request.method!=='POST'||new URL(request.url).pathname!=='/action')
      return answer(false,404);
    if(!configured(env))return answer(false,503);
    if(!secretEqual(request.headers.get('X-KEP-Internal-Token'),env.VERIFIER_CALL_SECRET))
      return answer(false,403);
    if(!request.headers.get('Content-Type')?.toLowerCase().startsWith('application/json'))
      return answer(false,415);
    if(Number(request.headers.get('Content-Length')||0)>MAX_BYTES)
      return answer(false,413);
    let raw;
    try{raw=await request.text();}catch{return answer(false,400);}
    if(encoder.encode(raw).byteLength>MAX_BYTES)return answer(false,413);
    let body;
    try{body=JSON.parse(raw);}catch{return answer(false,400);}
    if(!body||typeof body!=='object'||Array.isArray(body)
      ||!validEmail(body.email)||!['request','confirm'].includes(body.mode)
      ||Object.keys(body).some(k=>!['mode','email','code'].includes(k))
      ||(body.mode==='request'&&'code' in body)
      ||(body.mode==='confirm'&&!(typeof body.code==='string'&&/^\d{8}$/.test(body.code))))
      return answer(false,400);
    try{
      return body.mode==='request'
        ?await requestCode(body.email,env,Date.now())
        :await confirmCode(body.email,body.code,env,Date.now());
    }catch{return answer(false,503);}
  },
  async scheduled(_event,env){
    if(!env.OTP_DB?.prepare)return;
    await env.OTP_DB.prepare('DELETE FROM otp_verifications WHERE requested_at_ms<?')
      .bind(Date.now()-24*HOUR_MS).run();
  }
};
export {newCode,digest,validEmail,configured,requestCode,confirmCode};
export default worker;
