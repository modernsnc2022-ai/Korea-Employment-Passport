import test from "node:test";
import assert from "node:assert/strict";
import { evaluateSource, statusTransitions, runWatchdog } from "../src/watchdog.mjs";
import handler from "../src/watchdog.mjs";

class WatchdogD1 {
  constructor() {this.health=new Map();this.states=new Map();this.events=[];this.batches=0;this.throwBatch=false;}
  prepare(sql) {
    const db=this;
    return {
      async all() {
        if(sql.includes("FROM monitor_source_health")) return {results:[...db.health.entries()].map(([source_id,row])=>({source_id,...row}))};
        if(sql.includes("FROM monitor_watchdog_state")) return {results:[...db.states.entries()].map(([source_id,row])=>({source_id,...row}))};
        throw Error("UNEXPECTED_D1_READ");
      },
      bind(...values) {return {sql,values};}
    };
  }
  async batch(work) {
    this.batches++;
    if(this.throwBatch) throw Error("D1_BATCH_TRANSACTION_FAILED");
    const events=[...this.events],state=new Map(this.states);
    for(const item of work){
      if(item.sql.includes("INSERT INTO monitor_watchdog_events")){
        const [source_id,event_kind,reason_code,observed_utc]=item.values;
        events.push({source_id,event_kind,reason_code,observed_utc});
      }else if(item.sql.includes("INSERT INTO monitor_watchdog_state")){
        const [id,status,reason_code,last_checked_utc,last_changed_utc]=item.values;
        const former=state.get(id);
        // Model the M14 D1 BEFORE UPDATE trigger in the transactional scratch state.
        // The local event array is only committed after the entire batch succeeds.
        if(former && last_checked_utc<=former.last_checked_utc)
          throw Error("STALE_MONITOR_WATCHDOG");
        state.set(id,{status,reason_code,last_checked_utc,
          last_changed_utc:former?.status===status && former?.reason_code===reason_code
            ? former.last_changed_utc:last_changed_utc});
      }else throw Error("UNEXPECTED_D1_MUTATION");
    }
    this.events=events;this.states=state;
    return work.map(()=>({success:true}));
  }
  setHealthy(id, success="2026-10-16T01:00:00Z") {
    this.health.set(id,{last_success_utc:success,last_failure_utc:null,
      consecutive_failures:0,error_kind:null});
  }
  setFailure(id, count=1) {
    const old=this.health.get(id);
    this.health.set(id,{...old,last_failure_utc:"2026-10-16T02:00:00Z",
      consecutive_failures:count,error_kind:"Error"});
  }
}
const when = iso => ()=>new Date(iso);
function enabled(db) {return {MONITOR_WATCHDOG_ENABLED:"true",MONITOR_DB:db};}

test("disabled is a no-op and public fetch is 404",async()=>{
  assert.deepEqual(await runWatchdog({MONITOR_WATCHDOG_ENABLED:"false"}),{status:"disabled"});
  assert.equal((await handler.fetch()).status,404);
});

test("missing initial source checkpoint becomes one durable health alarm, repeated runs dedup",async()=>{
  const db=new WatchdogD1();
  const first=await runWatchdog(enabled(db),{now:when("2026-10-16T01:00:00Z")});
  assert.equal(first.status,"degraded");
  assert.equal(first.transitions.length,2);
  assert.equal(db.events.length,2);
  assert.ok(db.events.every(x=>x.event_kind==="opened"));
  assert.equal(first.deliveredNotifications,0);
  const second=await runWatchdog(enabled(db),{now:when("2026-10-16T02:00:00Z")});
  assert.equal(second.status,"degraded");
  assert.equal(second.transitions.length,0);
  assert.equal(db.events.length,2);
  assert.equal(db.states.size,2);
});

test("healthy source initial -> stale -> no duplicate -> fresh recovery",async()=>{
  const db=new WatchdogD1();db.setHealthy("kp2mi");db.setHealthy("hrdk");
  let r=await runWatchdog(enabled(db),{now:when("2026-10-16T02:00:00Z")});
  assert.equal(r.status,"healthy");assert.equal(db.events.length,0);
  r=await runWatchdog(enabled(db),{now:when("2026-10-16T05:30:00Z")});
  assert.equal(r.status,"degraded");assert.equal(db.events.length,2);
  assert.ok(db.events.every(x=>x.reason_code==="stale_success"));
  r=await runWatchdog(enabled(db),{now:when("2026-10-16T06:00:00Z")});
  assert.equal(r.transitions.length,0);
  db.setHealthy("kp2mi","2026-10-16T06:15:00Z");
  db.setHealthy("hrdk","2026-10-16T06:15:00Z");
  r=await runWatchdog(enabled(db),{now:when("2026-10-16T06:30:00Z")});
  assert.equal(r.status,"healthy");
  assert.equal(db.events.filter(x=>x.event_kind==="recovered").length,2);
});

test("KP2MI failed while HRD fresh emits only affected official source",async()=>{
  const db=new WatchdogD1();db.setHealthy("hrdk");db.setHealthy("kp2mi");
  db.setFailure("kp2mi",2);
  const r=await runWatchdog(enabled(db),{now:when("2026-10-16T02:10:00Z")});
  assert.equal(r.status,"degraded");
  assert.equal(db.events.length,1);
  assert.equal(db.events[0].source_id,"kp2mi");
  assert.equal(db.events[0].reason_code,"source_fetch_failed");
  assert.equal(db.states.get("hrdk").status,"healthy");
  assert.equal(db.states.get("kp2mi").status,"degraded");
  assert.equal(r.acceptedSourceHashes,0);
  assert.equal(r.betaOpened,false);
});

