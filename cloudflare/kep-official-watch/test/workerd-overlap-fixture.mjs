// M13 local-only monotonic-source-overlap D1 trigger + batch rollback proof.
 // Local Wrangler + D1 resource count probe ONLY. Never a production Worker entry.
import { processSchedulePartitioned, sourceUrls } from "../src/index.mjs";
const {KP,HR,HD}=sourceUrls();
let kpRevisions=0,hrRevisions=0, lastProbe=null, fakeStamp='2026-10-16T01:00:00Z';
const officialText=url=>{
  const u=new URL(url);
  if(url.startsWith(KP)){
    const data=Array.from({length:50},(_,i)=>({
      id:50000-i,tanggal:"2026-10-16",
      judul:'<a href="/gtog-detail/korea/fixture-'+i+'">Synthetic Indonesia Manufacturing 2026 '+i+'</a>',
      gtgkorea:"<p>SYNTHETIC LOCAL TEST "+i+(i<kpRevisions?" changed":"")+"</p>"
    }));
    return JSON.stringify({draw:1,recordsTotal:5000,recordsFiltered:5000,data});
  }
  if(url.startsWith(HR)){
    const p=Number(u.searchParams.get("pageIndex"));
    let tr="";
    for(let i=0;i<8;i++){
      const seq=(p-1)*8+i;
      const examNo=10+seq;
      tr+='<tr id="tr_'+examNo+'" lcnsId="001" examYear="2026" examNot="'+examNo+
        '" examNation="011"><td>CBT</td><td>Philippines Manufacturing '+seq+
        '</td><td>Philippines</td><td>'+
        (seq<hrRevisions?"Synthetic revised application date":"Undecided")+
        '</td><td>Undecided</td><td>Undecided</td></tr>';
    }
    return '<html><body><input id="pageIndex" value="'+p+'"/><table>'+tr+'</table>'+
      [1,2,3,4,5,6].map(n=>'<a href="?pageIndex='+n+'">'+n+'</a>').join("")+'</body></html>';
  }
  if(url.startsWith(HD)){
    const city=u.searchParams.get("examNot")==="14"?"Jakarta":"Semarang";
    return "<html><body>SYNTHETIC Indonesia(Manufacturing)_"+city+
      " 2026-01-20 2026-06-04 2026-09-10</body></html>";
  }
  throw Error("UNEXPECTED_SYNTHETIC_URL");
};
function countingDb(db,stats){
  return {
    prepare(sql){stats.queryStatementsPrepared++;
      return db.prepare(sql);},
    batch(stmts){stats.batchCalls++;stats.batchStatementCount+=stmts.length;
      return db.batch(stmts);}
  };
}
const fakeFetcher=async url=>new Response(officialText(url),{status:200});
export default {
  async fetch(request){
    const path=new URL(request.url).pathname;
    if(path==="/test/metrics")return Response.json({localOnly:true,stats:lastProbe});
    if(path==="/test/newer"){
      kpRevisions=2;hrRevisions=2;fakeStamp="2026-10-16T05:00:00Z";
      return Response.json({testOnly:true,phase:"newer"});
    }
    if(path==="/test/stale"){
      kpRevisions=1;hrRevisions=1;fakeStamp="2026-10-16T03:00:00Z";
      return Response.json({testOnly:true,phase:"stale"});
    }
    if(path==="/test/set-burst"){
      kpRevisions=16;hrRevisions=16;
      return Response.json({testOnly:true,kpRevisions,hrRevisions});
    }
    if(path==="/test/status")return Response.json({testOnly:true,kpRevisions,hrRevisions});
    return new Response("Not Found",{status:404});
  },
  async scheduled(_controller,env,ctx){
    const stats={queryStatementsPrepared:0,batchCalls:0,batchStatementCount:0};
    const tempEnv={...env, MONITOR_DB:countingDb(env.MONITOR_DB,stats)};
    const started=performance.now();
    ctx.waitUntil(processSchedulePartitioned(tempEnv,{fetcher:fakeFetcher,now:()=>new Date(fakeStamp)}).then(result=>{
      const elapsed=performance.now()-started;
      const item={...stats,
        localWallMs:Math.round(elapsed*100)/100,
        providerResults:result.checked,
        status:result.status,
        changed:result.candidateChanges,
        // This is an upper-bound estimate from every D1 statement prepared.
        underFreeD1Query50:stats.queryStatementsPrepared<=50,
        // Local simulated CPU can differ materially from Cloudflare production.
        cloudflareProductionCPUVerified:false};
      lastProbe=item;
      console.log("KEP_LOCAL_COST_PROBE",JSON.stringify(item));
      if(!item.underFreeD1Query50)throw Error("LOCAL_COST_BUDGET_FAILED");
    }));
  }
};
