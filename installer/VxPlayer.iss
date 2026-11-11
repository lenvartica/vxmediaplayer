#define AppName "VxPlayer"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{3B7A4562-2D77-4D96-93B9-66B5AB8D82E7}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Decan Konnect
AppPublisherURL=https://github.com/lenvartica/vxmediaplayer
AppSupportURL=https://github.com/lenvartica/vxmediaplayer/issues
AppUpdatesURL=https://github.com/lenvartica/vxmediaplayer/releases
LicenseFile=..\LICENSE
DefaultDirName={autopf}\VxPlayer
DefaultGroupName=VxPlayer
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\VxPlayer.exe
SetupIconFile=..\src\assets\vxplayer.ico
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
OutputDir=output
OutputBaseFilename=VxPlayer-Setup
VersionInfoCompany=Decan Konnect
VersionInfoDescription=VxPlayer Media Player Setup
VersionInfoProductName=VxPlayer
VersionInfoProductVersion={#AppVersion}
VersionInfoVersion={#AppVersion}.0

[Tasks]
Name: "createicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\VxPlayer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\VxPlayer"; Filename: "{app}\VxPlayer.exe"; WorkingDir: "{app}"
Name: "{autoprograms}\Uninstall VxPlayer"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VxPlayer"; Filename: "{app}\VxPlayer.exe"; WorkingDir: "{app}"; Tasks: createicon

[Run]
Filename: "{app}\VxPlayer.exe"; Description: "Launch VxPlayer"; Flags: postinstall nowait skipifsilent
