from playwright.async_api import async_playwright
import os
import json
from bs4 import BeautifulSoup

COOKIES_FILE = "tiktok_cookies.json"

async def get_tiktok_bio(username: str) -> str | None:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            # Cookies laden
            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(f"https://www.tiktok.com/@{username}?lang=en", timeout=20000)
            await page.wait_for_timeout(7000)

            html = await page.content()
            await browser.close()

            soup = BeautifulSoup(html, "html.parser")
            all_divs = soup.find_all("div")

            for div in all_divs:
                text = div.get_text(strip=True)
                if "#elysium" in text.lower():
                    return text

            return None
    except Exception as e:
        print(f"Playwright error: {e}")
        return None
