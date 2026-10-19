/**
 * Actual intake Worker -> private OTP Worker -> Resend transport, backed by
 * Node built-in REAL SQLite (Node 24+). No network, PII, deployed D1 or email.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import intake from '../src/worker.js';
import verifier from '../email-verifier/src/worker.js';

const ROOT=new URL('..',import.meta.url);
const INTAKE_SQL=new URL('../migrations/0001_private_beta_applications.sql',import.meta.url);
const OTP_SQL=new URL('../email-verifier/migrations/0001_email_verification.sql',import.meta.url);
const QUOTA_SQL=new URL('../email-verifier/migrations/0002_resend_daily_quota.sql',import.meta.url);
const ORIGIN='https://www.gdglobal.kr';
const ENDPOINT='https://kep-beta-intake.internal/v1/beta/applicant';
const INTERNAL_SECRET='synthetic-internal-call-secret-at-least-32';
const SYNTHETIC_EMAIL='applicant@example.test';
const OTHER_EMAIL='other@example.test';
const TEST_NOW=1_790_000_000_000;

function sqliteD1(schemas){
  const db=new DatabaseSync(':memory:');
  for(const schema of [].concat(schemas))db.exec(readFileSync(schema,'utf8'));
  return {
    db,
    prepare(sql){
      let args=[];
      return {
        bind(...values){args=values;return this;},
        async first(){return db.prepare(sql).get(...args)||null;},
        async run(){return db.prepare(sql).run(...args);}
      };
    }
  };
}
async function withSetup(fn,{mailFails=false,intakeFails=false}={}){
  const origFetch=globalThis.fetch,origDate=Date.now;
  const inbox=new Map(),seen=new Set();
  const storage=sqliteD1(INTAKE_SQL);
  const otp=sqliteD1([OTP_SQL,QUOTA_SQL]);
  let now=TEST_NOW,serial=0;
  const envVerification={
    VERIFIER_ENABLED:'true',
    OTP_DB:otp,
    VERIFIER_CALL_SECRET:INTERNAL_SECRET,
    OTP_HMAC_SECRET:'different-synthetic-otp-hmac-secret-12345',
    EMAIL_DELIVERY_PROVIDER:'resend',
    RESEND_API_KEY:'re_synthetic-integration-test-no-network-123',
    EMAIL_FROM:'noreply@mail.gdglobal.kr'
  };
  const envIntake={
    INTAKE_ENABLED:'true',
    KEP_BETA_DB:intakeFails?{prepare(){throw new Error('synthetic_db_unavailable');}}:storage,
    INTAKE_HMAC_SECRET:'synthetic-hmac-key-for-intake-at-least-32',
    TURNSTILE_SECRET:'synthetic-turnstile-private-secret',
    VERIFIER_CALL_SECRET:INTERNAL_SECRET,
    ALLOWED_ORIGINS:ORIGIN,
    EMAIL_VERIFIER:{fetch:(request)=>verifier.fetch(request,envVerification)}
  };
  globalThis.fetch=async(url,init)=>{
    if(url==='https://challenges.cloudflare.com/turnstile/v0/siteverify'){
      const params=new URLSearchParams(init.body),token=params.get('response');
      const success=token?.startsWith('challenge-')&&!seen.has(token);
      seen.add(token);
      return Response.json({success,hostname:'www.gdglobal.kr'});
    }
    if(url==='https://api.resend.com/emails'){
      assert.equal(init.headers.Authorization,
        'Bearer '+envVerification.RESEND_API_KEY);
      if(mailFails)return Response.json({message:'rejected'}, {status:503});
      const mail=JSON.parse(init.body);
      assert.equal(mail.from,envVerification.EMAIL_FROM);
      const code=mail.text.match(/\b\d{8}\b/)?.[0];
      assert.match(code,/^\d{8}$/);
      const all=inbox.get(mail.to)||[];
      all.push(code);
      inbox.set(mail.to,all);
      return Response.json({id:'synthetic-message-'+(++serial)});
    }
    throw new Error('unexpected external URL in offline integration: '+url);
  };
  Date.now=()=>now;
  const payload=(email=SYNTHETIC_EMAIL,code)=>({
    kind:'active_applicant',contactEmail:email,
    stageId:'registration',stageTitle:'Pendaftaran',
    cycle:'2026',sourceCode:'website',activeProcess:true,
    feedbackAgreement:true,website:'',
    turnstileToken:'challenge-'+(++serial),
    ...(code===undefined?{}:{verificationCode:code})
  });
  const submit=async(body,requestCode=false)=>{
    const request=new Request(ENDPOINT+(requestCode?'/verify-request':''),{
      method:'POST',headers:{
        'Content-Type':'application/json',Origin:ORIGIN
      },body:JSON.stringify(body)
    });
    const response=await intake.fetch(request,envIntake);
    return {status:response.status,body:await response.json()};
  };
  const count=()=>storage.db.prepare('SELECT count(*) AS n FROM beta_applications').get().n;
  const otpRequest=async(email)=>{
    const response=await verifier.fetch(new Request('https://kep-email-verify.internal/action',{
      method:'POST',headers:{'Content-Type':'application/json',
      'X-KEP-Internal-Token':INTERNAL_SECRET},
      body:JSON.stringify({mode:'request',email})
    }),envVerification);
    return response.status;
  };
  const codeFor=(email=SYNTHETIC_EMAIL)=>inbox.get(email)?.at(-1);
  try{await fn({payload,submit,codeFor,count,otpRequest,storage,otp,envIntake,envVerification,
    addTime(ms){now+=ms;}});}
  finally{
    globalThis.fetch=origFetch;
    Date.now=origDate;
    storage.db.close();otp.db.close();
  }
}

test('real SQLite cross-Worker full path: request -> deliver -> verify -> receipt -> replay denied -> duplicate',async()=>{
  await withSetup(async h=>{
    let start=await h.submit(h.payload(),true);
    assert.equal(start.status,202);
    assert.deepEqual(start.body,{ok:true,verificationRequired:true,expiresMinutes:10});
    assert.equal(h.count(),0);
    const code=h.codeFor();
    assert.match(code,/^\d{8}$/);
    let receipt=await h.submit(h.payload(SYNTHETIC_EMAIL,code));
    assert.equal(receipt.status,201);
    assert.match(receipt.body.submissionId,/^KEP-I-[A-F0-9]{32}$/);
    assert.equal(h.count(),1);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,code))).status,403);
    assert.equal(h.count(),1);
    h.addTime(60001);
    assert.equal((await h.submit(h.payload(),true)).status,202);
    const duplicate=await h.submit(h.payload(SYNTHETIC_EMAIL,h.codeFor()));
    assert.equal(duplicate.status,200);
    assert.equal(duplicate.body.duplicate,true);
    assert.equal(duplicate.body.submissionId,receipt.body.submissionId);
    assert.equal(h.count(),1);
  });
});

test('ownership of address A cannot redeem receipt for address B',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL),true)).status,202);
    const codeA=h.codeFor(SYNTHETIC_EMAIL);
    assert.equal((await h.submit(h.payload(OTHER_EMAIL),true)).status,202);
    const codeB=h.codeFor(OTHER_EMAIL);
    assert.equal((await h.submit(h.payload(OTHER_EMAIL,codeA))).status,403);
    assert.equal(h.count(),0);
    assert.equal((await h.submit(h.payload(OTHER_EMAIL,codeB))).status,201);
    assert.equal(h.count(),1);
  });
});

test('five bad OTP guesses block the real code, without creating a receipt',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(),true)).status,202);
    const code=h.codeFor();
    const wrong=code==='00000000'?'00000001':'00000000';
    for(let i=0;i<5;i++)
      assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,wrong))).status,403);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,code))).status,403);
    assert.equal(h.count(),0);
  });
});

test('Resend provider rejection cannot mint receipt; challenge remains unusable',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(),true)).status,403);
    assert.equal(h.codeFor(),undefined);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,'12345678'))).status,403);
    assert.equal(h.count(),0);
  },{mailFails:true});
});

test('missing private verifier binding fails closed before a receipt is created',async()=>{
  await withSetup(async h=>{
    h.envIntake.EMAIL_VERIFIER=null;
    assert.equal((await h.submit(h.payload(),true)).status,503);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,'12345678'))).status,503);
    assert.equal(h.count(),0);
  });
});

test('application D1 write failure returns no receipt after correct email proof',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(),true)).status,202);
    const code=h.codeFor();
    const failure=await h.submit(h.payload(SYNTHETIC_EMAIL,code));
    assert.equal(failure.status,503);
    assert.equal(failure.body.ok,false);
    assert.equal(failure.body.submissionId,undefined);
    assert.equal(h.count(),0);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,code))).status,403);
  },{intakeFails:true});
});

test('two simultaneous redemptions of one OTP allow exactly one real SQLite receipt',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(),true)).status,202);
    const code=h.codeFor();
    const results=await Promise.all([
      h.submit(h.payload(SYNTHETIC_EMAIL,code)),
      h.submit(h.payload(SYNTHETIC_EMAIL,code))
    ]);
    assert.deepEqual(results.map(x=>x.status).sort(),[201,403]);
    assert.equal(h.count(),1);
  });
});

test('expired email code fails even with fresh Turnstile, and resending recovers',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(),true)).status,202);
    const old=h.codeFor();
    h.addTime(600001);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,old))).status,403);
    assert.equal(h.count(),0);
    assert.equal((await h.submit(h.payload(),true)).status,202);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,h.codeFor()))).status,201);
  });
});

test('Resend Free global 90/day enforced by ACTUAL production SQLite under concurrency',async()=>{
  await withSetup(async h=>{
    const day=Math.floor(TEST_NOW/86400000);
    const results=await Promise.all(Array.from({length:100},(_,i)=>
      h.otpRequest('realquota'+i+'@example.test')));
    assert.equal(results.filter(x=>x===200).length,90);
    assert.equal(results.filter(x=>x===429).length,10);
    const quota=h.otp.db.prepare(
      'SELECT requested_count FROM otp_resend_daily_quota WHERE day_utc=?'
    ).get(day);
    assert.equal(quota.requested_count,90);
    assert.equal(h.count(),0);
    h.addTime(86400000);
    assert.equal(await h.otpRequest('realquota-nextday@example.test'),200);
    assert.equal(h.otp.db.prepare(
      'SELECT requested_count FROM otp_resend_daily_quota WHERE day_utc=?'
    ).get(day+1).requested_count,1);
  });
});

test('Resend provider rejection conservatively consumes real SQLite daily quota',async()=>{
  await withSetup(async h=>{
    const day=Math.floor(TEST_NOW/86400000);
    assert.equal(await h.otpRequest('provider-failed@example.test'),503);
    assert.equal(h.otp.db.prepare(
      'SELECT requested_count FROM otp_resend_daily_quota WHERE day_utc=?'
    ).get(day).requested_count,1);
    assert.equal(h.count(),0);
  },{mailFails:true});
});

test('scheduled cleanup purges only expired rows even while both Workers are disabled',async()=>{
  await withSetup(async h=>{
    assert.equal((await h.submit(h.payload(),true)).status,202);
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,h.codeFor()))).status,201);
    assert.equal(h.count(),1);
    assert.equal(h.otp.db.prepare('SELECT count(*) AS n FROM otp_verifications').get().n,1);
    assert.equal(h.otp.db.prepare('SELECT count(*) AS n FROM otp_resend_daily_quota').get().n,1);
    // Cleanup must be independent of the public application/verification switches.
    h.envIntake.INTAKE_ENABLED='false';
    h.envVerification.VERIFIER_ENABLED='false';
    h.addTime(25*60*60*1000);
    await verifier.scheduled({},h.envVerification);
    await intake.scheduled({},h.envIntake);
    assert.equal(h.otp.db.prepare('SELECT count(*) AS n FROM otp_verifications').get().n,0);
    assert.equal(h.count(),1,'90-day applicant record must not be purged after 25h');
    h.addTime(8*24*60*60*1000);
    await verifier.scheduled({},h.envVerification);
    assert.equal(h.otp.db.prepare('SELECT count(*) AS n FROM otp_resend_daily_quota').get().n,0);
    assert.equal(h.count(),1,'90-day applicant record must persist after 9 days');
    h.addTime(83*24*60*60*1000);
    await intake.scheduled({},h.envIntake);
    assert.equal(h.count(),0,'expired applicant data must be purged after 90 days');
  });
});

test('shared call-secret rotation must match on both Workers and fails closed otherwise',async()=>{
  await withSetup(async h=>{
    const shared=h.envVerification.VERIFIER_CALL_SECRET;
    h.envIntake.VERIFIER_CALL_SECRET='synthetic-mismatched-intake-secret-over-32';
    assert.equal((await h.submit(h.payload(),true)).status,403);
    assert.equal(h.codeFor(),undefined,'mismatch must never dispatch live delivery');
    assert.equal(h.count(),0,'mismatch must never create applicant record');
    h.envIntake.VERIFIER_CALL_SECRET=shared;
    assert.equal((await h.submit(h.payload(),true)).status,202);
    const code=h.codeFor();
    assert.match(code,/^\d{8}$/);
    h.envVerification.VERIFIER_CALL_SECRET='synthetic-mismatched-verifier-secret-over-32';
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,code))).status,403);
    assert.equal(h.count(),0,'mismatch must not redeem OTP to create applicant record');
    h.envVerification.VERIFIER_CALL_SECRET=shared;
    assert.equal((await h.submit(h.payload(SYNTHETIC_EMAIL,code))).status,201);
    assert.equal(h.count(),1,'equal rotated values permit one approved receipt');
  });
});
