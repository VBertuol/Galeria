@echo off
rem Gera dist\Galeria\ (o programa em pasta) e dist\Galeria-Setup-<versao>.exe (o instalador).
rem Precisa de Python com: pip install -r requirements.txt, e do Inno Setup 6 (ISCC no PATH ou na pasta padrao).
setlocal
cd /d "%~dp0"
for /f %%v in ('python tools\versao.py build\versao.txt') do set VERSAO=%%v
python app\galeria.py --icone build\galeria.ico || exit /b 1
python -m PyInstaller --noconfirm --clean --onedir --windowed --name Galeria --icon "%~dp0build\galeria.ico" ^
  --version-file "%~dp0build\versao.txt" --add-data "%~dp0app\acervo.json;." ^
  --distpath dist --workpath build\pyinstaller --specpath build app\galeria.py || exit /b 1
set ISCC=ISCC
where ISCC >nul 2>nul || set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
%ISCC% /Q /DVersao=%VERSAO% installer\galeria.iss || exit /b 1
echo Pronto: dist\Galeria-Setup-%VERSAO%.exe
