import test from "node:test";
import assert from "node:assert/strict";
import { KP, HR, HD, officialUrl, kpRecords, hrdRows, collect, changes, processSchedule } from "../src/index.mjs";
import worker from "../src/index.mjs";

const kp = (suffix="") => Array.from({ length: 50 }, (_, i) => ({
  id: 20000 - i, tanggal: "15 October 2026",
  judul: '<a href="/gtog-detail/korea/notice-' + (20000-i) + '">PENGUMUMAN ' +
    (i===0 ? "UBT UMUM SEKTOR MANUFAKTUR TAHUN 2026" : "PENGUMUMAN PEKERJA MIGRAN 2026") + "</a>",
  gtgkorea: "<p>Official notice body for item " + i + (i===0 ? suffix : "") + "</p>"
}));
function page(pageNo) {
  let rows = "";
  for (let i = 0; i < 8; i++) {
    const n=200-pageNo*10-i;
    const name = i%2 ? "Indonesia(Root Industry/Mold)" : "Philippines Manufacturing";
    const country = i%2 ? "Indonesia" : "Philippines";
    const nation = i%2 ? "012" : "011";
    rows += '<tr id="tr_' + n + '" lcnsId="001" examYear="2026" examNot="' + n +
      '" examNation="' + nation + '"><td>CBT</td><td><a href="#">' + name +
      '</a></td><td>' + country +
      '</td><td>2026-02-10 ~ 2026-02-12</td><td>Undecided</td><td>Undecided</td></tr>';
  }
  return '<html><body><form><input id="pageIndex" name="pageIndex" type="hidden" value="' +
    pageNo + '"/></form><table>' + rows + '</table><div class="pagingArea">' +
    [1,2,3,4,5,6].map(n => '<a href="?pageIndex=' + n + '">' + n + '</a>').join("") +
    "</div></body></html>";
}
function officialMock({ suffix="", errorHost="" }={}) {
  let fetches = 0;
  const fn = async url => {
    fetches++;
    if (errorHost && url.includes(errorHost)) return { ok:false, status:503, url, text:async()=>"" };
    if (url.startsWith(KP)) {
      const data = JSON.stringify({ draw:1, recordsTotal:2300, recordsFiltered:2300, data:kp(suffix) });
      return {ok:true, status:200,url,text:async()=>data};
    }
    if (url.startsWith(HR)) {
      const n = Number(new URL(url).searchParams.get("pageIndex") || "1");
      return {ok:true,status:200,url,text:async()=>page(n)};
    }
    if (url.startsWith(HD)) {
      const id = new URL(url).searchParams.get("examNot");
      const city = id==="14" ? "Jakarta" : id==="15" ? "Semarang" : "Bad City";
      const data = "<html><body>HRD Korea official The 13th recruitment of the point system in Indonesia(Manufacturing)_" +
        city + " application 2026-02-10 ~ 2026-02-12 exam 2026-06-04 ~ 2026-06-29 " +
        "result announcement 2026-09-10 </body></html>";
      return {ok:true,status:200,url,text:async()=>data};
    }
    throw new Error("Unmocked external host: " + url);
  };
  return { fn, count:()=>fetches };
}
class FakeD1 {
  constructor() { this.snapshot=null; this.health=null; this.review=new Map(); }
  prepare(sql) {
    const self=this;
    return {
      bind(...params) {
        return {
          sql, params,
          async first() {
            assert.match(sql,/SELECT payload/);
            return self.snapshot ? {payload:self.snapshot.payload} : null;
          },
          async run() { return self.apply({sql,params}); }
        };
      },
      async first() {
        assert.match(sql,/SELECT payload/);
        return self.snapshot ? {payload:self.snapshot.payload} : null;
      }
    };
  }
  apply(stmt) {
    const {sql,params}=stmt;
    if (sql.includes("INSERT OR IGNORE INTO monitor_review")) {
      if (!this.review.has(params[0])) this.review.set(params[0], params);
    } else if (sql.includes("INSERT INTO monitor_snapshot")) {
      if (!this.snapshot || params[1]>this.snapshot.at) this.snapshot={payload:params[0],at:params[1]};
    } else if (sql.includes("INSERT INTO monitor_health") && sql.includes("last_success_utc")) {
      this.health={success:params[0],failure:null,count:0,error:null};
    } else if (sql.includes("INSERT INTO monitor_health") && sql.includes("last_failure_utc")) {
      this.health={success:this.health?.success||null,failure:params[0],
        count:(this.health?.count||0)+1,error:params[1]};
    } else throw new Error("UNEXPECTED_SQL");
  }
  async batch(statements) {
    // D1 real batches guarantee all-or-rollback; mock captures the intended data ops.
    for (const statement of statements) this.apply(statement);
    return statements.map(()=>({success:true}));
  }
}

