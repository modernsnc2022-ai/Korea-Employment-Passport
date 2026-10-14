import test from 'node:test';
import assert from 'node:assert/strict';
import worker,{validate,ready,emailKey} from '../src/worker.js';

const ORIGIN='https://www.gdglobal.kr';
const URL='https://intake.example.test/v1/beta/applicant';
const secret='unit-test-HMAC-key-with-more-than-32-characters';
const originalFetch=globalThis.fetch;

class FakeD1{
  constructor(){this.rows=new Map();this.failure=false;}
  prepare(sql){
    return {bind:(...args)=>({
      first:async()=>{
        if(this.failure)throw new Error('SECRET_DB_ERROR: personal@example.com');
        if(sql.startsWith('INSERT INTO beta_applications')){
          const [hash,submissionId,email,stage,cycle,source,now,expires]=args;
          const prior=this.rows.get(hash);
          if(!prior||prior.expires<=now){
            this.rows.set(hash,{submissionId,email,stage,cycle,source,now,expires});
            return {submission_id:submissionId};
          }
          return null;
        }
        if(sql.startsWith('SELECT submission_id')){
          const [hash,now]=args;
          const prior=this.rows.get(hash);
          return prior&&prior.expires>now?{submission_id:prior.submissionId}:null;
        }
        throw new Error('Unexpected D1 SQL query: '+sql.slice(0,50));
      },
      run:async()=>{
        if(this.failure)throw new Error('DB unavailable');
        if(!sql.startsWith('DELETE FROM beta_applications'))throw new Error('Bad cron SQL');
        const now=args[0];
        for(const [hash,row] of this.rows)if(row.expires<=now)this.rows.delete(hash);
        return {success:true};
      }
    })};
  }
}

function env(db=new FakeD1(),patch={}){
  return {
    INTAKE_ENABLED:'true',
    ALLOWED_ORIGINS:'https://www.gdglobal.kr,https://modernsnc2022-ai.github.io',
    INTAKE_HMAC_SECRET:secret,
    TURNSTILE_SECRET:'unit-test-turnstile-secret',
    KEP_BETA_DB:db,
    // Synthetic Cloudflare service binding. Real ownership is confirmed by a
    // separate not-yet-connected private email sender/verification service.
    EMAIL_VERIFIER:{fetch:async request=>{
      const {mode,code}=await request.json();
      const ok=mode==='request'||(mode==='confirm'&&code==='12345678');
      return new Response(JSON.stringify({ok}),{
        status:ok?200:403,headers:{'Content-Type':'application/json'}
      });
    }},
    ...patch
  };
}
function payload(patch={}){
  return {
    kind:'active_applicant',contactEmail:'Applicant@Example.com',
    stageId:'registration',stageTitle:'Pendaftaran',cycle:'2026',
    sourceCode:'website',activeProcess:true,feedbackAgreement:true,
    website:'',turnstileToken:'unit-test-challenge-token',...patch
  };
}
function req(p=payload(),{origin=ORIGIN,url=URL,method='POST'}={}){
  return new Request(url,{
    method,headers:{
      Origin:origin,'Content-Type':'application/json','Accept':'application/json'
    },
    body:method==='POST'?(typeof p==='string'?p:JSON.stringify(p)):undefined
  });
}
async function response(p=payload(),configuration=env(),options={}){
  // Public browser direct intake now needs a Turnstile-cleared OTP request,
  // followed by possession of a mocked 8-digit email code.
  const first=await worker.fetch(req(p,{
    ...options,url:URL+'/verify-request'
  }),configuration);
  const challenge=await first.json();
  if(first.status!==202||challenge.verificationRequired!==true){
    return {status:first.status,data:challenge,headers:first.headers};
  }
  const body=typeof p==='string'?p:{...p,verificationCode:'12345678'};
  const final=await worker.fetch(req(body,options),configuration);
  return {status:final.status,data:await final.json(),headers:final.headers};
}
function siteverify({success=true,hostname='www.gdglobal.kr',status=200}={}){
  const calls=[];
  globalThis.fetch=async(url,init)=>{
    calls.push({url,body:new URLSearchParams(init.body)});
    return new Response(JSON.stringify({success,hostname}),{
      status,headers:{'Content-Type':'application/json'}
    });
  };
  return calls;
}
test.afterEach(()=>{globalThis.fetch=originalFetch;});

