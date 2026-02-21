#!/usr/bin/env python3
"""
FieldLog — ArcGIS Browser Helper

Opens the ArcGIS Structure Viewer in a visible browser window and
continuously writes the current URL to a temp file so the Streamlit
app can read it and pre-fill the ArcGIS Link field.

Called automatically by FieldLog when you click "Open ArcGIS in Browser".
Requires playwright OR selenium+webdriver-manager (tries playwright first).

Install (one-time, pick one):
    pip install playwright && playwright install chromium
  OR
    pip install selenium webdriver-manager
"""

import sys
import time
import tempfile
from pathlib import Path

ARCGIS_URL = sys.argv[1] if len(sys.argv) > 1 else (
    "https://experience.arcgis.com/experience/f703e7a448e44768b11f7ca209b61edd"
)
URL_FILE = Path(tempfile.gettempdir()) / "_fieldlog_agx.txt"


def _try_playwright() -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled",
                  "--start-maximized"],
        )
        ctx  = browser.new_context(no_viewport=True)
        page = ctx.new_page()
        page.goto(ARCGIS_URL)
        print(f"[FieldLog] Browser open — watching for URL changes → {URL_FILE}")

        last = ""
        while True:
            try:
                url = page.url
                if url and url != last:
                    last = url
                    URL_FILE.write_text(url)
                    print(f"[FieldLog] Captured: {url[:100]}")
            except Exception:
                break
            time.sleep(0.4)

        browser.close()


def _try_selenium() -> None:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts,
    )
    driver.maximize_window()
    driver.get(ARCGIS_URL)
    print(f"[FieldLog] Browser open (selenium) — watching → {URL_FILE}")

    last = ""
    try:
        while True:
            try:
                url = driver.current_url
                if url and url != last:
                    last = url
                    URL_FILE.write_text(url)
                    print(f"[FieldLog] Captured: {url[:100]}")
            except Exception:
                break
            time.sleep(0.4)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def _fallback_webbrowser() -> None:
    import webbrowser
    webbrowser.open(ARCGIS_URL)
    print(
        "[FieldLog] Opened in system browser.\n"
        "URL monitoring is NOT active — install playwright or selenium for auto-capture.\n"
        "  pip install playwright && playwright install chromium\n"
        "  OR: pip install selenium webdriver-manager"
    )


if __name__ == "__main__":
    try:
        _try_playwright()
    except ImportError:
        try:
            _try_selenium()
        except ImportError:
            _fallback_webbrowser()
    except Exception as err:
        print(f"[FieldLog] Playwright error: {err} — trying selenium…")
        try:
            _try_selenium()
        except ImportError:
            _fallback_webbrowser()
        except Exception as err2:
            print(f"[FieldLog] Selenium error: {err2}")
            _fallback_webbrowser()
