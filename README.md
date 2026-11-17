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

## v3.8.1 Color theme fix
- Fixes saved custom color resetting to blue on startup.
- Accent picker now tints dashboard background, sidebar, search box, launcher tiles, hover surfaces and borders.
- Preserves dark contrast and logo-only transparent tiles.
- Fixes Add Launcher button reference (previously assigned None after pack()).

## v3.9.0
- Modern appearance dialog with custom HSV wheel, presets, hex input and preview.
- Animated tile hover transitions (~100 ms), with cancellation when pointer moves away.
- Existing compact controls, logo search and theme persistence retained.
- No extra dependencies.


## v3.9.1 Google Images logo picker
- Right-click a launcher and choose Search online for logo.
- Search Google opens Google Images in your default browser. CAPTCHA, if any, is completed there.
- Copy a direct image URL into the GameHub dialog and click Preview URL; or download the image and choose it from disk.
- Preview on the right before clicking Use this logo. The selected icon is stored locally as PNG.
- No API key, browser automation, or Google page scraping required.
- Google does not guarantee image access; some host sites block downloads. This version does not automatically populate an image-result grid inside GameHub.

## v3.9.2 clipboard image conversion
- Copy image pixels from Google Images, then click Paste image / URL.
- Supports copied HTTPS image URLs and copied image files.
- Converts supported images to RGBA PNG in memory, previews them, and saves PNG after Use this logo.
- Direct URL paste into the address field previews automatically.
- Google Images remains in the browser; no automatic Google result scraping.

## v3.9.4
Restores the scrollable in-app image gallery and side preview. Google Images HTML is searched without opening the browser. Results are best-effort: Google can change markup, block automated requests, or require verification; CAPTCHA cannot be completed inside this gallery. Selected results are automatically converted to PNG and stored locally. No Google API key required.

## v3.9.5
In-app scrollable image gallery now falls back to Wikimedia Commons when Google Images HTML extraction returns no usable results. The UI identifies the source and keeps automatic PNG conversion. Google scraping is not reliable; for dependable Google results an official supported search service is required.


## v3.9.6
Removed online logo search completely, including the context menu entry and its implementation. Choose logo from computer and Reset logo remain available.
