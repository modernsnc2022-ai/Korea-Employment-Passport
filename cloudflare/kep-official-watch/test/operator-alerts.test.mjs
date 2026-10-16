import test from "node:test";
import assert from "node:assert/strict";
import {formatHealth,formatReview,postComment,dispatchAlerts} from "../src/operator-alerts.mjs";
import dispatcher from "../src/operator-alerts.mjs";

const DATE="2026-10-16T01:00:00Z";
const REV="a".repeat(64);
const health={id:7,source_id:"kp2mi",event_kind:"opened",
  reason_code:"source_fetch_failed",observed_utc:DATE};
const review={revision_id:REV,source_key:"hrdk:012:2026:14:001",kind:"changed",
  title:"Indonesia Manufacturing 2026",url:"https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/sechduleDetail.do?examNot=14",
  scope_relevant:1,first_seen_utc:DATE};
function env(db,extra={}){
  return {ALERT_DELIVERY_ENABLED:"true",MONITOR_DB:db,
    GITHUB_ALERT_REPO:"modernsnc2022-ai/Korea-Employment-Passport",
    GITHUB_ALERT_ISSUE:"325",GITHUB_ALERT_TOKEN:"test_token_only",
    GITHUB_ALERT_START_UTC:"2026-10-15T00:00:00Z",...extra};
}
const now=()=>new Date("2026-10-16T02:00:00Z");
class Db {
  constructor(){this.events=[health];this.reviews=[review];this.outbox=new Map();this.failedAcks=false;this.queries=0;}
  prepare(sql){
    const db=this;
    return {
      bind(...params){return {sql,params,
        async all(){return db.read(sql,params);},
        async first(){return db.first(sql,params);},
        async run(){return db.exec(sql,params);}
      };},
      async all(){return db.read(sql,[]);}
    };
  }
  async read(sql,params){
    this.queries++;
    if(sql.includes("FROM monitor_watchdog_events")){
      return {results:this.events.filter(x=>x.observed_utc>params[0] &&
        !this.outbox.has("health:"+x.id)).sort((a,b)=>a.id-b.id).slice(0,50)};
    }
    if(sql.includes("FROM monitor_review")){
      return {results:this.reviews.filter(x=>x.first_seen_utc>params[0] &&
        x.scope_relevant===1 && !this.outbox.has("review:"+x.revision_id))
        .sort((a,b)=>a.first_seen_utc.localeCompare(b.first_seen_utc)||
          a.revision_id.localeCompare(b.revision_id)).slice(0,50)};
    }
    if(sql.includes("FROM monitor_alert_outbox") && sql.includes("WHERE event_key IN (")){
      return {results:params.filter(key=>this.outbox.has(key)).map(event_key=>({event_key}))};
    }
    if(sql.includes("FROM monitor_alert_outbox")){
      return {results:[...this.outbox.values()].filter(x=>x.status==="queued")
        .sort((a,b)=>a.first_seen_utc.localeCompare(b.first_seen_utc)||a.event_key.localeCompare(b.event_key))
        .slice(0,2).map(x=>({event_key:x.event_key}))};
    }
    throw Error("READ_SQL_UNEXPECTED");
  }
  async first(sql,p){
    if(sql.includes("UPDATE monitor_alert_outbox SET status='sending'")){
      const row=this.outbox.get(p[1]);
      if(!row||row.status!=="queued"||row.attempts>=10)return null;
      row.status="sending";row.attempts++;row.claimed_utc=p[0];
      return {event_key:row.event_key,body:row.body};
    }
    if(sql.includes("UPDATE monitor_alert_outbox SET status='sent'")){
      if(this.failedAcks)throw Error("DB_ACK_FAILED");
      const row=this.outbox.get(p[2]);
      if(!row||row.status!=="sending")return null;
      row.status="sent";row.delivered_utc=p[0];row.github_comment_id=p[1];
      return {event_key:row.event_key};
    }
    throw Error("FIRST_SQL_UNEXPECTED");
  }
  async exec(sql,p){
    if(sql.includes("status='reconcile_required'")){
      const row=this.outbox.get(p[1]);
      if(row&&row.status==="sending"){row.status="reconcile_required";row.last_failure_code=p[0];}
      return {success:true};
    }
    throw Error("EXEC_SQL_UNEXPECTED");
  }
  async batch(statements){
    for(const {sql,params} of statements){
      if(!sql.includes("INSERT OR IGNORE INTO monitor_alert_outbox"))throw Error("BAD_BATCH_SQL");
      if(!this.outbox.has(params[0])){
        this.outbox.set(params[0],{event_key:params[0],body:params[1],
          first_seen_utc:params[2],status:"queued",attempts:0});
      }
    }
    return statements.map(()=>({success:true}));
  }
}
function posted() {
  const calls=[];
  const fetcher=async(url,opts)=>{
    calls.push({url,opts});
    assert.equal(opts.redirect,"manual");
    assert.equal(opts.headers["Authorization"],"Bearer test_token_only");
    assert.equal(new URL(url).hostname,"api.github.com");
    const id=111+calls.length;
    return {status:201,json:async()=>({
      id,html_url:"https://github.com/modernsnc2022-ai/Korea-Employment-Passport/issues/325#issuecomment-"+id
    })};
  };
  return {calls,fetcher};
}

