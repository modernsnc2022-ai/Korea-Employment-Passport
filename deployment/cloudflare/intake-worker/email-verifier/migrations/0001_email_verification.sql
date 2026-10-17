-- Pseudonymous keyed digests only. No email address or OTP plaintext.
CREATE TABLE IF NOT EXISTS otp_verifications (
  email_hmac TEXT PRIMARY KEY NOT NULL CHECK(length(email_hmac)=64),
  code_hmac TEXT NOT NULL CHECK(length(code_hmac)=64),
  requested_at_ms INTEGER NOT NULL,
  expires_at_ms INTEGER NOT NULL,
  window_started_ms INTEGER NOT NULL,
  requests_in_window INTEGER NOT NULL CHECK(requests_in_window BETWEEN 1 AND 3),
  attempts INTEGER NOT NULL CHECK(attempts BETWEEN 0 AND 5),
  delivery_state TEXT NOT NULL CHECK(delivery_state IN ('pending','sent','failed')),
  consumed_at_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_otp_requests_expiry ON otp_verifications(requested_at_ms);
