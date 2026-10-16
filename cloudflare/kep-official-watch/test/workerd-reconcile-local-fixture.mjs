// LOCAL WORKERD TEST ONLY: no network, no repo credentials, no D1 writes.
// Replays exactly the previously seeded synthetic comment receipts in local D1.
import {auditOperatorAlerts} from "../src/alert-reconciliation.mjs";
export default {
  async fetch() {return new Response("Not Found",{status:404});},
  async scheduled(_controller,env,ctx) {
    const fakeFetch=async (url,options)=>{
      if(options.method!=="GET" || !url.startsWith(
        "https://api.github.com/repos/modernsnc2022-ai/Korea-Employment-Passport/issues/325/comments?"))
        throw Error("NON_READONLY_TEST_REQUEST");
      const rows=await env.MONITOR_DB.prepare(
        "SELECT body,github_comment_id FROM monitor_alert_outbox WHERE status='sent'"
      ).all();
      const comments=rows.results.map(x=>({
        id:x.github_comment_id,body:x.body,
        html_url:"https://github.com/modernsnc2022-ai/Korea-Employment-Passport/issues/325#issuecomment-"+x.github_comment_id
      }));
      return {status:200,url,json:async()=>comments};
    };
    ctx.waitUntil(auditOperatorAlerts(env,{fetcher:fakeFetch}).then(report=>{
      console.log("KEP_RECONCILIATION_LOCAL_READONLY",JSON.stringify({
        status:report.status,rows:report.rowsRead,comments:report.commentsRead,
        actionsNeeded:report.operatorActionRequired,
        decisions:report.items.map(i=>i.decision),posts:report.postsMade
      }));
      if(report.operatorActionRequired) throw Error("RECONCILIATION_REVIEW_REQUIRED");
    }));
  }
};
