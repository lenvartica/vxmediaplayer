#define AppName "VxPlayer Setup"
#define SetupOutput "VxPlayer-Setup"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{A8D9A944-AD93-45C2-8452-BB73A1F20941}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Decan Konnect
AppPublisherURL=https://github.com/lenvartica/vxmediaplayer
DefaultDirName={tmp}\VxPlayerBootstrap
CreateAppDir=no
Uninstallable=no
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=..\src\assets\vxplayer.ico
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
OutputBaseFilename={#SetupOutput}
VersionInfoCompany=Decan Konnect
VersionInfoDescription=VxPlayer Online Setup
VersionInfoProductName=VxPlayer
VersionInfoProductVersion={#AppVersion}
VersionInfoVersion={#AppVersion}

[Messages]
WelcomeLabel1=Welcome to VxPlayer Setup
WelcomeLabel2=This small setup downloads the full VxPlayer installer. The regular setup wizard will then let you choose the installation folder and options.
InstallingLabel=Downloading the full VxPlayer installer...

[Files]
Source: "{#PayloadUrl}"; DestName: "VxPlayer-Setup-Full.exe"; DestDir: "{tmp}"; Hash: "{#PayloadSha256}"; ExternalSize: {#PayloadSize}; Flags: external download ignoreversion

[Code]
function GetFullInstallerArguments(Param: String): String;
var
  CommandLine: String;
  InternalArgumentEnd: Integer;
  LogSwitchPosition: Integer;
  LogValueStart: Integer;
  LogValueEnd: Integer;
begin
  CommandLine := GetCmdTail;
  if CompareText(Copy(CommandLine, 1, 5), '/SL5=') = 0 then
  begin
    InternalArgumentEnd := Pos(' /', CommandLine);
    if InternalArgumentEnd = 0 then
      CommandLine := ''
    else
      CommandLine := Copy(
        CommandLine,
        InternalArgumentEnd + 1,
        Length(CommandLine)
      );
  end;
  LogSwitchPosition := Pos('/LOG=', Uppercase(CommandLine));
  if LogSwitchPosition > 0 then
  begin
    LogValueStart := LogSwitchPosition + 5;
    if Copy(CommandLine, LogValueStart, 1) = '"' then
    begin
      LogValueEnd := Pos('"', Copy(CommandLine, LogValueStart + 1, Length(CommandLine)));
      if LogValueEnd > 0 then
        LogValueEnd := LogValueStart + LogValueEnd
      else
        LogValueEnd := Length(CommandLine);
    end
    else
    begin
      LogValueEnd := Pos(' ', Copy(CommandLine, LogValueStart, Length(CommandLine)));
      if LogValueEnd > 0 then
        LogValueEnd := LogValueStart + LogValueEnd - 2
      else
        LogValueEnd := Length(CommandLine);
    end;
    if (LogValueEnd < Length(CommandLine)) and (Copy(CommandLine, LogValueEnd + 1, 1) = ' ') then
      LogValueEnd := LogValueEnd + 1;
    Delete(CommandLine, LogSwitchPosition, LogValueEnd - LogSwitchPosition + 1);
  end;
  Result := CommandLine;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if not Exec(
      ExpandConstant('{tmp}\VxPlayer-Setup-Full.exe'),
      GetFullInstallerArguments(''),
      '',
      SW_SHOWNORMAL,
      ewWaitUntilTerminated,
      ResultCode
    ) then
      RaiseException('Could not launch the full VxPlayer setup.');
    if ResultCode <> 0 then
      RaiseException(Format('The full VxPlayer setup failed with exit code %d.', [ResultCode]));
  end;
end;
