; Pacote de atualização - Gestão Inteligente 3.0
; Mesmo AppId do instalador original: atualiza os arquivos em cima da instalação existente.
; Os dados (banco, backups) ficam em %LOCALAPPDATA%\GestaoInteligente e não são tocados.
#define AppName "Gestão Inteligente 3.0"
#define AppVersion "3.0.5"
#define AppExe "GestaoInteligente.exe"
#define UpdateName "Atualização - Gestão Inteligente 3.0"

[Setup]
AppId={{7B1F6C52-3A7E-4C4D-9B58-2E5A9D0C3F31}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#UpdateName} {#AppVersion}
AppPublisher=Gestão Inteligente
DefaultDirName={autopf}\Gestao Inteligente 3.0
UsePreviousAppDir=yes
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=atualizacao_gestaointeligente{#AppVersion}
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
VersionInfoVersion=3.0.5.0
VersionInfoDescription=Pacote de Atualização do {#AppName}
VersionInfoProductName={#UpdateName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Messages]
; Textos do assistente reescritos para deixar claro que e uma ATUALIZACAO (nao uma instalacao nova).
brazilianportuguese.WelcomeLabel1=Bem-vindo ao Assistente de Atualização do [name]
brazilianportuguese.WelcomeLabel2=Esta atualização vai atualizar o [name/ver] já instalado neste computador.%n%nSeus dados (vendas, produtos, clientes e configurações) serão mantidos.%n%nRecomenda-se fechar o sistema antes de continuar.%n%nClique em Avançar para continuar.
brazilianportuguese.WizardReady=Pronto para Atualizar
brazilianportuguese.ReadyLabel1=O assistente está pronto para atualizar o [name] neste computador.
brazilianportuguese.ReadyLabel2a=Clique em Atualizar para iniciar a atualização.
brazilianportuguese.ReadyLabel2b=Clique em Atualizar para iniciar a atualização.
brazilianportuguese.ButtonInstall=&Atualizar
brazilianportuguese.WizardInstalling=Atualizando
brazilianportuguese.InstallingLabel=Aguarde enquanto o [name] é atualizado neste computador.
brazilianportuguese.FinishedHeadingLabel=Concluindo a Atualização do [name]
brazilianportuguese.FinishedLabelNoIcons=A atualização do [name] foi concluída com sucesso.
brazilianportuguese.FinishedLabel=A atualização do [name] foi concluída com sucesso. Seus dados foram mantidos.
brazilianportuguese.ClickFinish=Clique em Concluir para sair do Assistente de Atualização.
brazilianportuguese.SetupWindowTitle=Atualização - %1
brazilianportuguese.ExitSetupTitle=Sair da Atualização
brazilianportuguese.ExitSetupMessage=A atualização não foi concluída. Se sair agora, o sistema não será atualizado.%n%nVocê pode executar este arquivo novamente mais tarde para concluir a atualização.%n%nDeseja sair?
brazilianportuguese.ErrorTitle=Erro na Atualização

[Files]
Source: "build\dist\GestaoInteligente\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent
