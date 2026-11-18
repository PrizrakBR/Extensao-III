; Instalador - TI Papanduva v1.5 (Inno Setup 6)
#define AppName "TI Papanduva"
#define AppVersion "1.5"
#define AppExe "TI_Papanduva.exe"

[Setup]
; Mesmo AppId das versões anteriores: atualizar mantém os dados existentes
AppId={{7B1E2F4A-5C3D-4E8A-9B6F-2A1D0C9E8F11}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Prefeitura Municipal de Papanduva - SC
AppComments=Sistema de Estoque e Agendamentos de TI
DefaultDirName={autopf}\TI Papanduva
DefaultGroupName=TI Papanduva
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\saida_instalador
OutputBaseFilename=Setup_TI_Papanduva_v{#AppVersion}
SetupIconFile=..\icone.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\icone.ico
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\dist_v15\TI_Papanduva\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\icone.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\TI Papanduva"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\icone.ico"; Tasks: desktopicon
Name: "{autoprograms}\TI Papanduva"; Filename: "{app}\{#AppExe}"; WorkingDir: "{app}"; IconFilename: "{app}\icone.ico"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o TI Papanduva agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Os dados (banco) ficam em %LOCALAPPDATA%\TI_Papanduva e NÃO são apagados na desinstalação.
