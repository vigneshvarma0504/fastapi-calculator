import subprocess
import time
from playwright.sync_api import sync_playwright

def test_app_running():
    # Start FastAPI server
    process = subprocess.Popen(["uvicorn", "main:app"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Give the server time to start

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("http://127.0.0.1:8000/docs")
            assert "FastAPI" in page.title()
            browser.close()
    finally:
        process.terminate()
