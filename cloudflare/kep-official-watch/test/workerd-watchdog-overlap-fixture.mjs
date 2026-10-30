// M14 local-only watchdog overlap + D1 trigger/transaction rollback proof.
// No network, real Cloudflare resources, notifications, or applicant data.
import {runWatchdog} from "../src/watchdog.mjs";
let fakeNow="2026-10-16T05:00:00Z";
export default {
  async fetch(request,env){
    const p=new URL(request.url).pathname;
    if(p==="/test/stale-recovery"){
      await env.MONITOR_DB.batch(["kp2mi","hrdk"].map(source=>
        env.MONITOR_DB.prepare(
          "INSERT INTO monitor_source_health(source_id,last_success_utc,consecutive_failures,error_kind) VALUES(?,?,0,NULL) ON CONFLICT(source_id) DO UPDATE SET last_success_utc=excluded.last_success_utc,consecutive_failures=0,error_kind=NULL"
        ).bind(source,"2026-10-16T04:58:00Z")));
      fakeNow="2026-10-16T04:59:00Z";
      return Response.json({fixtureOnly:true,mode:"stale_after_newer"});
    }
    if(p==="/test/legitimate-recovery"){
      fakeNow="2026-10-16T05:01:00Z";
      return Response.json({fixtureOnly:true,mode:"newer_recovery"});
    }
    return new Response("Not Found",{status:404});
  },
  async scheduled(_controller,env,ctx){
    ctx.waitUntil(runWatchdog(env,{now:()=>new Date(fakeNow)}).then(value=>{
      console.log("KEP_M14_LOCAL_D1_WATCHDOG_RACE",JSON.stringify({
        at:fakeNow,status:value.status,transitions:value.transitions
      }));
    }).catch(error=>{
      console.log("KEP_M14_LOCAL_D1_RACE_REJECTED",JSON.stringify({
        at:fakeNow,reason:error.message
      }));
      throw error;
    }));
  }
};
