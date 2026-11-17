@echo off
cd /d "%~dp0"
py -m pip install --upgrade pyinstaller pillow customtkinter
if errorlevel 1 goto fail
py -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all customtkinter --add-data "assets;assets" --icon "assets\gamehub.ico" --name GameHub gamehub.py
if errorlevel 1 goto fail
echo Built dist\GameHub.exe
exit /b 0
:fail
echo Build failed. Check Python installation.
exit /b 1
