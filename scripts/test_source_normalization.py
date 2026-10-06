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
    require(NORMALIZATION_REVISION=="kp2mi-current-page-date-v1","normalization revision drift")
    print("SOURCE_NORMALIZATION_SELFTEST_PASS")

if __name__=="__main__":
    main()
