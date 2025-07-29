from playwright.async_api import async_playwright
import os
import json

COOKIES_FILE = "instagram_cookies.json"

async def get_instagram_bio(username: str, code: str) -> str | None:
    print(f"[INSTAGRAM] Scraping profile: {username}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(f"https://www.instagram.com/{username}/", timeout=20000)
            await page.wait_for_timeout(8000)

            full_text = await page.locator("body").inner_text()
            print(f"[INSTAGRAM] Full text length: {len(full_text)}")

            if code.lower() in full_text.lower():
                print(f"[INSTAGRAM] Found code in profile!")
                await browser.close()
                return full_text
            else:
                print("[INSTAGRAM] Code not found in profile.")
                await browser.close()
                return None
    except Exception as e:
        print(f"[INSTAGRAM] Error: {e}")
        return None
