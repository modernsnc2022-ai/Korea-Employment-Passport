#!/usr/bin/env python3
"""M31 original 2025-vs-2026 stage lineage evidence, no 2025->2026 document import."""
from __future__ import annotations
import argparse, copy, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from check_official_sources import _fetch_response,TextExtractor,normalize_source_text

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUT=ROOT/"research/source_reviews/indonesia_m31_2025_vs_2026_official_job_docs_lineage_2026-10-17.json"
OFFICIAL="https://kp2mi.go.id/gtog-detail/korea/"
SRC=[
  {"id":"manufacturing_2025_final_result","year":2025,
   "stage":"prior_year_final_result_await_followup",
   "url":OFFICIAL+"pengumuman-hasil-akhir-kelulusan-eps-topik-ubt-umum-sektor-manufaktur-program-g-to-g-ke-korea-selatan-tahun-2025",
   "mustInclude":["HASIL AKHIR KELULUSAN","MANUFAKTUR","TAHUN 2025","pengumuman lebih lanjut"]},
  {"id":"manufacturing_2025_final_docs","year":2025,
   "stage":"prior_year_final_online_application_docs_not_2026",
   "url":OFFICIAL+"pengumuman-pembagian-sertifikat-kelulusan-digital-e-sertifikat-ujian-eps-topik-ubt-umum-sektor-manufaktur-dan-pengajuan-lamaran-online-calon-pekerja-migran-indonesia-program-g-to-g-korea-tahun-2025",
   "mustInclude":["e-SERTIFIKAT","MANUFAKTUR","TAHUN 2025","10 Desember 2025","scan ijazah"]},
  {"id":"manufacturing_2026_first_stage","year":2026,
   "stage":"2026_eps_topik_stage_one_not_final",
   "url":OFFICIAL+"pengumuman-hasil-ujian-kemampuan-bahasa-korea-eps-topik-ubt-umum-sektor-manufaktur-tahun-2026",
   "mustInclude":["MANUFAKTUR","TAHUN 2026","belum merupakan hasil kelulusan akhir","WAJIB mengikuti Skill Test"]},
  {"id":"manufacturing_2026_exam_enrollment","year":2026,
   "stage":"2026_initial_exam_registration_not_final",
   "url":OFFICIAL+"pengumuman-pendaftaran-ubt-umum-sektor-perikanan-dan-sektor-manufaktur-progam-g-to-g-ke-korea-selatan-dengan-sistem-poin-tahun-2026",
   "mustInclude":["MANUFAKTUR","TAHUN 2026","lamaran online","HIMPSI"]},
]
def read(path):return json.loads((ROOT/path).read_text(encoding="utf-8-sig"))
def need(ok,message):
    if not ok:raise ValueError("M31_OFFICIAL_STAGE_LINEAGE_HOLD "+message)
def baseline():
    m29=read("research/source_reviews/indonesia_m29_slbfe_and_kp2mi_context_2026-10-17.json")
    m30=read("research/source_reviews/indonesia_m30_post_skill_notice_candidates_corrected_r1_2026-10-17.json")
    sign=read("recruitment/ID_BETA_SOURCE_SIGNOFF_20261017.json")
    pack=read("docs/data/document_packs_2026.json")
    route=read("docs/data/id_e9_manufacturing_2026.json")
    need(m29["kp2miOfficialNoticePagesRead"]==7 and m29["kp2miCurrentTextShaMatchesM21"]==7
       and m29["finalOnlineManufacturingJobDocsOfficialEvidenceEstablished"] is False
       and m29["jobDocs"]=="hold","M29 direct 2026 originals")
    need(m30["correctedCandidateCount"]==9 and m30["removedPsychologyFalsePositives"]==2
       and m30["manufacturingExplicitFinalOnlineApplicationTitles"]==0
       and m30["jobDocs"]=="hold" and m30["publicBetaAccess"]=="hold",
       "M30 official title inventory")
    need(sign["reviewer"] is None and sign["approvedAt"] is None
       and sign["status"]=="pending_manual_source_signoff",
       "official-source human review absent")
    job=next(x for x in route["stages"] if x["id"]=="job_application")
    dp=next(x for x in pack["packs"] if x["id"]=="job_application_manufacturing")
    need(job["brokerReplacement"]=="held_official_notice"
       and job["sourceUrl"]=="https://kp2mi.go.id/gtog-korea/pengumuman"
       and dp["status"]=="awaiting_sector_notice" and dp["items"]==[],
       "app must not show invented checklist")
    return True
def get_one(item,tls):
    url=item["url"]
    uri=urlparse(url)
    need(uri.scheme=="https" and uri.hostname=="kp2mi.go.id" and uri.path.startswith("/gtog-detail/korea/"),
         "official original url")
    record={"sourceId":item["id"],"cohortYear":item["year"],"stage":item["stage"],
            "originalOfficialUrl":url,"retrieval":"inconclusive",
            "normalizedTextSha256":None,"allKeyClausesMatched":False,
            "foundKeyClauses":[],"missingKeyClauses":[],
            "humanLegalSemanticSignoff":False,
            "applicableTo2026ManufacturingFinalJobDocs":False,
            "authorizes2026Checklist":False}
    try:
        raw,ctype,charset,final,mode=_fetch_response(url,tls)
        host=urlparse(final).hostname
        need(urlparse(final).scheme=="https" and host in {"kp2mi.go.id","www.kp2mi.go.id"},
             "redirect outside KP2MI")
        need(ctype in {"text/html","application/xhtml+xml",""},"official format")
        parser=TextExtractor()
        parser.feed(raw.decode(charset,errors="replace"))
        text=normalize_source_text(" ".join(parser.parts),final)
        need(len(text)>800,"official body unexpectedly short")
        matching=[q for q in item["mustInclude"] if q.lower() in text.lower()]
        missing=[q for q in item["mustInclude"] if q.lower() not in text.lower()]
        sha=hashlib.sha256(text.encode("utf-8")).hexdigest()
        record.update(retrieval="official_html_verified",effectiveUrl=final,
            tlsMode=mode,normalizedCharacters=len(text),normalizedTextSha256=sha,
            foundKeyClauses=matching,missingKeyClauses=missing,
            allKeyClausesMatched=not missing)
        # Prior-cycle exact list is CONTEXT ONLY; never a 2026 doc claim.
        if item["id"]=="manufacturing_2025_final_docs":
            excerpt={}
            for needle in ["10 Desember 2025","scan ijazah","medical check up","Pemenuhan Dokumen"]:
                pos=text.lower().find(needle.lower())
                excerpt[needle]=text[max(0,pos-100):pos+180] if pos>=0 else None
            record["historicScopeExcerpts"]=excerpt
    except Exception as exc:
        record["readError"]=type(exc).__name__+": "+str(exc)[:140]
    return record
def make(tls=None,do_fetch=False):
    baseline()
    rows=[get_one(x,tls) if do_fetch else {
         "sourceId":x["id"],"cohortYear":x["year"],"stage":x["stage"],
         "originalOfficialUrl":x["url"],"retrieval":"inconclusive",
         "normalizedTextSha256":None,"allKeyClausesMatched":False,
         "foundKeyClauses":[],"missingKeyClauses":[],
         "humanLegalSemanticSignoff":False,
         "applicableTo2026ManufacturingFinalJobDocs":False,
         "authorizes2026Checklist":False} for x in SRC]
    return {"version":"1.0.0","checkedAtJakartaDate":DAY,
        "sourceType":"machine_readonly_official_2025_2026_stage_context",
        "officialSourceIndex":"https://kp2mi.go.id/gtog-korea/pengumuman",
        "pages":rows,"officialHtmlPagesRetrieved":sum(x["retrieval"]=="official_html_verified" for x in rows),
        "clausesChecked":sum(x["allKeyClausesMatched"] for x in rows),
        "historic2025ApplicationDocumentsNotApplicableTo2026":True,
        "2026EpsTopikStageOneNotFinal":True,
        "2026ManufacturingFinalApplicationAnnexUnverified":True,
        "2026ManufacturingFinalJobDocs":"hold",
        "sourceSHAAutoAccepted":False,"humanSignoff":False,
        "productionDeploymentAuthorized":False,"betaAccess":"hold",
        "releaseAuthorized":False,
        "warning":"Never import Dec 2025 exact medical/education/phone/scan/upload rules into 2026. Even all 4 HTML originals matching does not prove that the 2026 post-Skill Test job application annex exists or is verified."}
def verify(p):
    need(p["checkedAtJakartaDate"]==DAY and
        p["sourceType"]=="machine_readonly_official_2025_2026_stage_context","evidence date/type")
    rows=p["pages"]
    need(len(rows)==4 and {x["sourceId"] for x in rows}=={x["id"] for x in SRC},"all original URLs")
    lookup={x["id"]:x for x in SRC}
    for r in rows:
        o=lookup[r["sourceId"]]
        need(r["cohortYear"]==o["year"] and r["stage"]==o["stage"]
            and r["originalOfficialUrl"]==o["url"]
            and r["humanLegalSemanticSignoff"] is False
            and r["applicableTo2026ManufacturingFinalJobDocs"] is False
            and r["authorizes2026Checklist"] is False,"no cross-year import")
        if r["retrieval"]=="official_html_verified":
            need(bool(re.fullmatch("[0-9a-f]{64}",r["normalizedTextSha256"]))
               and r["normalizedCharacters"]>800
               and r["allKeyClausesMatched"] is (len(r["missingKeyClauses"])==0)
               and set(r["foundKeyClauses"])|set(r["missingKeyClauses"])==set(o["mustInclude"]),
               "original text content proof")
        else:
            need(r["retrieval"]=="inconclusive" and r["normalizedTextSha256"] is None,
                 "do not pretend failed GET success")
    need(p["officialHtmlPagesRetrieved"]==sum(x["retrieval"]=="official_html_verified" for x in rows)
       and p["clausesChecked"]==sum(x["allKeyClausesMatched"] for x in rows),"exact counts")
    need(p["historic2025ApplicationDocumentsNotApplicableTo2026"] is True
       and p["2026EpsTopikStageOneNotFinal"] is True
       and p["2026ManufacturingFinalApplicationAnnexUnverified"] is True
       and p["2026ManufacturingFinalJobDocs"]=="hold"
       and p["sourceSHAAutoAccepted"] is False and p["humanSignoff"] is False
       and p["betaAccess"]=="hold" and p["productionDeploymentAuthorized"] is False
       and p["releaseAuthorized"] is False,"unapproved release/lineage")
    return True
def selftest():
    p=make();verify(p)
    actions=[
      lambda x:x.update(releaseAuthorized=True),
      lambda x:x.update(betaAccess="open"),
      lambda x:x.update(humanSignoff=True),
      lambda x:x.update(sourceSHAAutoAccepted=True),
      lambda x:x.update({"2026ManufacturingFinalJobDocs":"verified"}),
      lambda x:x.update(historic2025ApplicationDocumentsNotApplicableTo2026=False),
      lambda x:x.update({"2026EpsTopikStageOneNotFinal":False}),
      lambda x:x["pages"][1].update(cohortYear=2026),
      lambda x:x["pages"][1].update(applicableTo2026ManufacturingFinalJobDocs=True),
      lambda x:x["pages"][1].update(authorizes2026Checklist=True),
      lambda x:x["pages"][2].update(stage="final_skill_pass"),
      lambda x:x["pages"][1].update(originalOfficialUrl="https://evil.invalid/source"),
      lambda x:x["pages"][0].update(retrieval="official_html_verified"),
    ]
    for i,action in enumerate(actions):
        q=copy.deepcopy(p);action(q)
        try:verify(q)
        except (ValueError,KeyError,TypeError):pass
        else:raise AssertionError("M31 bad evidence pass "+str(i))
    print("M31_CROSSYEAR_OFFICIAL_LINEAGE_SELF_TEST_PASS 13_fail_closed_mutations 4_official_sources no_2025_import")
def main():
    p=argparse.ArgumentParser()
    for flag in ("self-test","run","check"):p.add_argument("--"+flag,action="store_true")
    a=p.parse_args()
    if a.self_test:selftest()
    if a.run:
        require_date=datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()
        need(require_date==DAY and not OUT.exists(),"append-only observation date")
        result=make(tls=read("monitor/tls_pins.json"),do_fetch=True)
        verify(result)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for item in result["pages"]:
            print("M31",item["sourceId"],item["retrieval"],"clauses="+str(item["allKeyClausesMatched"]),
                  "missing="+",".join(item["missingKeyClauses"]),flush=True)
        print("M31_CROSS_YEAR_CONTEXT_READONLY",result["officialHtmlPagesRetrieved"],
             "of 4; full_key_clauses="+str(result["clausesChecked"]),
             "job_docs_HOLD beta_HOLD")
    if a.check:
        packet=read("research/source_reviews/indonesia_m31_2025_vs_2026_official_job_docs_lineage_2026-10-17.json")
        verify(packet)
        print("M31_CROSSYEAR_ORIGINAL_SOURCE_INTEGRITY_PASS")
    if not(a.self_test or a.run or a.check):p.error("choose action")
if __name__=="__main__":main()
