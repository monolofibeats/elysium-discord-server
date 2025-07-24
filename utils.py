import re

def parse_number_from_text(text):
    text = text.lower().replace(",", "").strip()
    replacements = {
        "o": "0", "O": "0", "i": "1", "l": "1", "I": "1",
        "”": "", "~": "", "“": "", "‘": "", "’": "",
        "a": "", "v": "", "—": "", "|": "", "›": "", "«": "", "»": ""
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    matches = re.findall(r"(\d+(?:\.\d+)?)([km]?)", text)
    if not matches:
        return 0

    number_str, suffix = matches[-1]
    try:
        number = float(number_str)
        if suffix == "k":
            return int(number * 1_000)
        elif suffix == "m":
            return int(number * 1_000_000)
        else:
            return int(number)
    except:
        return 0

import os

def list_sorted_images(folder):
    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
    files = [f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in valid_exts]
    files.sort()
    return [os.path.join(folder, f) for f in files]

import json
from datetime import datetime

def compare_and_save_tiktok(username, followers, videos):
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = f"data/tiktok/{username}.json"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    last_entry = next(reversed(data.values()), None)
    data[today] = {"followers": followers, "videos": videos}

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    if last_entry:
        diff_followers = followers - last_entry["followers"]
        diff_videos = videos - last_entry["videos"]
        return {
            "followers_now": followers,
            "followers_before": last_entry["followers"],
            "followers_diff": diff_followers,
            "videos_now": videos,
            "videos_before": last_entry["videos"],
            "new_videos": diff_videos,
        }
    else:
        return {
            "followers_now": followers,
            "followers_before": None,
            "followers_diff": None,
            "videos_now": videos,
            "videos_before": None,
            "new_videos": None,
        }

import json
from pathlib import Path
from http.cookiejar import Cookie
from typing import List

async def load_cookies(context, cookies_path: str):
    import json

    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    cleaned_cookies = []
    for cookie in cookies:
        if "expirationDate" in cookie:
            cookie["expires"] = int(cookie["expirationDate"])
            del cookie["expirationDate"]

        # Entferne Felder, die Playwright stören
        cookie.pop("sameSite", None)
        cookie.pop("storeId", None)
        cookie.pop("hostOnly", None)

        cleaned_cookies.append({
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie.get("path", "/"),
            "secure": cookie.get("secure", True),
            "httpOnly": cookie.get("httpOnly", False),
            "expires": cookie.get("expires", -1),
        })

    await context.add_cookies(cleaned_cookies)

def save_submissions_json(data: dict, submissions_path: str = "data/submissions.json"):
    Path("data").mkdir(parents=True, exist_ok=True)
    with open(submissions_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


import json
from datetime import datetime

def save_youtube_subscriber_count(username: str, count: str):
    month = datetime.now().strftime("%Y-%m")

    try:
        with open("submissions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    if "youtube" not in data:
        data["youtube"] = {}

    if username not in data["youtube"]:
        data["youtube"][username] = {"subscribers": {}}

    if "subscribers" not in data["youtube"][username]:
        data["youtube"][username]["subscribers"] = {}

    data["youtube"][username]["subscribers"][month] = count

    with open("submissions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)




