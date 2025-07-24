import os
import re
from datetime import datetime
from extract_text_from_image import extract_text
from utils import parse_number_from_text, list_sorted_images

def extract_tiktok_stats(image_path):
    raw_text = extract_text(image_path).lower()
    print("📃 Raw OCR Text:")
    print(raw_text)

    stats = {"followers": 0, "videos": 0}
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    for line in lines:
        if "followers" in line:
            stats["followers"] = parse_number_from_text(line)
        elif "videos" in line or "video" in line:
            stats["videos"] = parse_number_from_text(line)

    return stats

def analyze_tiktok(username):
    folder = f"uploads/tiktok/{username}"
    images = list_sorted_images(folder)

    if len(images) < 2:
        print("⚠️ Not enough data to compare.")
        return None

    current_image = images[-1]
    previous_image = images[-2]

    current_stats = extract_tiktok_stats(current_image)
    previous_stats = extract_tiktok_stats(previous_image)

    result = {
        "followers_now": current_stats["followers"],
        "followers_before": previous_stats["followers"],
        "followers_diff": current_stats["followers"] - previous_stats["followers"],

        "videos_now": current_stats["videos"],
        "videos_before": previous_stats["videos"],
        "new_videos": current_stats["videos"] - previous_stats["videos"],
    }

    print("📊 Comparison Result:", result)
    return result

# TEST
if __name__ == "__main__":
    analyze_tiktok("vagabondmusic")  # <- Username anpassen
