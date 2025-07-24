from playwright.async_api import async_playwright
import os
import json

COOKIES_FILE = "spotify_cookies.json"

async def get_playlist_description(playlist_id: str) -> str | None:
    try:
        print(f"[SPOTIFY] Scraping playlist: {playlist_id}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent="Mozilla/5.0")

            # Cookies laden
            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(f"https://open.spotify.com/playlist/{playlist_id}", timeout=20000)
            await page.wait_for_timeout(8000)

            # Cookies speichern
            cookies = await context.cookies()
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f)
                print("[SPOTIFY] Cookies saved.")

            # Inhalte scrapen
            divs = await page.locator("div").all_text_contents()
            for text in divs:
                if "#elysium" in text.lower():
                    print(f"[SPOTIFY] Found code in: {text.strip()}")
                    await browser.close()
                    return text.strip()

            print("[SPOTIFY] No code found.")
            await browser.close()
            return None
    except Exception as e:
        print(f"[SPOTIFY] Error: {e}")
        return None
