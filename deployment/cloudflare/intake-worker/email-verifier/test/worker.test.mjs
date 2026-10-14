import test from 'node:test';
import assert from 'node:assert/strict';
import verifier,{newCode,digest,configured} from '../src/worker.js';

const INTERNAL='https://kep-email-verify.internal/action';
const CALL_SECRET='verification-binding-secret-longer-than-32-bytes';
const HMAC_SECRET='different-otp-hmac-secret-longer-than-32-bytes';
const EMAIL='candidate@example.test';
const NOW=1_790_000_000_000;

class MemoryD1{
  constructor(){this.rows=new Map();}
  prepare(sql){
    const db=this;
    return {bind(...args){
      const operation=async()=>{
        if(sql.startsWith('INSERT INTO otp_verifications')){
          const [k,d,at,expiry,window]=args,old=db.rows.get(k);
          if(old&&(at-old.requestedAt<60000||
            (at-old.window<3600000&&old.count>=3)))return null;
          const sameWindow=old&&at-old.window<3600000;
          db.rows.set(k,{k,d,requestedAt:at,expiry,
            window:sameWindow?old.window:window,
            count:sameWindow?old.count+1:1,attempts:0,state:'pending',used:null});
          return {email_hmac:k};
        }
        if(sql.startsWith('UPDATE otp_verifications SET delivery_state=')){
          const [k,hash]=args,row=db.rows.get(k);
          if(!row||row.d!==hash||row.state!=='pending')return null;
          row.state=sql.includes("delivery_state='sent'")?'sent':'failed';
          return {email_hmac:k};
        }
        if(sql.startsWith('UPDATE otp_verifications SET consumed_at_ms=')){
          const [at,k,hash,now]=args,row=db.rows.get(k);
          if(!row||row.d!==hash||row.state!=='sent'||row.used!==null||
            row.expiry<=now||row.attempts>=5)return null;
          row.used=at;return {email_hmac:k};
        }
        if(sql.startsWith('UPDATE otp_verifications SET attempts=')){
          const [k,now]=args,row=db.rows.get(k);
          if(row&&row.state==='sent'&&row.used===null&&row.expiry>now&&row.attempts<5)
            row.attempts++;
          return null;
        }
        if(sql.startsWith('DELETE FROM otp_verifications')){
          const [threshold]=args;
          for(const [key,row] of db.rows)if(row.requestedAt<threshold)db.rows.delete(key);
          return null;
        }
        throw new Error('Unexpected D1 statement');
      };
      return {first:operation,run:async()=>{await operation();return {success:true};}};
    }};
  }
}
function setup(patch={}){
  const db=new MemoryD1(),mail=[];
  const env={VERIFIER_ENABLED:'true',OTP_DB:db,
    VERIFIER_CALL_SECRET:CALL_SECRET,OTP_HMAC_SECRET:HMAC_SECRET,
    EMAIL_FROM:'noreply@gdglobal.kr',
    EMAIL:{send:async message=>{mail.push(message);return {messageId:'synthetic'};}},
    ...patch};
  return {db,mail,env};
}
async function call(env,mode,email=EMAIL,code,opts={}){
  const body={mode,email,...(code===undefined?{}:{code})};
  const req=new Request(opts.url||INTERNAL,{
    method:'POST',headers:{'Content-Type':'application/json',
      'X-KEP-Internal-Token':opts.token??CALL_SECRET},
    body:JSON.stringify(opts.body||body)
  });
  const r=await verifier.fetch(req,env);
  return {status:r.status,body:await r.json()};
}
function mailedCode(mail){return mail.at(-1).text.match(/\d{8}/)?.[0];}
function fakeClock(){
  const original=Date.now;let now=NOW;Date.now=()=>now;
  return {add(ms){now+=ms;},restore(){Date.now=original;}};
}
test('disabled secret or missing email-send binding blocks service',async()=>{
  const good=setup();
  for(const patch of [{VERIFIER_ENABLED:'false'},{EMAIL:null},{OTP_DB:null},
    {OTP_HMAC_SECRET:'bad'},{VERIFIER_CALL_SECRET:'short'},
    {EMAIL_FROM:'fake@not-allowed.test'}]){
    const e={...good.env,...patch};
    assert.equal(configured(e),false);
    assert.equal((await call(e,'request')).status,503);
  }
});
test('private action refuses unbound caller and rejects other paths',async()=>{
  const {env,db,mail}=setup();
  assert.equal((await call(env,'request',EMAIL,undefined,{token:'wrong'})).status,403);
  assert.equal((await call(env,'request',EMAIL,undefined,
    {url:'https://internal/other'})).status,404);
  assert.equal(db.rows.size,0);assert.equal(mail.length,0);
});
test('invalid fields, identities, and unrequested code are rejected',async()=>{
  const {env,db,mail}=setup();
  for(const bad of ['victim@invalid','UPPER@example.test','victim+@domain',''])
    assert.equal((await call(env,'request',bad)).status,400);
  assert.equal((await call(env,'confirm',EMAIL,'11111111')).status,403);
  assert.equal((await call(env,'request',EMAIL,undefined,
    {body:{mode:'request',email:EMAIL,passport:'X'}})).status,400);
  assert.equal(db.rows.size,0);assert.equal(mail.length,0);
});
test('request sends random 8 digits and stores only HMACs',async()=>{
  const clock=fakeClock();
  try{
    const {env,db,mail}=setup();
    assert.equal((await call(env,'request')).status,200);
    assert.match(mailedCode(mail),/^\d{8}$/);
    assert.equal(mail[0].to,EMAIL);
    assert.equal(db.rows.size,1);
    const row=[...db.rows.values()][0];
    assert.match(row.k,/^[0-9a-f]{64}$/);assert.match(row.d,/^[0-9a-f]{64}$/);
    assert.equal(JSON.stringify(row).includes(EMAIL),false);
    assert.equal(JSON.stringify(row).includes(mailedCode(mail)),false);
    assert.equal(row.expiry-row.requestedAt,600000);
    assert.equal(row.state,'sent');
  }finally{clock.restore();}
});
test('resend waits 60 seconds and limits to 3 per hour',async()=>{
  const clock=fakeClock();
  try{
    const {env,mail}=setup();
    for(let i=0;i<3;i++){
      if(i)clock.add(60000);
      assert.equal((await call(env,'request')).status,200);
    }
    clock.add(60000);
    assert.equal((await call(env,'request')).status,429);
    assert.equal(mail.length,3);
    clock.add(3600000);
    assert.equal((await call(env,'request')).status,200);
    assert.equal(mail.length,4);
  }finally{clock.restore();}
});
test('five invalid attempts lock the code, even when the right code follows',async()=>{
  const clock=fakeClock();
  try{
    const {env,mail}=setup();
    assert.equal((await call(env,'request')).status,200);
    const code=mailedCode(mail),wrong=code==='00000000'?'00000001':'00000000';
    for(let i=0;i<5;i++)assert.equal((await call(env,'confirm',EMAIL,wrong)).status,403);
    assert.equal((await call(env,'confirm',EMAIL,code)).status,403);
  }finally{clock.restore();}
});
test('valid code is one-time even across concurrent redemptions',async()=>{
  const clock=fakeClock();
  try{
    const {env,mail}=setup();await call(env,'request');
    const code=mailedCode(mail);
    const outcomes=await Promise.all([call(env,'confirm',EMAIL,code),
      call(env,'confirm',EMAIL,code)]);
    assert.deepEqual(outcomes.map(x=>x.status).sort(),[200,403]);
    assert.equal((await call(env,'confirm',EMAIL,code)).status,403);
  }finally{clock.restore();}
});
test('expired code fails; replacing it invalidates the old code',async()=>{
  const clock=fakeClock();
  try{
    const {env,mail}=setup();await call(env,'request');
    const old=mailedCode(mail);
    clock.add(600001);
    assert.equal((await call(env,'confirm',EMAIL,old)).status,403);
    await call(env,'request');const updated=mailedCode(mail);
    assert.equal((await call(env,'confirm',EMAIL,old)).status,403);
    assert.equal((await call(env,'confirm',EMAIL,updated)).status,200);
  }finally{clock.restore();}
});
test('mailer failure is fail-closed and does not reset request rate limit',async()=>{
  const clock=fakeClock();
  try{
    const {env,db}=setup({EMAIL:{send:async()=>{throw new Error('private error');}}});
    assert.equal((await call(env,'request')).status,503);
    assert.equal([...db.rows.values()][0].state,'failed');
    assert.equal((await call(env,'confirm',EMAIL,'12345678')).status,403);
    assert.equal((await call(env,'request')).status,429);
  }finally{clock.restore();}
});
test('scheduled cleanup removes only old pseudonymous attempts',async()=>{
  const clock=fakeClock();
  try{
    const {env,db}=setup();await call(env,'request');
    clock.add(25*3600000);
    await verifier.scheduled({},env);
    assert.equal(db.rows.size,0);
  }finally{clock.restore();}
});
test('secure RNG returns 8 digits and HMAC separates inputs',async()=>{
  assert.match(newCode(),/^\d{8}$/);
  assert.equal((await digest(['x','y'],HMAC_SECRET)).length,64);
  assert.notEqual(await digest(['x','y'],HMAC_SECRET),
    await digest(['x','z'],HMAC_SECRET));
});

