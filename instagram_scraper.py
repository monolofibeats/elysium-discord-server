from playwright.async_api import async_playwright
import os
import json

COOKIES_FILE = "instagram_cookies.json"

async def get_instagram_bio(username: str) -> str | None:
    print(f"[INSTAGRAM] Scraping profile: {username}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Sichtbar für Debug
            context = await browser.new_context()

            # Cookies laden
            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(f"https://www.instagram.com/{username}/", timeout=20000)
            await page.wait_for_timeout(8000)

            # Vollständigen Textinhalt der Seite auslesen
            full_text = await page.locator("body").inner_text()
            print(f"[INSTAGRAM] Full text length: {len(full_text)}")

            await browser.close()
            return full_text
    except Exception as e:
        print(f"[INSTAGRAM] Error: {e}")
        return None
