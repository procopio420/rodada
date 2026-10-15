#!/usr/bin/env python3
"""Static public marketing contract: semantic copy, brand files and progressive UX."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
LANDING=ROOT/"apps/landing"
HTML=LANDING/"index.html"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements=[]
        self.text=[]
    def handle_starttag(self,tag,attrs):
        self.elements.append((tag,dict(attrs)))
    def handle_data(self,data):
        self.text.append(data)

class LandingMarketingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=HTML.read_text(encoding="utf-8")
        cls.doc=Parser()
        cls.doc.feed(cls.html)

    def test_copy_and_identity(self):
        content=" ".join(self.doc.text)
        self.assertIn("Mais uma",content)
        self.assertIn("rodada.",content)
        self.assertIn("Menos trabalho.",content)
        self.assertIn("Seu bar merece movimento. Menos correria.",content)
        self.assertIn('href="https://rodada.bar/"',self.html)
        self.assertIn('lang="pt-BR"',self.html)
        self.assertNotIn("Seu bar merece movimento. Não confusão.",content)

    def test_links_and_legal(self):
        anchors=[a.get("href","") for tag,a in self.doc.elements if tag=="a"]
        self.assertTrue(any(x.startswith("https://wa.me/5524936180751?text=") for x in anchors))
        for x in ("/privacidade","/termos","/exclusao-de-conta"):
            self.assertIn(x,anchors)
        self.assertFalse(any(x.startswith("http:") for x in anchors))

    def test_assets_and_disclaimers(self):
        imgs=[a for tag,a in self.doc.elements if tag=="img"]
        self.assertGreaterEqual(len(imgs),5)
        for a in imgs:
            self.assertTrue(a.get("alt","").strip(),a)
            self.assertTrue(a["src"].startswith("/"),a)
            self.assertTrue((LANDING/a["src"].lstrip("/")).is_file(),a)
        self.assertIn("Cena ilustrativa criada por IA",self.html)
        self.assertIn("QR mostrado é decorativo",self.html)
        self.assertIn("capturas do ambiente de teste",self.html)
        self.assertIn('property="og:image"',self.html)
        self.assertTrue((LANDING/"marketing"/"rodada-campanha.jpg").is_file())
        self.assertTrue((LANDING/"marketing"/"rodada-campanha-mobile.webp").is_file())
        docker=(LANDING/"Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY apps/landing/marketing/",docker)
        self.assertIn("COPY apps/landing/screens/",docker)

    def test_structure_and_accessibility(self):
        tags=[tag for tag,_ in self.doc.elements]
        self.assertEqual(tags.count("main"),1)
        self.assertEqual(tags.count("h1"),1)
        self.assertIn("details",tags)
        self.assertIn("nav",tags)
        self.assertEqual(self.html.count('role="tab"'),3)
        self.assertEqual(self.html.count('role="tabpanel"'),3)
        self.assertIn('role="tablist"',self.html)
        self.assertIn('aria-selected="true"',self.html)
        self.assertIn('aria-controls="panel-manage"',self.html)
        self.assertIn("ArrowRight",self.html)
        self.assertIn("prefers-reduced-motion",self.html)
        self.assertIn(":focus-visible",self.html)
        self.assertIn("max-width:380px",self.html)
        self.assertIn('class="mobile-cta" hidden',self.html)

    def test_no_tracking_dependencies(self):
        self.assertEqual(self.html.lower().count("<script"),1)
        self.assertNotIn("<script src=",self.html.lower())
        self.assertNotIn("fetch(",self.html.lower())
        self.assertNotIn("XMLHttpRequest",self.html)
        self.assertNotIn("google-analytics",self.html.lower())
        self.assertNotIn("fonts.googleapis.com",self.html.lower())
        self.assertIn("new IntersectionObserver",self.html)

if __name__=="__main__":
    unittest.main()
