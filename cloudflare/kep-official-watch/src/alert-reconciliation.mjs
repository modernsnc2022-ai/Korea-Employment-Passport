// Read-only, operator-invoked GitHub alert reconciliation.
// Never changes D1 statuses, sends comments, retries uncertain POSTs or approves facts.
// Every result is advisory: even a matching marker must be checked by the owner.
const REPO = "modernsnc2022-ai/Korea-Employment-Passport";
const ISSUE = 325;
const MAX_OUTBOX = 100;
const PER_PAGE = 100;
const MAX_PAGES = 10;
const STATUSES = new Set(["queued","sending","sent","reconcile_required"]);
const KEY = /^(?:health:[1-9]\d*|review:[a-f0-9]{64})$/;
const MARKER = /<!--\s*kep-monitor-alert:(health:[1-9]\d*|review:[a-f0-9]{64})\s*-->/g;

export function parseMarkers(body) {
  if (typeof body !== "string" || body.length > 30000) throw Error("INVALID_COMMENT_BODY");
  return [...body.matchAll(MARKER)].map(m => m[1]);
}
function verifyIssueComment(comment) {
  if (!comment || !Number.isSafeInteger(comment.id) || comment.id < 1 ||
      typeof comment.body !== "string" || comment.body.length > 30000 ||
      typeof comment.html_url !== "string") throw Error("BAD_GITHUB_COMMENT");
  const url = new URL(comment.html_url);
  if (url.protocol !== "https:" || url.hostname !== "github.com" ||
      url.pathname !== "/"+REPO+"/issues/"+ISSUE ||
      url.hash !== "#issuecomment-"+comment.id) throw Error("UNEXPECTED_COMMENT_DESTINATION");
}
function validateOutbox(row) {
  if (!row || !KEY.test(row.event_key || "") || !STATUSES.has(row.status) ||
      typeof row.body !== "string" || row.body.length > 30000 ||
      parseMarkers(row.body).length !== 1 ||
      parseMarkers(row.body)[0] !== row.event_key ||
      !Number.isSafeInteger(Number(row.attempts)) || Number(row.attempts) < 0 ||
      Number(row.attempts) > 10 ||
      (row.github_comment_id != null &&
       (!Number.isSafeInteger(row.github_comment_id) || row.github_comment_id < 1)))
    throw Error("BAD_OUTBOX_ROW");
}
export function reconcileOutbox(rows, comments) {
  if (!Array.isArray(rows) || rows.length > MAX_OUTBOX ||
      !Array.isArray(comments) || comments.length > PER_PAGE*MAX_PAGES) throw Error("RECONCILE_LIMIT_EXCEEDED");
  const markers = new Map(), commentIds = new Set(), outboxKeys = new Set();
  for (const c of comments) {
    verifyIssueComment(c);
    if (commentIds.has(c.id)) throw Error("DUPLICATE_COMMENT_ID");
    commentIds.add(c.id);
    for (const key of parseMarkers(c.body)) {
      if (!markers.has(key)) markers.set(key,[]);
      markers.get(key).push(c);
    }
  }
  const items=[];
  for (const row of rows) {
    validateOutbox(row);
    if (outboxKeys.has(row.event_key)) throw Error("DUPLICATE_OUTBOX_KEY");
    outboxKeys.add(row.event_key);
    const matching = markers.get(row.event_key) || [];
    const exact = matching.filter(c => c.body === row.body);
    let decision;
    if (matching.length > 1) decision="DUPLICATE_GITHUB_MARKERS_MANUAL_INVESTIGATION";
    else if (matching.length === 1 && exact.length === 0) decision="MARKER_BODY_MISMATCH_MANUAL_INVESTIGATION";
    else if (row.status === "sent") {
      decision = exact.length === 1 && row.github_comment_id === exact[0].id ?
        "RECEIPT_MATCHED_READ_ONLY" : "SENT_RECEIPT_DISAGREEMENT_INVESTIGATE";
    } else if (row.status === "sending" || row.status === "reconcile_required") {
      decision = exact.length === 1 ?
        "POSSIBLE_POST_FOUND_OWNER_VERIFY_BEFORE_REPAIR" :
        "AMBIGUOUS_POST_NOT_FOUND_DO_NOT_RETRY";
    } else {
      decision = exact.length === 1 ? "QUEUED_BUT_COMMENT_EXISTS_STOP_AND_INVESTIGATE" :
        "QUEUED_NO_COMMENT_NO_ACTION";
    }
    items.push({eventKey:row.event_key,outboxStatus:row.status,
      attemptCount:Number(row.attempts),possibleCommentIds:matching.map(c=>c.id),
      recordedCommentId:row.github_comment_id ?? null,decision});
  }
  const unknown = [...markers.entries()]
    .filter(([key]) => !outboxKeys.has(key))
    .map(([key,values]) => ({eventKey:key,commentIds:values.map(c=>c.id)}));
  return {issue:ISSUE,readOnly:true,postsMade:0,rowsRead:rows.length,
    commentsRead:comments.length,operatorActionRequired:items.some(x =>
      !["RECEIPT_MATCHED_READ_ONLY","QUEUED_NO_COMMENT_NO_ACTION"].includes(x.decision)
    ) || unknown.length > 0,items,unmatchedGitHubMarkers:unknown};
}
export async function getIssueComments(fetcher=fetch,token=null) {
  const all = [];
  for (let page=1;page<=MAX_PAGES;page++) {
    const url="https://api.github.com/repos/"+REPO+"/issues/"+ISSUE+
      "/comments?per_page="+PER_PAGE+"&page="+page;
    const headers={"Accept":"application/vnd.github+json",
      "User-Agent":"KEP-Official-Monitor-ReadOnly",
      "X-GitHub-Api-Version":"2022-11-28"};
    if (token) headers.Authorization="Bearer "+token;
    const response=await fetcher(url,{method:"GET",redirect:"manual",headers,
      signal:AbortSignal.timeout(12000)});
    if(response.status!==200) throw Error("GITHUB_READ_FAILED_"+response.status);
    if(response.url && response.url!==url) throw Error("GITHUB_READ_REDIRECT");
    const pageItems=await response.json();
    if(!Array.isArray(pageItems) || pageItems.length > PER_PAGE)
      throw Error("GITHUB_BAD_COMMENT_PAGE");
    for(const c of pageItems) verifyIssueComment(c);
    all.push(...pageItems);
    if(pageItems.length<PER_PAGE) return all;
  }
  // Fail closed rather than calling a truncated list "no corresponding comment".
  throw Error("GITHUB_COMMENT_HISTORY_EXCEEDS_AUDIT_BOUND");
}
export async function auditOperatorAlerts(env,deps={}) {
  if(env.ALERT_RECONCILE_ENABLED!=="true") return {status:"disabled",readOnly:true,postsMade:0};
  if(!env.MONITOR_DB) throw Error("MONITOR_D1_NOT_BOUND");
  if(env.GITHUB_ALERT_REPO!==REPO ||
      Number(env.GITHUB_ALERT_ISSUE)!==ISSUE) throw Error("AUDIT_DESTINATION_NOT_ALLOWED");
  const data=await env.MONITOR_DB.prepare(
    "SELECT event_key,body,status,attempts,github_comment_id FROM monitor_alert_outbox ORDER BY first_seen_utc,event_key LIMIT 101"
  ).all();
  if(!Array.isArray(data?.results) || data.results.length>MAX_OUTBOX)
    throw Error("D1_OUTBOX_EXCEEDS_AUDIT_BOUND");
  const comments=await getIssueComments(deps.fetcher||fetch,env.GITHUB_ALERT_TOKEN||null);
  const report=reconcileOutbox(data.results,comments);
  return {status:"audited",...report};
}