test("reason change is one transition, then KP2MI recovery closes alarm",async()=>{
  const db=new WatchdogD1();db.setHealthy("kp2mi");db.setHealthy("hrdk");
  db.setFailure("kp2mi");
  await runWatchdog(enabled(db),{now:when("2026-10-16T02:00:00Z")});
  let r=await runWatchdog(enabled(db),{now:when("2026-10-16T06:00:00Z")});
  assert.deepEqual(r.transitions.map(x=>[x.sourceId,x.kind]),
    [["kp2mi","updated"],["hrdk","opened"]]);
  assert.match(r.transitions[0].reasonCode,/source_fetch_failed/);
  assert.match(r.transitions[0].reasonCode,/stale_success/);
  db.setHealthy("kp2mi","2026-10-16T06:05:00Z");
  r=await runWatchdog(enabled(db),{now:when("2026-10-16T06:10:00Z")});
  assert.deepEqual(r.transitions.map(x=>x.kind),["recovered"]);
  // HRD transitioned to stale, so its independent health alarm remains open.
  assert.equal(r.status,"degraded");
  assert.equal(db.states.get("kp2mi").status,"healthy");
  assert.equal(db.states.get("hrdk").status,"degraded");
});

test("future success, invalid timestamps and corrupt counters fail closed",async()=>{
  const good=evaluateSource("hrdk",{last_success_utc:"2026-10-16T01:00:00Z",
    consecutive_failures:0},new Date("2026-10-16T01:30:00Z"),4);
  assert.equal(good.status,"healthy");
  const future=evaluateSource("hrdk",{last_success_utc:"2026-10-16T02:00:00Z",
    consecutive_failures:0},new Date("2026-10-16T01:30:00Z"),4);
  assert.equal(future.reasonCode,"future_clock_skew");
  assert.throws(()=>evaluateSource("other",null,new Date()),/UNKNOWN_MONITOR_SOURCE/);
  assert.throws(()=>evaluateSource("kp2mi",{consecutive_failures:"NaN"},
    new Date()),/BAD_FAILURE_COUNT/);
  assert.throws(()=>evaluateSource("kp2mi",{last_success_utc:"invalid",
    consecutive_failures:0},new Date()),/BAD_LAST_SUCCESS_TIME/);
  assert.throws(()=>statusTransitions({status:"any"},good),/INVALID_PREVIOUS_WATCHDOG_STATE/);
});

test("malformed D1 results and failed transaction never silently report healthy",async()=>{
  const db=new WatchdogD1();
  db.health.set("evil",{consecutive_failures:0,last_success_utc:"2026-10-16T01:00:00Z"});
  await assert.rejects(runWatchdog(enabled(db),{now:when("2026-10-16T01:30:00Z")}),/INVALID_SOURCE_HEALTH_ROW/);
  assert.equal(db.events.length,0);
  db.health.delete("evil");db.throwBatch=true;
  await assert.rejects(runWatchdog(enabled(db),{now:when("2026-10-16T01:30:00Z")}),/D1_BATCH_TRANSACTION_FAILED/);
  assert.equal(db.states.size,0);
  assert.equal(db.events.length,0);
});

test("M14 older watchdog run cannot emit false recovery or rewind state within clock-skew window",async()=>{
  const db=new WatchdogD1();
  const original=await runWatchdog(enabled(db),{now:when("2026-10-16T05:00:00Z")});
  assert.equal(original.status,"degraded");
  assert.equal(db.events.length,2);
  // A new origin success can arrive while an older watchdog execution is still running.
  db.setHealthy("kp2mi","2026-10-16T04:58:00Z");
  db.setHealthy("hrdk","2026-10-16T04:58:00Z");
  const eventsBefore=structuredClone(db.events),statesBefore=new Map(db.states);
  // One-minute delay is inside the existing two-minute clock-skew tolerance,
  // therefore the DB trigger (not the JS precheck) must reject it atomically.
  await assert.rejects(runWatchdog(enabled(db),{now:when("2026-10-16T04:59:00Z")}),
    /STALE_MONITOR_WATCHDOG/);
  assert.deepEqual(db.events,eventsBefore);
  assert.deepEqual(db.states,statesBefore);
  assert.ok(db.events.every(e=>e.event_kind==="opened"));
  assert.ok([...db.states.values()].every(e=>e.last_checked_utc==="2026-10-16T05:00:00.000Z"));
  // A future legitimate watchdog run still closes both incidents.
  const recovered=await runWatchdog(enabled(db),{now:when("2026-10-16T05:01:00Z")});
  assert.equal(recovered.status,"healthy");
  assert.deepEqual(recovered.transitions.map(x=>x.kind),["recovered","recovered"]);
});
test("M14 equal-time watchdog replay cannot duplicate alert transitions",async()=>{
  const db=new WatchdogD1();
  await runWatchdog(enabled(db),{now:when("2026-10-16T05:00:00Z")});
  await assert.rejects(runWatchdog(enabled(db),{now:when("2026-10-16T05:00:00Z")}),
    /STALE_MONITOR_WATCHDOG/);
  assert.equal(db.events.length,2);
  assert.equal(db.states.get("kp2mi").last_checked_utc,"2026-10-16T05:00:00.000Z");
});
