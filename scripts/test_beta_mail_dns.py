#!/usr/bin/env python3
"""Offline regression of 2026 Resend TXT DKIM + CNAME sending records."""
import unittest

from check_beta_mail_dns import assess, decode_txt, mx_hosts, resend_mta_target


def fixtures():
    return {
        ("gdglobal.kr", "MX"): (
            "10 mx.zoho.com.", "20 mx2.zoho.com.", "50 mx3.zoho.com."),
        ("gdglobal.kr", "TXT"): (
            '"v=spf1 include:zohomail.com ~all"', '"zoho-verification=safe"'),
        ("_dmarc.gdglobal.kr", "TXT"): (
            '"v=DMARC1; p=none; rua=mailto:ops@example.test"',),
        ("rsend.mail.gdglobal.kr", "CNAME"): (
            "rsend-ap-synthetic-region.mta.net.",),
        ("send.mail.gdglobal.kr", "CNAME"): (
            "send.synthetic-routing.mta.net.",),
        ("resend._domainkey.mail.gdglobal.kr", "TXT"): (
            '"p=" "' + "A" * 120 + '"',),
    }


class DnsAssessmentTests(unittest.TestCase):
    def assess(self, records, return_path="send"):
        return assess(lambda name, typ: records.get((name, typ), ()), return_path)

    def test_shape_only_never_claims_resend_verification_or_beta_open(self):
        result = self.assess(fixtures())
        self.assertTrue(result["dns_prerequisites_present"])
        self.assertEqual(result["status"], "DNS_SHAPE_PRESENT_MANUAL_GATES_HOLD")
        self.assertFalse(result["resend_exact_record_values_verified"])
        self.assertFalse(result["resend_provider_verified"])
        self.assertFalse(result["synthetic_mail_received"])
        self.assertFalse(result["beta_release_authorized"])

    def test_empty_or_missing_sending_records_fail(self):
        records = fixtures()
        for name in ("send.mail.gdglobal.kr", "rsend.mail.gdglobal.kr",
                     "resend._domainkey.mail.gdglobal.kr"):
            for typ in ("CNAME", "TXT"):
                records.pop((name, typ), None)
        result = self.assess(records)
        self.assertFalse(result["dns_prerequisites_present"])
        self.assertFalse(result["resend_dkim_present"])
        self.assertFalse(result["resend_rsend_cname_present"])
        self.assertFalse(result["resend_return_path_cname_present"])

    def test_old_legacy_mx_spf_does_not_count_as_new_cname(self):
        records = fixtures()
        records.pop(("rsend.mail.gdglobal.kr", "CNAME"))
        records.pop(("send.mail.gdglobal.kr", "CNAME"))
        records[("send.mail.gdglobal.kr", "MX")] = (
            "10 feedback-smtp.us-east-1.amazonses.com.",)
        records[("send.mail.gdglobal.kr", "TXT")] = (
            '"v=spf1 include:amazonses.com ~all"',)
        self.assertFalse(self.assess(records)["dns_prerequisites_present"])

    def test_bad_cname_destination_is_blocker(self):
        records = fixtures()
        records[("send.mail.gdglobal.kr", "CNAME")] = ("attacker.invalid.",)
        self.assertFalse(self.assess(records)["resend_return_path_cname_present"])
        self.assertFalse(resend_mta_target(("other.invalid.",)))

    def test_accidental_root_mx_replacement_is_blocker(self):
        records = fixtures()
        records[("gdglobal.kr", "MX")] = ("10 alternative.example.org.",)
        self.assertFalse(self.assess(records)["zoho_mx_preserved"])
        self.assertFalse(self.assess(records)["dns_prerequisites_present"])

    def test_second_root_spf_record_is_blocker(self):
        records = fixtures()
        records[("gdglobal.kr", "TXT")] += ('"v=spf1 include:amazonses.com ~all"',)
        self.assertFalse(self.assess(records)["zoho_spf_preserved"])
        self.assertFalse(self.assess(records)["dns_prerequisites_present"])

    def test_custom_return_path_checks_right_cname(self):
        records = fixtures()
        self.assertFalse(self.assess(records, "outbound")["dns_prerequisites_present"])
        records[("outbound.mail.gdglobal.kr", "CNAME")] = records[
            ("send.mail.gdglobal.kr", "CNAME")]
        self.assertTrue(self.assess(records, "outbound")["dns_prerequisites_present"])

    def test_invalid_return_path_rejected(self):
        with self.assertRaises(ValueError):
            assess(lambda n, t: (), "../danger")

    def test_dns_txt_and_mx_decoding(self):
        self.assertEqual(decode_txt('"v=spf1 " "include:zohomail.com ~all"'),
                         "v=spf1 include:zohomail.com ~all")
        self.assertEqual(mx_hosts(("10 mx.zoho.com.", "20 mx2.zoho.com.")),
                         frozenset(("mx.zoho.com", "mx2.zoho.com")))


if __name__ == "__main__":
    unittest.main()
