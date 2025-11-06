; Inno Setup Installer Script for PANN POS System
; Compile with: iscc installer.iss

[Setup]
AppName=PANN POS System
AppVersion=1.0.0
AppPublisher=PANN Systems
AppPublisherURL=https://www.pann.com
DefaultDirName={autopf}\PANN\POS_System
DefaultGroupName=PANN POS System
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=PANN_POS_System_Setup
Compression=lzma2/ultra
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "backend\dist\PANN_POS_System.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "backend\.env"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall
; Include any additional files needed

[Icons]
Name: "{group}\PANN POS System"; Filename: "{app}\PANN_POS_System.exe"
Name: "{group}\{cm:UninstallProgram,PANN POS System}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\PANN POS System"; Filename: "{app}\PANN_POS_System.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\PANN POS System"; Filename: "{app}\PANN_POS_System.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\PANN_POS_System.exe"; Description: "{cm:LaunchProgram,PANN POS System}"; Flags: nowait postinstall skipifsilent


