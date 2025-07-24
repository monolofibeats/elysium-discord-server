import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def count_tiktok_posts_30d(username):
    url = f"https://www.tiktok.com/@{username}"

    chrome_options = Options()
    chrome_options.debugger_address = "localhost:9222"
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)

    for _ in range(6):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    video_links = list({a["href"] for a in soup.find_all("a", href=True) if "/video/" in a["href"]})

    print(f"Found {len(video_links)} video links")

    now = datetime.datetime.now(datetime.timezone.utc)
    recent_posts = 0

    for link in video_links:
        full_url = link if link.startswith("http") else "https://www.tiktok.com" + link
        try:
            driver.get(full_url)
            time.sleep(3)
            video_soup = BeautifulSoup(driver.page_source, "html.parser")

            time_tag = video_soup.find("time")
            if not time_tag or not time_tag.has_attr("datetime"):
                continue

            post_time = datetime.datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            if (now - post_time).days <= 30:
                recent_posts += 1
        except Exception as e:
            print(f"Error checking {full_url}: {e}")
            continue

    driver.quit()
    return recent_posts

# TEST
if __name__ == "__main__":
    print(count_tiktok_posts_30d("therock"))  # 👈 Username anpassen
