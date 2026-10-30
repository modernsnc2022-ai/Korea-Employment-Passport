// Independent watchdog for source-specific scan freshness, not a notice scanner.
// No HTTP fetch, applicant data, operator outbound alert or source approval.
const SOURCES = ["kp2mi", "hrdk"];
const DEFAULT_MAX_AGE_HOURS = 4;
const CLOCK_SKEW_MS = 2 * 60_000;

export function evaluateSource(sourceId, health, nowValue, maxAgeHours=DEFAULT_MAX_AGE_HOURS) {
  if (!SOURCES.includes(sourceId)) throw new Error("UNKNOWN_MONITOR_SOURCE");
  if (!Number.isInteger(maxAgeHours) || maxAgeHours < 1 || maxAgeHours > 24)
    throw new Error("INVALID_STALE_LIMIT");
  const at = new Date(nowValue);
  if (Number.isNaN(at.valueOf())) throw new Error("INVALID_WATCHDOG_TIME");
  const reasons = [];
  if (!health) {
    reasons.push("never_observed");
  } else {
    const failures = Number(health.consecutive_failures);
    if (!Number.isSafeInteger(failures) || failures < 0) throw new Error("BAD_FAILURE_COUNT");
    if (failures > 0) reasons.push("source_fetch_failed");
    if (!health.last_success_utc) {
      reasons.push("never_succeeded");
    } else {
      const success = new Date(health.last_success_utc);
      if (Number.isNaN(success.valueOf())) throw new Error("BAD_LAST_SUCCESS_TIME");
      const elapsed = at.valueOf() - success.valueOf();
      if (elapsed < -CLOCK_SKEW_MS) reasons.push("future_clock_skew");
      else if (elapsed > maxAgeHours * 3_600_000) reasons.push("stale_success");
    }
  }
  return { sourceId, status: reasons.length ? "degraded" : "healthy",
    reasonCode: reasons.length ? reasons.join("+") : "none" };
}

export function statusTransitions(previous, current) {
  if (!previous) return current.status === "degraded" ? "opened" : null;
  if (previous.status !== "healthy" && previous.status !== "degraded")
    throw new Error("INVALID_PREVIOUS_WATCHDOG_STATE");
  if (previous.status === "healthy" && current.status === "degraded") return "opened";
  if (previous.status === "degraded" && current.status === "healthy") return "recovered";
  if (previous.status === "degraded" && current.status === "degraded" &&
      previous.reason_code !== current.reasonCode) return "updated";
  return null;
}

export async function runWatchdog(env, deps={}) {
  if (env.MONITOR_WATCHDOG_ENABLED !== "true") return { status: "disabled" };
  if (!env.MONITOR_DB) throw new Error("WATCHDOG_DATABASE_NOT_BOUND");
  const hours = env.MONITOR_STALE_HOURS === undefined
    ? DEFAULT_MAX_AGE_HOURS : Number(env.MONITOR_STALE_HOURS);
  if (!Number.isInteger(hours) || hours < 1 || hours > 24)
    throw new Error("INVALID_STALE_LIMIT");
  const at = (deps.now || (() => new Date()))();
  const now = new Date(at);
  if (Number.isNaN(now.valueOf())) throw new Error("INVALID_WATCHDOG_TIME");
  const checkedAt = now.toISOString(), db = env.MONITOR_DB;
  // These reads come only from the dedicated official-monitor D1.
  const [healthRows, states] = await Promise.all([
    db.prepare("SELECT source_id,last_success_utc,last_failure_utc,consecutive_failures,error_kind FROM monitor_source_health").all(),
    db.prepare("SELECT source_id,status,reason_code,last_checked_utc FROM monitor_watchdog_state").all()
  ]);
  if (!Array.isArray(healthRows?.results) || !Array.isArray(states?.results))
    throw new Error("INVALID_WATCHDOG_D1_RESULTS");
  const sourceMap = new Map();
  const stateMap = new Map();
  for (const row of healthRows.results) {
    if (!SOURCES.includes(row.source_id) || sourceMap.has(row.source_id))
      throw new Error("INVALID_SOURCE_HEALTH_ROW");
    sourceMap.set(row.source_id, row);
  }
  for (const row of states.results) {
    if (!SOURCES.includes(row.source_id) || stateMap.has(row.source_id))
      throw new Error("INVALID_WATCHDOG_STATE_ROW");
    stateMap.set(row.source_id, row);
  }
  const statements=[], transitions=[], evaluations=[];
  for (const sourceId of SOURCES) {
    const computed = evaluateSource(sourceId, sourceMap.get(sourceId), now, hours);
    evaluations.push(computed);
    const old = stateMap.get(sourceId), action = statusTransitions(old, computed);
    if (old && new Date(old.last_checked_utc).valueOf() > now.valueOf() + CLOCK_SKEW_MS)
      throw new Error("WATCHDOG_STATE_FROM_FUTURE");
    if (action) {
      statements.push(db.prepare(
        "INSERT INTO monitor_watchdog_events(source_id,event_kind,reason_code,observed_utc) VALUES(?,?,?,?)"
      ).bind(sourceId,action,computed.reasonCode,checkedAt));
      transitions.push({sourceId,kind:action,reasonCode:computed.reasonCode});
    }
    statements.push(db.prepare(
      "INSERT INTO monitor_watchdog_state(source_id,status,reason_code,last_checked_utc,last_changed_utc) VALUES(?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET status=excluded.status,reason_code=excluded.reason_code,last_checked_utc=excluded.last_checked_utc,last_changed_utc=CASE WHEN monitor_watchdog_state.status<>excluded.status OR monitor_watchdog_state.reason_code<>excluded.reason_code THEN excluded.last_changed_utc ELSE monitor_watchdog_state.last_changed_utc END"
    ).bind(sourceId,computed.status,computed.reasonCode,checkedAt,checkedAt));
  }
  // D1 batch guarantees transition events and current-state status stay atomic.
  await db.batch(statements);
  return { status: evaluations.some(x=>x.status==="degraded") ? "degraded" : "healthy",
    evaluatedAtUtc:checkedAt, sources:evaluations, transitions, deliveredNotifications:0,
    acceptedSourceHashes:0, betaOpened:false };
}
export default {
  async fetch() {return new Response("Not Found",{status:404});},
  async scheduled(_controller, env,ctx) {
    ctx.waitUntil(runWatchdog(env).then(r=>{
      console.log("KEP_MONITOR_WATCHDOG",JSON.stringify(r));
      if(r.status==="degraded") throw new Error("MONITOR_WATCHDOG_DEGRADED");
    }));
  }
};
