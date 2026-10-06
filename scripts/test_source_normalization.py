#!/usr/bin/env python3
from check_official_sources import NORMALIZATION_REVISION, normalize_source_text

KP2MI="https://kp2mi.go.id/gtog-detail/korea/example"

def require(ok, message):
    if not ok:
        raise SystemExit("SOURCE_NORMALIZATION_SELFTEST_FAIL: "+message)

def main():
    sunday=(
        "Sunday, 4 October 2026 0800-1000 Webmail "
        "Bahasa Inggris 10.30 27 January 2026 123 "
        "PENGUMUMAN Manufacturing quota 1000 fee 350000 visa 1260000 minimum 1500000 "
        "Total Visitors 5 9 0 3 5 7 1 0"
    )
    tuesday=(
        "Tuesday, 6 October 2026 0800-1000 Webmail "
        "Bahasa Inggris 10.30 27 January 2026 999 "
        "PENGUMUMAN Manufacturing quota 1000 fee 350000 visa 1260000 minimum 1500000 "
        "Total Visitors 5 9 0 3 5 8 8 8"
    )
    a=normalize_source_text(sunday,KP2MI)
    b=normalize_source_text(tuesday,KP2MI)
    require(a==b,"KP2MI current page date / view counters / visitor total must normalize identically")
    require(a.startswith("<dynamic-page-date>"),"only the leading KP2MI current date should be normalized")
    for value in ("1000","350000","1260000","1500000","27 January 2026"):
        require(value in a,f"semantic notice value must be preserved: {value}")

    body_date="Notice remains valid Monday, 5 October 2026 quota 1000"
    body=normalize_source_text(body_date,KP2MI)
    require("Monday, 5 October 2026" in body,"non-leading notice dates must not be stripped")

    non_kp2mi=normalize_source_text(
        "Tuesday, 6 October 2026 official date 1000",
        "https://example.gov/notice",
    )
    require(non_kp2mi.startswith("Tuesday, 6 October 2026"),"date normalization must be scoped to KP2MI")
    mm_a=normalize_source_text(
        "Users Today : 67 Views This Month : 5215 Your IP Address : 158.23.190.67 EPS Manufacturing notice",
        "https://www.mol.gov.mm/mol-department-of-labour/eps-opportunity/",
    )
    mm_b=normalize_source_text(
        "Users Today : 72 Views This Month : 5220 Your IP Address : 203.0.113.10 EPS Manufacturing notice",
        "https://www.mol.gov.mm/mol-department-of-labour/eps-opportunity/",
    )
    require(mm_a==mm_b,"Myanmar visitor/IP telemetry must normalize identically")
    require("EPS Manufacturing notice" in mm_a,"Myanmar notice text must be preserved")

    vn_a=normalize_source_text(
        "THỐNG KÊ Trực tuyến: 380 Hôm nay: 28,238 Tháng này: 10,584,997 Tổng số: 121,573,863 EPS notice",
        "https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx",
    )
    vn_b=normalize_source_text(
        "THỐNG KÊ Trực tuyến: 384 Hôm nay: 28,242 Tháng này: 10,585,001 Tổng số: 121,573,867 EPS notice",
        "https://colab.moha.gov.vn/tin-tucs/357/Chuong-trinh-EPS.aspx",
    )
    require(vn_a==vn_b,"Vietnam live visitor statistics must normalize identically")
    require("EPS notice" in vn_a,"Vietnam notice text must be preserved")

    mm_clock_a=normalize_source_text(
        "Official notice Nay Pyi Taw,MM 10:21 AM, Tuesday, 6th October 2026 Government Website Link",
        "https://www.mol.gov.mm/mol-department-of-labour/",
    )
    mm_clock_b=normalize_source_text(
        "Official notice Nay Pyi Taw,MM 10:22 AM, Tuesday, 6th October 2026 Government Website Link",
        "https://www.mol.gov.mm/mol-department-of-labour/",
    )
    require(mm_clock_a==mm_clock_b,"Myanmar government live clock must normalize identically")
    require("Official notice" in mm_clock_a and "Government Website Link" in mm_clock_a,
            "Myanmar semantic page text must survive clock normalization")

    require(NORMALIZATION_REVISION=="cross-site-volatile-widget-v3","normalization revision drift")
    print("SOURCE_NORMALIZATION_SELFTEST_PASS")

if __name__=="__main__":
    main()
