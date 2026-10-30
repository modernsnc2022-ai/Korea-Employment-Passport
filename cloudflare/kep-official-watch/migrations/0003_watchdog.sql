-- Dedicated monitor-only, append-only health transition audit.
-- This does not approve official sources or expose applicant data.
CREATE TABLE IF NOT EXISTS monitor_watchdog_state (
 source_id TEXT PRIMARY KEY CHECK (source_id IN ('kp2mi','hrdk')),
 status TEXT NOT NULL CHECK (status IN ('healthy','degraded')),
 reason_code TEXT NOT NULL,
 last_checked_utc TEXT NOT NULL,
 last_changed_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitor_watchdog_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 source_id TEXT NOT NULL CHECK (source_id IN ('kp2mi','hrdk')),
 event_kind TEXT NOT NULL CHECK (event_kind IN ('opened','updated','recovered')),
 reason_code TEXT NOT NULL,
 observed_utc TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS monitor_watchdog_events_time
 ON monitor_watchdog_events(observed_utc,source_id);
