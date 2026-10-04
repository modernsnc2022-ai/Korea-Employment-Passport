#!/usr/bin/env python3
from __future__ import annotations

import argparse
import calendar
import csv
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
PROGRAM = ROOT / "docs" / "data" / "beta_program_v1.json"
ROUTE = ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json"
SUPPORTED_STAGES = {
    row["id"] for row in json.loads(ROUTE.read_text(encoding="utf-8-sig")).get("stages", [])
}

def add_months(value: date, months: int) -> date:
    idx = value.month - 1 + months
    year = value.year + idx // 12
    month = idx % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("received timestamp must include timezone")
    return parsed

def load_tracker():
    with TRACKER.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)

def acceptance_link(row: dict[str, str]) -> str:
    base = str(row.get("beta_link", "")).strip()
    stage = str(row.get("current_stage", "")).strip()
    if not base or stage not in SUPPORTED_STAGES:
        return base
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}stage={stage}"


def acceptance_message(row: dict[str, str]) -> str:
    return "\n".join([
        "Korea Employment Passport — akses beta diterima",
        "",
        f"ID beta anonim: {row.get('tester_id', '')}",
        f"Link beta: {acceptance_link(row)}",
        f"Tahap awal yang tercatat: {row.get('current_stage', '')}",
        f"Akses gratis sampai: {row.get('free_until', '')} (6 bulan sejak aktivasi)",
        "",
        "Buka link beta di atas. ID KEP pada link memisahkan feedback beta Anda dari peserta lain.",
        "Untuk feedback yang akan dihitung sebagai bukti beta, balas melalui email/thread pribadi yang sama dengan pendaftaran atau kanal pribadi yang telah dikonfirmasi tim.",
        "Pada pengaturan awal, pilih tahap paling awal yang belum selesai jika posisi yang tercatat perlu dikoreksi.",
        "Jangan kirim foto paspor/KTP/ARC, nomor identitas, atau alamat rumah/asrama dalam feedback.",
        "Akses beta tidak menjamin pekerjaan, pemilihan perusahaan, SLC, visa, atau keberangkatan."
    ])

def assign(rows, received_at, activation_date, current_stage, source_channel, opened_at=None):
    if current_stage not in SUPPORTED_STAGES:
        raise ValueError(f"unsupported current_stage: {current_stage}")
    received = parse_ts(received_at)
    if opened_at:
        opened = parse_ts(opened_at)
        if received < opened:
            raise ValueError("application receipt is earlier than public beta OPEN timestamp")
    activation = date.fromisoformat(activation_date)
    if activation < received.date():
        raise ValueError(
            "activation date cannot be earlier than this application's received date"
        )
    public = [r for r in rows if r.get("target_group", "").strip() == "active_applicant"]
    assigned = [r for r in public if r.get("application_received_at", "").strip()]
    if assigned and received < parse_ts(assigned[-1]["application_received_at"].strip()):
        raise ValueError("received timestamp is earlier than the last assigned eligible application")
    target = next((r for r in public if not r.get("application_received_at", "").strip()), None)
    if target is None:
        raise ValueError("all 30 public beta slots are already assigned")
    target["application_received_at"] = received_at
    target["eligibility_status"] = "accepted"
    target["activated_at"] = activation.isoformat()
    target["free_until"] = add_months(activation, 6).isoformat()
    target["feedback_status"] = "not_started"
    target["current_stage"] = current_stage
    target["source_channel"] = source_channel
    target["role"] = "public_beta_tester"
    target["created_at"] = activation.isoformat()
    return target

def self_test():
    rows = [{
        "tester_id": f"KEP-{i:04d}",
        "target_group": "active_applicant" if i <= 30 else "e9_worker_korea",
        "application_received_at": "", "eligibility_status": "", "activated_at": "",
        "free_until": "", "feedback_status": "", "current_stage": "",
        "source_channel": "", "role": "", "created_at": "", "beta_link": ""
    } for i in range(1, 51)]
    opened_at = "2026-10-05T08:30:00+07:00"
    first = assign(rows, "2026-10-05T09:00:00+07:00", "2026-10-06", "roster", "community", opened_at)
    second = assign(rows, "2026-10-05T09:01:00+07:00", "2026-10-05", "slc", "community", opened_at)
    assert first["tester_id"] == "KEP-0001"
    assert first["free_until"] == "2027-04-06"
    assert second["tester_id"] == "KEP-0002"
    assert second["activated_at"] < first["activated_at"]
    first["beta_link"] = "https://example.invalid/app.html?beta=KEP-0001"
    assert acceptance_link(first).endswith("?beta=KEP-0001&stage=roster")
    assert "stage=roster" in acceptance_message(first)
    try:
        assign(rows, "2026-10-05T08:29:59+07:00", "2026-10-05", "visa_docs", "community", opened_at)
    except ValueError as exc:
        assert "earlier than public beta OPEN timestamp" in str(exc)
    else:
        raise AssertionError("pre-OPEN application receipt was accepted")
    try:
        assign(rows, "2026-10-08T09:02:00+07:00", "2026-10-07", "visa_docs", "community", opened_at)
    except ValueError as exc:
        assert "activation date cannot be earlier" in str(exc)
    else:
        raise AssertionError("activation before application receipt was accepted")
    try:
        assign(rows, "2026-10-05T08:59:00+07:00", "2026-10-07", "visa_docs", "community", opened_at)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-order receipt was not rejected")
    try:
        assign(rows, "2026-10-05T09:02:00+07:00", "2026-10-07", "not_a_stage", "community", opened_at)
    except ValueError as exc:
        assert "unsupported current_stage" in str(exc)
    else:
        raise AssertionError("unsupported stage was not rejected")
    print("BETA_SLOT_ASSIGNMENT_SELF_TEST_PASS")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--received-at")
    parser.add_argument("--activation-date")
    parser.add_argument("--current-stage")
    parser.add_argument("--source-channel")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    program = json.loads(PROGRAM.read_text(encoding="utf-8-sig"))
    if program.get("status") != "open":
        raise SystemExit("BETA_SLOT_ASSIGNMENT_BLOCKED recruitment status is not OPEN")
    release = program.get("releaseDecision", {})
    approved_at = str(release.get("approvedAt") or "").strip()
    if release.get("publicBeta") != "approved_manual" or not approved_at:
        raise SystemExit("BETA_SLOT_ASSIGNMENT_BLOCKED public beta OPEN has no explicit approved release decision")
    try:
        parse_ts(approved_at)
    except ValueError as exc:
        raise SystemExit("BETA_SLOT_ASSIGNMENT_BLOCKED OPEN approval timestamp must include timezone") from exc
    required = [args.received_at, args.activation_date, args.current_stage, args.source_channel]
    if not all(required):
        parser.error("--received-at, --activation-date, --current-stage and --source-channel are required")
    fields, rows = load_tracker()
    target = assign(rows, *required, opened_at=approved_at)
    if args.write:
        with TRACKER.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(
        "BETA_SLOT_" + ("WRITTEN" if args.write else "DRY_RUN") +
        " tester_id=" + target["tester_id"] +
        " free_until=" + target["free_until"] +
        " beta_link=" + target.get("beta_link", "")
    )
    print("BETA_ACCEPTANCE_MESSAGE_BEGIN")
    print(acceptance_message(target))
    print("BETA_ACCEPTANCE_MESSAGE_END")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
