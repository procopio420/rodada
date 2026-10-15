#!/usr/bin/env python3
"""Static contract checks for the public Rodada landing (no network required)."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "apps/landing"
HTML = LANDING / "index.html"

class LandingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs = []
        self.text = []
    def handle_starttag(self, tag, attrs):
        self.attrs.append((tag, dict(attrs)))
    def handle_data(self, data):
        self.text.append(data)

class LandingMarketingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.document = LandingParser()
        cls.document.feed(cls.html)
        cls.elements = cls.document.attrs

    def test_brand_and_headline(self):
        visible = " ".join(self.document.text)
        self.assertIn("Mais uma rodada.", visible)
        self.assertIn("Menos trabalho.", visible)
        self.assertIn("Seu bar merece movimento. Não confusão.", visible)
        self.assertIn('href="https://rodada.bar/"', self.html)
        self.assertIn('lang="pt-BR"', self.html)

    def test_links_and_legal_routes(self):
        links = [attrs.get("href", "") for tag, attrs in self.elements if tag == "a"]
        self.assertTrue(any(link.startswith("https://wa.me/5524936180751?text=") for link in links))
        for target in ["/privacidade", "/termos", "/exclusao-de-conta"]:
            self.assertIn(target, links)
        self.assertFalse(any(link.startswith("http:") for link in links))

    def test_local_screens_and_alt(self):
        pics = [attrs for tag, attrs in self.elements if tag == "img"]
        self.assertGreaterEqual(len(pics), 4)
        for pic in pics:
            self.assertTrue(pic.get("alt", "").strip(), pic)
            src = pic["src"]
            self.assertTrue(src.startswith("/"), src)
            self.assertTrue((LANDING / src.removeprefix("/")).is_file(), src)
        self.assertIn("Capturas do ambiente de teste", self.html)

    def test_semantics_and_accessibility(self):
        tags = [tag for tag, _ in self.elements]
        self.assertEqual(tags.count("main"), 1)
        self.assertEqual(tags.count("h1"), 1)
        self.assertIn("nav", tags)
        self.assertIn("details", tags)
        self.assertIn(":focus-visible", self.html)
        self.assertIn("prefers-reduced-motion", self.html)
        self.assertIn("max-width:380px", self.html)

    def test_no_third_party_scripts_or_tracking(self):
        # One audited inline enhancement may control the mobile sticky CTA.
        self.assertEqual(self.html.lower().count("<script"), 1)
        self.assertNotIn("<script src=", self.html.lower())
        self.assertNotIn("fetch(", self.html.lower())
        self.assertNotIn("XMLHttpRequest", self.html)
        self.assertIn('const observer = new IntersectionObserver', self.html)
        self.assertIn('class="mobile-cta" hidden', self.html)
        self.assertIn('class="nav-cta-short"', self.html)
        self.assertNotIn("google-analytics", self.html.lower())
        self.assertNotIn("fonts.googleapis.com", self.html.lower())
        self.assertNotIn("100% garantido", self.html.lower())

if __name__ == "__main__":
    unittest.main()
