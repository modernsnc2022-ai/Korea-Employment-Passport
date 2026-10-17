import test from "node:test";
import assert from "node:assert/strict";
import {parseMarkers,reconcileOutbox,getIssueComments,auditOperatorAlerts} from "../src/alert-reconciliation.mjs";

const key="health:12";
const body="### KEP official-source monitor health\nSource: kp2mi\n<!-- kep-monitor-alert:health:12 -->";
const id=91234;
const comment=(marker=key,bodyText=body,number=id)=>({
  id:number,body:bodyText,html_url:
    "https://github.com/modernsnc2022-ai/Korea-Employment-Passport/issues/325#issuecomment-"+number
});
const entry=(status="sending",extra={})=>({
  event_key:key,body,status,attempts:1,github_comment_id:null,...extra
});
const config=db=>({ALERT_RECONCILE_ENABLED:"true",MONITOR_DB:db,
  GITHUB_ALERT_REPO:"modernsnc2022-ai/Korea-Employment-Passport",
  GITHUB_ALERT_ISSUE:"325"});
const response=(comments,url="")=>({status:200,url,json:async()=>comments});

test("no-op when operator audit is not explicitly enabled, no D1 reads or remote traffic", async()=>{
  let calls=0;
  assert.deepEqual(await auditOperatorAlerts({ALERT_RECONCILE_ENABLED:"false"},
    {fetcher:()=>{calls++;}}),{status:"disabled",readOnly:true,postsMade:0});
  assert.equal(calls,0);
});
test("no duplicate network POST: ambiguous sending with matching verified marker remains manual",()=>{
  const r=reconcileOutbox([entry("sending")],[comment()]);
  assert.equal(r.readOnly,true);assert.equal(r.postsMade,0);
  assert.equal(r.items[0].decision,"POSSIBLE_POST_FOUND_OWNER_VERIFY_BEFORE_REPAIR");
  assert.equal(r.items[0].possibleCommentIds[0],id);
  assert.equal(r.operatorActionRequired,true);
});
test("reconcile-required with no comment is not automatically retried",()=>{
  const r=reconcileOutbox([entry("reconcile_required")],[]);
  assert.equal(r.items[0].decision,"AMBIGUOUS_POST_NOT_FOUND_DO_NOT_RETRY");
  assert.equal(r.postsMade,0);
});
test("recorded delivered id must match exact content, marker, and comment id",()=>{
  const ok=reconcileOutbox([entry("sent",{github_comment_id:id})],[comment()]);
  assert.equal(ok.items[0].decision,"RECEIPT_MATCHED_READ_ONLY");
  assert.equal(ok.operatorActionRequired,false);
  const wrong=reconcileOutbox([entry("sent",{github_comment_id:444})],[comment()]);
  assert.equal(wrong.items[0].decision,"SENT_RECEIPT_DISAGREEMENT_INVESTIGATE");
  assert.equal(wrong.operatorActionRequired,true);
});
test("duplicate marker or altered comment never auto repairs a row",()=>{
  const dup=reconcileOutbox([entry("sending")],[comment(),comment(key,body,91235)]);
  assert.equal(dup.items[0].decision,"DUPLICATE_GITHUB_MARKERS_MANUAL_INVESTIGATION");
  const mismatch=reconcileOutbox([entry("sending")],[comment(key,body+" changed",id)]);
  assert.equal(mismatch.items[0].decision,"MARKER_BODY_MISMATCH_MANUAL_INVESTIGATION");
  assert.equal(mismatch.postsMade,0);
});
test("already-queued row with GitHub comment requires investigation, no automatic repost",()=>{
  const r=reconcileOutbox([entry("queued",{attempts:0})],[comment()]);
  assert.equal(r.items[0].decision,"QUEUED_BUT_COMMENT_EXISTS_STOP_AND_INVESTIGATE");
  assert.equal(r.postsMade,0);
});
test("orphan comment marker is flagged, no D1 or comment mutation",()=>{
  const r=reconcileOutbox([],[comment()]);
  assert.equal(r.unmatchedGitHubMarkers.length,1);
  assert.equal(r.operatorActionRequired,true);
  assert.equal(r.postsMade,0);
});
test("forged source, forged issue, missing expected marker, and duplicate row are rejected",()=>{
  assert.throws(()=>reconcileOutbox([entry("sent",{body:"no marker"})],[]),/BAD_OUTBOX_ROW/);
  assert.throws(()=>reconcileOutbox([entry(),entry()],[]),/DUPLICATE_OUTBOX_KEY/);
  assert.throws(()=>reconcileOutbox([],[
    {...comment(),html_url:"https://github.com/modernsnc2022-ai/Korea-Employment-Passport/issues/999#issuecomment-91234"}]),/UNEXPECTED_COMMENT_DESTINATION/);
  assert.throws(()=>reconcileOutbox([],[comment(),comment()]),/DUPLICATE_COMMENT_ID/);
  assert.deepEqual(parseMarkers("n/a"),[]);
});
test("GitHub GET is bounded, official read-only, validates server response",async()=>{
  const urls=[];
  const comments=await getIssueComments(async(url,init)=>{
    urls.push(url);
    assert.equal(init.method,"GET");
    assert.equal(init.redirect,"manual");
    assert.equal(init.headers.Authorization,undefined);
    return response([comment()]);
  });
  assert.equal(comments.length,1);
  assert.equal(urls.length,1);
  assert.ok(urls[0].startsWith("https://api.github.com/repos/modernsnc2022-ai/Korea-Employment-Passport/issues/325/comments?"));
  await assert.rejects(getIssueComments(async()=>({status:403})),/GITHUB_READ_FAILED_403/);
  await assert.rejects(getIssueComments(async()=>response([{id:1,body:"a",html_url:"https://evil.invalid/1"}])),
    /UNEXPECTED_COMMENT_DESTINATION/);
});
test("audit from isolated D1 is read-only; wrong issue denied before reads",async()=>{
  let reads=0;
  const db={prepare(sql){
    reads++;assert.match(sql,/SELECT event_key/);
    return {all:async()=>({results:[entry("sending")]})};
  }};
  let posts=0;
  const f=async(url,init)=>{
    if(init.method!=="GET")posts++;
    return response([comment()]);
  };
  const result=await auditOperatorAlerts(config(db),{fetcher:f});
  assert.equal(result.status,"audited");
  assert.equal(result.rowsRead,1);assert.equal(reads,1);
  assert.equal(result.postsMade,0);assert.equal(posts,0);
  assert.equal(result.items[0].decision,"POSSIBLE_POST_FOUND_OWNER_VERIFY_BEFORE_REPAIR");
  await assert.rejects(auditOperatorAlerts({...config(db),GITHUB_ALERT_ISSUE:"324"},{fetcher:f}),
    /AUDIT_DESTINATION_NOT_ALLOWED/);
  assert.equal(reads,1);
});
test("outbox snapshot beyond bounded 100 rows fails, never incorrectly says no comment",async()=>{
  let sent=false;
  const db={prepare(){return {all:async()=>({results:Array.from({length:101},()=>entry())})}}};
  await assert.rejects(auditOperatorAlerts(config(db),{fetcher:()=>{sent=true;}}),
    /D1_OUTBOX_EXCEEDS_AUDIT_BOUND/);
  assert.equal(sent,false);
});
test("pagination fails closed if issue exceeds ten full pages",async()=>{
  let calls=0;
  await assert.rejects(getIssueComments(async(url)=>{
    calls++;
    const page=Number(new URL(url).searchParams.get("page"));
    return response(Array.from({length:100},(_,i)=>comment(key,body,page*1000+i+1)),url);
  }),/GITHUB_COMMENT_HISTORY_EXCEEDS_AUDIT_BOUND/);
  assert.equal(calls,10);
});