test("default-disabled transport never queries DB, sends no network and public fetch returns 404",async()=>{
  let called=0;
  const r=await dispatchAlerts({ALERT_DELIVERY_ENABLED:"false"},{fetcher:()=>{called++;}});
  assert.deepEqual(r,{status:"disabled",sent:0,attempted:0});
  assert.equal(called,0);
  assert.equal((await dispatcher.fetch()).status,404);
});
test("approved destination and UTC cutoff required before any reads or network",async()=>{
  const db=new Db(), f=posted();
  await assert.rejects(dispatchAlerts(env(db,{GITHUB_ALERT_ISSUE:"0"}),{now,fetcher:f.fetcher}),/NOT_APPROVED/);
  await assert.rejects(dispatchAlerts(env(db,{GITHUB_ALERT_ISSUE:"999"}),{now,fetcher:f.fetcher}),/NOT_APPROVED/);
  await assert.rejects(dispatchAlerts(env(db,{GITHUB_ALERT_TOKEN:""}),{now,fetcher:f.fetcher}),/SECRET_NOT_BOUND/);
  await assert.rejects(dispatchAlerts(env(db,{GITHUB_ALERT_REPO:"different/repo"}),{now,fetcher:f.fetcher}),/DESTINATION/);
  await assert.rejects(dispatchAlerts(env(db,{GITHUB_ALERT_START_UTC:"2023-01-01T00:00:00Z"}),{now,fetcher:f.fetcher}),/CUTOFF_OUT_OF_BOUNDS/);
  assert.equal(db.queries,0);assert.equal(f.calls.length,0);
});
test("safe message formatting filters unsafe hosts, sensitive body and mass mentions",()=>{
  const message=formatHealth({...health,reason_code:"fetch_failed @everyone"});
  assert.match(message.body,/fetch_failed/);
  assert.equal(message.body.includes("@everyone"),false);
  assert.equal(message.key,"health:7");
  const ok=formatReview({...review,title:"Manufacturing <script>bad</script> @all"});
  assert.equal(ok.body.includes("@all"),false);
  assert.equal(ok.body.includes("<script>"),false);
  assert.equal(ok.body.includes("Official URL:"),true);
  assert.throws(()=>formatReview({...review,url:"https://evil.test/notice"}),/INVALID_OFFICIAL_LINK/);
  assert.throws(()=>formatReview({...review,scope_relevant:0}),/INVALID_REVIEW_EVENT/);
  assert.throws(()=>formatHealth({...health,source_id:"outsider"}),/INVALID_HEALTH_EVENT/);
});
test("two distinct review/health events are posted once, repeated runs do not duplicate",async()=>{
  const db=new Db(),f=posted();
  const first=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(first.sent,2);assert.equal(first.reconcileRequired,0);
  assert.equal(db.outbox.size,2);assert.equal(f.calls.length,2);
  assert.ok([...db.outbox.values()].every(x=>x.status==="sent"&&x.github_comment_id>0&&x.attempts===1));
  const again=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(again.attempted,0);assert.equal(f.calls.length,2);
  assert.equal(again.officialRulesApproved,0);assert.equal(again.betaOpened,false);
});
test("ambiguous failure enters manual-reconcile hold and NEVER gets blindly re-sent",async()=>{
  const db=new Db(),f={calls:0,fetcher:async()=>{f.calls++;throw Error("connection reset after POST");}};
  const first=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(first.attempted,2);assert.equal(first.sent,0);
  assert.equal(first.reconcileRequired,2);
  assert.ok([...db.outbox.values()].every(x=>x.status==="reconcile_required"&&x.attempts===1));
  const second=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(second.attempted,0);assert.equal(f.calls,2);
});
test("post success but local D1 ack failure stays claimed, no duplicate repost",async()=>{
  const db=new Db(),f=posted();db.failedAcks=true;
  await assert.rejects(dispatchAlerts(env(db),{now,fetcher:f.fetcher}),/DB_ACK_FAILED/);
  assert.equal(f.calls.length,1);
  db.failedAcks=false;
  const after=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(after.attempted,1);
  assert.equal(f.calls.length,2);
  assert.equal([...db.outbox.values()].filter(x=>x.status==="sending").length,1);
});
test("low-level GitHub sender rejects any destination other than Issue 325",async()=>{
  let called=false;
  await assert.rejects(postComment({issue:999,token:"test_token_only",body:"sample"},
    async()=>{called=true;return {status:201};}),/GITHUB_ISSUE_NOT_APPROVED/);
  assert.equal(called,false);
});
test("GitHub API response errors or wrong ack never count as delivered",async()=>{
  const bad=await postComment({issue:325,token:"test_token_only",body:"fixture"},
    async()=>({status:403}));
  assert.deepEqual(bad,{delivered:false,reason:"NON_201_403"});
  const wrong=await postComment({issue:325,token:"test_token_only",body:"fixture"},
    async()=>({status:201,json:async()=>({id:22,html_url:"https://evil.test/a"})}));
  assert.equal(wrong.reason,"ACK_INVALID");
});

