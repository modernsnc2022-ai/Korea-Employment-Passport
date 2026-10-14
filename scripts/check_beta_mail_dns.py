#!/usr/bin/env python3
"""Read-only KEP beta Resend DNS audit; never edits records or sends mail.

Exit 0: DNS *shape* present, but NOT proof of Resend verification/delivery.
Exit 2: DNS records missing/incorrect; exit 1: DNS resolver unavailable.
Current Resend dashboard (2026-10-14) requires TXT DKIM and two CNAMEs
for mail.gdglobal.kr. Legacy MX/TXT patterns must NOT be added instead.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = "gdglobal.kr"
SENDER = "mail.gdglobal.kr"
ZOHO_MX = frozenset({"mx.zoho.com", "mx2.zoho.com", "mx3.zoho.com"})
DNS_TYPES = {"MX": 15, "TXT": 16, "CNAME": 5}


def google_doh(name: str, record_type: str) -> tuple[str, ...]:
    query = urlencode({"name": name, "type": record_type})
    request = Request(
        "https://dns.google/resolve?" + query,
        headers={"Accept": "application/dns-json", "User-Agent": "KEP-ReadOnly-DNS-Preflight/2.0"},
    )
    with urlopen(request, timeout=12) as response:
        data = json.load(response)
    if data.get("Status") not in (0, 3):
        raise RuntimeError("DNS resolver returned error status")
    return tuple(
        str(item["data"])
        for item in data.get("Answer", ())
        if item.get("type") == DNS_TYPES[record_type]
        and str(item.get("name", "")).rstrip(".").lower() == name
    )


def decode_txt(value: str) -> str:
    # Google DoH encloses each TXT chunk in double quotes.
    return value.replace('" "', "").strip('"').strip().lower()


def mx_hosts(records: tuple[str, ...]) -> frozenset[str]:
    hosts = set()
    for record in records:
        parts = record.split()
        if len(parts) == 2 and parts[0].isdigit():
            hosts.add(parts[1].lower().rstrip("."))
    return frozenset(hosts)


def resend_mta_target(records: tuple[str, ...]) -> bool:
    """Match displayed Resend CNAME infrastructure suffix; not proof of ownership."""
    return any(v.lower().rstrip(".").endswith(".mta.net") for v in records)


def assess(resolve: Callable[[str, str], tuple[str, ...]], return_path: str = "send") -> dict:
    if not return_path or len(return_path) > 63 or not return_path[0].isalpha() \
            or not return_path[-1].isalnum() \
            or not all(c.isalnum() or c == "-" for c in return_path):
        raise ValueError("invalid return path label")
    result = {}
    root_mx = mx_hosts(resolve(ROOT, "MX"))
    root_txt = [decode_txt(v) for v in resolve(ROOT, "TXT")]
    root_spf = [v for v in root_txt if v.startswith("v=spf1")]
    root_dmarc = [decode_txt(v) for v in resolve("_dmarc." + ROOT, "TXT")]
    result["zoho_mx_preserved"] = root_mx == ZOHO_MX
    result["zoho_spf_preserved"] = (
        len(root_spf) == 1 and "include:zohomail.com" in root_spf[0]
        and "amazonses.com" not in root_spf[0]
    )
    result["root_dmarc_exists"] = any(v.startswith("v=dmarc1;") for v in root_dmarc)

    # Resend owner dashboard 2026-10-14: TXT resend._domainkey.mail,
    # CNAME rsend.mail, CNAME send.mail, no receiving records.
    # New provider-specific exact CNAME contents must be copied from dashboard.
    return_domain = return_path + "." + SENDER
    result["resend_rsend_cname_present"] = resend_mta_target(
        resolve("rsend." + SENDER, "CNAME")
    )
    result["resend_return_path_cname_present"] = resend_mta_target(
        resolve(return_domain, "CNAME")
    )
    dkim_txt = [decode_txt(v) for v in resolve("resend._domainkey." + SENDER, "TXT")]
    result["resend_dkim_present"] = any(
        "p=" in v and len(v) > 80 for v in dkim_txt
    )
    result["dns_prerequisites_present"] = all(result.values())
    # No false claims: public DNS shape cannot verify exact dashboard targets,
    # Resend provider account state, synthetic mail receipt or beta permission.
    result["resend_exact_record_values_verified"] = False
    result["resend_provider_verified"] = False
    result["synthetic_mail_received"] = False
    result["beta_release_authorized"] = False
    result["status"] = (
        "DNS_SHAPE_PRESENT_MANUAL_GATES_HOLD"
        if result["dns_prerequisites_present"]
        else "DNS_PREREQUISITES_MISSING_HOLD"
    )
    result["checked_domain"] = SENDER
    result["return_path_name"] = return_domain
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--return-path", default="send",
                        help="Resend configured return-path label (default: send)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = assess(google_doh, args.return_path)
    except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
        print("BETA_EMAIL_DNS_LOOKUP_BLOCKED type=" + type(exc).__name__, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print(report["status"])
        for name in ("zoho_mx_preserved", "zoho_spf_preserved", "root_dmarc_exists",
                     "resend_rsend_cname_present", "resend_return_path_cname_present",
                     "resend_dkim_present", "resend_exact_record_values_verified",
                     "resend_provider_verified", "synthetic_mail_received",
                     "beta_release_authorized"):
            print(f"{name}={str(report[name]).upper()}")
        print("Public DNS only: no exact dashboard-value comparison, DNS edits, mail or secrets.")
    return 0 if report["dns_prerequisites_present"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
