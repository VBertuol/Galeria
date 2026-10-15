; Instalador da Galeria (Inno Setup 6). Compilado por build.cmd ou pelo GitHub Actions:
;   ISCC /DVersao=1.0.0 installer\galeria.iss
#ifndef Versao
  #define Versao "0.0.0"
#endif

[Setup]
AppId={{6F2C1E4B-6A0D-4C5E-9B57-3A1F0D2B8C71}
AppName=Galeria
AppVersion={#Versao}
AppVerName=Galeria {#Versao}
AppPublisher=Vinicius Bertuol
AppPublisherURL=https://github.com/VBertuol/galeria
VersionInfoVersion={#Versao}
VersionInfoProductName=Galeria
VersionInfoProductVersion={#Versao}
DefaultDirName={localappdata}\Programs\Galeria
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Galeria-Setup-{#Versao}
SetupIconFile=..\build\galeria.ico
UninstallDisplayIcon={app}\Galeria.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; fecha o programa antes de atualizar ou desinstalar
AppMutex=GaleriaPapelDeParede,Global\GaleriaPapelDeParede
LicenseFile=..\LICENSE

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
ptbr.Iniciar=Abrir a Galeria quando o Windows iniciar (cria um atalho na pasta Inicializar)
en.Iniciar=Open Galeria when Windows starts (adds a shortcut to the Startup folder)
ptbr.Abrir=Abrir a Galeria agora
en.Abrir=Open Galeria now

[Tasks]
Name: "iniciar"; Description: "{cm:Iniciar}"

[Files]
Source: "..\dist\Galeria\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Galeria"; Filename: "{app}\Galeria.exe"
Name: "{userstartup}\Galeria"; Filename: "{app}\Galeria.exe"; Tasks: iniciar

[Run]
Filename: "{app}\Galeria.exe"; Description: "{cm:Abrir}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; estado e cache do programa (config.json, imagens baixadas, papel de parede montado)
Type: filesandordirs; Name: "{localappdata}\Galeria"
