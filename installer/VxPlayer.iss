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
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\VxPlayer.exe
SetupIconFile=..\src\assets\vxplayer.ico
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
DisableWelcomePage=no
DisableDirPage=no
OutputDir=output
OutputBaseFilename=VxPlayer-Setup
VersionInfoCompany=Decan Konnect
VersionInfoDescription=VxPlayer Media Player Setup
VersionInfoProductName=VxPlayer
VersionInfoProductVersion={#AppVersion}
VersionInfoVersion={#AppVersion}.0

[Tasks]
Name: "createicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "mediaassoc"; Description: "Register VxPlayer for supported media files (choose it in Windows Default apps)"; GroupDescription: "Windows integration:"
Name: "explorermenu"; Description: "Add a Play with VxPlayer right-click menu for media files"; GroupDescription: "Windows integration:"

[Messages]
WelcomeLabel1=Welcome to the VxPlayer Setup Wizard
WelcomeLabel2=This wizard will install VxPlayer, the modern media player by Decan Konnect.%n%nChoose an installation folder and optional Windows integration, then follow the installation progress.
SelectDirDesc=Choose the folder where VxPlayer should be installed.
SelectDirLabel3=Setup will install VxPlayer into the following folder. Click Next to continue, or Browse to choose another location.
PreparingDesc=Setup is preparing the VxPlayer installation.
InstallingLabel=Please wait while VxPlayer is installed on your computer.
StatusExtractFiles=Installing VxPlayer application files...

[Files]
Source: "..\dist\VxPlayer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\VxPlayer"; Filename: "{app}\VxPlayer.exe"; WorkingDir: "{app}"
Name: "{autoprograms}\Uninstall VxPlayer"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VxPlayer"; Filename: "{app}\VxPlayer.exe"; WorkingDir: "{app}"; Tasks: createicon

[Registry]
Root: HKCR; Subkey: "VxPlayer.MediaFile"; ValueType: string; ValueName: ""; ValueData: "VxPlayer media file"; Flags: uninsdeletekey; Tasks: mediaassoc
Root: HKCR; Subkey: "VxPlayer.MediaFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\VxPlayer.exe,0"; Tasks: mediaassoc
Root: HKCR; Subkey: "VxPlayer.MediaFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "VxPlayer"; Flags: uninsdeletekey; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "VxPlayer media player"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities"; ValueType: string; ValueName: "ApplicationIcon"; ValueData: "{app}\VxPlayer.exe,0"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mp4"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mkv"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".avi"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mov"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".wmv"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".flv"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".webm"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".3gp"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mp3"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".wav"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".flac"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".aac"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".ogg"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".m4a"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".m4v"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mpg"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mpeg"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".ts"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".m2ts"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".vob"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".ogv"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".opus"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".wma"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\Decan Konnect\VxPlayer\Capabilities\FileAssociations"; ValueType: string; ValueName: ".aiff"; ValueData: "VxPlayer.MediaFile"; Tasks: mediaassoc
Root: HKLM; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "VxPlayer"; ValueData: "Software\Decan Konnect\VxPlayer\Capabilities"; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".mp4\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".mkv\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".avi\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".mov\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".wmv\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".flv\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".webm\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".3gp\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".mp3\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".wav\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".flac\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".aac\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".ogg\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".m4a\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".m4v\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".mpg\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".mpeg\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".ts\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".m2ts\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".vob\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".ogv\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".opus\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".wma\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: ".aiff\OpenWithProgids"; ValueType: string; ValueName: "VxPlayer.MediaFile"; ValueData: ""; Flags: uninsdeletevalue; Tasks: mediaassoc
Root: HKCR; Subkey: "SystemFileAssociations\.mp4\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mp4\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mkv\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mkv\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.avi\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.avi\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mov\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mov\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.wmv\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.wmv\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.flv\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.flv\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.webm\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.webm\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.3gp\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.3gp\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mp3\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mp3\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.wav\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.wav\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.flac\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.flac\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.aac\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.aac\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.ogg\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.ogg\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4a\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4a\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4v\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.m4v\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpg\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpg\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpeg\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.mpeg\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.ts\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.ts\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.m2ts\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.m2ts\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.vob\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.vob\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.ogv\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.ogv\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.opus\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.opus\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.wma\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.wma\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.aiff\shell\VxPlayer.Play"; ValueType: string; ValueName: ""; ValueData: "Play with VxPlayer"; Flags: uninsdeletekey; Tasks: explorermenu
Root: HKCR; Subkey: "SystemFileAssociations\.aiff\shell\VxPlayer.Play\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VxPlayer.exe"" ""%1"""; Tasks: explorermenu

[Run]
Filename: "{app}\VxPlayer.exe"; Description: "Launch VxPlayer"; Flags: postinstall nowait skipifsilent
