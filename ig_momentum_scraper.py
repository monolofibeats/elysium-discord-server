import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def scrape_instagram_momentum(username, headless=True):
    url = f"https://www.instagram.com/{username}/"

    chrome_options = Options()
    chrome_options.debugger_address = "localhost:9222"  # Verbindung zu deiner Session
    if headless:
        print("⚠️ Cookies funktionieren nur im sichtbaren Modus.")
        return

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)

    try:
        # Cookie-Overlay wegklicken
        driver.find_element(By.XPATH, '//button[text()="Allow all cookies"]').click()
        time.sleep(2)
    except:
        pass

    # Scroll + Interaktion erzwingen
    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(3)

    # Mehrere Scrolls zum Nachladen
    for _ in range(6):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    print("DEBUG: Soup Preview:")
    print(soup.prettify()[:1000])  # zeige die ersten 1000 Zeichen der Seite

    post_elements = soup.find_all("a", href=True)
    post_links = [a['href'] for a in post_elements if a['href'].startswith('/p/') or a['href'].startswith('/reel/')]
    post_links = list(dict.fromkeys(post_links))  # Duplikate raus

    print(f"Found {len(post_links)} posts for {username}")

    views_30d = 0
    posts_30d = 0
    now = datetime.datetime.now(datetime.timezone.utc)

    for link in post_links:
        post_url = f"https://www.instagram.com{link}"
        print(f"Checking: {post_url}")
        try:
            driver.get(post_url)
            time.sleep(3)
            post_soup = BeautifulSoup(driver.page_source, "html.parser")

            # Datum auslesen
            time_element = post_soup.find("time")
            print("DEBUG TIME ELEMENT:", time_element)
            if not time_element or not time_element.has_attr("datetime"):
                continue

            timestamp_str = time_element["datetime"]
            post_time = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            if (now - post_time).days > 30:
                continue

            posts_30d += 1

            # Views auslesen
            spans = post_soup.find_all("span")
            view_count = 0
            for span in spans:
                if "views" in span.text.lower() or "Aufrufe" in span.text:
                    digits = ''.join(filter(str.isdigit, span.text))
                    if digits:
                        view_count = int(digits)
                        break

            views_30d += view_count

        except Exception as e:
            print(f"Error loading {post_url}: {e}")
            continue

    driver.quit()

    avg_views = int(views_30d / posts_30d) if posts_30d else 0

    return {
        "username": username,
        "posts_30d": posts_30d,
        "views_30d": views_30d,
        "avg_views": avg_views
    }

# Test
if __name__ == "__main__":
    username = "nasa"
    data = scrape_instagram_momentum(username, headless=False)
    print(data)
