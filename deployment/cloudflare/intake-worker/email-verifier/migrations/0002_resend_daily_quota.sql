-- Free-tier safeguard. At most 90 attempted Resend sends per UTC day.
-- A 31-day month is at most 2790 requests, below the 3000/month Free quota.
-- Records are global counters: no applicant identifiers, email, IP or OTP.
CREATE TABLE IF NOT EXISTS otp_resend_daily_quota (
  day_utc INTEGER PRIMARY KEY NOT NULL,
  requested_count INTEGER NOT NULL CHECK(requested_count BETWEEN 1 AND 90)
);
