import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "choose-ui"
PLUGIN_DIR = ROOT / ".claude-plugin"
SKILL_FILE = SKILL_DIR / "SKILL.md"


class SkillStructure(unittest.TestCase):
    def setUp(self):
        self.content = SKILL_FILE.read_text(encoding="utf-8")

    def test_frontmatter_has_required_fields(self):
        match = re.match(r"\A---\n(.*?)\n---\n", self.content, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name: choose-ui$")
        self.assertRegex(frontmatter, r"(?m)^description: \S.+$")

    def test_frontmatter_includes_required_keys(self):
        match = re.match(r"\A---\n(.*?)\n---\n", self.content, re.DOTALL)
        keys = set(re.findall(r"(?m)^([a-zA-Z0-9_-]+):", match.group(1)))
        self.assertTrue({"name", "description"}.issubset(keys))

    def test_description_defines_negative_activation_boundary(self):
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", self.content, re.DOTALL).group(1)
        self.assertIn("component type is unresolved", frontmatter)
        self.assertIn("must require a choice among interaction patterns", frontmatter)

    def test_skill_is_concise_and_finished(self):
        self.assertLess(len(self.content.splitlines()), 500)
        self.assertNotIn("TODO", self.content)

    def test_claude_plugin_uses_canonical_skill_directory(self):
        manifest = json.loads((PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("choose-ui", manifest["name"])
        self.assertEqual("./.claude/skills/", manifest["skills"])
        self.assertEqual("https://github.com/ProgWon/choose-ui", manifest["repository"])

    def test_claude_marketplace_installs_root_plugin(self):
        marketplace = json.loads((PLUGIN_DIR / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual("progwon-skills", marketplace["name"])
        plugin = marketplace["plugins"][0]
        self.assertEqual("choose-ui", plugin["name"])
        self.assertEqual("./", plugin["source"])
        self.assertTrue(plugin["strict"])

    def test_readme_documents_marketplace_install(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("/plugin marketplace add ProgWon/choose-ui", readme)
        self.assertIn("/plugin install choose-ui@progwon-skills", readme)

    def test_referenced_files_exist(self):
        links = re.findall(r"\]\((references/[^)]+)\)", self.content)
        self.assertGreaterEqual(len(links), 5)
        for relative in links:
            with self.subTest(reference=relative):
                self.assertTrue((SKILL_DIR / relative).is_file())

    def test_recommender_exists(self):
        self.assertTrue((SKILL_DIR / "scripts" / "recommend.py").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "rule_engine.py").is_file())
        self.assertTrue((SKILL_DIR / "scripts" / "rules_tool.py").is_file())
        self.assertTrue((ROOT / "evals" / "run_skill_evals.py").is_file())


if __name__ == "__main__":
    unittest.main()
