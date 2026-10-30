#!/usr/bin/env python3
"""Unattended watcher checkpoint tests; synthetic inputs, no HTTP/production effects."""
import copy
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import official_discovery_state as state
import watch_id_official_discovery as watcher


def observation(when="2026-10-15T07:00:00+00:00"):
    kp = [
        {"key": "kp2mi:165", "provider": "kp2mi", "id": 165,
         "date": "15 October 2026", "title": "UBT UMUM MANUFAKTUR 2026",
         "url": "https://kp2mi.go.id/gtog-detail/korea/official",
         "bodyDigest": "0" * 64, "generalManufacturing2026": True,
         "generalManufacturingFinalCandidate": False, "genericApplicationReview": False}
    ]
    hrd = [
        {"key": "hrdk:012:2026:14:001", "provider": "hrdk", "nation": "012",
         "year": "2026", "examNo": "14", "lcnsId": "001",
         "type": "CBT", "title": "Indonesia(Manufacturing)_Jakarta",
         "countryName": "Indonesia", "period": "2026-02-10",
         "testDate": "2026-06-04", "resultDate": "2026-09-10",
         "url": "https://epstopik.hrdkorea.or.kr/epstopik/abot/exam/sechduleDetail.do?examNot=14",
         "generalManufacturing2026": True}
    ]
    return watcher.snapshot(kp, hrd, observed=when)


def next_time(snap, minutes=5):
    d = copy.deepcopy(snap)
    stamp = datetime.fromisoformat(snap["observedAtUtc"]) + timedelta(minutes=minutes)
    d["observedAtUtc"] = stamp.isoformat()
    return d


class StateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "official-observations.sqlite3"
        self.repo = Path(__file__).resolve().parents[1]
        self.first = observation()

    def save(self, snap):
        return state.record_success(self.db, snap, watcher.diff)

    def test_first_run_seeds_no_false_alerts(self):
        result = self.save(self.first)
        self.assertTrue(result["firstRun"])
        self.assertEqual(result["newQueued"], 0)
        self.assertEqual(state.pending_events(self.db), [])
        self.assertTrue(state.health(self.db, at="2026-10-15T07:30:00+00:00")["healthy"])

    def test_new_notice_and_changed_revision_create_dedup_review_events(self):
        self.save(self.first)
        second = next_time(self.first)
        added = copy.deepcopy(next(x for x in second["records"] if x["provider"] == "kp2mi"))
        added["key"] = "kp2mi:166"
        added["id"] = 166
        added["title"] = "MANUFACTURING 2026 NEW ONLINE JOB APPLICATION"
        added["url"] = "https://kp2mi.go.id/gtog-detail/korea/another"
        added["generalManufacturingFinalCandidate"] = True
        second["records"].append(added)
        result = self.save(second)
        self.assertEqual((result["eventsDetected"], result["newQueued"]), (1, 1))
        self.assertEqual(len(state.pending_events(self.db)), 1)
        self.assertTrue(state.pending_events(self.db)[0]["possible_final_application"])
        unchanged = next_time(second)
        self.assertEqual(self.save(unchanged)["newQueued"], 0)
        changed = next_time(unchanged)
        changed["records"][-1]["bodyDigest"] = "a" * 64
        self.assertEqual(self.save(changed)["newQueued"], 1)
        self.assertEqual(len(state.pending_events(self.db)), 2)
        later = next_time(changed)
        later["records"][-1]["bodyDigest"] = "0" * 64
        self.assertEqual(self.save(later)["newQueued"], 1)
        revisit = next_time(later)
        revisit["records"][-1]["bodyDigest"] = "a" * 64
        self.assertEqual(self.save(revisit)["newQueued"], 0)  # already reviewed revision

    def test_fetch_failure_preserves_checkpoint_and_does_not_approve(self):
        self.save(self.first)
        self.assertEqual(state.record_failure(self.db, RuntimeError("offline"), at="2026-10-15T07:15:00+00:00"), 1)
        self.assertEqual(state.record_failure(self.db, TimeoutError("offline"), at="2026-10-15T07:30:00+00:00"), 2)
        status = state.health(self.db, at="2026-10-15T07:31:00+00:00")
        self.assertFalse(status["healthy"])
        self.assertEqual(status["lastSuccessUtc"], self.first["observedAtUtc"])
        self.assertEqual(status["consecutiveFailures"], 2)
        self.assertEqual(len(state.pending_events(self.db)), 0)
        with closing(sqlite3.connect(self.db)) as conn:
            raw = conn.execute("SELECT last_observed_utc FROM checkpoint").fetchone()[0]
        self.assertEqual(raw, self.first["observedAtUtc"])
        later = next_time(self.first, 35)
        self.save(later)
        self.assertTrue(state.health(self.db, at="2026-10-15T07:36:00+00:00")["healthy"])

    def test_stale_and_never_healthy_are_not_silent_success(self):
        self.assertFalse(state.health(self.db, at="2026-10-15T07:00:00+00:00")["healthy"])
        self.save(self.first)
        self.assertFalse(state.health(self.db, at="2026-10-15T13:00:00+00:00", stale_hours=4)["healthy"])

    def test_out_of_order_time_and_unsafe_approved_payload_rejected(self):
        self.save(self.first)
        with self.assertRaises(ValueError):
            self.save(copy.deepcopy(self.first))
        bad = next_time(self.first)
        bad["betaOpenAuthorized"] = True
        with self.assertRaises(ValueError):
            self.save(bad)
        bad = next_time(self.first)
        bad["sourceHashAutoAccepted"] = True
        with self.assertRaises(ValueError):
            self.save(bad)
        with closing(sqlite3.connect(self.db)) as conn:
            stamp = conn.execute("SELECT last_observed_utc FROM checkpoint").fetchone()[0]
        self.assertEqual(stamp, self.first["observedAtUtc"])

    def test_missing_category_and_duplicate_identity_are_rejected(self):
        bad = copy.deepcopy(self.first)
        bad["records"] = [x for x in bad["records"] if x["provider"] != "hrdk"]
        with self.assertRaises(ValueError):
            self.save(bad)
        bad = copy.deepcopy(self.first)
        bad["records"].append(copy.deepcopy(bad["records"][0]))
        with self.assertRaises(ValueError):
            self.save(bad)
        self.assertFalse(self.db.exists())  # invalid data cannot even seed the DB

    def test_state_location_guard_prevents_committing_monitor_db(self):
        with self.assertRaises(ValueError):
            state.safe_external_path(self.repo / "monitor" / "live.db", self.repo)
        with self.assertRaises(ValueError):
            state.safe_external_path(Path(self.tmp.name) / "other.json", self.repo)
        self.assertEqual(state.safe_external_path(self.db, self.repo), self.db.resolve())


if __name__ == "__main__":
    unittest.main(verbosity=2)
