"""
capture_screenshot.py
---------------------
Uses a headless Chromium browser (via Playwright) to capture a live screenshot
of the running Streamlit dashboard at http://localhost:8501.

Requirements:
    pip install playwright
    python -m playwright install chromium

Usage:
    # Make sure Streamlit is running first:
    # streamlit run scripts/dashboard_streamlit.py
    python scripts/capture_screenshot.py
"""

import os
import time
from playwright.sync_api import sync_playwright

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "screenshots", "streamlit_live.png")
URL = "http://localhost:8501"


def capture():
    print(f"Connecting to {URL} ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(URL, wait_until="networkidle", timeout=30000)
        # Give Streamlit time to render charts
        time.sleep(4)
        page.screenshot(path=OUT_PATH, full_page=False)
        browser.close()
    print(f"Screenshot saved to: {OUT_PATH}")


if __name__ == "__main__":
    capture()
