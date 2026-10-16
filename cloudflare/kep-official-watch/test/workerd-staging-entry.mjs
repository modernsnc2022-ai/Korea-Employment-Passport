// Workerd integration harness ONLY. This module is never the deployable Worker entrypoint.
// Official source responses below are synthetic fixtures, not new announcements.
import { processSchedule, sourceUrls } from "../src/index.mjs";
const { KP, HR, HD } = sourceUrls();
function fakeText(u) {
  const url = new URL(u);
  if (u.startsWith(KP)) {
    const data = Array.from({length:50}, (_,i) => ({
      id:50000-i,
      tanggal:"16 October 2026",
      judul:'<a href="/gtog-detail/korea/fixture-'+i+'">TEST GENERAL MANUFACTURING 2026 NOTICE '+i+'</a>',
      gtgkorea:"<p>SYNTHETIC TEST BODY index "+i+"</p>"
    }));
    return JSON.stringify({draw:1,recordsTotal:5000,recordsFiltered:5000,data});
  }
  if (u.startsWith(HR)) {
    const p=Number(url.searchParams.get("pageIndex")||1);
    let rows="";
    for(let i=0;i<8;i++) {
      const no=p*10+i+10;
      rows+='<tr id="tr_'+no+'" lcnsId="001" examYear="2026" examNot="'+no+
        '" examNation="011"><td>CBT</td><td>Philippines Manufacturing test fixture</td>'+
        '<td>Philippines</td><td>Undecided</td><td>Undecided</td><td>Undecided</td></tr>';
    }
    return '<html><body><input id="pageIndex" value="'+p+'"/><table>'+rows+'</table>'+
      [1,2,3,4,5,6].map(n=>'<a href="?pageIndex='+n+'">'+n+'</a>').join("")+'</body></html>';
  }
  if (u.startsWith(HD)) {
    const no=url.searchParams.get("examNot"), city=no==="14"?"Jakarta":"Semarang";
    return '<html><body>FICTITIOUS FIXTURE Indonesia(Manufacturing)_'+city+
      ' 2026-02-10 ~ 2026-02-12 2026-06-04 ~ 2026-06-29 </body></html>';
  }
  throw Error("INVALID_TEST_URL");
}
const fixtureFetcher = async input => new Response(fakeText(input), {status:200});
export default {
  async fetch() {return new Response("Not Found",{status:404})},
  async scheduled(_controller,env,ctx) {
    ctx.waitUntil(processSchedule(env,{fetcher:fixtureFetcher}).then(
      x=>console.log("KEP_WORKERD_SYNTHETIC_TEST_RESULT",JSON.stringify(x))
    ));
  }
};
