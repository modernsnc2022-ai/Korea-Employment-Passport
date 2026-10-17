#!/usr/bin/env python3
"""Local durable, fail-closed observation queue for KEP official discovery.

This is NOT a release approval store and never accepts official-source hashes.
Only a read-only scanner may call record_success with a *complete* observation.
SQLite lives outside the Git worktree and is never a public applicant database.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

SCHEMA = "kep-id-official-discovery-v1"


def safe_external_path(path: Path, repo: Path) -> Path:
    destination = path.resolve()
    root = repo.resolve()
    if destination == root or root in destination.parents:
        raise ValueError("Operational observations cannot be written into tracked repo")
    if destination.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("Operational observations require a SQLite database path")
    if not destination.parent.is_dir():
        raise ValueError("Explicit external SQLite parent directory must exist")
    return destination


def utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Observation must include UTC timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None or dt.utcoffset().total_seconds() != 0:
        raise ValueError("Observation timestamp must be UTC and timezone-aware")
    return dt


def validated_snapshot(value: dict) -> None:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("Unknown or missing observation schema")
    if set(value.get("sourcesComplete", [])) != {"kp2mi", "hrdk"}:
        raise ValueError("Incomplete official source observation")
    if value.get("sourceHashAutoAccepted") is not False or value.get("betaOpenAuthorized") is not False:
        raise ValueError("Only unsigned, non-release observations are allowed")
    utc(value.get("observedAtUtc"))
    rows = value.get("records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Missing official source records")
    keys = set()
    providers = set()
    for row in rows:
        if not isinstance(row, dict) or not row.get("key") or not row.get("url"):
            raise ValueError("Invalid row in discovery observation")
        if row["key"] in keys:
            raise ValueError("Duplicate official source observation identity")
        keys.add(row["key"])
        p = str(row.get("provider", ""))
        if p not in {"kp2mi", "hrdk"} or not str(row["key"]).startswith(p + ":"):
            raise ValueError("Bad provider/source identity mapping")
        providers.add(p)
    if providers != {"kp2mi", "hrdk"}:
        raise ValueError("Both source categories must be represented")


@contextmanager
def connect(path: Path):
    db = sqlite3.connect(str(path), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS checkpoint (
        only_row INTEGER PRIMARY KEY CHECK(only_row=1),
        last_snapshot_json TEXT NOT NULL,
        last_observed_utc TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS review_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_revision TEXT UNIQUE NOT NULL,
        provider_key TEXT NOT NULL,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        review_required INTEGER NOT NULL CHECK(review_required=1),
        route_relevant INTEGER NOT NULL,
        possible_final_application INTEGER NOT NULL,
        first_seen_utc TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status='pending')
    );
    CREATE TABLE IF NOT EXISTS monitor_health (
        only_row INTEGER PRIMARY KEY CHECK(only_row=1),
        last_success_utc TEXT,
        last_failure_utc TEXT,
        consecutive_failures INTEGER NOT NULL DEFAULT 0,
        last_failure_summary TEXT
    );
    """)
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def record_success(path: Path, current: dict, diff_fn) -> dict:
    validated_snapshot(current)
    now_utc = current["observedAtUtc"]
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        last = db.execute("SELECT last_snapshot_json,last_observed_utc FROM checkpoint WHERE only_row=1").fetchone()
        old = json.loads(last["last_snapshot_json"]) if last else None
        if old:
            validated_snapshot(old)
            if utc(now_utc) <= utc(last["last_observed_utc"]):
                raise ValueError("Stale/nonmonotonic official observation timestamp")
        result = diff_fn(old, current)
        fresh = 0
        for event in result["events"]:
            key = event["key"]
            item = next((x for x in current["records"] if x["key"] == key), None)
            if item is None or not event["needsHumanReview"]:
                raise ValueError("Invalid review event outside full observation")
            stamp = hashlib.sha256(json.dumps(
                {"key": key, "kind": event["kind"], "data": item},
                sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            inserted = db.execute("""INSERT OR IGNORE INTO review_queue
                 (unique_revision,provider_key,kind,title,url,review_required,
                  route_relevant,possible_final_application,first_seen_utc)
                  VALUES(?,?,?,?,?,?,?,?,?)""", (
                stamp, key, event["kind"], event["title"], event["url"], 1,
                int(event["routeRelevant"]), int(event["maybeFinalApplication"]), now_utc
            ))
            fresh += inserted.rowcount
        db.execute("""INSERT INTO checkpoint(only_row,last_snapshot_json,last_observed_utc)
            VALUES(1,?,?) ON CONFLICT(only_row) DO UPDATE SET
              last_snapshot_json=excluded.last_snapshot_json,
              last_observed_utc=excluded.last_observed_utc""",
                   (json.dumps(current, ensure_ascii=False, sort_keys=True), now_utc))
        db.execute("""INSERT INTO monitor_health(only_row,last_success_utc,consecutive_failures,
                      last_failure_summary)
                      VALUES(1,?,0,NULL) ON CONFLICT(only_row) DO UPDATE SET
                      last_success_utc=excluded.last_success_utc,
                      consecutive_failures=0,last_failure_summary=NULL""",
                   (now_utc,))
        count = db.execute("SELECT COUNT(*) FROM review_queue").fetchone()[0]
    return {"firstRun": result["initial"], "eventsDetected": len(result["events"]),
            "newQueued": fresh, "pendingTotal": count,
            "notSeenInBoundedWindow": result.get("notSeenInBoundedWindow", 0),
            "autopublished": False}


def record_failure(path: Path, error: Exception, *, at: str | None = None) -> int:
    stamp = at or datetime.now(timezone.utc).isoformat()
    utc(stamp)
    # Do not log exception URLs (which could include untrusted query or applicant data).
    summary = type(error).__name__
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""INSERT INTO monitor_health
             (only_row,last_failure_utc,consecutive_failures,last_failure_summary)
             VALUES(1,?,1,?)
             ON CONFLICT(only_row) DO UPDATE SET
             last_failure_utc=excluded.last_failure_utc,
             consecutive_failures=monitor_health.consecutive_failures+1,
             last_failure_summary=excluded.last_failure_summary""", (stamp, summary))
        failures = db.execute("SELECT consecutive_failures FROM monitor_health WHERE only_row=1").fetchone()[0]
    return failures


def pending_events(path: Path, limit: int = 20) -> list[dict]:
    if not (1 <= limit <= 100):
        raise ValueError("Pending queue limit must be 1..100")
    with connect(path) as db:
        rows = db.execute("""SELECT provider_key,kind,title,url,route_relevant,
                possible_final_application,first_seen_utc FROM review_queue
                WHERE status='pending'
                ORDER BY route_relevant DESC, possible_final_application DESC,id DESC
                LIMIT ?""", (limit,)).fetchall()
    return [dict(row) for row in rows]


def health(path: Path, *, at: str | None = None, stale_hours: int = 4) -> dict:
    if not (1 <= stale_hours <= 168):
        raise ValueError("stale_hours must be 1..168")
    now = utc(at or datetime.now(timezone.utc).isoformat())
    with connect(path) as db:
        row = db.execute("SELECT * FROM monitor_health WHERE only_row=1").fetchone()
    last_success = row["last_success_utc"] if row else None
    failure_count = row["consecutive_failures"] if row else 0
    stale = not last_success or (now - utc(last_success)).total_seconds() > stale_hours * 3600
    if last_success and now < utc(last_success):
        stale = True
    return {"healthy": bool(not stale and not failure_count),
            "lastSuccessUtc": last_success,
            "lastFailureUtc": row["last_failure_utc"] if row else None,
            "consecutiveFailures": failure_count,
            "stale": bool(stale),
            "lastFailureSummary": row["last_failure_summary"] if row else None}


if __name__ == "__main__":
    raise SystemExit("Import this module from the read-only watcher; no scheduling/approval here")
