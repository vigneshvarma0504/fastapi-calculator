import pytest
from playwright.sync_api import sync_playwright

def test_register_and_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Register
        page.goto("http://localhost:8081/register.html")
        page.fill("#email", "e2euser@example.com")
        page.fill("#password", "password123")
        page.fill("#confirm", "password123")
        page.click("button[type=submit]")
        page.wait_for_selector(".success")
        assert "successful" in page.inner_text("#message").lower()
        # Login
        page.goto("http://localhost:8081/login.html")
        page.fill("#email", "e2euser@example.com")
        page.fill("#password", "password123")
        page.click("button[type=submit]")
        page.wait_for_selector(".success")
        assert "login successful" in page.inner_text("#message").lower()
        browser.close()
