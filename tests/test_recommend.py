import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / ".claude" / "skills" / "choose-ui" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from rule_engine import choose_ui  # noqa: E402


class RecommendationCases(unittest.TestCase):
    def test_public_evaluation_cases(self):
        cases_path = ROOT / "evals" / "cases.json"
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 20)

        for case in cases:
            with self.subTest(case=case["name"]):
                result = choose_ui(case["input"])
                self.assertEqual(case["expected"], result.recommendation)
                self.assertEqual(case["rule"], result.rule_id)
                if "confidence" in case:
                    self.assertEqual(case["confidence"], result.confidence)

    def test_negative_option_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            choose_ui({"intent": "input", "options": -1})

    def test_missing_option_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "options is required"):
            choose_ui({"intent": "input"})

    def test_boolean_option_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be an integer"):
            choose_ui({"intent": "input", "options": True})

    def test_expected_max_cannot_shrink_current_count(self):
        with self.assertRaisesRegex(ValueError, "cannot be smaller"):
            choose_ui({"intent": "input", "options": 8, "expected_max_options": 4})

    def test_credible_upper_bound_changes_result_and_is_explained(self):
        result = choose_ui(
            {
                "intent": "input",
                "options": 3,
                "expected_max_options": 9,
                "platform": "mobile",
            }
        )
        self.assertEqual("input button opening a selection sheet", result.recommendation)
        self.assertTrue(any("credible upper bound" in item for item in result.assumptions))

    def test_reviewed_boundary_regressions(self):
        cases = [
            (
                {"intent": "setting", "options": 1, "effect": "submit"},
                "checkbox",
            ),
            (
                {"intent": "filter", "options": 6, "selection": "multiple", "search": True},
                "multi-select combobox",
            ),
            ({"intent": "view-switch", "options": 9}, "view menu"),
            ({"intent": "filter", "options": 3, "selection": "single"}, "select"),
            ({"intent": "input", "options": 5, "platform": "desktop"}, "select"),
            (
                {"intent": "input", "options": 6, "platform": "mobile"},
                "input button opening a selection sheet",
            ),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                self.assertEqual(expected, choose_ui(payload).recommendation)

    def test_documented_project_relative_cli_path_runs(self):
        completed = subprocess.run(
            [
                sys.executable,
                ".claude/skills/choose-ui/scripts/recommend.py",
                "--intent",
                "input",
                "--options",
                "5",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Recommendation: select", completed.stdout)


if __name__ == "__main__":
    unittest.main()
