#!/usr/bin/env python3
"""Offline regression for the read-only KEP mail-DNS release audit."""
import unittest

from check_beta_mail_dns import assess, decode_txt, mx_hosts


def fixtures():
    return {
        ("gdglobal.kr", "MX"): (
            "10 mx.zoho.com.", "20 mx2.zoho.com.", "50 mx3.zoho.com."),
        ("gdglobal.kr", "TXT"): (
            '"v=spf1 include:zohomail.com ~all"', '"zoho-verification=safe"'),
        ("_dmarc.gdglobal.kr", "TXT"): (
            '"v=DMARC1; p=none; rua=mailto:ops@example.test"',),
        ("send.mail.gdglobal.kr", "MX"): (
            "10 feedback-smtp.us-east-1.amazonses.com.",),
        ("send.mail.gdglobal.kr", "TXT"): (
            '"v=spf1 include:amazonses.com ~all"',),
        ("resend._domainkey.mail.gdglobal.kr", "TXT"): (
            '"p=" "' + "A" * 120 + '"',),
    }


class DnsAssessmentTests(unittest.TestCase):
    def assess(self, records):
        return assess(lambda name, typ: records.get((name, typ), ()))

    def test_valid_dns_never_claims_provider_or_beta_open(self):
        result = self.assess(fixtures())
        self.assertTrue(result["dns_prerequisites_present"])
        self.assertEqual(result["status"], "DNS_PREREQUISITES_PRESENT_MANUAL_GATES_HOLD")
        self.assertFalse(result["resend_provider_verified"])
        self.assertFalse(result["synthetic_mail_received"])
        self.assertFalse(result["beta_release_authorized"])

    def test_unconfigured_sending_subdomain_fails_readiness(self):
        records = fixtures()
        for name in ("send.mail.gdglobal.kr", "resend._domainkey.mail.gdglobal.kr"):
            records.pop((name, "MX"), None)
            records.pop((name, "TXT"), None)
        result = self.assess(records)
        self.assertFalse(result["dns_prerequisites_present"])
        self.assertFalse(result["resend_dkim_present"])
        self.assertFalse(result["resend_return_path_spf_exists"])

    def test_accidental_root_mx_replacement_is_blocker(self):
        records = fixtures()
        records[("gdglobal.kr", "MX")] = ("10 alternative.example.org.",)
        result = self.assess(records)
        self.assertFalse(result["zoho_mx_preserved"])
        self.assertFalse(result["dns_prerequisites_present"])

    def test_accidental_root_spf_second_record_is_blocker(self):
        records = fixtures()
        records[("gdglobal.kr", "TXT")] += ('"v=spf1 include:amazonses.com ~all"',)
        result = self.assess(records)
        self.assertFalse(result["zoho_spf_preserved"])
        self.assertFalse(result["dns_prerequisites_present"])

    def test_custom_return_path_must_match_resend_records(self):
        records = fixtures()
        self.assertFalse(assess(lambda n, t: records.get((n, t), ()), "outbound")[
            "dns_prerequisites_present"])
        records[("outbound.mail.gdglobal.kr", "MX")] = records[
            ("send.mail.gdglobal.kr", "MX")]
        records[("outbound.mail.gdglobal.kr", "TXT")] = records[
            ("send.mail.gdglobal.kr", "TXT")]
        self.assertTrue(assess(lambda n, t: records.get((n, t), ()), "outbound")[
            "dns_prerequisites_present"])

    def test_invalid_return_path_not_accepted(self):
        with self.assertRaises(ValueError):
            assess(lambda n, t: (), "../danger")

    def test_dns_decoding_and_host_parsing(self):
        self.assertEqual(decode_txt('"v=spf1 " "include:zohomail.com ~all"'),
                         "v=spf1 include:zohomail.com ~all")
        self.assertEqual(mx_hosts(("10 mx.zoho.com.", "20 mx2.zoho.com.")),
                         frozenset(("mx.zoho.com", "mx2.zoho.com")))


if __name__ == "__main__":
    unittest.main()
