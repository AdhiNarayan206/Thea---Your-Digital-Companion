; Thea — Windows installer
;
; Per-user install, no elevation:
;   %LOCALAPPDATA%\Programs\Thea
; Start Menu shortcut always, optional desktop shortcut, optional launch on finish,
; plus a standard Apps & features uninstall entry.
;
; Build:
;   installer\build.ps1
;   (or) "C:\Users\<you>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer\Thea.iss
;
; Code signing is intentionally not enabled yet. See installer\build.ps1 — set
; THEA_SIGN_CERT / THEA_SIGN_PASSWORD and pass -Sign to sign setup + uninstaller.

#define AppName "Thea"
#define AppVersion "0.1.0"
#define AppPublisher "Thea - Your Digital Companion"
#define AppExe "Thea.exe"
#define AppMutexName "Local\TheaOverlay"

[Setup]
AppId={{7C4E1B52-9D3A-4F8B-9C21-6A5D2E8F4B17}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppComments=A tiny black-and-white pixel companion for your Windows desktop.
VersionInfoVersion=0.1.0.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Thea {#AppVersion} installer
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=no
DisableWelcomePage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=output
OutputBaseFilename=Thea-Setup-{#AppVersion}
SetupIconFile=..\assets\thea.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
AllowNoIcons=yes
CloseApplications=no
AppMutex={#AppMutexName}
; Signing (enable later):
; SignTool=signtool
; SignedUninstaller=yes
; SignToolRetryCount=3
; SignToolMinimumTimeBetween=1000

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\Thea\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Comment: "Thea — your digital companion"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon; Comment: "Thea — your digital companion"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch Thea now"; Flags: nowait postinstall skipifsilent

; The app holds Local\TheaOverlay while it runs, so Inno asks the user to quit it
; before uninstalling. Nothing else to tear down: settings live in %APPDATA%\Thea.

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if CheckForMutexes('{#AppMutexName}') then
  begin
    if MsgBox('Thea is still running.' + #13#10 + #13#10 +
              'Right-click her tray icon and choose Quit, then run this installer again.',
              mbError, MB_OK) = IDOK then
      Result := False;
  end;
end;
