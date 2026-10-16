-- GitHub operator-alert outbox. Distinct from applicant/OTP data and accepted-source hashes.
-- Event keys are unique. Sending states require operator reconciliation after ambiguous failures.
CREATE TABLE IF NOT EXISTS monitor_alert_outbox (
 event_key TEXT PRIMARY KEY,
 channel TEXT NOT NULL CHECK(channel='github-issue-comment'),
 body TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','sending','sent','reconcile_required')),
 attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts BETWEEN 0 AND 10),
 first_seen_utc TEXT NOT NULL,
 claimed_utc TEXT,
 delivered_utc TEXT,
 github_comment_id INTEGER,
 last_failure_code TEXT
);
CREATE INDEX IF NOT EXISTS monitor_alert_pending ON monitor_alert_outbox(status,first_seen_utc);
