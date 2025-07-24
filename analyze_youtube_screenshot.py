# analyze_youtube_screenshot.py
import easyocr, re, pathlib

reader = easyocr.Reader(['en'], gpu=False)

def to_int(txt: str):
    txt = txt.lower().replace(',', '').strip()
    m = re.match(r'(\d+(?:\.\d+)?)([km]?)', txt)
    if not m: return None
    num, suf = m.groups()
    val = float(num)
    return int(val*1_000) if suf=='k' else int(val*1_000_000) if suf=='m' else int(val)

def analyze_youtube_screenshot(img_path: str):
    lines = [t.lower().strip() for t in reader.readtext(img_path, detail=0) if t.strip()]
    shorts = vids = publ = 0

    # --- Views-Block --------------------------------------------------------
    views_idx = next((i for i,l in enumerate(lines) if 'views' in l and 'viewer' not in l), None)
    if views_idx is not None:
        for i in range(views_idx, min(views_idx+8, len(lines))):
            if 'short' in lines[i]:
                val = next((to_int(lines[j]) for j in range(i, i+3) if j<len(lines) and to_int(lines[j])), None)
                if val: shorts = val
            if 'video' in lines[i]:
                val = next((to_int(lines[j]) for j in range(i, i+3) if j<len(lines) and to_int(lines[j])), None)
                if val: vids = val

    # --- Published-Block ----------------------------------------------------
    pub_idx = next((i for i,l in enumerate(lines) if 'published' in l), None)
    if pub_idx is not None:
        for i in range(pub_idx, min(pub_idx+6, len(lines))):
            if 'short' in lines[i]:
                val = next((to_int(lines[j]) for j in range(i, i+3) if j<len(lines) and to_int(lines[j])), None)
                if val: publ = val
                break

    return shorts, vids, publ