test("disabled by default: no official network and no database touched", async()=>{
  const result=await processSchedule({MONITOR_ENABLED:"false"}, {fetcher:()=>{throw Error("should not fetch")}});
  assert.deepEqual(result,{status:"disabled"});
  const res=await worker.fetch();
  assert.equal(res.status,404);
});
test("scope isolation and official-only URL checks", async()=>{
  assert.throws(()=>officialUrl("http://kp2mi.go.id/gtog-data/korea/Pengumuman"),/NON_OFFICIAL/);
  assert.throws(()=>officialUrl("https://evil.invalid/path"),/NON_OFFICIAL/);
  assert.throws(()=>officialUrl("https://kp2mi.go.id.evil.invalid/"),/NON_OFFICIAL/);
  assert.throws(()=>officialUrl("https://user:pass@kp2mi.go.id/path"),/NON_OFFICIAL/);
  const recs=await kpRecords({recordsTotal:200,data:kp()});
  assert.equal(recs.length,50);
  assert.equal(recs[0].routeRelevant,true);
  assert.equal(recs[1].routeRelevant,false);
  assert.equal(JSON.stringify(recs).includes("Official notice body"),false);
  const hrd=hrdRows(page(1),1);
  assert.equal(hrd.length,8);
  assert.ok(hrd.every(x=>!x.routeRelevant));
  assert.throws(()=>hrdRows(page(2),1),/WRONG_PAGE/);
  assert.throws(()=>hrdRows(page(1).replace('href="?pageIndex=6"','href="?pageIndex=7"'),1),/PAGECOUNT/);
});
test("bounded official fetches include missing archived ID manufacturing details", async()=>{
  const fake=officialMock();
  const shot=await collect(fake.fn);
  assert.equal(shot.records.length,100);
  assert.equal(fake.count(),9); // 1 KP list + 6 HR pages + 2 indexed-away details.
  const ids=shot.records.filter(x=>x.routeRelevant && x.provider==="hrdk").map(x=>x.key).sort();
  assert.deepEqual(ids,["hrdk:012:2026:14:001","hrdk:012:2026:15:001"]);
  assert.equal((await changes(null,shot)).length,0);
  assert.equal((await changes(shot,shot)).length,0);
});
test("live shaped data first run seeds, next edits queue once, repeated revision dedups", async()=>{
  const db=new FakeD1(), env={MONITOR_ENABLED:"true",MONITOR_DB:db};
  const now=()=>new Date("2026-10-16T01:00:00.000Z");
  const a=await processSchedule(env,{fetcher:officialMock().fn,now});
  assert.equal(a.records,100); assert.equal(a.changes,0); assert.equal(db.review.size,0);
  assert.equal(db.health.count,0); assert.ok(db.snapshot);
  const changed=await processSchedule(env,{fetcher:officialMock({suffix:" updated"}).fn,now:()=>new Date("2026-10-16T03:00:00Z")});
  assert.equal(changed.changes,1); assert.equal(db.review.size,1);
  const rpt=await processSchedule(env,{fetcher:officialMock({suffix:" updated"}).fn,now:()=>new Date("2026-10-16T05:00:00Z")});
  assert.equal(rpt.changes,0); assert.equal(db.review.size,1);
  await processSchedule(env,{fetcher:officialMock().fn,now:()=>new Date("2026-10-16T07:00:00Z")});
  await processSchedule(env,{fetcher:officialMock({suffix:" updated"}).fn,now:()=>new Date("2026-10-16T09:00:00Z")});
  assert.equal(db.review.size,2); // revert is a distinct revision of same record; replay is deduped.
  assert.ok([...db.review.values()].every(x=>x[8]==="pending"));
});
test("official source failure preserves previous snapshot and increments health", async()=>{
  const db=new FakeD1(), env={MONITOR_ENABLED:"true",MONITOR_DB:db};
  await processSchedule(env,{fetcher:officialMock().fn,now:()=>new Date("2026-10-16T01:00:00Z")});
  const saved=db.snapshot.payload;
  await assert.rejects(processSchedule(env,{fetcher:officialMock({errorHost:"selectSechduleDescList.do"}).fn,
    now:()=>new Date("2026-10-16T03:00:00Z")}),/OFFICIAL_HTTP_FAILURE/);
  assert.equal(db.snapshot.payload,saved);assert.equal(db.health.count,1);
  await processSchedule(env,{fetcher:officialMock().fn,now:()=>new Date("2026-10-16T05:00:00Z")});
  assert.equal(db.health.count,0);
});
test("incomplete or invalid KP2MI JSON never creates a publishable snapshot", async()=>{
  const bad=kp().slice(0,49);
  await assert.rejects(kpRecords({data:bad,recordsTotal:2300}),/INCOMPLETE/);
  const malicious=kp(); malicious[0].judul='<a href="https://evil.invalid/fake">MANUFACTURING</a>';
  await assert.rejects(kpRecords({data:malicious,recordsTotal:2300}),/NON_OFFICIAL/);
});
