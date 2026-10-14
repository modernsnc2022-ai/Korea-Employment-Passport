#!/usr/bin/env python3
"""Offline exact-SQL D1 OTP verifier gate. Uses synthetic in-memory SQLite."""
from __future__ import annotations

import ast
import pathlib
import re
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "deployment/cloudflare/intake-worker"
VERIFIER = BASE / "email-verifier"


def extract_sql(source: str, start: str) -> str:
    part = re.split(r"\n\s*\)\.bind\(", source.split(start, 1)[1], maxsplit=1)[0]
    chunks = re.findall(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"", part)
    return "".join(ast.literal_eval(chunk) for chunk in chunks)


def check() -> None:
    source = (VERIFIER / "src/worker.js").read_text(encoding="utf-8")
    migration = (VERIFIER / "migrations/0001_email_verification.sql").read_text(encoding="utf-8")
    quota_migration = (VERIFIER / "migrations/0002_resend_daily_quota.sql").read_text(encoding="utf-8")
    config = (VERIFIER / "wrangler.toml.example").read_text(encoding="utf-8")
    resend = (VERIFIER / "wrangler.resend.toml.example").read_text(encoding="utf-8")
    intake = (BASE / "wrangler.toml.example").read_text(encoding="utf-8")
    required_source = (
        "VERIFIER_CALL_SECRET", "OTP_HMAC_SECRET", "env.EMAIL.send(",
        "consumed_at_ms IS NULL", "attempts<5",
        "requests_in_window<3", "requested_at_ms>=60000", "expires_at_ms",
        "delivery_state='sent'", "delivery_state='failed'",
    )
    for item in required_source:
        assert item in source, f"missing OTP invariant: {item}"
    for item in ('workers_dev = false', 'VERIFIER_ENABLED = "false"',
                 'name = "EMAIL"', 'binding = "OTP_DB"'):
        assert item in config, f"missing private deployment invariant: {item}"
    for item in ('workers_dev = false', 'VERIFIER_ENABLED = "false"',
                 'EMAIL_DELIVERY_PROVIDER = "resend"', 'binding = "OTP_DB"'):
        assert item in resend, f"missing free-sender fail-closed config: {item}"
    assert 'https://api.resend.com/emails' in source
    assert 'RESEND_API_KEY' in source
    assert "env.EMAIL_FROM==='noreply@mail.gdglobal.kr'" in source
    assert "env.EMAIL_FROM==='noreply@gdglobal.kr'" in source
    for item in ('binding = "EMAIL_VERIFIER"', 'service = "kep-beta-email-verifier"',
                 'INTAKE_ENABLED = "false"'):
        assert item in intake, f"missing intake binding: {item}"

    insert = extract_sql(source, "const row=await env.OTP_DB.prepare(")
    consume = extract_sql(source, "const used=await env.OTP_DB.prepare(")
    reserve_global = extract_sql(source, "const permitted=await env.OTP_DB.prepare(")
    db = sqlite3.connect(":memory:")
    db.executescript(migration)
    db.executescript(quota_migration)
    t = 1_790_000_000_000
    digest = "a" * 64

    def reserve(at: int, code: str):
        return db.execute(insert, (digest, code, at, at + 600_000, at)).fetchone()

    assert reserve(t, "1" * 64) == (digest,)
    assert reserve(t + 59_999, "2" * 64) is None
    assert reserve(t + 60_000, "2" * 64) == (digest,)
    assert reserve(t + 120_000, "3" * 64) == (digest,)
    assert reserve(t + 180_000, "4" * 64) is None
    assert db.execute("SELECT requests_in_window FROM otp_verifications").fetchone() == (3,)
    assert reserve(t + 3_600_000, "4" * 64) == (digest,)
    assert db.execute("SELECT requests_in_window FROM otp_verifications").fetchone() == (1,)
    db.execute("UPDATE otp_verifications SET delivery_state='sent' WHERE email_hmac=?", (digest,))
    assert db.execute(consume, (t + 3_600_001, digest, "0" * 64, t + 3_600_001)).fetchone() is None
    assert db.execute(consume, (t + 3_600_001, digest, "4" * 64, t + 3_600_001)).fetchone() == (digest,)
    assert db.execute(consume, (t + 3_600_002, digest, "4" * 64, t + 3_600_002)).fetchone() is None
    day = t // 86_400_000
    for n in range(90):
        assert db.execute(reserve_global, (day,)).fetchone() == (n + 1,)
    for _ in range(10):
        assert db.execute(reserve_global, (day,)).fetchone() is None
    assert db.execute("SELECT requested_count FROM otp_resend_daily_quota WHERE day_utc=?",
                      (day,)).fetchone() == (90,)
    assert db.execute(reserve_global, (day+1,)).fetchone() == (1,)
    db.close()
    print("KEP_OTP_REAL_SQLITE_PASS atomic_hourly_limit_one_time_consume_resend_daily_90_private_disabled")


if __name__ == "__main__":
    check()
