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
; escolhe sozinho pela língua do Windows; só pergunta quando não acha
ShowLanguageDialog=auto

[Languages]
; inglês primeiro: é o que vale quando a língua do Windows não está na lista (o chinês, por exemplo,
; não tem tradução oficial do Inno Setup, e o instalador sai em inglês; o programa tem chinês)
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "ja"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "ar"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "ko"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
en.Iniciar=Open Galeria when Windows starts (adds a shortcut to the Startup folder)
en.Abrir=Open Galeria now
ptbr.Iniciar=Abrir a Galeria quando o Windows iniciar (cria um atalho na pasta Inicializar)
ptbr.Abrir=Abrir a Galeria agora
es.Iniciar=Abrir Galeria al iniciar Windows (crea un acceso directo en la carpeta Inicio)
es.Abrir=Abrir Galeria ahora
fr.Iniciar=Ouvrir Galeria au démarrage de Windows (ajoute un raccourci dans le dossier Démarrage)
fr.Abrir=Ouvrir Galeria maintenant
de.Iniciar=Galeria beim Start von Windows öffnen (legt eine Verknüpfung im Autostart-Ordner an)
de.Abrir=Galeria jetzt öffnen
it.Iniciar=Apri Galeria all'avvio di Windows (aggiunge un collegamento nella cartella Esecuzione automatica)
it.Abrir=Apri Galeria ora
ja.Iniciar=Windows の起動時に Galeria を開く（スタートアップ フォルダーにショートカットを追加）
ja.Abrir=今すぐ Galeria を開く
ar.Iniciar=فتح Galeria عند بدء تشغيل Windows (يضيف اختصارًا إلى مجلد بدء التشغيل)
ar.Abrir=فتح Galeria الآن
ko.Iniciar=Windows 시작 시 Galeria 열기 (시작 프로그램 폴더에 바로 가기 추가)
ko.Abrir=지금 Galeria 열기
ru.Iniciar=Открывать Galeria при запуске Windows (добавляет ярлык в папку «Автозагрузка»)
ru.Abrir=Открыть Galeria сейчас

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
