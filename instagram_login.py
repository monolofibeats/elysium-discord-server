import os
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

def save_instagram_cookies():
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.instagram.com/accounts/login/", timeout=20000)
        page.wait_for_timeout(5000)

        # Akzeptiere Cookies (falls sichtbar)
        try:
            page.click("text=Only allow essential cookies", timeout=5000)
        except:
            pass

        # Login
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")

        page.wait_for_timeout(10000)  # warte auf Login + Weiterleitung

        cookies = context.cookies()
        with open("instagram_cookies.json", "w") as f:
            json.dump(cookies, f)
            print("[LOGIN] Cookies saved to instagram_cookies.json")

        browser.close()

if __name__ == "__main__":
    save_instagram_cookies()
