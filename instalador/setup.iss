; Instalador - Gestão Inteligente 3.0
#define AppName "Gestão Inteligente 3.0"
#define AppVersion "3.0"
#define AppExe "GestaoInteligente.exe"

[Setup]
AppId={{7B1F6C52-3A7E-4C4D-9B58-2E5A9D0C3F31}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName}
AppPublisher=Gestão Inteligente
DefaultDirName={autopf}\Gestao Inteligente 3.0
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=gestaointeligente3.0
SetupIconFile=logo_sistema.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
CloseApplications=yes
VersionInfoVersion=3.0.0.0
VersionInfoDescription=Instalador do {#AppName}
VersionInfoProductName={#AppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce

[Files]
Source: "build\dist\GestaoInteligente\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.env"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "logo_sistema.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\logo_sistema.ico"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\logo_sistema.ico"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\logo_sistema.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent
