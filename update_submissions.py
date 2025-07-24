import json, datetime
from pathlib import Path
from analyze_youtube_screenshot import analyze_youtube_screenshot
from scrape_youtube_profile     import scrape_youtube_profile

# ── 1. Daten holen ────────────────────────────────────────────────────────
IMG   = r"uploads/youtube/risingvagabond/2025-07-09_overview.jpg"
URL   = "https://www.youtube.com/@risingvagabond"

views_short, views_vid, published = analyze_youtube_screenshot(IMG)
subs                                = scrape_youtube_profile(URL)

# ── 2. JSON-Zeile bauen ───────────────────────────────────────────────────
entry = {
    "date"            : datetime.date.today().isoformat(),
    "channel"         : "risingvagabond",
    "shorts_views"    : views_short,
    "video_views"     : views_vid,
    "published_shorts": published,
    "subscribers"     : subs
}

# ── 3. File update ────────────────────────────────────────────────────────
FILE = Path("submissions.json")
data = []
if FILE.exists():
    data = json.loads(FILE.read_text())

# überschreiben, falls Datum+Channel schon existiert
data = [e for e in data if not (e["date"]==entry["date"] and e["channel"]==entry["channel"])]
data.append(entry)

FILE.write_text(json.dumps(sorted(data, key=lambda x: (x["date"], x["channel"])), indent=2))
print("✅  submissions.json aktualisiert")
