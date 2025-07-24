import re
import pytesseract
from PIL import Image

# 🔍 Fehlerkorrektur & Parsing
def parse_number_from_text(text):
    text = text.lower().replace(",", "").strip()
    replacements = {
        "o": "0", "O": "0",
        "i": "1", "l": "1", "I": "1",
        "”": "", "~": "", "“": "", "‘": "", "’": "",
        "a": "", "v": "", "—": "", "|": "", ">": "", "<": ""
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    matches = re.findall(r"(\d+(?:\.\d+)?)([km]?)", text)
    if not matches:
        return 0

    number_str, suffix = matches[-1]

    # Fix für fehlenden Punkt bei 3-stelligen 'k'-Werten (z. B. 771k → 77.1k)
    if suffix == "k" and len(number_str) == 3 and "." not in number_str:
        number_str = number_str[:2] + "." + number_str[2:]

    try:
        number = float(number_str)
        if suffix == "k":
            return int(number * 1_000)
        elif suffix == "m":
            return int(number * 1_000_000)
        else:
            return int(number)
    except ValueError:
        return 0

# 🧠 Tesseract OCR-Funktion
def extract_text_custom(image_path):
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, config="--psm 6")

# 🧪 Hauptauswertung
def analyze_instagram_image(image_path):
    raw_text = extract_text_custom(image_path).lower()
    print("📃 Raw OCR Text:")
    print(raw_text)

    lines = [line.strip() for line in raw_text.splitlines()]
    stats = {"views": 0, "interactions": 0, "new_followers": 0, "content_shared": 0}
    keys = list(stats.keys())

    for i, line in enumerate(lines):
        for key in keys:
            label = key.replace("_", " ")
            if label in line:
                value = parse_number_from_text(line)
                if value == 0:
                    for j in range(1, 4):
                        if i + j < len(lines):
                            value = parse_number_from_text(lines[i + j])
                            if value != 0:
                                break
                stats[key] = value

        # Spezialbehandlung: „content you shared“
        if "content you shared" in line:
            before, _, after = line.partition("content you shared")

            def clean_and_extract(text):
                cleaned = text.replace("d", "").replace("o", "0").replace("l", "1").replace("i", "1")
                match = re.search(r"(\d+)", cleaned)
                return int(match.group(1)) if match else 0

            val = clean_and_extract(before.strip()) or clean_and_extract(after.strip())
            if val == 0 and i + 1 < len(lines):
                val = clean_and_extract(lines[i + 1])
            stats["content_shared"] = val

    print("📊 Parsed Stats:", stats)
    return stats

# 🚀 Start
if __name__ == "__main__":
    analyze_instagram_image("uploads/instagram/the_rock/2025-07-09_overview.jpg")
