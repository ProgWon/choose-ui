import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "choose-ui"


class CanonicalRules(unittest.TestCase):
    def test_generated_matrix_is_current_and_rules_are_valid(self):
        completed = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "rules_tool.py"), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("matrix is current", completed.stdout)

    def test_matrix_declares_canonical_source(self):
        matrix = (SKILL_DIR / "references" / "selection-controls.md").read_text(encoding="utf-8")
        self.assertIn("Generated from `selection-rules.json`", matrix)
        self.assertIn("first matching row wins", matrix)

    def test_skill_level_eval_has_activation_boundaries(self):
        path = ROOT / "evals" / "skill-cases.json"
        suite = json.loads(path.read_text(encoding="utf-8"))
        trigger_cases = suite["trigger_cases"]
        self.assertGreaterEqual(sum(case["should_trigger"] for case in trigger_cases), 3)
        self.assertGreaterEqual(sum(not case["should_trigger"] for case in trigger_cases), 3)

    def test_skill_level_eval_covers_output_and_judgment(self):
        suite = json.loads((ROOT / "evals" / "skill-cases.json").read_text(encoding="utf-8"))
        behavior = suite["behavior_cases"]
        modes = {case["expected_mode"] for case in behavior}
        self.assertEqual({"quick", "full"}, modes)
        self.assertTrue(any(case.get("expected_confidence") == "low" for case in behavior))
        self.assertTrue(any("must_not_include" in case for case in behavior))

    def test_seed_links_use_canonical_component_paths(self):
        sources = (SKILL_DIR / "references" / "sources.md").read_text(encoding="utf-8")
        self.assertNotIn("seed-design.io/docs/components", sources)


if __name__ == "__main__":
    unittest.main()
