import re
import unittest
from pathlib import Path

FRAME = Path(__file__).resolve().parents[2] / "skills" / "show-me" / "scripts" / "frame.html"
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs"
HLJS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"
ALLOWED_HOSTS = {"https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com",
                 "https://fonts.googleapis.com", "https://fonts.gstatic.com"}
COMPONENT_CLASSES = ["diagram", "compare", "option", "letter", "note", "mock", "mock-bar", "mock-url",
                     "mock-body", "mock-nav", "mock-tabs", "mock-form", "mock-actions", "field", "input",
                     "toggle", "btn", "placeholder", "pin", "legend", "tree", "tree-head", "row", "trace",
                     "trace-steps", "callout", "warn", "on"]


class FrameTest(unittest.TestCase):
    def setUp(self):
        self.html = FRAME.read_text(encoding="utf-8")

    def test_placeholders_appear_once(self):
        for name in ("TITLE", "CONTENT", "BOOT"):
            self.assertEqual(self.html.count("{{%s}}" % name), 1, name)

    def test_dom_contract(self):
        self.assertIn('<script id="sm-boot" type="application/json">{{BOOT}}</script>', self.html)
        for element_id in ("sm-tabs", "sm-content", "sm-status", "sm-banner"):
            self.assertIn('id="%s"' % element_id, self.html)

    def test_pinned_libraries_and_no_other_hosts(self):
        self.assertIn(MERMAID, self.html)
        self.assertIn(HLJS, self.html)
        hosts = set(re.findall(r"""(https://[^/"'\s)]+)""", self.html))
        self.assertLessEqual(hosts, ALLOWED_HOSTS)

    def test_every_component_class_is_styled(self):
        css = "".join(re.findall(r"<style[^>]*>(.*?)</style>", self.html, re.S))
        for cls in COMPONENT_CLASSES:
            self.assertRegex(css, r"\.%s(?![\w-])" % re.escape(cls), cls)

    def test_light_dark_and_stored_choice(self):
        self.assertIn("prefers-color-scheme: dark", self.html)
        self.assertIn('[data-theme="dark"]', self.html)
        self.assertIn("show-me-theme", self.html)
