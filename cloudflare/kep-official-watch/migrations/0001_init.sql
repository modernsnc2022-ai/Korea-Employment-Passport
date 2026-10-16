-- Dedicated KEP official-change monitor. Never bind applicant/OTP databases here.
CREATE TABLE IF NOT EXISTS monitor_snapshot (
 id INTEGER PRIMARY KEY CHECK(id=1),
 payload TEXT NOT NULL,
 checked_at_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitor_review (
 revision_id TEXT PRIMARY KEY,
 source_key TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('new','changed')),
 title TEXT NOT NULL,
 url TEXT NOT NULL,
 scope_relevant INTEGER NOT NULL CHECK(scope_relevant IN (0,1)),
 possible_application INTEGER NOT NULL CHECK(possible_application IN (0,1)),
 first_seen_utc TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status='pending')
);
CREATE INDEX IF NOT EXISTS monitor_review_pending ON monitor_review(status,scope_relevant,first_seen_utc);
CREATE TABLE IF NOT EXISTS monitor_health (
 id INTEGER PRIMARY KEY CHECK(id=1),
 last_success_utc TEXT,
 last_failure_utc TEXT,
 consecutive_failures INTEGER NOT NULL DEFAULT 0,
 error_kind TEXT
);
