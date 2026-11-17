# GameHub v3.6 — Windows installer and GitHub updates

GameHub is a Windows gaming-launcher dashboard. This project builds on v3.5 and keeps launcher scanning, right-click rename/logo changes, and custom apps.


## GameHub v3.8.0
- Rainbow button opens the Windows full-color picker; custom accent is saved.
- Right-click launcher > Search online for logo opens a thumbnail grid with a preview panel and Use this logo button.
- Free default search: Wikimedia Commons (no account or API key required; results vary by name).
- Optional Google Programmable Search JSON at `%APPDATA%\\GameHub\\google_image_search.json`:
  `{"api_key": "YOUR_KEY", "cx": "YOUR_SEARCH_ENGINE_ID"}`
  Google search requires a configured Programmable Search Engine with image search enabled and is subject to Google's quotas/terms.
- Images are downloaded to `%APPDATA%\\GameHub\\downloaded_icons`, converted to PNG and saved as launcher icon overrides.
- Image search requires internet access. Check image licensing before reusing third-party artwork.
