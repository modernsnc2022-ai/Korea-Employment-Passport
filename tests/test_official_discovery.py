#!/usr/bin/env python3
"""Offline regression tests for official KP2MI/HRD discovery (never contacts network)."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import watch_id_official_discovery as d


def kp_input(title="PENGUMUMAN PENDAFTARAN UBT UMUM SEKTOR MANUFAKTUR TAHUN 2026"):
    return {"recordsTotal": 2300, "data": [
        {"id": 11, "tanggal": "15 October 2026",
         "judul": '<a href="/gtog-detail/korea/new"> ' + title + "</a>",
         "gtgkorea": "<p>Schedule may change</p>"},
        {"id": 10, "tanggal": "30 December 2025",
         "judul": '<a href="/gtog-detail/korea/old">2025 closed</a>',
         "gtgkorea": "<p>Previous cohort</p>"}
    ]}


def hrd_input():
    return """<form><input id="pageIndex" name="pageIndex" type="hidden" value="1"/></form>
    <tr id="tr_1" lcnsId="001" examYear="2026" examNot="14" examNation="012">
      <td>CBT</td><td>The 13th recruitment of the point system in Indonesia(Manufacturing)_Jakarta</td>
      <td>Indonesia</td><td>2026-02-10 ~ 2026-02-12</td>
      <td>2026-06-04 ~ 2026-06-29</td><td>2026-09-10</td></tr>
    <tr id="tr_2" lcnsId="001" examYear="2026" examNot="54" examNation="012">
      <td>CBT</td><td>Indonesia(Root Industry/Mold)</td>
      <td>Indonesia</td><td>2026-02-10</td><td>Undecided</td><td>Undecided</td></tr>
    <tr id="tr_3" lcnsId="001" examYear="2026" examNot="99" examNation="011">
      <td>CBT</td><td>Philippines Manufacturing</td><td>Philippines</td>
      <td>Undecided</td><td>Undecided</td><td>Undecided</td></tr>"""


class TestDiscovery(unittest.TestCase):
    def setUp(self):
        self.kp = d.canonical_kp2mi(kp_input())
        self.hrd, _ = d.parse_hrd_page(hrd_input(), 1)
        self.current = d.snapshot(self.kp, self.hrd, observed="2026-10-15T07:23:00+00:00")

    def test_actual_kp2mi_api_body_not_persisted(self):
        self.assertEqual(len(self.kp), 2)
        self.assertNotIn("gtgkorea", self.kp[0])
        self.assertNotIn("Schedule may change", str(self.kp))
        self.assertEqual(len(self.kp[0]["bodyDigest"]), 64)

    def test_hrd_indonesia_general_vs_other_cohorts(self):
        matching = [x for x in self.hrd if x["generalManufacturing2026"]]
        self.assertEqual([x["examNo"] for x in matching], ["14"])
        self.assertEqual(sum(x["generalManufacturing2026"] for x in self.hrd), 1)
        self.assertEqual(self.hrd[0]["nation"], "012")
        self.assertEqual(self.hrd[0]["type"], "CBT")

    def test_first_run_is_seed_not_new_alert(self):
        report = d.diff(None, self.current)
        self.assertTrue(report["initial"])
        self.assertEqual(report["events"], [])
        self.assertEqual(report["suppressedFirstRun"], 5)

    def test_unchanged_repeat_deduplicates(self):
        self.assertEqual(d.diff(self.current, copy.deepcopy(self.current))["events"], [])

    def test_new_important_notice_requires_review(self):
        updated = copy.deepcopy(self.current)
        template = copy.deepcopy(self.kp[0])
        template["key"] = "kp2mi:98"
        template["id"] = 98
        template["title"] = "PENGUMUMAN LAMARAN ONLINE GENERAL MANUFACTURING 2026"
        template["generalManufacturingFinalCandidate"] = True
        updated["records"].append(template)
        events = d.diff(self.current, updated)["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["kind"], "new_notice_or_exam")
        self.assertTrue(events[0]["maybeFinalApplication"])
        self.assertTrue(events[0]["needsHumanReview"])
        self.assertFalse(updated["betaOpenAuthorized"])

    def test_body_change_also_triggers_review(self):
        changed = copy.deepcopy(self.current)
        notice = next(x for x in changed["records"] if x["key"] == "kp2mi:11")
        notice["bodyDigest"] = "9" * 64
        events = d.diff(self.current, changed)["events"]
        self.assertEqual([x["kind"] for x in events], ["changed_notice_or_exam"])

    def test_missing_from_window_not_authoritative_delete(self):
        updated = copy.deepcopy(self.current)
        updated["records"] = [x for x in updated["records"] if x["key"] != "kp2mi:10"]
        result = d.diff(self.current, updated)
        self.assertEqual(result["events"], [])
        self.assertEqual(result["notSeenInBoundedWindow"], 1)

    def test_wrong_issuer_or_empty_lists_fail_closed(self):
        bad = kp_input()
        bad["data"][0]["judul"] = '<a href="https://evil.test/private">CLAIM</a>'
        with self.assertRaises(ValueError):
            d.canonical_kp2mi(bad)
        with self.assertRaises(ValueError):
            d.snapshot(self.kp, [], observed="2026-10-15T07:23:00+00:00")
        with self.assertRaises(ValueError):
            d.parse_hrd_page(hrd_input().replace('value="1"', 'value="2"'), 1)

    def test_prior_source_coverage_required(self):
        malformed = copy.deepcopy(self.current)
        malformed["sourcesComplete"] = ["kp2mi"]
        with self.assertRaises(ValueError):
            d.diff(malformed, self.current)
        self.assertFalse(self.current["sourceHashAutoAccepted"])
        self.assertFalse(self.current["betaOpenAuthorized"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
