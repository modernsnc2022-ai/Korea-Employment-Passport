// KEP opt-in GitHub issue comments; no external sends by default.
// No applicant records, approval rules, or auto-retries of ambiguous HTTP outcomes.
const REPO="modernsnc2022-ai/Korea-Employment-Passport";
const APPROVED_OPERATOR_ISSUE=325; // Dedicated repo issue created 2026-10-16; does NOT activate sending.
const SOURCES=new Set(["kp2mi","hrdk"]);
// Even a 100-item historical change burst must stay well under the D1 Free
// per-invocation query limit. Already staged keys are skipped in later runs.
export const MAX_OUTBOX_NEW_PER_INVOCATION = 12;

function iso(s) {
  if(typeof s!=="string" || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(s) ||
      !Number.isFinite(Date.parse(s))) throw Error("INVALID_UTC");
  return Date.parse(s);
}
function text(s,max=200) {
  return String(s||"").replace(/<[^>]*>/g," ").replace(/[\r\n\t\x00-\x1f\x7f]/g," ")
   .replace(/@/g,"@\u200b").replace(/\s+/g," ").trim().slice(0,max);
}
function officialLink(raw,source){
  const u=new URL(raw);
  if (!SOURCES.has(source)||u.protocol!=="https:" || u.username||u.password||u.port||
      u.hostname!==(source==="kp2mi"?"kp2mi.go.id":"epstopik.hrdkorea.or.kr"))
    throw Error("INVALID_OFFICIAL_LINK");
  if(source==="kp2mi"&&!u.pathname.startsWith("/gtog-detail/korea/"))throw Error("INVALID_KP_DETAIL");
  if(source==="hrdk"&&!u.pathname.endsWith("/sechduleDetail.do"))throw Error("INVALID_HRD_DETAIL");
  return u.toString();
}
export function formatHealth(row) {
  if(!Number.isSafeInteger(row.id)||row.id<1||!SOURCES.has(row.source_id)||
    !["opened","updated","recovered"].includes(row.event_kind)) throw Error("INVALID_HEALTH_EVENT");
  const at=iso(row.observed_utc),reason=text(row.reason_code,80);
  if(!reason)throw Error("INVALID_REASON");
  const key="health:"+row.id;
  return {key,at,body:[
    "### KEP official-source monitor health",
    "**Source:** "+row.source_id,"**Transition:** "+row.event_kind,
    "**Reason code:** "+reason,"**Observed UTC:** "+row.observed_utc,"",
    "Observation only. No change to country-pack rules, official-source approvals or beta.",
    "<!-- kep-monitor-alert:"+key+" -->"].join("\n")};
}
export function formatReview(row) {
  if(!/^[a-f0-9]{64}$/.test(row.revision_id||"")||
    !/^(kp2mi|hrdk):/.test(row.source_key||"") ||
    !["new","changed"].includes(row.kind)||Number(row.scope_relevant)!==1)
    throw Error("INVALID_REVIEW_EVENT");
  const source=row.source_key.split(":")[0],url=officialLink(row.url,source);
  const at=iso(row.first_seen_utc),title=text(row.title,190);
  if(!title)throw Error("INVALID_TITLE");
  const key="review:"+row.revision_id;
  return {key,at,body:[
    "### KEP official notice needs human review","**Source:** "+source,
    "**Change:** "+row.kind,"**Title:** "+title,
    "**Official URL:** "+url,"**First observed UTC:** "+row.first_seen_utc,"",
    "Unapproved observation; check source, country, cohort and dates before modifying service.",
    "<!-- kep-monitor-alert:"+key+" -->"].join("\n")};
}
function settings(env,now){
  if(env.GITHUB_ALERT_REPO!==REPO)throw Error("GITHUB_DESTINATION_NOT_APPROVED");
  const issue=Number(env.GITHUB_ALERT_ISSUE);
  if(!Number.isSafeInteger(issue)||issue!==APPROVED_OPERATOR_ISSUE)throw Error("GITHUB_ISSUE_NOT_APPROVED");
  if(typeof env.GITHUB_ALERT_TOKEN!=="string"||!env.GITHUB_ALERT_TOKEN.trim())
    throw Error("GITHUB_SECRET_NOT_BOUND");
  const cutoff=iso(env.GITHUB_ALERT_START_UTC);
  if(cutoff>now.getTime()+120000||cutoff<now.getTime()-31*86400000)
    throw Error("GITHUB_ALERT_CUTOFF_OUT_OF_BOUNDS");
  return {issue,cutoff};
}
export async function readEligibleEvents(db,cutoff){
  const date=new Date(cutoff).toISOString();
  const [a,b]=await Promise.all([
    db.prepare("SELECT id,source_id,event_kind,reason_code,observed_utc FROM monitor_watchdog_events WHERE observed_utc>? ORDER BY id DESC LIMIT 50").bind(date).all(),
    db.prepare("SELECT revision_id,source_key,kind,title,url,scope_relevant,first_seen_utc FROM monitor_review WHERE scope_relevant=1 AND first_seen_utc>? ORDER BY first_seen_utc DESC LIMIT 50").bind(date).all()
  ]);
  if(!Array.isArray(a?.results)||!Array.isArray(b?.results)||
      a.results.length>50||b.results.length>50)throw Error("INVALID_ALERT_EVENT_QUERY");
  return [...a.results.map(formatHealth),...b.results.map(formatReview)].sort((x,y)=>x.at-y.at);
}
export async function postComment({issue,body,token},fetcher=fetch){
  if (issue!==APPROVED_OPERATOR_ISSUE) throw Error("GITHUB_ISSUE_NOT_APPROVED");
  const url="https://api.github.com/repos/"+REPO+"/issues/"+issue+"/comments";
  let res;
  try {
    res=await fetcher(url,{method:"POST",redirect:"manual",
      headers:{"Accept":"application/vnd.github+json","Content-Type":"application/json",
        "Authorization":"Bearer "+token,"X-GitHub-Api-Version":"2026-03-10",
        "User-Agent":"KEP-Official-Source-Monitor"},
      body:JSON.stringify({body}),signal:AbortSignal.timeout(12000)});
  } catch {return {delivered:false,reason:"NETWORK_OUTCOME_UNKNOWN"};}
  if(res.status!==201)return {delivered:false,reason:"NON_201_"+res.status};
  try {
    const ack=await res.json();
    const link=new URL(ack.html_url);
    if(!Number.isSafeInteger(ack.id)||ack.id<1||link.hostname!=="github.com"||
      link.pathname!=="/"+REPO+"/issues/"+issue||
      link.hash!=="#issuecomment-"+ack.id)
      return {delivered:false,reason:"ACK_INVALID"};
    return {delivered:true,commentId:ack.id};
  }catch{return {delivered:false,reason:"ACK_INVALID"};}
}
export async function dispatchAlerts(env,deps={}){
  if(env.ALERT_DELIVERY_ENABLED!=="true")return {status:"disabled",sent:0,attempted:0};
  if(!env.MONITOR_DB)throw Error("ALERT_DB_MISSING");
  const now=(deps.now||(()=>new Date()))();
  if(!(now instanceof Date)||Number.isNaN(now.getTime()))throw Error("INVALID_DISPATCH_TIME");
  const {issue,cutoff}=settings(env,now),db=env.MONITOR_DB;
  const found=await readEligibleEvents(db,cutoff);
  // One indexed D1 query checks the bounded event keys first. Repeated invocations
  // advance through unqueued items instead of starving newer items forever.
  let newEvents = found;
  if(found.length){
    const placeholders=found.map(()=>"?").join(",");
    const existing=await db.prepare(
      "SELECT event_key FROM monitor_alert_outbox WHERE event_key IN ("+placeholders+")"
    ).bind(...found.map(e=>e.key)).all();
    if(!Array.isArray(existing?.results)||existing.results.length>found.length)
      throw Error("OUTBOX_EXISTING_KEYS_INCOMPLETE");
    const keys=new Set();
    for(const row of existing.results){
      if(typeof row.event_key!=="string" || keys.has(row.event_key) ||
         !found.some(event=>event.key===row.event_key))
        throw Error("OUTBOX_EXISTING_KEYS_INVALID");
      keys.add(row.event_key);
    }
    newEvents=found.filter(e=>!keys.has(e.key)).slice(0,MAX_OUTBOX_NEW_PER_INVOCATION);
    if(newEvents.length){
      await db.batch(newEvents.map(e=>db.prepare(
        "INSERT OR IGNORE INTO monitor_alert_outbox(event_key,channel,body,status,attempts,first_seen_utc) VALUES(?,'github-issue-comment',?,'queued',0,?)"
      ).bind(e.key,e.body,now.toISOString())));
    }
  }
  const waiting=await db.prepare(
    "SELECT event_key FROM monitor_alert_outbox WHERE status='queued' ORDER BY first_seen_utc,event_key LIMIT 2"
  ).all();
  if(!Array.isArray(waiting?.results))throw Error("INVALID_PENDING_OUTBOX");
  let attempted=0,sent=0;
  for(const item of waiting.results){
    const claimed=await db.prepare(
      "UPDATE monitor_alert_outbox SET status='sending',attempts=attempts+1,claimed_utc=? WHERE event_key=? AND status='queued' AND attempts<10 RETURNING event_key,body"
    ).bind(now.toISOString(),item.event_key).first();
    if(!claimed)continue; // Concurrent invocation already claimed.
    attempted++;
    const reply=await postComment({
      issue,token:env.GITHUB_ALERT_TOKEN,body:claimed.body
    },deps.fetcher||fetch);
    if(!reply.delivered){
      await db.prepare(
        "UPDATE monitor_alert_outbox SET status='reconcile_required',last_failure_code=? WHERE event_key=? AND status='sending'"
      ).bind(reply.reason,item.event_key).run();
      // Unknown remote outcome: absolutely no blind retry.
      continue;
    }
    // If this local ack fails, the item stays sending, requiring reconciliation.
    const receipt=await db.prepare(
      "UPDATE monitor_alert_outbox SET status='sent',delivered_utc=?,github_comment_id=?,last_failure_code=NULL WHERE event_key=? AND status='sending' RETURNING event_key"
    ).bind(now.toISOString(),reply.commentId,item.event_key).first();
    if(!receipt)throw Error("GITHUB_POST_ACK_UNPERSISTED");
    sent++;
  }
  return {status:"ok",eligible:found.length,queuedThisRun:newEvents.length,attempted,sent,
    reconcileRequired:attempted-sent,officialRulesApproved:0,betaOpened:false};
}
export default {
  async fetch(){return new Response("Not Found",{status:404});},
  async scheduled(_controller,env,ctx){
    ctx.waitUntil(dispatchAlerts(env).then(result=>{
      console.log("KEP_OPERATOR_ALERTS",JSON.stringify(result));
      if(result.reconcileRequired)throw Error("GITHUB_OPERATOR_RECONCILIATION_REQUIRED");
    }));
  }
};
