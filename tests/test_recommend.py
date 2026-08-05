import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "choose-ui" / "scripts" / "recommend.py"
SPEC = importlib.util.spec_from_file_location("choose_ui_recommend", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RecommendationCases(unittest.TestCase):
    def test_public_evaluation_cases(self):
        cases_path = ROOT / "evals" / "cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 10)

        for case in cases:
            with self.subTest(case=case["name"]):
                result = MODULE.choose_ui(case["input"])
                self.assertEqual(case["expected"], result.recommendation)

    def test_negative_option_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            MODULE.choose_ui({"intent": "input", "options": -1})

    def test_missing_option_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "options is required"):
            MODULE.choose_ui({"intent": "input"})

    def test_boolean_option_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be an integer"):
            MODULE.choose_ui({"intent": "input", "options": True})

    def test_dynamic_context_is_explained(self):
        result = MODULE.choose_ui({"intent": "input", "options": 8, "dynamic": True})
        self.assertTrue(any("upper-bound" in item for item in result.assumptions))


if __name__ == "__main__":
    unittest.main()
