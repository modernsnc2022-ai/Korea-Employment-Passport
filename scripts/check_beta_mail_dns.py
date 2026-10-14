#!/usr/bin/env python3
"""Read-only KEP beta outbound mail DNS audit; never edits DNS or sends mail.

Exit 0: public DNS prerequisites present (NOT provider authorization).
Exit 2: a DNS readiness HOLD; exit 1: DNS resolver unavailable.
Resend Dashboard domain=verified, API-key provisioning, authorized synthetic
mailbox delivery, and owner OPEN remain separate mandatory manual gates.
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
DNS_TYPES = {"MX": 15, "TXT": 16}


def google_doh(name: str, record_type: str) -> tuple[str, ...]:
    query = urlencode({"name": name, "type": record_type})
    request = Request(
        "https://dns.google/resolve?" + query,
        headers={"Accept": "application/dns-json", "User-Agent": "KEP-ReadOnly-DNS-Preflight/1.0"},
    )
    with urlopen(request, timeout=12) as response:
        data = json.load(response)
    if data.get("Status") not in (0, 3):  # NXDOMAIN is a valid unconfigured state
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

    # Resend's default custom Return-Path is send.<verified-sending-domain>.
    # Exact values and any custom return-path name must be read from Resend.
    return_domain = return_path + "." + SENDER
    sending_mx = mx_hosts(resolve(return_domain, "MX"))
    sending_txt = [decode_txt(v) for v in resolve(return_domain, "TXT")]
    dkim_txt = [decode_txt(v) for v in resolve("resend._domainkey." + SENDER, "TXT")]
    result["resend_return_path_mx_exists"] = bool(sending_mx)
    result["resend_return_path_spf_exists"] = any(
        v.startswith("v=spf1") and "include:amazonses.com" in v
        for v in sending_txt
    )
    result["resend_dkim_present"] = any(
        "p=" in v and len(v) > 80 for v in dkim_txt
    )
    result["dns_prerequisites_present"] = all(result.values())
    result["resend_provider_verified"] = False  # Public DNS alone can never confirm this
    result["synthetic_mail_received"] = False   # No mail must be sent by this audit
    result["beta_release_authorized"] = False  # Requires separate owner authorization
    result["status"] = (
        "DNS_PREREQUISITES_PRESENT_MANUAL_GATES_HOLD"
        if result["dns_prerequisites_present"]
        else "DNS_PREREQUISITES_MISSING_HOLD"
    )
    result["checked_domain"] = SENDER
    result["return_path_name"] = return_domain
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--return-path", default="send",
                        help="Resend-configured return-path label (default: send)")
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
                     "resend_return_path_mx_exists", "resend_return_path_spf_exists",
                     "resend_dkim_present", "resend_provider_verified",
                     "synthetic_mail_received", "beta_release_authorized"):
            print(f"{name}={str(report[name]).upper()}")
        print("Public DNS read-only; no credentials, DNS edits or emails performed.")
    return 0 if report["dns_prerequisites_present"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
