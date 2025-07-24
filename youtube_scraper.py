from playwright.async_api import async_playwright
import os
import json

COOKIES_FILE = "youtube_cookies.json"

async def get_youtube_description(channel_name: str) -> str | None:
    try:
        print(f"[YOUTUBE] Scraping /about page: {channel_name}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent="Mozilla/5.0")

            # Cookies laden
            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(f"https://www.youtube.com/@{channel_name}/about", timeout=20000)
            await page.wait_for_timeout(8000)

            # Cookies speichern
            cookies = await context.cookies()
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f)
                print("[YOUTUBE] Cookies saved.")

            # Inhalte scrapen
            divs = await page.locator("div").all_text_contents()
            for text in divs:
                if "#elysium" in text.lower():
                    print(f"[YOUTUBE] Found code in: {text.strip()}")
                    await browser.close()
                    return text.strip()

            print("[YOUTUBE] No code found.")
            await browser.close()
            return None
    except Exception as e:
        print(f"[YOUTUBE] Error: {e}")
        return None