test('health cannot be mistaken for active intake; disabled until explicitly configured',async()=>{
  const e=env(undefined,{INTAKE_ENABLED:'false'});
  const r=await worker.fetch(new Request('https://intake.example.test/health'),e);
  assert.deepEqual(await r.json(),{
    ok:true,service:'kep-beta-intake',acceptingApplications:false
  });
  assert.equal((await response(payload(),e)).status,503);
});
test('CORS is explicit-origin only; no wildcard or cross-origin credentials',async()=>{
  siteverify();
  const blocked=await response(payload(),env(),{origin:'https://evil.example'});
  assert.equal(blocked.status,403);
  assert.equal(blocked.headers.get('Access-Control-Allow-Origin'),null);
  const preflight=await worker.fetch(new Request(URL,{
    method:'OPTIONS',headers:{Origin:ORIGIN,'Access-Control-Request-Method':'POST'}
  }),env());
  assert.equal(preflight.status,204);
  assert.equal(preflight.headers.get('Access-Control-Allow-Origin'),ORIGIN);
  assert.equal(preflight.headers.get('Access-Control-Allow-Credentials'),null);
});
test('strict payload parsing rejects unexpected identity fields, invalid route, wrong year and oversized data',async()=>{
  const db=new FakeD1();const e=env(db);siteverify();
  for(const x of [
    payload({passportNumber:'123456'}),
    payload({phone:'12345'}),
    payload({stageId:'fake_stage'}),
    payload({cycle:'2038'}),
    payload({activeProcess:false}),
    payload({contactEmail:'not-an-email'}),
    payload({sourceCode:'<script>alert(1)</script>'}),
  ])assert.equal((await response(x,e)).status,400);
  assert.equal((await response('{"broken":',e)).status,400);
  assert.equal((await response(payload({stageTitle:'x'.repeat(5000)}),e)).status,413);
  assert.equal(db.rows.size,0);
});
test('hidden bot-trap does not store or claim successful receipt',async()=>{
  const db=new FakeD1();siteverify();
  const r=await response(payload({website:'https://spam.example'}),env(db));
  assert.equal(r.status,202);
  assert.equal(r.data.ok,false);
  assert.equal(db.rows.size,0);
});
test('Turnstile failures or hostname mismatches prevent all storage',async()=>{
  const db=new FakeD1();const e=env(db);
  siteverify({success:false});
  assert.equal((await response(payload(),e)).status,403);
  siteverify({hostname:'attacker.example'});
  assert.equal((await response(payload(),e)).status,403);
  assert.equal(db.rows.size,0);
});
test('no Turnstile remote IP sent and no user IP persisted',async()=>{
  const db=new FakeD1(),calls=siteverify();
  const r=await response(payload(),env(db));
  assert.equal(r.status,201);
  assert.equal(calls.length,2);
  assert.equal(calls[0].body.has('remoteip'),false);
  assert.equal(calls[0].body.has('secret'),true);
  const row=[...db.rows.values()][0];
  assert.equal(row.email,'applicant@example.com');
  assert.deepEqual(Object.keys(row).sort(),[
    'cycle','email','expires','now','source','stage','submissionId'
  ].sort());
});
test('first write returns validated receipt, same email repeats previous receipt without new record',async()=>{
  const db=new FakeD1();siteverify();const e=env(db);
  const a=await response(payload(),e);
  assert.equal(a.status,201);
  assert.match(a.data.submissionId,/^KEP-I-[A-F0-9]{32}$/);
  const b=await response(payload({contactEmail:'  applicant@EXAMPLE.COM  '}),e);
  assert.equal(b.status,200);
  assert.deepEqual(b.data,{ok:true,submissionId:a.data.submissionId,duplicate:true});
  assert.equal(db.rows.size,1);
});
test('concurrent duplicate requests preserve one receipt via D1 unique-email semantics',async()=>{
  const db=new FakeD1();siteverify();const e=env(db);
  const [a,b,c]=await Promise.all([
    response(payload(),e),response(payload(),e),response(payload(),e)
  ]);
  assert.equal(db.rows.size,1);
  assert.equal(new Set([a.data.submissionId,b.data.submissionId,c.data.submissionId]).size,1);
  assert.equal([a.status,b.status,c.status].filter(x=>x===201).length,1);
});
test('data retention is exactly 90 days; later re-application may get a fresh receipt',async()=>{
  const db=new FakeD1();siteverify();const e=env(db);
  const originalNow=Date.now;
  let now=1760000000000;
  Date.now=()=>now;
  try{
    const first=await response(payload(),e);
    now+=89*24*60*60*1000;
    assert.equal((await response(payload(),e)).data.submissionId,first.data.submissionId);
    now+=2*24*60*60*1000;
    const second=await response(payload(),e);
    assert.equal(second.status,201);
    assert.notEqual(second.data.submissionId,first.data.submissionId);
    now+=91*24*60*60*1000;
    await worker.scheduled({},e);
    assert.equal(db.rows.size,0);
  }finally{Date.now=originalNow;}
});
test('database errors fail closed without exposing applicant, query or provider error text',async()=>{
  const db=new FakeD1();db.failure=true;siteverify();
  const r=await response(payload(),env(db));
  assert.equal(r.status,503);
  assert.deepEqual(r.data,{ok:false,error:'storage_unavailable'});
  assert.equal(JSON.stringify(r.data).includes('applicant@example.com'),false);
});
test('server signing does not leak raw email; distinct HMAC keys for distinct emails',async()=>{
  assert.match(await emailKey('applicant@example.com',secret),/^[a-f0-9]{64}$/);
  assert.notEqual(await emailKey('a@example.com',secret),await emailKey('b@example.com',secret));
});
test('missing required private secrets or database binding always disables intake',async()=>{
  for(const patch of [
    {INTAKE_HMAC_SECRET:''},{TURNSTILE_SECRET:''},{KEP_BETA_DB:null},
    {ALLOWED_ORIGINS:''},{INTAKE_ENABLED:'false'},{EMAIL_VERIFIER:null}
  ])assert.equal(ready(env(new FakeD1(),patch)),false);
});

test('an unverified address can never retrieve or issue an applicant receipt',async()=>{
  siteverify();
  const db=new FakeD1(),e=env(db);
  const direct=await worker.fetch(req({...payload(),verificationCode:'00000000'}),e);
  assert.equal(direct.status,403);
  assert.deepEqual(await direct.json(),{ok:false,error:'email_verification_required'});
  assert.equal(db.rows.size,0);
  const first=await worker.fetch(req(payload(),{url:URL+'/verify-request'}),e);
  assert.equal(first.status,202);
  const challenge=await first.json();
  assert.equal(challenge.verificationRequired,true);
  assert.equal('submissionId' in challenge,false);
  const bogus=await worker.fetch(req({...payload(),verificationCode:'00000000'}),e);
  assert.equal(bogus.status,403);
  assert.equal(db.rows.size,0);
});

test('missing private mail-verification binding blocks both request and receipt',async()=>{
  siteverify();
  const e=env(new FakeD1(),{EMAIL_VERIFIER:null});
  const r=await worker.fetch(req(payload(),{url:URL+'/verify-request'}),e);
  assert.equal(r.status,503);
  assert.equal((await r.json()).ok,false);
});
