; Pacote de atualização - Gestão Inteligente 3.0
; Mesmo AppId do instalador original: atualiza os arquivos em cima da instalação existente.
; Os dados (banco, backups) ficam em %LOCALAPPDATA%\GestaoInteligente e não são tocados.
#define AppName "Gestão Inteligente 3.0"
#define AppExe "GestaoInteligente.exe"

[Setup]
AppId={{7B1F6C52-3A7E-4C4D-9B58-2E5A9D0C3F31}
AppName={#AppName}
AppVersion=3.0.1
AppPublisher=Gestão Inteligente
DefaultDirName={autopf}\Gestao Inteligente 3.0
UsePreviousAppDir=yes
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=atualizacao_gestaointeligente3.0
SetupIconFile=logo_sistema.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
CloseApplications=yes
CreateUninstallRegKey=no
UpdateUninstallLogAppName=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "build\dist\GestaoInteligente\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent
