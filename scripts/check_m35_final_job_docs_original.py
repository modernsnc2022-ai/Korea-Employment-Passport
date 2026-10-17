#!/usr/bin/env python3
"""M35 structural completeness guard for 2026 General Manufacturing FINAL job-doc evidence.

NOT a policy fact checker or a live official-document fetcher. Verified-looking
fields are NOT approval. Applicant job_docs and beta stay HOLD until real
original byte/page review, named signature and separately reviewed code release.
"""
from __future__ import annotations
import argparse, copy, json, re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
DAY="2026-10-17"
OUT=ROOT/"research/source_reviews/indonesia_m35_final_job_docs_evidence_template_2026-10-17.json"
INDEX="https://kp2mi.go.id/gtog-korea/pengumuman"
SHA=re.compile(r"^[0-9a-f]{64}$")
ROUTE="Indonesia > Korea > E-9 > General Manufacturing 2026"
BAD_TITLE=re.compile(r"PERIKANAN|ROOT\s*INDUSTRY|UBT\s*KHUSUS|PENDAFTARAN\s+UJIAN|"+
                     r"UJIAN\s+BAHASA\s+KOREA\s+TAHAP\s+PERTAMA",re.I)
FINAL_WORDS=re.compile(r"LAMARAN\s+ONLINE|PENGAJUAN\s+LAMARAN",re.I)
SECTOR_WORDS=re.compile(r"MANUFAKTUR|MANUFACTURING",re.I)
def read(p):return json.loads((ROOT/p).read_text(encoding="utf-8-sig"))
def need(v,why):
    if not v:raise ValueError("M35_FINAL_JOBDOCS_EVIDENCE_BLOCKED "+why)
def official_url(url,notice=False):
    need(isinstance(url,str) and bool(url) and url==url.strip(),
         "non-empty original official URL required")
    u=urlsplit(url)
    need(u.scheme=="https" and u.hostname in {"kp2mi.go.id","www.kp2mi.go.id"}
         and u.username is None and u.password is None and not u.fragment,
         "exact KP2MI HTTPS host, no credentials or fragment")
    need(u.path.startswith("/gtog-detail/korea/") if notice else
         (u.path.lower().endswith(".pdf") and u.path.startswith("/")),
         "official original notice or PDF URL path")
    return True
def validate_sources():
    m34=read("research/source_reviews/indonesia_m34_unsigned_release_review_packet_2026-10-17.json")
    m33=read("research/source_reviews/indonesia_m33_exact_final_job_docs_preflight_2026-10-17.json")
    route=read("docs/data/id_e9_manufacturing_2026.json")
    packs=read("docs/data/document_packs_2026.json")
    need(m34["asOfJakarta"]==DAY and m34["pendingReviewTasks"]==20
       and not m34["explicitFinalManufacturingApplicationHeadlineCandidates"]
       and m34["publicBetaAccess"]=="hold" and m34["releaseAuthorized"] is False,
       "M34 official source index and unsigned reviews")
    need(next(x for x in m33["gates"] if x["id"]==
         "exact_2026_manufacturing_final_job_documents")["status"]=="PENDING",
         "M33 nonwaivable source gate")
    job=next(x for x in route["stages"] if x["id"]=="job_application")
    doc=next(x for x in packs["packs"] if x["id"]=="job_application_manufacturing")
    need(route["country"]=="ID" and route["sector"]=="manufacturing"
       and route["cycle"]==2026 and job["brokerReplacement"]=="held_official_notice"
       and doc["status"]=="awaiting_sector_notice" and doc["items"]==[],
       "never invent actual applicant 2026 final required documents")
def template():
    validate_sources()
    return {
       "version":"1.0.0",
       "kind":"UNSIGNED_FINAL_MANUFACTURING_DOCUMENT_EVIDENCE_INTAKE",
       "asOfJakarta":DAY,"route":ROUTE,
       "officialIndexUrl":INDEX,
       "cohort":{"country":"Indonesia","visa":"E-9","sector":"General Manufacturing",
                 "year":2026,"stage":"post_Skill_Test_final_online_job_application"},
       "source":{"officialNoticeUrl":None,"officialNoticeTitle":None,
                 "officialNoticePublishedDate":None,"verifiedOriginalHtmlSha256":None,
                 "noticeParagraphCitation":None,"annexes":[],"requiredDocuments":[]},
       "operator":{"reviewerFullName":None,"reviewedAtTimeZoneAware":None,
                   "specificReasonForApplicability":None,
                   "humanSignoffNotImplied":True},
       "sourceEvidenceStatus":"official_2026_final_notice_not_established",
       "evidenceFieldsStructurallyComplete":False,
       "sourceOriginalBytesRetrievedByThisChecker":False,
       "sameDayHumanSourceApproval":False,
       "applicantChecklistPromoted":False,"automaticHashAcceptance":False,
       "manualPublicBetaApproved":False,"betaAccess":"hold",
       "releaseAuthorized":False,
       "limitations":"Structural input validator only. Does not perform live official GET, authenticate named reviewer, accept a source hash, approve original semantics, create document-pack rules or authorize beta."}
def full_evidence(candidate):
    s=candidate["source"]
    op=candidate["operator"]
    official_url(s["officialNoticeUrl"],True)
    title=s["officialNoticeTitle"]
    need(isinstance(title,str) and FINAL_WORDS.search(title)
       and SECTOR_WORDS.search(title)
       and not BAD_TITLE.search(title) and "2026" in title,
       "notice title must explicitly state same 2026 General Manufacturing FINAL online application")
    notice_path=urlsplit(s["officialNoticeUrl"]).path.lower()
    need("2026" in notice_path and ("manufaktur" in notice_path or
         "manufacturing" in notice_path)
         and ("lamaran" in notice_path or "pengajuan" in notice_path)
         and not any(t in notice_path for t in
                     ["perikanan","root-industry","ubt-khusus","pendaftaran-ubt"]),
         "wrong sector/year or exam-only URL")
    try:
        notice_date=date.fromisoformat(s["officialNoticePublishedDate"])
    except (ValueError,TypeError):
        raise ValueError("M35_FINAL_JOBDOCS_EVIDENCE_BLOCKED official original notice date")
    need(date(2026,9,17)<=notice_date<=date.fromisoformat(candidate["asOfJakarta"]),
         "post Skill-Test 2026 current-cycle announcement only")
    need(isinstance(s["verifiedOriginalHtmlSha256"],str)
         and bool(SHA.fullmatch(s["verifiedOriginalHtmlSha256"])),
         "64-byte original HTML SHA-256 digest")
    need(isinstance(s["noticeParagraphCitation"],str)
         and len(s["noticeParagraphCitation"].strip())>=15,
         "precise official HTML paragraph citation needed")
    annexes=s["annexes"];docs=s["requiredDocuments"]
    need(isinstance(annexes,list) and isinstance(docs,list) and 0<len(docs)<=40
       and 0<len(annexes)<=30,"actual final applicant file list plus PDF originals")
    known_annex={}
    for a in annexes:
        need(isinstance(a,dict),"annex object")
        official_url(a.get("officialPdfUrl"),False)
        sha=a.get("originalPdfSha256")
        need(isinstance(sha,str) and bool(SHA.fullmatch(sha)),"annex bytes SHA-256")
        need(type(a.get("pages")) is int and a["pages"]>=1,
             "official PDF page count")
        need(a["officialPdfUrl"] not in known_annex,"duplicate PDF URL")
        known_annex[a["officialPdfUrl"]]=a
    seen=set()
    for doc in docs:
        need(isinstance(doc,dict),"document checklist entry")
        code=doc.get("id")
        need(isinstance(code,str) and re.fullmatch(r"[a-z][a-z0-9_]{2,60}",code)
           and code not in seen,"unique applicant document id")
        seen.add(code)
        need(isinstance(doc.get("labelIndonesian"),str) and
             len(doc["labelIndonesian"].strip())>=5,"source-specific doc name")
        need(type(doc.get("mandatory")) is bool,"must explicitly define required/optional")
        pdf=doc.get("officialPdfUrl");page=doc.get("page")
        need(pdf in known_annex and type(page) is int
             and 1<=page<=known_annex[pdf]["pages"],
             "every requirement must be anchored to real PDF original + page")
        need(isinstance(doc.get("sourceQuote"),str) and
             len(doc["sourceQuote"].strip())>=18,"required exact source paragraph citation")
    reviewer=op.get("reviewerFullName")
    need(isinstance(reviewer,str) and len(reviewer.strip())>=4
         and not re.search(r"(?i)\b(?:test|synthetic|example|dummy|fake|placeholder)\b",reviewer),
         "real responsible internal human name required")
    when=op.get("reviewedAtTimeZoneAware")
    try:stamp=datetime.fromisoformat(when.replace("Z","+00:00"))
    except (ValueError,TypeError,AttributeError):
        raise ValueError("M35_FINAL_JOBDOCS_EVIDENCE_BLOCKED human signature timestamp")
    need(stamp.tzinfo is not None and
         stamp.astimezone(ZoneInfo("Asia/Jakarta")).date().isoformat()==candidate["asOfJakarta"],
         "actual source review time must be same Indonesia review day")
    need(isinstance(op.get("specificReasonForApplicability"),str) and
         len(op["specificReasonForApplicability"].strip())>=35,
         "operator must document real same-cohort applicability rationale")
    return True
def validate(packet):
    validate_sources()
    need(packet["kind"]=="UNSIGNED_FINAL_MANUFACTURING_DOCUMENT_EVIDENCE_INTAKE"
        and packet["asOfJakarta"]==DAY and packet["route"]==ROUTE
        and packet["officialIndexUrl"]==INDEX
        and packet["cohort"]==template()["cohort"],"fixed country/year/stage")
    need(packet["sourceEvidenceStatus"] in
         {"official_2026_final_notice_not_established","human_evidence_input_under_review"},
         "only unapproved review states")
    if packet["sourceEvidenceStatus"]=="official_2026_final_notice_not_established":
        need(packet["source"]==template()["source"] and
             packet["operator"]==template()["operator"] and
             packet["evidenceFieldsStructurallyComplete"] is False,
             "pending template contains no fabricated original source or human")
    else:
        need(full_evidence(packet),"completed proposal needs source and human evidence")
        need(packet["evidenceFieldsStructurallyComplete"] is True,
             "structural proposal cannot imply official approval")
    need(packet["sourceOriginalBytesRetrievedByThisChecker"] is False
      and packet["sameDayHumanSourceApproval"] is False
      and packet["applicantChecklistPromoted"] is False
      and packet["automaticHashAcceptance"] is False
      and packet["manualPublicBetaApproved"] is False
      and packet["operator"]["humanSignoffNotImplied"] is True
      and packet["betaAccess"]=="hold"
      and packet["releaseAuthorized"] is False,
      "no source approval, no applicant promotion and beta HOLD")
    return True
