#!/usr/bin/env python3
"""Source-level pre-release checks. Run from repository root: python3 scripts/check_site_release.py
This does not verify rendering, email delivery, browser APIs, live HTTP, privacy compliance or indexing.
"""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
HOMES = {"it": "index.html", "en": "en/index.html", "fr": "fr.html",
         "de": "de.html", "es": "es.html", "pt": "pt.html"}
SERVICES = {"it": "servizi/index.html", "en": "services/index.html",
            "fr": "services/fr/index.html", "de": "services/de/index.html",
            "es": "services/es/index.html", "pt": "services/pt/index.html"}

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.language = None
        self.canonical = []
        self.alternates = {}
        self.ids = set()
        self.links = []
        self.noscript = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html": self.language = a.get("lang")
        if "id" in a: self.ids.add(a["id"])
        if tag == "link":
            if a.get("rel") == "canonical": self.canonical.append(a.get("href"))
            if a.get("rel") == "alternate" and a.get("hreflang"):
                self.alternates[a["hreflang"]] = a.get("href")
        if tag == "a": self.links.append(a.get("href", ""))
        if tag == "noscript": self.noscript += 1

problems = []
def check(ok, reason):
    if not ok: problems.append(reason)

for family, pages in [("home", HOMES), ("services", SERVICES)]:
    docs = {}
    for lang, path in pages.items():
        p = ROOT / path
        check(p.is_file(), f"{family}/{lang}: missing {path}")
        if not p.is_file(): continue
        s = p.read_text(encoding="utf-8")
        d = Document()
        d.feed(s)
        docs[lang] = d
        check(d.language == lang, f"{path}: wrong lang")
        check(len(d.canonical) == 1, f"{path}: need exactly one canonical")
        check(all(k in d.alternates for k in [*pages, "x-default"]),
              f"{path}: incomplete hreflang")
        check("<title>" in s and 'name="description"' in s,
              f"{path}: missing title/description")
        if family == "services":
            check({"sv-form", "sv-status", "sv-name", "sv-email", "sv-message"}.issubset(d.ids),
                  f"{path}: missing contact controls")
            check(d.noscript > 0 and "mailto:gossmere@gmail.com" in s,
                  f"{path}: missing fallback")
            check("<noscript><style>" not in s, f"{path}: CSP-incompatible inline fallback")
            check("/assets/services-contact.js" in s and "/assets/services-premium.css" in s,
                  f"{path}: missing CSS/JS link")
    for lang, doc in docs.items():
        for alt, url in doc.alternates.items():
            if alt == "x-default": continue
            other = docs.get(alt)
            if other and len(other.canonical) == 1:
                check(url == other.canonical[0],
                      f"{family}/{lang}: hreflang {alt} does not match canonical")
    if len(docs) == len(pages):
        for lang, doc in docs.items():
            for other_lang, other in docs.items():
                if other_lang in doc.alternates and lang in other.alternates:
                    check(doc.alternates[other_lang] == other.canonical[0],
                          f"{family}: inconsistent reciprocal mapping")

css = ROOT / "assets/services-premium.css"
js = ROOT / "assets/services-contact.js"
if css.exists() and js.exists():
    styles = css.read_text(encoding="utf-8")
    script = js.read_text(encoding="utf-8")
    check("html:not(.sv-js-enabled) .sv-contact .sv-form" in styles,
          "contact CSS missing JS readiness guard")
    check('classList.add("sv-js-enabled")' in script,
          "contact JS missing readiness marker")
else:
    problems.append("Missing shared contact assets")

sitemap = ROOT / "sitemap.xml"
if sitemap.exists():
    try: ET.parse(sitemap)
    except ET.ParseError as ex: problems.append(f"invalid sitemap XML: {ex}")
else: problems.append("missing sitemap.xml")

# Protect the exact site identity against future SEO regressions.
import json
for lang, path in HOMES.items():
    source = (ROOT / path).read_text(encoding="utf-8")
    blocks = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', source)
    parsed = []
    for block in blocks:
        try:
            parsed.append(json.loads(block))
        except json.JSONDecodeError:
            problems.append(f"{path}: invalid JSON-LD")
    site_nodes = [obj for obj in parsed if isinstance(obj, dict) and obj.get("@type") == "WebSite"]
    check(len(site_nodes) == 1, f"{path}: expected one WebSite JSON-LD node")
    if site_nodes:
        node = site_nodes[0]
        check(node.get("name") == "Gossmere", f"{path}: incorrect site name")
        check(node.get("alternateName") == "gossmere.com", f"{path}: missing domain fallback")
        check(node.get("url") == "https://gossmere.com/", f"{path}: incorrect domain URL")
    org_nodes = [obj for obj in parsed if isinstance(obj, dict) and obj.get("@type") == "Organization"]
    check(len(org_nodes) == 1, f"{path}: expected one Organization JSON-LD node")
    if org_nodes:
        org = org_nodes[0]
        check(org.get("@id") == "https://gossmere.com/#organization", f"{path}: organization ID changed")
        check("https://www.linkedin.com/company/gossmere/" in org.get("sameAs", []),
              f"{path}: missing verified official LinkedIn sameAs")
    check('href="https://www.linkedin.com/company/gossmere/"' in source,
          f"{path}: missing visible official LinkedIn link")
    check('property="og:site_name" content="Gossmere"' in source, f"{path}: missing Open Graph brand")
    check("Gossamer" not in source and "Gossamere" not in source,
          f"{path}: other brand spelling in identity signals")

if problems:
    for p in problems: print("FAIL:", p)
    sys.exit(1)
print("PASS: source consistency checks; browser and delivery QA still required")
