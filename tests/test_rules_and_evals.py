import itertools
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "choose-ui"
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.path.insert(0, str(ROOT / "evals"))

from rule_engine import choose_ui  # noqa: E402
from run_skill_evals import (  # noqa: E402
    TRIGGER_TOOLS,
    contains_all_groups,
    field_block,
    parse_stream,
    score_behavior,
    score_trigger,
)


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
        self.assertEqual(["Skill", "Read", "Grep", "Glob"], TRIGGER_TOOLS)

    def test_skill_level_eval_covers_output_and_judgment(self):
        suite = json.loads((ROOT / "evals" / "skill-cases.json").read_text(encoding="utf-8"))
        behavior = suite["behavior_cases"]
        modes = {case["expected_mode"] for case in behavior}
        self.assertEqual({"quick", "full"}, modes)
        self.assertTrue(any("low" in case.get("confidence_terms", []) for case in behavior))
        self.assertTrue(all(case.get("semantic_checks") for case in behavior))
        self.assertFalse(any("must_include" in case for case in behavior))
        inventory_case = next(case for case in behavior if case["name"] == "project component inventory adapts names")
        self.assertEqual(["Skill", "Read", "Grep", "Glob"], inventory_case["tools"])

    def test_rulebook_covers_full_flag_grid_without_fallback(self):
        fields = itertools.product(
            ["input", "filter", "view-switch", "action", "navigation", "setting"],
            [0, 1, 2, 4, 5, 6, 12],
            ["single", "multiple"],
            ["low", "high"],
            ["any", "mobile", "desktop"],
            ["submit", "immediate"],
            ["low", "high"],
            [False, True],
            [False, True],
            [False, True],
        )
        total = 0
        for intent, options, selection, comparison, platform, effect, frequency, search, custom, rich in fields:
            total += 1
            result = choose_ui(
                {
                    "intent": intent,
                    "options": options,
                    "selection": selection,
                    "comparison": comparison,
                    "platform": platform,
                    "effect": effect,
                    "frequency": frequency,
                    "search": search,
                    "custom_value": custom,
                    "rich_options": rich,
                }
            )
            self.assertNotEqual("manual-context-required", result.rule_id)
        self.assertEqual(16_128, total)

    def test_live_eval_stream_parser_and_language_tolerant_scoring(self):
        stream = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "tool_use", "name": "Skill", "input": {"skill": "choose-ui"}}
                            ]
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "result",
                        "is_error": False,
                        "result": "추천: 정적 값\n이유: 선택지가 하나뿐입니다.",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        transcript = parse_stream(stream)
        trigger = score_trigger({"name": "positive", "should_trigger": True}, transcript)
        behavior = score_behavior(
            {
                "name": "quick",
                "expected_mode": "quick",
                "recommendation_terms": ["static value", "정적 값"],
                "semantic_checks": ["one choice"],
            },
            transcript,
        )
        self.assertTrue(trigger.passed)
        self.assertTrue(behavior.passed)

    def test_recommendation_term_groups_require_each_concept(self):
        groups = [["search", "검색"], ["multiple", "다중"], ["list", "리스트", "combobox"]]
        self.assertTrue(contains_all_groups("추천: 검색 가능한 다중 선택 리스트", groups))
        self.assertFalse(contains_all_groups("추천: 검색 가능한 단일 선택 리스트", groups))

    def test_multiline_recommendation_is_scored_as_one_field(self):
        response = "\n".join(
            [
                "Recommendation: 모바일 필터 패널",
                "  상단 검색 입력과 다중 선택 체크박스 리스트",
                "Confidence: medium",
                "Why: 명시된 검색 요구를 유지합니다.",
            ]
        )
        block = field_block(response, "recommendation")
        self.assertIn("검색 입력", block)
        self.assertNotIn("Confidence", block)

    def test_full_korean_field_aliases_accept_natural_avoid_label(self):
        response = "\n".join(
            [
                "추천: 체크박스",
                "확신도: 높음",
                "이유: 제출 시점에 확정되는 독립 동의입니다.",
                "피해야 할 것: 스위치",
                "필요한 상태: 선택, 미선택, 오류",
                "접근성: 레이블을 체크박스와 연결합니다.",
                "가정: 없음",
                "근거: WAI-ARIA APG",
            ]
        )
        stream = "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [
                                {"type": "tool_use", "name": "Skill", "input": {"skill": "choose-ui"}}
                            ]
                        },
                    }
                ),
                json.dumps({"type": "result", "is_error": False, "result": response}, ensure_ascii=False),
            ]
        )
        result = score_behavior(
            {
                "name": "Korean full",
                "expected_mode": "full",
                "recommendation_terms": ["checkbox", "체크박스"],
                "confidence_terms": ["high", "높음"],
            },
            parse_stream(stream),
        )
        self.assertTrue(result.passed, result.checks)

    def test_seed_links_use_canonical_component_paths(self):
        sources = (SKILL_DIR / "references" / "sources.md").read_text(encoding="utf-8")
        self.assertNotIn("seed-design.io/docs/components", sources)


if __name__ == "__main__":
    unittest.main()
