import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "auto_activate.py"
SPEC = importlib.util.spec_from_file_location("auto_activate", SCRIPT)
auto_activate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(auto_activate)


class AutoActivationHook(unittest.TestCase):
    def test_broad_product_builds_are_nudged(self):
        prompts = [
            "이런 반려동물 예약 서비스를 처음부터 개발해줘.",
            "Build a subscription management SaaS from scratch.",
            "Create an admin dashboard for our inventory product.",
            "로그인 화면을 구현해줘.",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertTrue(auto_activate.should_nudge(prompt))

    def test_non_ui_scopes_are_not_nudged(self):
        prompts = [
            "결제 서비스의 백엔드만 개발해줘.",
            "Build the API only for this service.",
            "Build the server-side only for this app.",
            "앱의 PrimaryButton 색상만 바꿔줘.",
            "데이터베이스 마이그레이션을 작성해줘.",
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertFalse(auto_activate.should_nudge(prompt))

    def test_cli_emits_discrete_additional_context(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "쇼핑몰 서비스를 만들어줘.",
                },
                ensure_ascii=False,
            ),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual("UserPromptSubmit", output["hookEventName"])
        self.assertIn("invoke the available choose-ui skill", output["additionalContext"])

    def test_cli_is_silent_for_unrelated_prompt(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "README 오타를 고쳐줘."}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)


if __name__ == "__main__":
    unittest.main()
