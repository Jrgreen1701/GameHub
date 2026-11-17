#define MyAppVersion "3.9.6"
[Setup]
AppId={{1D4A906C-CA71-4C1B-912D-AD120F9285A1}
AppName=GameHub
AppVersion={#MyAppVersion}
AppPublisher=Jrgreen1701
DefaultDirName={localappdata}\Programs\GameHub
DefaultGroupName=GameHub
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=GameHub_Setup_v{#MyAppVersion}
SetupIconFile=GameHub\assets\gamehub.ico
UninstallDisplayIcon={app}\GameHub.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
[Files]
Source: "GameHub\dist\GameHub.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\GameHub"; Filename: "{app}\GameHub.exe"
Name: "{autodesktop}\GameHub"; Filename: "{app}\GameHub.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
[Run]
Filename: "{app}\GameHub.exe"; Description: "Launch GameHub"; Flags: nowait postinstall skipifsilent
