// LOCALLY INJECTED SYNTHETIC GitHub response; this entrypoint must NEVER deploy.
// Calls the identical production dispatchAlerts + isolated D1, but cannot send HTTP.
import {dispatchAlerts} from "../src/operator-alerts.mjs";
let replies=0;
const fakeGithub=async(url,opts)=>{
  if(!url.startsWith("https://api.github.com/repos/modernsnc2022-ai/Korea-Employment-Passport/issues/999/comments"))
    throw Error("UNAPPROVED_TEST_URL");
  if(opts.method!=="POST"||!opts.headers["Authorization"].startsWith("Bearer local_fixture_"))
    throw Error("UNAPPROVED_TEST_AUTH");
  const commentId=810000+(++replies);
  return Response.json({id:commentId,
    html_url:"https://github.com/modernsnc2022-ai/Korea-Employment-Passport/issues/999#issuecomment-"+commentId
  },{status:201});
};
export default {
  async fetch(){return new Response("Not Found",{status:404});},
  async scheduled(_controller,env,ctx){
    ctx.waitUntil(dispatchAlerts(env,{fetcher:fakeGithub,
      now:()=>new Date("2026-10-16T03:00:00Z")}).then(
      out=>console.log("KEP_ALERT_SYNTHETIC_LOCAL_ONLY",JSON.stringify(out))));
  }
};
