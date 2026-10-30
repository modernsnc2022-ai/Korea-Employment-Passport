import unittest
from pathlib import Path
from release_copy_contract import RELEASE_GATES, validate_release_gate_copy

PAGE = (Path(__file__).resolve().parents[1] / 'docs/beta.html').read_text(encoding='utf-8')

class ReleaseCopyContractTest(unittest.TestCase):
    def test_current_public_explanation(self):
        self.assertEqual(validate_release_gate_copy(PAGE), [])

    def test_each_requirement_is_mandatory(self):
        for key in RELEASE_GATES:
            with self.subTest(key=key):
                changed = PAGE.replace(f'data-release-gate="{key}"', 'data-release-gate="missing"')
                self.assertTrue(validate_release_gate_copy(changed))

    def test_empty_requirement_cannot_pass_by_id_alone(self):
        for key, terms in RELEASE_GATES.items():
            with self.subTest(key=key):
                self.assertTrue(validate_release_gate_copy(PAGE.replace(terms[0], 'REMOVED')))

    def test_hidden_and_duplicate_explanation_rejected(self):
        self.assertTrue(validate_release_gate_copy(PAGE.replace('id="releaseGateNote"', 'id="releaseGateNote" hidden')))
        self.assertTrue(validate_release_gate_copy(PAGE + PAGE))

    def test_interest_does_not_grant_access_and_final_documents_stay_held(self):
        for phrase in ('tahap lamaran final tetap HOLD', 'pengiriman minat bukan aktivasi akses beta'):
            with self.subTest(phrase=phrase):
                self.assertTrue(validate_release_gate_copy(PAGE.replace(phrase, 'REMOVED')))

if __name__ == '__main__':
    unittest.main()
