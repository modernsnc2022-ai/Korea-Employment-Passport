// LOCAL TEST ENTRYPOINT ONLY. Synthetic source fixtures, no public deployment.
// Calls the same production source-isolated scheduling logic.
import { processSchedulePartitioned, sourceUrls } from "../src/index.mjs";
const { KP, HR, HD } = sourceUrls();
let kpDown = false, hrdRevision = 0, kpRevisedCount = 0;
function fakeText(u) {
  const url = new URL(u);
  if (u.startsWith(KP)) {
    const data = Array.from({length:50}, (_,i) => ({
      id:50000-i,
      tanggal:"16 October 2026",
      judul:'<a href="/gtog-detail/korea/fixture-'+i+'">SYNTHETIC GENERAL MANUFACTURING 2026 NOTICE '+i+'</a>',
      gtgkorea:"<p>SYNTHETIC BODY index "+i+(i<kpRevisedCount?" REVISED":"")+"</p>"
    }));
    return JSON.stringify({draw:1,recordsTotal:5000,recordsFiltered:5000,data});
  }
  if (u.startsWith(HR)) {
    const page = Number(url.searchParams.get("pageIndex")||1);
    let rows="";
    for(let i=0;i<8;i++) {
      const no=page*10+i+10;
      rows+='<tr id="tr_'+no+'" lcnsId="001" examYear="2026" examNot="'+no+
        '" examNation="011"><td>CBT</td><td>Philippines Manufacturing fixture</td>'+
        '<td>Philippines</td><td>Undecided</td><td>Undecided</td><td>Undecided</td></tr>';
    }
    return '<html><body><input id="pageIndex" value="'+page+'"/><table>'+rows+'</table>'+
      [1,2,3,4,5,6].map(n=>'<a href="?pageIndex='+n+'">'+n+'</a>').join("")+'</body></html>';
  }
  if (u.startsWith(HD)) {
    const no = url.searchParams.get("examNot");
    const city = no==="14" ? "Jakarta" : "Semarang";
    const revisedDate = hrdRevision === 0 ? "2026-09-10" : "2026-09-11";
    return '<html><body>SYNTHETIC Indonesia(Manufacturing)_'+city+
      ' 2026-02-10 ~ 2026-02-12 2026-06-04 ~ 2026-06-29 '+revisedDate+'</body></html>';
  }
  throw Error("INVALID_SYNTHETIC_URL");
}
const fixtureFetcher = async input => {
  if (kpDown && input.startsWith(KP)) return new Response("Synthetic KP2MI error", { status: 503 });
  return new Response(fakeText(input), { status: 200 });
};
export default {
  async fetch(request) {
    const path = new URL(request.url).pathname;
    if (path === "/test/force-kp-outage-and-hrd-change") {
      kpDown = true;
      hrdRevision++;
      return Response.json({testOnly:true,kpDown,hrdRevision});
    }
    if (path === "/test/force-kp-17-changes") {
      kpRevisedCount = 17;
      kpDown = false;
      return Response.json({testOnly:true,kpRevisedCount});
    }
    if (path === "/test/recover-kp") {
      kpDown = false;
      return Response.json({testOnly:true,kpDown});
    }
    return new Response("Not Found",{status:404});
  },
  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(processSchedulePartitioned(env,{fetcher:fixtureFetcher}).then(
      result => console.log("KEP_SOURCE_ISOLATION_SYNTHETIC",JSON.stringify(result))
    ));
  }
};
