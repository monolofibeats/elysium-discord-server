from playwright.sync_api import sync_playwright
import re, time

def scrape_spotify_playlist_followers(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # erstmal sichtbar für Debug
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(5000)  # Zeit geben, JS zu laden

        # Alle Spans abfragen
        spans = page.query_selector_all("span")

        for span in spans:
            text = span.inner_text().lower()
            if "followers" in text:
                print(f"👥 Gefunden: {text}")
                return text.split()[0]

        print("❌ Keine Follower-Zahl gefunden")
        return None

# Test:
if __name__ == "__main__":
    url = "https://open.spotify.com/playlist/2V1Lwkv8CMfyW04Rz34GXA?si=d8be681d61994cba"
    scrape_spotify_playlist_followers(url)
