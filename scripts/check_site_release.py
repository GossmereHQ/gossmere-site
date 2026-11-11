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
        check(not re.search(r">\s*(?:undefined|null)\s*<", s, re.I),
              f"{path}: unresolved visible placeholder")
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
            check(bool(re.search(r'<form\b[^>]*\bid="sv-form"[^>]*\bmethod="dialog"', s)),
                  f"{path}: unexpected contact form submit method")
            check(all(re.search(r'\bname="' + field + r'"', s) for field in
                      ("name", "company", "email", "phone", "service", "message")),
                  f"{path}: missing expected enquiry field")
            check('type="email"' in s and "aria-live=\"polite\"" in s,
                  f"{path}: missing email validation or accessible status")
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
    try:
        tree = ET.parse(sitemap)
        xml_ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        xhtml_ns = "{http://www.w3.org/1999/xhtml}"
        service_urls = {
            "it": "https://gossmere.com/servizi/",
            "en": "https://gossmere.com/services/",
            "fr": "https://gossmere.com/services/fr/",
            "de": "https://gossmere.com/services/de/",
            "es": "https://gossmere.com/services/es/",
            "pt": "https://gossmere.com/services/pt/",
            "x-default": "https://gossmere.com/services/",
        }
        sitemap_records = {}
        for entry in tree.getroot().findall(xml_ns + "url"):
            loc = entry.findtext(xml_ns + "loc")
            if loc:
                sitemap_records.setdefault(loc, []).append(entry)
        for locale, url in service_urls.items():
            if locale == "x-default":
                continue
            entries = sitemap_records.get(url, [])
            check(len(entries) == 1, f"sitemap service/{locale}: expected one URL")
            if len(entries) != 1:
                continue
            links = entries[0].findall(xhtml_ns + "link")
            actual = {}
            for link in links:
                if link.get("rel") == "alternate":
                    code = link.get("hreflang")
                    check(code not in actual, f"sitemap service/{locale}: duplicate hreflang {code}")
                    actual[code] = link.get("href")
            check(actual == service_urls,
                  f"sitemap service/{locale}: incomplete or inconsistent hreflang cluster")
    except ET.ParseError as ex:
        problems.append(f"invalid sitemap XML: {ex}")
else: problems.append("missing sitemap.xml")

# Legal pages belong to the public sitemap and must advertise their own canonicals.
for legal in ("privacy.html", "terms.html"):
    source = (ROOT / legal).read_text(encoding="utf-8")
    expected = f"https://gossmere.com/{legal}"
    parser = Document()
    parser.feed(source)
    check(parser.canonical == [expected], f"{legal}: missing or incorrect canonical")
    if sitemap.exists() and "sitemap_records" in locals():
        check(len(sitemap_records.get(expected, [])) == 1,
              f"{legal}: missing or duplicate sitemap URL")

# Verify the dedicated Italian SEO offer has one indexable URL and a clear route to contact.
seo_landing = ROOT / "servizi/seo/index.html"
check(seo_landing.is_file(), "missing Italian SEO audit landing")
if seo_landing.is_file():
    seo_source = seo_landing.read_text(encoding="utf-8")
    seo_doc = Document()
    seo_doc.feed(seo_source)
    seo_url = "https://gossmere.com/servizi/seo/"
    check(seo_doc.language == "it", "SEO audit landing: incorrect page language")
    check(seo_doc.canonical == [seo_url], "SEO audit landing: incorrect canonical")
    check(len(sitemap_records.get(seo_url, [])) == 1,
          "SEO audit landing: missing or duplicate sitemap URL")
    check('href="/servizi/#contact"' in seo_source,
          "SEO audit landing: missing existing contact form route")
    check(bool(re.search(r'<h1\b', seo_source)), "SEO audit landing: missing H1")
hub_source = (ROOT / "servizi/index.html").read_text(encoding="utf-8")
check('href="/servizi/seo/"' in hub_source, "services hub: missing SEO audit landing link")

