; Inno Setup — Instalador Windows profissional
; Requer Inno Setup 6: https://jrsoftware.org/isinfo.php

#define MyAppName "Company Email Extractor"
#define MyAppVersion "2.11.0"
#define MyAppPublisher "Company Email Extractor"
#define MyAppExeName "CompanyEmailExtractor.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=CompanyEmailExtractor-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho no Ambiente de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\dist\CompanyEmailExtractor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\COMO_USAR.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LEIA-ME.txt"; DestDir: "{app}"; Flags: ignoreversion
; Se usar build onedir, descomente:
; Source: "..\dist\CompanyEmailExtractor\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Guia do Utilizador (LEIA-ME)"; Filename: "{sys}\notepad.exe"; Parameters: """{app}\LEIA-ME.txt"""
Name: "{group}\Guia Completo (COMO_USAR)"; Filename: "{sys}\notepad.exe"; Parameters: """{app}\COMO_USAR.md"""
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\CompanyEmailExtractor"
