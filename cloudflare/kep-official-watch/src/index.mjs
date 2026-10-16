// KEP independent official source change watcher. Disabled until separately approved.
// Never opens beta, sends messages, accepts official source hashes or reads applicant D1.
const KP = "https://kp2mi.go.id/gtog-data/korea/Pengumuman";
const HR = "https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/selectSechduleDescList.do";
const HD = "https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/sechduleDetail.do";
const ALLOWED = new Set(["kp2mi.go.id", "epstopik.hrdkorea.or.kr"]);
const WINDOW = 50, HR_PAGES = 6, VERSION = "kep-cloudflare-watch-v1";
// Named exports must be callable handlers in workerd; do not export raw strings.
export function sourceUrls() { return { KP, HR, HD }; }

export function officialUrl(value) {
  const u = new URL(value);
  if (u.protocol !== "https:" || !ALLOWED.has(u.hostname) || u.username || u.password ||
      (u.port && u.port !== "443")) throw new Error("NON_OFFICIAL_URL");
  return u.toString();
}
function plain(html) {
  return String(html).replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]*>/g, " ").replace(/&nbsp;|&#160;/gi, " ")
    .replace(/&amp;/gi, "&").replace(/&quot;/gi, '"')
    .replace(/\s+/g, " ").trim();
}
async function digest(value) {
  const bytes = new TextEncoder().encode(value);
  const arr = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return Array.from(arr, b => b.toString(16).padStart(2, "0")).join("");
}
async function officialText(url, fetcher) {
  const expected = officialUrl(url);
  const r = await fetcher(expected, { redirect: "manual", method: "GET",
    headers: { "Accept-Language": "en,id;q=0.9,ko;q=0.8" },
    signal: AbortSignal.timeout(12000) });
  if (r.status >= 300 && r.status < 400) throw new Error("OFFICIAL_REDIRECT_BLOCKED");
  if (!r.ok) throw new Error("OFFICIAL_HTTP_FAILURE");
  if (r.url && officialUrl(r.url) !== expected) throw new Error("OFFICIAL_REDIRECT");
  const txt = await r.text();
  if (txt.length < 100 || txt.length > 5000000) throw new Error("OFFICIAL_RESPONSE_SIZE");
  return txt;
}
export async function kpRecords(data) {
  if (!data || !Array.isArray(data.data) || data.data.length !== WINDOW ||
      Number(data.recordsTotal) < WINDOW) throw new Error("KP_INCOMPLETE_WINDOW");
  const result = [], ids = new Set();
  for (const row of data.data) {
    if (!Number.isSafeInteger(row.id) || typeof row.judul !== "string") throw new Error("KP_BAD_ROW");
    const match = row.judul.match(/<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/i);
    if (!match) throw new Error("KP_MISSING_DETAIL_LINK");
    const url = officialUrl(new URL(match[1], "https://kp2mi.go.id").toString());
    if (!new URL(url).pathname.startsWith("/gtog-detail/korea/")) throw new Error("KP_WRONG_DETAIL");
    const title = plain(match[2]), key = "kp2mi:" + row.id;
    if (!title || ids.has(key)) throw new Error("KP_EMPTY_OR_DUPLICATE");
    ids.add(key);
    const text = plain(row.gtgkorea || "").replace(/\b(?:views|hits)\s*:?\s*\d+/gi, "views [count]");
    result.push({ key, provider: "kp2mi", title, url,
      date: String(row.tanggal || "").slice(0, 80), bodyDigest: await digest(text),
      routeRelevant: /manufactur|manufaktur/i.test(title) && /2026/.test(title) &&
        !/khusus|root industry|mold/i.test(title),
      possibleApplication: /lamaran|job application|pendaftaran online/i.test(title) &&
        !/khusus|root industry|mold/i.test(title) });
  }
  return result;
}
function attr(tag, name) {
  const match = tag.match(new RegExp("\\b" + name + '="([^"]+)"', "i"));
  return match && match[1];
}
export function hrdRows(html, page) {
  const input = html.match(/<input\b[^>]*\bid="pageIndex"[^>]*>/i);
  if (!input || Number(attr(input[0], "value")) !== page) throw new Error("HR_WRONG_PAGE");
  const pages = [...html.matchAll(/\?pageIndex=(\d+)/g)].map(x => Number(x[1]));
  if (pages.some(n => n < 1 || n > HR_PAGES)) throw new Error("HR_PAGECOUNT_CHANGED");
  const out = [];
  for (const m of html.matchAll(/<tr\b([^>]*\bid="tr_\d+"[^>]*)>([\s\S]*?)<\/tr>/gi)) {
    const nation = attr(m[1], "examNation"), year = attr(m[1], "examYear"),
      examNo = attr(m[1], "examNot"), lcns = attr(m[1], "lcnsId");
    const cells = [...m[2].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)].map(x => plain(x[1]));
    if (!nation || !year || !examNo || !lcns || cells.length !== 6) throw new Error("HR_BAD_ROW");
    const key = "hrdk:" + [nation, year, examNo, lcns].join(":");
    const url = officialUrl(HD + "?" + new URLSearchParams({
      examNation: nation, examNot: examNo, examYear: year, lang: "ko", lcnsId: lcns
    }));
    out.push({ key, provider: "hrdk", nation, year, examNo, lcns, title: cells[1],
      url, type: cells[0], country: cells[2], applicationDates: cells[3],
      examDates: cells[4], resultDates: cells[5],
      routeRelevant: nation === "012" && year === "2026" &&
        /indonesia/i.test(cells[1]) && /manufacturing/i.test(cells[1]) &&
        !/root industry|mold|special|khusus/i.test(cells[1]),
      possibleApplication: false });
  }
  if (out.length < 1 || out.length > 20) throw new Error("HR_NO_ROWS");
  return out;
}
export async function collect(fetcher = fetch) {
  const params = new URLSearchParams({ draw: "1", start: "0", length: String(WINDOW),
    "search[value]": "", "search[regex]": "false" });
  const kp = await kpRecords(JSON.parse(await officialText(KP + "?" + params, fetcher)));
  const hrd = [];
  for (let p = 1; p <= HR_PAGES; p++) {
    const u = HR + "?" + new URLSearchParams({ lang: "en", pageIndex: String(p) });
    hrd.push(...hrdRows(await officialText(u, fetcher), p));
  }
  if (new Set(hrd.map(x => x.key)).size !== hrd.length) throw new Error("HR_DUPLICATE_ID");
  for (const [examNo, city] of [["14", "Jakarta"], ["15", "Semarang"]]) {
    const key = "hrdk:012:2026:" + examNo + ":001";
    if (!hrd.some(x => x.key === key)) {
      const url = officialUrl(HD + "?" + new URLSearchParams({
        examNation: "012", examNot: examNo, examYear: "2026", lang: "ko", lcnsId: "001" }));
      const detail = plain(await officialText(url, fetcher));
      if (!detail.includes("Indonesia(Manufacturing)_" + city) ||
          !/2026-\d\d-\d\d/.test(detail)) throw new Error("HR_DETAIL_MISSING");
      hrd.push({ key, provider: "hrdk", nation: "012", year: "2026", examNo,
        lcns: "001", title: "Indonesia(Manufacturing)_" + city, url,
        detailDates: [...new Set(detail.match(/2026-\d\d-\d\d/g))].sort(),
        routeRelevant: true, possibleApplication: false });
    }
  }
  const records = [...kp, ...hrd].sort((a, b) => a.key.localeCompare(b.key));
  if (records.length < 90 || !records.some(x => x.provider === "hrdk" && x.routeRelevant))
    throw new Error("INCOMPLETE_OFFICIAL_OBSERVATION");
  return { version: VERSION, sources: ["kp2mi", "hrdk"], records };
}
export async function changes(previous, current) {
  if (!current || current.version !== VERSION || current.sources.join(",") !== "kp2mi,hrdk" ||
      current.records.length < 90) throw new Error("BAD_CURRENT_SNAPSHOT");
  if (!previous) return [];  // First scan seeds historical data, no alarm flood.
  if (previous.version !== VERSION || previous.sources.join(",") !== "kp2mi,hrdk") {
    throw new Error("BAD_PREVIOUS_SNAPSHOT");
  }
  const old = new Map(previous.records.map(x => [x.key, x]));
  const result = [];
  for (const x of current.records) {
    const earlier = old.get(x.key);
    if (earlier && JSON.stringify(earlier) === JSON.stringify(x)) continue;
    result.push({ ...x, kind: earlier ? "changed" : "new",
      revision: await digest(JSON.stringify(x)), needsHumanReview: true });
  }
  // An old notice leaving the bounded 50-row index is not official retraction.
  return result;
}
export async function processSchedule(env, deps = {}) {
  if (env.MONITOR_ENABLED !== "true") return { status: "disabled" };
  if (!env.MONITOR_DB) throw new Error("MONITOR_DB_NOT_BOUND");
  const db = env.MONITOR_DB, when = (deps.now || (() => new Date()))().toISOString();
  try {
    const snapshot = await collect(deps.fetcher || fetch);
    const stored = await db.prepare("SELECT payload FROM monitor_snapshot WHERE id=1").first();
    const events = await changes(stored ? JSON.parse(stored.payload) : null, snapshot);
    const work = events.map(e => db.prepare(
      "INSERT OR IGNORE INTO monitor_review(revision_id,source_key,kind,title,url,scope_relevant,possible_application,first_seen_utc,status) VALUES(?,?,?,?,?,?,?,?,?)"
    ).bind(e.revision, e.key, e.kind, e.title.slice(0, 320), e.url,
      e.routeRelevant ? 1 : 0, e.possibleApplication ? 1 : 0, when, "pending"));
    work.push(db.prepare(
      "INSERT INTO monitor_snapshot(id,payload,checked_at_utc) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,checked_at_utc=excluded.checked_at_utc WHERE excluded.checked_at_utc>monitor_snapshot.checked_at_utc"
    ).bind(JSON.stringify(snapshot), when));
    work.push(db.prepare(
      "INSERT INTO monitor_health(id,last_success_utc,consecutive_failures,error_kind) VALUES(1,?,0,NULL) ON CONFLICT(id) DO UPDATE SET last_success_utc=excluded.last_success_utc,consecutive_failures=0,error_kind=NULL"
    ).bind(when));
    await db.batch(work); // D1 batch transaction: roll back all on failure.
    return { status: "ok", records: snapshot.records.length, changes: events.length,
      notified: 0, published: false };
  } catch (err) {
    try {
      await db.prepare(
        "INSERT INTO monitor_health(id,last_failure_utc,consecutive_failures,error_kind) VALUES(1,?,1,?) ON CONFLICT(id) DO UPDATE SET last_failure_utc=excluded.last_failure_utc,consecutive_failures=monitor_health.consecutive_failures+1,error_kind=excluded.error_kind"
      ).bind(when, err instanceof Error ? err.name : "Unknown").run();
    } catch { /* Do not hide the initial failure. */ }
    throw err;
  }
}
export default {
  async fetch() { return new Response("Not Found", { status: 404 }); },
  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(processSchedule(env).then(x => console.log("KEP_WATCH", JSON.stringify(x))));
  }
};