def selftest():
    q=template();validate(q)
    changes=[
      lambda x:x.update(betaAccess="open"),
      lambda x:x.update(releaseAuthorized=True),
      lambda x:x.update(sameDayHumanSourceApproval=True),
      lambda x:x.update(applicantChecklistPromoted=True),
      lambda x:x.update(automaticHashAcceptance=True),
      lambda x:x.update(manualPublicBetaApproved=True),
      lambda x:x.update(sourceOriginalBytesRetrievedByThisChecker=True),
      lambda x:x.update(sourceEvidenceStatus="human_evidence_input_under_review"),
      lambda x:x["source"].update(officialNoticeUrl="https://kp2mi.go.id/gtog-detail/korea/invented"),
      lambda x:x["source"].update(requiredDocuments=[{"id":"imaginary_2025"}]),
      lambda x:x["operator"].update(reviewerFullName="synthetic"),
      lambda x:x["cohort"].update(year=2025),
      lambda x:x["cohort"].update(sector="Fisheries"),
      lambda x:x["source"].update(annexes=[{"officialPdfUrl":"https://evil.invalid/a.pdf"}]),
      lambda x:x.update(evidenceFieldsStructurallyComplete=True),
      lambda x:x.update(asOfJakarta="2026-10-16"),
      lambda x:x["operator"].update(humanSignoffNotImplied=False),
      lambda x:x.update(officialIndexUrl="https://kp2mi.go.id/gtog-korea/info"),
    ]
    for i,fn in enumerate(changes):
        v=copy.deepcopy(q);fn(v)
        try:validate(v)
        except (ValueError,KeyError,TypeError,AttributeError):pass
        else:raise AssertionError("unsafe M35 template input accepted #"+str(i))
    # A future structurally filled form is NEVER treated as a released rule.
    # All positive/negative evidence tests are synthetic, none persisted.
    ex=copy.deepcopy(q)
    ex["sourceEvidenceStatus"]="human_evidence_input_under_review"
    ex["source"].update(
       officialNoticeUrl="https://kp2mi.go.id/gtog-detail/korea/pengajuan-lamaran-online-ubt-umum-manufaktur-2026",
       officialNoticeTitle="PENGAJUAN LAMARAN ONLINE UBT UMUM SEKTOR MANUFAKTUR TAHUN 2026",
       officialNoticePublishedDate="2026-10-17",
       verifiedOriginalHtmlSha256="a"*64,
       noticeParagraphCitation="Section final applicant file list, item 3",
       annexes=[{"officialPdfUrl":"https://kp2mi.go.id/uploads/manufacturing-2026-final-docs.pdf",
                 "originalPdfSha256":"b"*64,"pages":3}],
       requiredDocuments=[{"id":"sample_file_1","labelIndonesian":"Dokumen simulasi",
             "mandatory":True,"officialPdfUrl":"https://kp2mi.go.id/uploads/manufacturing-2026-final-docs.pdf",
             "page":2,"sourceQuote":"SIMULATED ONLY: section 3 mandatory document checklist"}]
    )
    ex["operator"].update(
      reviewerFullName="Authorized Internal Reviewer",
      reviewedAtTimeZoneAware="2026-10-17T14:00:00+07:00",
      specificReasonForApplicability="This is a synthetic fixture for 2026 General Manufacturing.")
    ex["evidenceFieldsStructurallyComplete"]=True
    # Positive structural fixture is in-memory ONLY. This is no real 2026
    # official original, person, or approval. A fake SHA alone proves nothing.
    need(full_evidence(ex) is True,"valid structural fixture")
    need(validate(ex) is True and ex["releaseAuthorized"] is False
         and ex["betaAccess"]=="hold", "structural completeness never approves beta")
    for name,patch in [
        ("wrong_year",lambda z:z["source"].update(officialNoticePublishedDate="2025-12-05")),
        ("wrong_sector",lambda z:z["source"].update(officialNoticeTitle="PENGAJUAN LAMARAN ONLINE SEKTOR PERIKANAN TAHUN 2026")),
        ("initial_exam",lambda z:z["source"].update(officialNoticeUrl="https://kp2mi.go.id/gtog-detail/korea/pendaftaran-ubt-umum-manufaktur-2026")),
        ("no_pdf",lambda z:z["source"].update(annexes=[])),
        ("bad_page",lambda z:z["source"]["requiredDocuments"][0].update(page=99)),
        ("old_pdf",lambda z:z["source"]["requiredDocuments"][0].update(officialPdfUrl="https://kp2mi.go.id/uploads/2025.pdf")),
        ("fake_human",lambda z:z["operator"].update(reviewerFullName="Synthetic Person")),
        ("placeholder_human",lambda z:z["operator"].update(reviewerFullName="Human Reviewer Placeholder")),
        ("future_date",lambda z:z["source"].update(officialNoticePublishedDate="2026-11-08")),
    ]:
        z=copy.deepcopy(ex);patch(z)
        try:full_evidence(z)
        except (ValueError,KeyError,TypeError,AttributeError):pass
        else:raise AssertionError("unsafe M35 structured evidence accepted: "+name)
    print("M35_EXACT_MANUFACTURING_DOC_EVIDENCE_SELF_TEST_PASS 27_fail_closed_cases 2025_fisheries_exam_optional_pdf_rejected 2026_job_docs_HOLD")
def main():
    cli=argparse.ArgumentParser()
    for arg in ("self-test","write","check"):cli.add_argument("--"+arg,action="store_true")
    a=cli.parse_args()
    if a.self_test:selftest()
    if a.write:
        need(not OUT.exists(),"append-only template exists")
        t=template();validate(t)
        OUT.write_text(json.dumps(t,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("M35_UNAPPROVED_DOCUMENT_EVIDENCE_TEMPLATE_WRITTEN job_docs_HOLD")
    if a.check:
        validate(read("research/source_reviews/indonesia_m35_final_job_docs_evidence_template_2026-10-17.json"))
        print("M35_DOCUMENT_PROVENANCE_TEMPLATE_INTEGRITY_PASS NO_SOURCE_SIGNOFF_NO_RELEASE")
    if not (a.self_test or a.write or a.check):cli.error("select --self-test, --write or --check")
if __name__=="__main__":main()
