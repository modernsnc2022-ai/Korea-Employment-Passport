#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "recruitment" / "BETA_TESTER_TRACKER.csv"
PROGRAM = ROOT / "docs" / "data" / "beta_program_v1.json"
ROUTE = ROOT / "docs" / "data" / "id_e9_manufacturing_2026.json"
SUPPORTED_STAGES = {
    row["id"] for row in json.loads(ROUTE.read_text(encoding="utf-8-sig")).get("stages", [])
}
BASE_URL = "https://modernsnc2022-ai.github.io/Korea-Employment-Passport/app.html?beta="
ALLOWED_SOURCE_CHANNELS = {"website", "email", "community", "community_admin", "social", "referral", "direct_outreach", "partner", "other", "epstopik_indonesia", "topikly", "apsan_hakwon", "owie_epstopik", "lpk_samwon"}

def invitation_link(row: dict[str, str]) -> str:
    base = str(row.get("beta_link", "")).strip()
    stage = str(row.get("current_stage", "")).strip()
    if not base:
        base = BASE_URL + str(row.get("tester_id", "")).strip()
    if stage not in SUPPORTED_STAGES:
        return base
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}stage={stage}"


def invitation_message(row: dict[str, str]) -> str:
    return "\n".join([
        "Korea Employment Passport — undangan validator E-9",
        "",
        f"ID validator anonim: {row.get('tester_id','')}",
        f"Link validator: {invitation_link(row)}",
        "",
        "Gunakan panel ini hanya untuk tahap yang benar-benar pernah Anda alami.",
        "Catat tahun pengalaman EPS sebelum menyimpan penilaian tahap.",
        "Jangan masukkan nama, nomor identitas, telepon, email, atau alamat asrama pribadi.",
        "Balas melalui kanal pribadi yang sudah dikonfirmasi tim agar feedback dapat dipetakan ke ID validator dengan benar."
    ])


def assign(rows, joined_date, current_stage, source_channel):
    date.fromisoformat(joined_date)
    if source_channel not in ALLOWED_SOURCE_CHANNELS:
        raise ValueError("unsupported source_channel; use a non-identifying channel code")
    if current_stage not in SUPPORTED_STAGES:
        raise ValueError(f"unsupported current_stage: {current_stage}")
    workers=[row for row in rows if row.get("target_group","").strip()=="e9_worker_korea"]
    target=next((row for row in workers if not row.get("created_at","").strip()),None)
    if target is None:
        raise ValueError("all 20 E-9 worker validator slots are already assigned")
    target["created_at"]=joined_date
    target["source_channel"]=source_channel
    target["role"]="e9_worker_validator"
    target["current_stage"]=current_stage
    target["in_korea"]="yes"
    target["e9_experience"]="confirmed"
    target["experience_year"]=""
    target["interview_status"]="new"
    target["workplace_evidence_status"]="pending"
    target["broker_gap_status"]="pending"
    target["retest_status"]="pending"
    if not str(target.get("beta_link","")).strip():
        target["beta_link"]=BASE_URL+target["tester_id"]
    return target

def self_test():
    rows=[{
      "tester_id":f"KEP-{i:04d}",
      "target_group":"active_applicant" if i<=30 else "e9_worker_korea",
      "created_at":"","source_channel":"","role":"","current_stage":"","in_korea":"",
      "e9_experience":"","interview_status":"new","broker_gap_status":"pending","retest_status":"pending"
    } for i in range(1,51)]
    first=assign(rows,"2026-10-04","employment_maintenance","community_admin")
    second=assign(rows,"2026-10-05","first_payroll_check","community_admin")
    assert first["tester_id"]=="KEP-0031"
    assert second["tester_id"]=="KEP-0032"
    assert first["in_korea"]=="yes"
    assert first["e9_experience"]=="confirmed"
    assert first["experience_year"]==""
    assert first["workplace_evidence_status"]=="pending"
    assert "stage=employment_maintenance" in invitation_link(first)
    assert "ID validator anonim: KEP-0031" in invitation_message(first)
    try:
        assign(rows,"2026-10-06","employment_maintenance","worker-name-here")
    except ValueError as exc:
        assert "unsupported source_channel" in str(exc)
    else:
        raise AssertionError("identifying/free-text source channel was accepted")
    try:
        assign(rows,"2026-10-06","not_a_stage","community_admin")
    except ValueError as exc:
        assert "unsupported current_stage" in str(exc)
    else:
        raise AssertionError("unsupported stage was not rejected")
    print("WORKER_VALIDATOR_ASSIGNMENT_SELF_TEST_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--joined-date")
    parser.add_argument("--current-stage",default="employment_maintenance")
    parser.add_argument("--source-channel")
    parser.add_argument("--write",action="store_true")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    program=json.loads(PROGRAM.read_text(encoding="utf-8-sig"))
    if program.get("retrospectivePanel",{}).get("status")!="open":
        raise SystemExit("WORKER_VALIDATOR_ASSIGNMENT_BLOCKED panel status is not OPEN")
    release=program.get("releaseDecision",{})
    if (
        release.get("retrospectivePanel")!="approved_manual"
        or not str(release.get("retrospectiveApprovedAt") or "").strip()
    ):
        raise SystemExit(
            "WORKER_VALIDATOR_ASSIGNMENT_BLOCKED worker panel OPEN has no explicit approved release decision"
        )
    if not args.joined_date or not args.source_channel:
        parser.error("--joined-date and --source-channel are required")
    with TRACKER.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle)
        fields=list(reader.fieldnames or [])
        rows=list(reader)
    target=assign(rows,args.joined_date,args.current_stage,args.source_channel)
    if args.write:
        with TRACKER.open("w",encoding="utf-8-sig",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n")
            writer.writeheader();writer.writerows(rows)
    print(
        "WORKER_VALIDATOR_SLOT_"+("WRITTEN" if args.write else "DRY_RUN")+
        " tester_id="+target["tester_id"]+
        " beta_link="+invitation_link(target)
    )
    print("WORKER_VALIDATOR_INVITATION_BEGIN")
    print(invitation_message(target))
    print("WORKER_VALIDATOR_INVITATION_END")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