# Verify the dedicated Italian corporate website offer and its conversion path.
web_landing = ROOT / "servizi/siti-web/index.html"
check(web_landing.is_file(), "missing Italian corporate websites landing")
if web_landing.is_file():
    web_source = web_landing.read_text(encoding="utf-8")
    web_doc = Document()
    web_doc.feed(web_source)
    web_url = "https://gossmere.com/servizi/siti-web/"
    check(web_doc.language == "it", "websites landing: incorrect page language")
    check(web_doc.canonical == [web_url], "websites landing: incorrect canonical")
    check(len(sitemap_records.get(web_url, [])) == 1,
          "websites landing: missing or duplicate sitemap URL")
    check('href="/servizi/#contact"' in web_source,
          "websites landing: missing existing contact form route")
    check(bool(re.search(r'<h1\b', web_source)), "websites landing: missing H1")
    check('BreadcrumbList' in web_source, "websites landing: missing breadcrumbs")
check('href="/servizi/siti-web/"' in hub_source,
      "services hub: missing corporate websites landing link")

# Verify the Italian automation offer, sitemap entry and contact route.
automation_landing = ROOT / "servizi/automazioni/index.html"
check(automation_landing.is_file(), "missing Italian automation landing")
if automation_landing.is_file():
    automation_source = automation_landing.read_text(encoding="utf-8")
    automation_doc = Document()
    automation_doc.feed(automation_source)
    automation_url = "https://gossmere.com/servizi/automazioni/"
    check(automation_doc.language == "it", "automation landing: incorrect language")
    check(automation_doc.canonical == [automation_url], "automation landing: incorrect canonical")
    check(len(sitemap_records.get(automation_url, [])) == 1,
          "automation landing: missing or duplicate sitemap URL")
    check('href="/servizi/#contact"' in automation_source,
          "automation landing: missing contact route")
    check(bool(re.search(r'<h1\b', automation_source)), "automation landing: missing H1")
    check('BreadcrumbList' in automation_source, "automation landing: missing breadcrumb")
check('href="/servizi/automazioni/"' in hub_source,
      "services hub: missing automation landing link")

# Ensure commercial landing pages are directly discoverable from the Italian homepage.
home_it_source = (ROOT / "index.html").read_text(encoding="utf-8")
for label, href in (
    ("corporate websites", "/servizi/siti-web/"),
    ("SEO audit", "/servizi/seo/"),
    ("automations", "/servizi/automazioni/"),
):
    check(bool(re.search(r'<a\\b[^>]*\\bhref="' + re.escape(href) + r'"', home_it_source)),
          f"homepage: missing descriptive link to {label}")

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

# Mirror the public CI's preflight in this locally runnable source gate.
# This protects releases even when GitHub-hosted CI cannot be used.
for essential in ("index.html", "nutridataset.html", "sitemap.xml", "robots.txt"):
    check((ROOT / essential).is_file(), f"missing public release essential: {essential}")
cname = ROOT / "CNAME"
check(cname.is_file() and cname.read_text(encoding="utf-8").strip() == "gossmere.com",
      "CNAME must be exactly gossmere.com")
forbidden_paths = (
    re.compile(r"checkpoint", re.I),
    re.compile(r"restore[_-]?point", re.I),
    re.compile(r"metodo[_-]?erika", re.I),
    re.compile(r"method[_-]?erika", re.I),
    re.compile(r"(^|/)\.env($|\.)", re.I),
    re.compile(r"(^|/)(private|internal|secrets?)(/|$)", re.I),
)
forbidden_exact = {"studio-commerciale.html", "invoice.html", "commercial-core.js"}
for item in ROOT.rglob("*"):
    if not item.is_file():
        continue
    relative = item.relative_to(ROOT)
    if ".git" in relative.parts or "node_modules" in relative.parts:
        continue
    name = relative.as_posix()
    if name in forbidden_exact or any(pattern.search(name) for pattern in forbidden_paths):
        problems.append(f"restricted public path: {name}")
robots_text = (ROOT / "robots.txt").read_text(encoding="utf-8") if (ROOT / "robots.txt").exists() else ""
check(not re.search(r"studio-commerciale\.html|invoice\.html|commercial-core\.js", robots_text, re.I),
      "robots.txt exposes internal business asset names")

if problems:
    for p in problems: print("FAIL:", p)
    sys.exit(1)
print("PASS: source consistency checks; browser and delivery QA still required")
