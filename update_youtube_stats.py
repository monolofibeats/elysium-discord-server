from analyze_youtube_screenshot import analyze_youtube_screenshot
from scrape_youtube_profile     import scrape_youtube_profile
import json, datetime, pathlib

# User-Daten
channel_id  = "risingvagabond"
img_path    = f"uploads/youtube/{channel_id}/2025-07-09_overview.jpg"

# 1. Screenshot-OCR
shorts_views, video_views, published_shorts = analyze_youtube_screenshot(img_path)

# 2. Abo-Zahl scrapen
subscribers = scrape_youtube_profile(channel_id)

# 3. JSON-Struktur aktualisieren
today = datetime.date.today().isoformat()
FILE  = pathlib.Path("submissions.json")
data  = json.loads(FILE.read_text("utf-8")) if FILE.exists() else {}

stats = data.setdefault("youtube", {}).setdefault(channel_id, {}).setdefault("stats", {})
stats[today] = {
    "shorts_views"    : shorts_views,
    "video_views"     : video_views,
    "published_shorts": published_shorts,
    "subscribers"     : subscribers,
}

data["youtube"][channel_id]["subscribers"] = subscribers

FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
print("✅ YouTube-Stats erfolgreich aktualisiert.")
