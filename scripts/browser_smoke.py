#!/usr/bin/env python3
"""Browser smoke test of the local static site. No outbound emails or live deployment."""
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ["/", "/en/", "/fr.html", "/de.html", "/es.html", "/pt.html",
          "/servizi/", "/services/", "/services/fr/", "/services/de/",
          "/services/es/", "/services/pt/"]
VIEWPORTS = [("desktop", {"width": 1366, "height": 768}),
             ("mobile", {"width": 390, "height": 844})]

@contextmanager
def local_server():
    import functools
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

def run():
    problems = []
    pages_tested = 0
    with local_server() as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        for device, viewport in VIEWPORTS:
            context = browser.new_context(viewport=viewport, device_scale_factor=1)
            for route in ROUTES:
                page = context.new_page()
                js_errors = []
                page.on("pageerror", lambda exc: js_errors.append(str(exc)))
                response = page.goto(base + route, wait_until="networkidle", timeout=25000)
                if not response or response.status != 200:
                    problems.append(f"{device} {route}: HTTP {response.status if response else 'no response'}")
                else:
                    pages_tested += 1
                    if route in ("/", "/servizi/"):
                        shot_dir = ROOT / "qa-screenshots"
                        shot_dir.mkdir(exist_ok=True)
                        page.screenshot(path=str(shot_dir / (device + ("-home" if route == "/" else "-services") + ".png")), full_page=True)
                    header = page.locator(".site-header.single-header")
                    if header.count():
                        rect = header.bounding_box()
                        if rect and rect["height"] > (76 if device == "mobile" else 92):
                            problems.append(f"{device} {route}: header enlarged to {rect['height']:.0f}px")
                    if route in ("/servizi/", "/services/", "/services/fr/", "/services/de/", "/services/es/", "/services/pt/"):
                        headline = page.locator("h1").inner_text().lower()
                        if "websites, seo" in headline or headline.startswith("siti web"):
                            problems.append(f"{device} {route}: generic web-design-first heading")
                        if not page.locator("#offer .sv-card").first.inner_text().lower().find("web") == -1:
                            problems.append(f"{device} {route}: web card still leads services")
                    if page.locator("h1").count() != 1:
                        problems.append(f"{device} {route}: expected exactly one H1")
                    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
                    if overflow > 2:
                        problems.append(f"{device} {route}: horizontal overflow {overflow}px")
                    if not page.locator(".brand-lockup").count():
                        problems.append(f"{device} {route}: missing brand")
                    if route in ("/", "/en/", "/fr.html", "/de.html", "/es.html", "/pt.html"):
                        if not page.locator(".hero-feature").count():
                            problems.append(f"{device} {route}: hero showcase missing")
                        if not page.locator(".language-select").count():
                            problems.append(f"{device} {route}: missing language selector")
                    else:
                        if not page.locator(".sv-creative").count():
                            problems.append(f"{device} {route}: creative services missing")
                        if not page.locator("#sv-form").count() or not page.locator("#sv-status").count():
                            problems.append(f"{device} {route}: form or status missing")
                    for e in js_errors:
                        problems.append(f"{device} {route}: JS: {e}")
                page.close()
            context.close()
        # Run the contact journey without letting an email client launch or sending a message.
        context = browser.new_context(viewport={"width": 1366, "height": 768})
        page = context.new_page()
        page.goto(base + "/servizi/", wait_until="networkidle")
        page.locator("#sv-name").fill("QA locale")
        page.locator("#sv-email").fill("qa@example.org")
        page.locator("#sv-message").fill("Richiesta di prova non inviata: controllo browser locale.")
        page.locator("#sv-form button[type=submit]").click(timeout=10000)
        try:
            page.wait_for_function("document.querySelector('#sv-status').textContent.trim().length > 0", timeout=3000)
        except Exception:
            problems.append("Italian contact form did not show honest mailto message")
        page.close()
        context.close()
        browser.close()
    print(f"Browser QA: {pages_tested}/24 responsive page loads checked; {len(problems)} errors")
    for problem in problems:
        print("FAIL:", problem)
    if problems:
        raise SystemExit(1)
    print("PASS: desktop/mobile smoke and local email-draft UI (NOT actual email delivery)")

if __name__ == "__main__":
    run()
