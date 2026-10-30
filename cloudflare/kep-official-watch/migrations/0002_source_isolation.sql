-- Independent HRD Korea and KP2MI checkpoints: one origin outage never silently
-- suppresses the other origin's verified changes.
-- These are monitoring observations only, NOT accepted official policy baselines.
CREATE TABLE IF NOT EXISTS monitor_source_snapshot (
 source_id TEXT PRIMARY KEY CHECK(source_id IN ('kp2mi','hrdk')),
 payload TEXT NOT NULL,
 checked_at_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitor_source_health (
 source_id TEXT PRIMARY KEY CHECK(source_id IN ('kp2mi','hrdk')),
 last_success_utc TEXT,
 last_failure_utc TEXT,
 consecutive_failures INTEGER NOT NULL DEFAULT 0,
 error_kind TEXT
);
