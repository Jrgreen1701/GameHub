# GameHub v3.6 — Windows installer and GitHub updates

GameHub is a Windows gaming-launcher dashboard. This project builds on v3.5 and keeps launcher scanning, right-click rename/logo changes, and custom apps.

## First-time GitHub setup

1. Sign in at https://github.com/new and create a repository named **GameHub** under **Jrgreen1701** (public recommended for public releases). Do not initialize with README.
2. Extract this archive, open a terminal in the extracted **GameHub_v3_6** folder, and run:

   ```powershell
   git init
   git add .
   git commit -m "GameHub v3.6 installer and updater"
   git branch -M main
   git remote add origin https://github.com/Jrgreen1701/GameHub.git
   git push -u origin main
   git tag v3.6.0
   git push origin v3.6.0
   ```

3. GitHub Actions builds the Windows app and Inno Setup installer, then publishes a release containing `GameHub_Setup_v3.6.0.exe` and `SHA256SUMS.txt`. View progress in the **Actions** tab. The first build may need workflow fixes depending on GitHub's current Windows runner image.
4. Download and run the installer from the **Releases** page. It creates Start-menu and optional desktop shortcuts and registers an uninstaller.

## Future hotfix releases

Update `APP_VERSION` in `GameHub/gamehub.py`, `MyAppVersion` in `installer.iss`, and commit the fix. Then tag and push the matching version (e.g. `v3.6.1`). The workflow builds and publishes the installer. Existing clients check the latest GitHub release at startup or using **Check for updates**.

## Update security and limitations

The updater uses HTTPS and checks SHA-256 against a checksum published in the *same GitHub release*. This protects against corrupted downloads but **does not establish independent publisher authenticity** if the release account is compromised. Code signing is recommended for public distribution. The installer runs silently after the user approves an update; GameHub then closes. The updater does not yet provide a progress bar, transactional rollback, or recovery from a failed installer. The GitHub release must be published before automatic updates work.

App settings remain in `%APPDATA%\GameHub` and are not removed by normal app updates.

## Build locally

Windows with Python 3.12+ and Inno Setup 6: run `GameHub\build_exe.bat`, then compile `installer.iss` in Inno Setup. The installer will appear under `output`.
