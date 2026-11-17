# GameHub v3.6 — Windows installer and GitHub updates

GameHub is a Windows gaming-launcher dashboard. This project builds on v3.5 and keeps launcher scanning, right-click rename/logo changes, and custom apps.



## v3.6.4 visual refresh
- New interlocking GH blue app icon (EXE, installer, title bar, sidebar).
- Softer off-white interface text and calmer headings.
- Existing launcher settings remain in AppData and are preserved on update.
- Push tag `v3.6.4` to publish this version through GitHub Actions.


## v3.6.4
Right-click any launcher to open a custom dark popup menu with rounded buttons. Escape dismisses it. The GH icon is also updated.


## v3.6.4
Top-right Logos only switch and small-to-large icon slider. Logo-only mode hides card backgrounds and launcher labels but retains invisible clickable/right-clickable tiles. View preferences persist in user settings.


## v3.6.4
Compact, right-aligned Logos only toggle and small-to-large icon slider in one row immediately above the search bar.


## GameHub v3.7.0
- Drag icons to rearrange; order persists in %APPDATA%\\GameHub\\preferences_v37.json.
- Right-click to pin or unpin favorites.
- Blue running indicators update every four seconds without redrawing the grid (process name detection).
- Close window to minimize to Windows tray; tray menu opens or exits GameHub.
- Sidebar accent selector with five presets.
- Requires psutil and pystray, installed by build_exe.bat.

## GameHub v3.8.0
- Rainbow button opens the Windows full-color picker; custom accent is saved.
- Right-click launcher > Search online for logo opens a thumbnail grid with a preview panel and Use this logo button.
- Free default search: Wikimedia Commons (no account or API key required; results vary by name).
- Optional Google Programmable Search JSON at `%APPDATA%\\GameHub\\google_image_search.json`:
  `{"api_key": "YOUR_KEY", "cx": "YOUR_SEARCH_ENGINE_ID"}`
  Google search requires a configured Programmable Search Engine with image search enabled and is subject to Google's quotas/terms.
- Images are downloaded to `%APPDATA%\\GameHub\\downloaded_icons`, converted to PNG and saved as launcher icon overrides.
- Image search requires internet access. Check image licensing before reusing third-party artwork.
