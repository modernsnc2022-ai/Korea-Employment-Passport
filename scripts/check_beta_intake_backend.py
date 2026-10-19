#!/usr/bin/env python3
"""Offline Cloudflare beta-intake D1 integrity + real SQLite atomic UPSERT QA.

No Cloudflare resources, applicant data or URLs are accessed. All rows are
synthetic and the database exists only in SQLite memory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def input_files(root: Path = ROOT) -> tuple[str, str, str, dict, str, str]:
    base = root / "deployment/cloudflare/intake-worker"
    return (
        (base / "src/worker.js").read_text(encoding="utf-8"),
        (base / "wrangler.toml.example").read_text(encoding="utf-8"),
        (base / "migrations/0001_private_beta_applications.sql").read_text(encoding="utf-8"),
        json.loads((root / "docs/data/beta_program_v1.json").read_text(encoding="utf-8")),
        (root / "docs/beta.js").read_text(encoding="utf-8"),
        (root / "docs/beta.html").read_text(encoding="utf-8"),
    )


def errors(worker: str, config: str, schema: str, program: dict, frontend: str,
           html: str) -> list[str]:
    issues = []
    direct = program["application"]["directIntake"]
    if direct["provider"] != "cloudflare_workers_d1":
        issues.append("provider must be Cloudflare private D1")
    if direct["retentionDays"] != 90 or program["privacy"]["directIntakeRetentionDays"] != 90:
        issues.append("applicant private intake retention must be exactly 90 days")
    if direct.get("endpoint") and not direct.get("turnstileSiteKey"):
        issues.append("HTTPS endpoint cannot be enabled without public Turnstile site key")
    if direct.get("releaseDecision") not in ("hold", "approved_manual"):
        issues.append("direct HTTPS intake requires an explicit HOLD or approved_manual decision")
    if direct.get("releaseDecision") == "approved_manual" and (
        not direct.get("approvedAt") or not direct.get("endpoint") or not direct.get("turnstileSiteKey")
    ):
        issues.append("manual direct intake requires a dated approval and configured HTTPS challenge")
    if program["status"] != "hold" or program["application"]["intakeStatus"] != "open":
        issues.append("pre-release beta HOLD / interest intake OPEN mismatch")
    for token in ("KEP_BETA_DB","email_hmac","TURNSTILE_SECRET","INTAKE_HMAC_SECRET",
                  "INTAKE_ENABLED","expires_at_ms","90*24*60*60*1000",
                  "ON CONFLICT(email_hmac) DO UPDATE","confirmTurnstile",
                  "data.hostname.toLowerCase()===host","remoteip"):
        if token not in worker:
            issues.append("Worker missing security invariant: "+token)
    if re.search(r"\bKEP_BETA_APPLICATIONS\b", worker):
        issues.append("Worker still uses non-atomic KV applicant storage")
    for token in ('INTAKE_ENABLED = "false"', "binding = \"KEP_BETA_DB\"",
                  'crons = ["0 3 * * *"]'):
        if token not in config:
            issues.append("safe Worker deployment template missing "+token)
    # A CAPTCHA protects the form from some bots, not the identity behind an
    # email address. Without an authenticated private verifier binding, no
    # existing receipt may be returned for a guessed email.
    for invariant in ("EMAIL_VERIFIER?.fetch", "VERIFIER_CALL_SECRET",
                      "privateEmailProof",
                      "email_verification_required", "verificationCode",
                      "verify-request"):
        # The literal route constant is distinct from the UI URL.
        search = "VERIFY_REQUEST_ROUTE" if invariant=="verify-request" else invariant
        if search not in worker:
            issues.append("direct receipt must require private email proof: "+invariant)
    if "    && Boolean(env.EMAIL_VERIFIER?.fetch)" not in worker:
        issues.append("private email proof must fail closed before request acceptance")
    if "body.verificationCode" not in frontend or "applicantEmailCodeFields" not in html:
        issues.append("browser lacks explicit confirmation code before a direct receipt")
    if "email_hmac TEXT NOT NULL PRIMARY KEY" not in schema or "submission_id TEXT NOT NULL UNIQUE" not in schema:
        issues.append("D1 must enforce real dedup and receipt uniqueness")
    if "WHERE expires_at_ms<=?" not in worker:
        issues.append("scheduled deletion must use bounded 90-day expiry")
    if "function directIntakeEnabled()" not in frontend or "turnstileSiteKey()" not in frontend:
        issues.append("frontend must fail closed without approved Turnstile site key")
    if "direct.releaseDecision!=='approved_manual'" not in frontend or "direct.approvedAt" not in frontend:
        issues.append("frontend must fail closed without dated, manual direct-intake authorization")
    if "turnstileToken:intakeTurnstileToken" not in frontend:
        issues.append("frontend must include server-verified challenge token")
    if "id=\"directIntakeChallenge\"" not in html:
        issues.append("frontend lacks accessible direct-intake challenge")
    return issues


def sql_upsert_from_worker(worker: str) -> str:
    # Rebuild the literal SQL expression actually sent to D1, rather than
    # separately testing a subtly different copy of the UPSERT statement.
    part = worker.split("const statement=env.KEP_BETA_DB.prepare(", 1)[1].split(
        "\n  );", 1
    )[0]
    chunks = re.findall(r"'([^']*)'", part)
    if len(chunks) < 3:
        raise AssertionError("D1 UPSERT SQL expression not extractable")
    return "".join(chunks)


def sqlite_test(schema: str, statement: str) -> None:
    db = sqlite3.connect(":memory:")
    db.executescript(schema)
    indexes = {x[1] for x in db.execute("PRAGMA index_list('beta_applications')")}
    assert "idx_beta_applications_expires_at" in indexes
    now = 1_760_000_000_000
    expiry = now + 90 * 86400 * 1000

    def insert(email_key: str, receipt: str, at: int, ttl: int):
        return db.execute(
            statement,
            (email_key, receipt, "test@example.invalid", "registration",
             "2026", "website", at, ttl)
        ).fetchone()

    a = insert("a" * 64, "KEP-I-" + "A" * 32, now, expiry)
    assert a == ("KEP-I-" + "A" * 32,)
    # Duplicate application must NOT alter initial timestamp or ID.
    b = insert("a" * 64, "KEP-I-" + "B" * 32, now+1000, expiry+1000)
    assert b is None
    got = db.execute("SELECT submission_id, received_at_ms FROM beta_applications").fetchone()
    assert got == ("KEP-I-" + "A" * 32, now)
    # New applicant has distinct HMAC digest and private receipt.
    assert insert("b" * 64, "KEP-I-" + "C" * 32, now, expiry)
    assert db.execute("SELECT count(*) FROM beta_applications").fetchone()[0] == 2
    # Once a record is expired, it can be atomically replaced.
    later = expiry + 1
    assert insert("a" * 64, "KEP-I-" + "D" * 32, later, later+90*86400*1000)
    assert db.execute(
        "SELECT submission_id FROM beta_applications WHERE email_hmac=?",
        ("a" * 64,)
    ).fetchone()[0] == "KEP-I-" + "D" * 32
    db.execute("DELETE FROM beta_applications WHERE expires_at_ms<=?", (later,))
    assert db.execute("SELECT count(*) FROM beta_applications").fetchone()[0] == 1
    db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    worker, config, schema, program, frontend, html = input_files()
    issues = errors(worker, config, schema, program, frontend, html)
    if issues:
        raise SystemExit("KEP_INTAKE_D1_STATIC_FAIL " + " / ".join(issues))
    sql_upsert = sql_upsert_from_worker(worker)
    sqlite_test(schema, sql_upsert)
    if args.self_test:
        copies = [
            (worker.replace("ON CONFLICT(email_hmac) DO UPDATE", "ON CONFLICT(email_hmac) DO NOTHING"),
             config, schema, program, frontend, html),
            (worker, config.replace('INTAKE_ENABLED = "false"', 'INTAKE_ENABLED = "true"'),
             schema, program, frontend, html),
            (worker, config, schema.replace("email_hmac TEXT NOT NULL PRIMARY KEY", "email_hmac TEXT NOT NULL"),
             program, frontend, html),
            (worker, config, schema,
             {**program, "application": {**program["application"],
                "directIntake": {**program["application"]["directIntake"],
                                 "endpoint": "https://intake.example.test"}}}, frontend, html),
            (worker, config, schema, program,
             frontend.replace("turnstileToken:intakeTurnstileToken", "turnstileToken:''"), html),
            (worker, config, schema,
             {**program, "application": {**program["application"],
                "directIntake": {**program["application"]["directIntake"],
                                 "releaseDecision": "approved_manual"}}}, frontend, html),
            (worker, config, schema, program,
             frontend.replace("direct.releaseDecision!=='approved_manual'",
                              "direct.releaseDecision!=='hold'"), html),
        ]
        for case in copies:
            assert errors(*case), "intake security invariant mutation not rejected"
        print("KEP_INTAKE_D1_SELF_TEST_PASS real_SQLite_UPSERT_7_fail_closed_mutations")
    else:
        print("KEP_INTAKE_D1_STATIC_PASS atomic_dedup_90day_retention_disabled_until_approved")


if __name__ == "__main__":
    main()
