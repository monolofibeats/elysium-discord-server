import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from utils import load_cookies, save_youtube_subscriber_count

USERNAME = "exhibitmusic"
PROFILE_URL = f"https://www.youtube.com/@{USERNAME}/videos"
COOKIE_FILE = "youtube_cookies.json"
SUBMISSIONS_PATH = "submissions.json"

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await load_cookies(context, COOKIE_FILE)

        page = await context.new_page()
        await page.goto(PROFILE_URL, timeout=60000)
        print("✅ YouTube-Seite geladen")

        # Abonnenten holen (wenn vorhanden)
        sub_el = await page.query_selector("span:has-text('subscribers')")
        subscribers = await sub_el.inner_text() if sub_el else "unknown"
        print(f"👥 Abonnenten: {subscribers}")

        # ➕ Monatswert speichern (strukturierter, pro Monat)
        save_youtube_subscriber_count(USERNAME, subscribers)

        await browser.close()

def scrape_youtube_profile(username):
    global USERNAME, PROFILE_URL
    USERNAME = username
    PROFILE_URL = f"https://www.youtube.com/@{username}/videos"
    asyncio.run(scrape())


if __name__ == "__main__":
    asyncio.run(scrape())