test('Resend free-provider adapter accepts only acknowledged API sends',async()=>{
  const old=globalThis.fetch,clock=fakeClock();
  const token='re_synthetic_test_api_key_more_than_20';
  const {env,db}=setup({EMAIL_DELIVERY_PROVIDER:'resend',EMAIL:null,
    RESEND_API_KEY:token,EMAIL_FROM:'noreply@mail.gdglobal.kr'});
  let outbound;
  globalThis.fetch=async(url,init)=>{
    assert.equal(url,'https://api.resend.com/emails');
    assert.equal(init.headers.Authorization,'Bearer '+token);
    outbound=JSON.parse(init.body);
    return new Response(JSON.stringify({id:'test-provider-id'}),{
      status:200,headers:{'Content-Type':'application/json'}
    });
  };
  try{
    assert.equal(configured(env),true);
    assert.equal((await call(env,'request')).status,200);
    assert.equal(outbound.to,EMAIL);
    assert.equal(outbound.from,'noreply@mail.gdglobal.kr');
    assert.match(outbound.text,/\d{8}/);
    assert.equal([...db.rows.values()][0].state,'sent');
  }finally{clock.restore();globalThis.fetch=old;}
});
test('Resend missing secret and rejected delivery fail closed',async()=>{
  const old=globalThis.fetch,clock=fakeClock();
  const {env,db}=setup({EMAIL_DELIVERY_PROVIDER:'resend',EMAIL:null,
    RESEND_API_KEY:'re_synthetic_test_api_key_more_than_20'});
  try{
    assert.equal(configured({...env,RESEND_API_KEY:''}),false);
    assert.equal((await call({...env,RESEND_API_KEY:''},'request')).status,503);
    globalThis.fetch=async()=>new Response(JSON.stringify({error:'rate_limited'}),{status:429});
    assert.equal((await call(env,'request')).status,503);
    assert.equal([...db.rows.values()][0].state,'failed');
  }finally{clock.restore();globalThis.fetch=old;}
});
test('Resend HTTP 200 without message ID does not unlock verification',async()=>{
  const old=globalThis.fetch,clock=fakeClock();
  const {env,db}=setup({EMAIL_DELIVERY_PROVIDER:'resend',EMAIL:null,
    RESEND_API_KEY:'re_synthetic_test_api_key_more_than_20'});
  try{
    globalThis.fetch=async()=>Response.json({});
    assert.equal((await call(env,'request')).status,503);
    assert.equal([...db.rows.values()][0].state,'failed');
  }finally{clock.restore();globalThis.fetch=old;}
});
