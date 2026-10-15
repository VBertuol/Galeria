"""Escreve o arquivo de versão do Windows que o PyInstaller embute no Galeria.exe.

Lê VERSAO de app/galeria.py, para a versão do programa, do .exe e do instalador ser uma só
(o SignPath exige os atributos de versão iguais em cada build). Uso: python tools/versao.py build/versao.txt
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
versao = re.search(r'^VERSAO = "([\d.]+)"', (RAIZ / "app" / "galeria.py").read_text(encoding="utf-8"), re.M)[1]
n = tuple(int(x) for x in versao.split(".")) + (0,) * (4 - len(versao.split(".")))
texto = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={n}, prodvers={n}),
  kids=[StringFileInfo([StringTable('041604b0', [
    StringStruct('CompanyName', 'Vinicius Bertuol'),
    StringStruct('FileDescription', 'Galeria: papel de parede com arte em dominio publico'),
    StringStruct('FileVersion', '{versao}'),
    StringStruct('InternalName', 'Galeria'),
    StringStruct('LegalCopyright', 'MIT License, Vinicius Bertuol'),
    StringStruct('OriginalFilename', 'Galeria.exe'),
    StringStruct('ProductName', 'Galeria'),
    StringStruct('ProductVersion', '{versao}')])]),
    VarFileInfo([VarStruct('Translation', [0x0416, 1200])])]
)
"""
saida = Path(sys.argv[1])
saida.parent.mkdir(parents=True, exist_ok=True)
saida.write_text(texto, encoding="utf-8")
print(versao)
