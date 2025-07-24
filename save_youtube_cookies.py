import asyncio
from playwright.async_api import async_playwright
import json

COOKIES_FILE = "youtube_cookies.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Öffne YouTube – du loggst dich jetzt manuell ein
        await page.goto("https://www.youtube.com", timeout=60000)
        print("🔐 Logge dich bitte manuell in YouTube ein...")

        input("➡️ Drücke [Enter], wenn du eingeloggt bist und alles geladen ist...")

        # Cookies speichern
        cookies = await context.cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)

        print(f"✅ Cookies gespeichert in '{COOKIES_FILE}'")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
