import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "show-me" / "SKILL.md"
COMPONENTS = ROOT / "skills" / "show-me" / "references" / "components.md"
README = ROOT / "README.md"
DESCRIPTION = (
    "Shows what is hard to picture in chat (UI mockups and layouts, architecture and flow diagrams, "
    "data structures, how code runs) as pages in a browser tab that refreshes itself. Use only when the "
    "user asks to see something drawn or mocked up (\"vẽ ra cho tôi xem\", \"show me\", \"mock it up\"); "
    "do not offer it on your own."
)
COMPONENT_CLASSES = ["diagram", "compare", "option", "letter", "note", "mock", "mock-bar", "mock-url",
                     "mock-body", "mock-nav", "mock-tabs", "mock-form", "mock-actions", "field", "input",
                     "toggle", "btn", "placeholder", "pin", "legend", "tree", "tree-head", "row", "trace",
                     "trace-steps", "callout", "warn", "on"]


class DocsTest(unittest.TestCase):
    def test_frontmatter(self):
        text = SKILL.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        self.assertTrue(m, "no frontmatter")
        fields = dict(line.split(": ", 1) for line in m.group(1).splitlines())
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], "show-me")
        self.assertEqual(fields["description"], DESCRIPTION)
        self.assertLessEqual(len(DESCRIPTION), 1024)

    def test_skill_names_the_start_command_and_the_catalog(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("scripts/server.py start", text)
        self.assertIn("--foreground", text)
        self.assertIn("references/components.md", text)

    def test_catalog_shows_every_component_class(self):
        doc = COMPONENTS.read_text(encoding="utf-8")
        for cls in COMPONENT_CLASSES:
            self.assertRegex(doc, r'class="(?:[^"]*\s)?%s(?:\s[^"]*)?"' % re.escape(cls), cls)

    def test_readme_lists_show_me(self):
        self.assertIn("- **show-me** - ", README.read_text(encoding="utf-8"))
