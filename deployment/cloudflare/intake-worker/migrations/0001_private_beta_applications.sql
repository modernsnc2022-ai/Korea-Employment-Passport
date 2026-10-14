-- KEP 2026 Indonesia beta applicant interest ONLY. Never place user rows in Git.
-- Identity-linked data lives in a private Cloudflare D1 instance. The HMAC
-- secret is a Worker secret, not a source file, DB column or public hash.
CREATE TABLE IF NOT EXISTS beta_applications (
  email_hmac TEXT NOT NULL PRIMARY KEY,
  submission_id TEXT NOT NULL UNIQUE,
  contact_email TEXT NOT NULL,
  stage_id TEXT NOT NULL,
  route_cycle TEXT NOT NULL,
  source_code TEXT NOT NULL,
  received_at_ms INTEGER NOT NULL,
  expires_at_ms INTEGER NOT NULL,
  CHECK(length(email_hmac)=64),
  CHECK(length(submission_id) BETWEEN 12 AND 54),
  CHECK(length(contact_email)<=254),
  CHECK(expires_at_ms>received_at_ms)
);
CREATE INDEX IF NOT EXISTS idx_beta_applications_expires_at
  ON beta_applications(expires_at_ms);
