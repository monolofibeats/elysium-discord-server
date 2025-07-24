import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright
from utils import load_cookies, save_submissions_json

COOKIES_FILE = "tiktok_cookies.json"
USERNAME = "risingvagabond"
PROFILE_URL = f"https://www.tiktok.com/@{USERNAME}"
SUBMISSIONS_PATH = "submissions.json"          # zentraler Speicherort

async def scrape():
    async with async_playwright() as p:
        # ── Browser + Cookies ─────────────────────────────────────────────
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await load_cookies(context, COOKIES_FILE)

        # ── Profilseite öffnen ────────────────────────────────────────────
        page = await context.new_page()
        await page.goto(PROFILE_URL, timeout=60_000)
        print("✅ Cookies geladen.")

        # Videos laden durch Scrollen
        for _ in range(10):  # 10x runter scrollen (anpassbar)
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(1.2)  # kurz warten, bis Inhalte laden
            
        # ── Follower auslesen ─────────────────────────────────────────────
        await page.wait_for_selector('strong[data-e2e="followers-count"]',
                                     timeout=15_000)
        followers_element = await page.query_selector(
            'strong[data-e2e="followers-count"]')
        followers = await followers_element.inner_text()
        print(f"👥 Follower: {followers}")

        # ── Alle Video-URLs einsammeln ────────────────────────────────────
        await page.wait_for_selector('div[data-e2e="user-post-item-list"] a',
                                     timeout=15_000)
        video_elements = await page.query_selector_all(
            'div[data-e2e="user-post-item-list"] a')

        video_urls = []
        for el in video_elements:
            href = await el.get_attribute("href")
            if href and ("/video/" in href or "/photo/" in href):
                video_urls.append(href)

        print(f"🎬 Gefundene Videos: {len(video_urls)}")

        # ── Erstes (neuestes) Video speichern ─────────────────────────────
        first_video = video_urls[0] if video_urls else None

        # ── submissions.json laden / initialisieren ───────────────────────
        Path(SUBMISSIONS_PATH).touch(exist_ok=True)
        try:
            with open(SUBMISSIONS_PATH, "r", encoding="utf-8") as f:
                submissions = json.load(f) or {}
        except json.JSONDecodeError:
            submissions = {}

        # ── Neue-Videos-Zählung ───────────────────────────────────────────
        last_known = submissions.get(USERNAME, {}).get("last_known_video")
        new_videos = 0

        if last_known:
            for url in video_urls:
                if url == last_known:
                    break
                new_videos += 1
        else:
            print("⚠️ Kein last_known_video gefunden – zähle keine neuen Videos.")

        print(f"🆕 Neue Videos seit letzter Messung: {new_videos}")

        # Bestehende Daten erhalten
        existing = submissions.get(USERNAME, {})
        existing.update({
            "followers": followers,
            "last_known_video": first_video,
            "new_videos": new_videos
        })
        submissions[USERNAME] = existing

        with open(SUBMISSIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(submissions, f, indent=2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape())
