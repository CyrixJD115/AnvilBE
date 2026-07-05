; Inno Setup Script for AutoBE Installer
; Author: TBL
; Application: AutoBE
; Company: CodeNex

[Setup]
AppId={{D4A77C38-9B1E-4F91-8A7F-1F214BBE7C6E}} ; Unique GUID
AppName=AutoBE
AppVersion=7.0.2.0
AppPublisher=CodeNex
DefaultDirName={autopf}\CodeNex\AutoBE
DefaultGroupName=AutoBE
OutputDir=Installer
OutputBaseFilename=AutoBE_7.0.2.0_Setup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=no
SetupIconFile=NEXBOX.ico
UninstallDisplayIcon={app}\NEXBOX.ico
UsePreviousAppDir=yes
AllowRootDirectory=no
AllowNoIcons=yes
; Automatically create directory structure
CreateAppDir=yes
; No SignTool directive - will be signed manually after compilation

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "startmenu"; Description: "Create Start Menu &shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce

[Dirs]
; Always create the music folder in install directory (even if no audio files are present)
Name: "{app}\music"
Name: "{app}\vendor"

[Files]
; Main executable (must exist: run build_exe.bat first)
Source: "dist\AutoBE.exe"; DestDir: "{app}"; Flags: ignoreversion
; Icon and licence
Source: "NEXBOX.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENCE.TXT"; DestDir: "{app}"; Flags: ignoreversion
Source: "MUSIC_CREDITS.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
; Include music assets from project music folder
Source: "music\*"; DestDir: "{app}\music"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
; Optional fallback: include music from local app-data style folder when present
Source: ".autobe\music\*"; DestDir: "{app}\music"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
; Vendor folder (required)
Source: "vendor\*"; DestDir: "{app}\vendor"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
; Desktop shortcut
Name: "{commondesktop}\AutoBE"; Filename: "{app}\AutoBE.exe"; Tasks: desktopicon; IconFilename: "{app}\NEXBOX.ico"
; Start menu shortcut
Name: "{group}\AutoBE"; Filename: "{app}\AutoBE.exe"; Tasks: startmenu; IconFilename: "{app}\NEXBOX.ico"
; Quick launch shortcut
Name: "{commonprograms}\Quick Launch\AutoBE"; Filename: "{app}\AutoBE.exe"; Tasks: quicklaunchicon; IconFilename: "{app}\NEXBOX.ico"

[Run]
; Automatically launch AutoBE after installation
Filename: "{app}\AutoBE.exe"; Description: "Launch AutoBE"; Flags: nowait postinstall skipifsilent

[Code]
// Initialize setup - directory structure will be created automatically
function InitializeSetup(): Boolean;
begin
  // {autopf} automatically resolves to the correct Program Files directory
  // CodeNex\AutoBE folder structure will be created automatically by Inno Setup
  Result := True;
end;

// Show admin reminder after installation
procedure ShowAdminReminder;
begin
  MsgBox('🔒 Important' + #13#10 + #13#10 +
         'For the best experience, please run AutoBE as Administrator.' + #13#10 + #13#10 +
         'Right-click the AutoBE icon and select "Run as administrator".' + #13#10 + #13#10 +
         'This ensures proper functionality and prevents permission issues.',
         mbInformation, MB_OK);
end;

// Automatically add Windows Defender exclusion and show admin reminder after installation
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Automatically add Windows Defender exclusion using PowerShell
    // This runs silently in the background
    Exec('powershell.exe', 
         '-Command "Add-MpPreference -ExclusionPath ''' + ExpandConstant('{app}') + '''"', 
         '', 
         SW_HIDE, 
         ewWaitUntilTerminated, 
         ResultCode);
    
    // Show admin reminder popup
    ShowAdminReminder;
  end;
end;