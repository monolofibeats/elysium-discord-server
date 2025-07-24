from tiktok_scraper import get_tiktok_bio

bio = get_tiktok_bio("simplesteveee")
print("Bio:", bio)

if bio and "#elysium" in bio.lower():
    print("✅ Verifizierungscode gefunden.")
else:
    print("❌ Kein Verifizierungscode in der Bio.")