test("30-event backlog advances across separate free-tier cycles, max 12 new D1 inserts each",async()=>{
  const db=new Db(),f=posted();
  db.events=Array.from({length:30},(_,i)=>({...health,id:i+1}));
  db.reviews=[];
  const first=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(first.eligible,30);
  assert.equal(first.queuedThisRun,12);
  assert.equal(db.outbox.size,12);
  const second=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(second.queuedThisRun,12);
  assert.equal(db.outbox.size,24);
  const third=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(third.queuedThisRun,6);
  assert.equal(db.outbox.size,30);
  const fourth=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(fourth.queuedThisRun,0);
  assert.equal(db.outbox.size,30);
  assert.equal(f.calls.length,8);
  assert.equal([...db.outbox.values()].filter(x=>x.status==="sent").length,8);
  assert.equal([...db.outbox.values()].filter(x=>x.attempts>1).length,0);
});

test("M12 130 event backlog never starves beyond the original newest-50 window",async()=>{
  const db=new Db(),f=posted();
  db.reviews=[];
  db.events=Array.from({length:130},(_,i)=>({...health,id:i+1,
    observed_utc:"2026-10-16T01:00:00Z"}));
  const scheduled=[];
  for(let i=0;i<11;i++){
    const result=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
    assert.equal(result.status,"ok");
    assert.ok(result.eligible<=50);
    assert.ok(result.queuedThisRun<=12);
    scheduled.push(result.queuedThisRun);
  }
  assert.deepEqual(scheduled,[12,12,12,12,12,12,12,12,12,12,10]);
  assert.equal(db.outbox.size,130);
  assert.ok(db.outbox.has("health:1"));
  assert.ok(db.outbox.has("health:130"));
  assert.equal([...db.outbox.values()].filter(x=>x.attempts>1).length,0);
  assert.equal([...db.outbox.values()].filter(x=>x.status==="sent").length,22);
  assert.equal(f.calls.length,22);
});
test("M12 previously staged items do not displace new relevant reviews",async()=>{
  const db=new Db(),f=posted();
  db.events=Array.from({length:52},(_,i)=>({...health,id:i+1}));
  db.reviews=[];
  for(let i=0;i<5;i++){
    await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  }
  assert.equal(db.outbox.size,52);
  db.events.push({...health,id:53});
  db.reviews.push(review);
  const next=await dispatchAlerts(env(db),{now,fetcher:f.fetcher});
  assert.equal(next.eligible,2);
  assert.equal(next.queuedThisRun,2);
  assert.ok(db.outbox.has("health:53"));
  assert.ok(db.outbox.has("review:"+REV));
});
