"""Galeria: troca o papel de parede do Windows por obras de arte em domínio público.

Fica na bandeja (perto do relógio). Menu: próxima obra, sobre esta obra, pausar, intervalo, sair.
Abrir com o Windows é opção do instalador (atalho na pasta Inicializar), não do programa: um programa
que se registra sozinho para iniciar e troca o papel de parede imita ransomware, e o antivírus bloqueia.
As obras vêm da lista curada `acervo.json` e as imagens são baixadas do Wikimedia Commons na hora, no
tamanho da tela, e guardadas num cache pequeno.
"""
import ctypes
import json
import math
import os
import random
import sys
import threading
import time
import webbrowser
from ctypes import HRESULT, POINTER, WINFUNCTYPE, byref, c_void_p, wintypes
from pathlib import Path
from urllib.parse import quote

import pystray
import requests
from PIL import Image, ImageDraw

import textos
from compor import TOLERANCIA_CORTE, compor

NOME = "Galeria"
VERSAO = "1.1.0"
UA = {"User-Agent": "Galeria/1.0 (papel de parede com arte em dominio publico)"}
BASE = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
PASTA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / NOME
CACHE = PASTA / "cache"
CONFIG = PASTA / "config.json"
MAX_CACHE = 40  # imagens guardadas para funcionar sem internet
# em segundos; os rótulos de cada língua estão em textos.py, na mesma ordem
INTERVALOS = [30, 60, 120, 300, 900, 1800, 3600, 10800, 86400]


# ---------- Windows ----------

def tela_e_area():
    """Resolução real do monitor principal e a área sem a barra de tarefas."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()
    u32 = ctypes.windll.user32
    W, H = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
    r = wintypes.RECT()
    u32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0)  # SPI_GETWORKAREA
    return (W, H), (r.left, r.top, r.right, r.bottom)


def _guid(texto):
    class GUID(ctypes.Structure):
        _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD), ("d3", wintypes.WORD), ("d4", ctypes.c_ubyte * 8)]
    g = GUID()
    ctypes.oledll.ole32.CLSIDFromString(texto, byref(g))
    return g


def pasta_imagens():
    """A pasta Imagens do usuário, onde o Windows está mesmo (pode ter sido movida, pelo OneDrive por exemplo)."""
    p = ctypes.c_wchar_p()
    try:
        ctypes.oledll.shell32.SHGetKnownFolderPath(byref(_guid("{33E28130-4E1E-4676-835A-98395C3BC3BB}")),  # Pictures
                                                   0, None, byref(p))
        return Path(p.value)
    except OSError:
        return Path.home() / "Pictures"
    finally:
        ctypes.windll.ole32.CoTaskMemFree(p)


def aplicar_papel(caminho):
    """Pede ao Explorer, pela interface IDesktopWallpaper, para pôr a imagem como papel de parede.

    Medido em 2026-10-15 no PC do Vinicius: o SystemParametersInfo devolvia sucesso e o Windows não
    trocava nada, porque o fundo tinha ficado em "cor sólida" (o Wallpaper Engine deixa assim) e porque
    o Windows reaproveita a cópia guardada de um caminho que ele já conhece. Por isso: Enable(TRUE)
    religa o modo imagem, e cada obra vai num arquivo de nome novo. A imagem já sai no tamanho exato
    da tela, então o estilo (preencher, centralizar) não importa e não se mexe nele."""
    ole = ctypes.oledll.ole32
    ole.CoInitialize(None)
    ptr = c_void_p()
    try:
        ole.CoCreateInstance(byref(_guid("{C2CF3110-460E-4fc1-B9D0-8A1C0C9CC4BD}")), None, 0x17,
                             byref(_guid("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")), byref(ptr))
        vtbl = ctypes.cast(ptr, POINTER(POINTER(c_void_p))).contents
        set_wallpaper = WINFUNCTYPE(HRESULT, c_void_p, wintypes.LPCWSTR, wintypes.LPCWSTR)(vtbl[3])
        enable = WINFUNCTYPE(HRESULT, c_void_p, wintypes.BOOL)(vtbl[18])
        release = WINFUNCTYPE(wintypes.ULONG, c_void_p)(vtbl[2])
        try:
            enable(ptr, True)
            set_wallpaper(ptr, None, str(caminho))
        finally:
            release(ptr)
    except OSError:
        # sem a interface (Windows antigo): o caminho clássico
        if not ctypes.windll.user32.SystemParametersInfoW(20, 0, str(caminho), 3):
            raise OSError("o Windows recusou o papel de parede")
    finally:
        ole.CoUninitialize()


def uma_instancia():
    ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\GaleriaPapelDeParede")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


# ---------- estado ----------

def ler_config():
    padrao = {"segundos": 1800, "pausado": False, "fila": [], "atual": None, "lingua": textos.PADRAO}
    try:
        padrao.update(json.loads(CONFIG.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError):
        pass
    if "intervalo" in padrao:  # a 1.0.0 guardava minutos
        padrao["segundos"] = padrao.pop("intervalo") * 60
    return padrao


def gravar_config(cfg):
    PASTA.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    tmp.replace(CONFIG)


# ---------- obras ----------

def largura_pedida(obra, tela):
    """Largura a pedir ao Commons: a que cobre a tela no encaixe inteiro, nunca mais que o original."""
    W, H = tela
    w, h = obra["largura"], obra["altura"]
    if abs((w / h) / (W / H) - 1) <= TOLERANCIA_CORTE:
        escala = max(W / w, H / h)  # vai preencher a tela cortando um pouco
    else:
        escala = min(W / w, H / h)  # vai inteira, com fundo desfocado
    return min(w, math.ceil(w * escala))


def baixar(obra, tela):
    CACHE.mkdir(parents=True, exist_ok=True)
    largura = largura_pedida(obra, tela)
    arq = CACHE / f"{obra['id']}-{largura}.jpg"
    if arq.exists():
        return arq
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(obra["arquivo"].replace(" ", "_"))
    r = requests.get(url, params={"width": largura}, headers=UA, timeout=120)
    r.raise_for_status()
    tmp = arq.with_suffix(".part")
    tmp.write_bytes(r.content)
    Image.open(tmp).verify()  # imagem truncada não entra no cache
    tmp.replace(arq)
    antigos = sorted(CACHE.glob("*.jpg"), key=lambda p: p.stat().st_mtime)
    for p in antigos[:-MAX_CACHE]:
        p.unlink(missing_ok=True)
    return arq


def em_cache(obra):
    achados = sorted(CACHE.glob(f"{obra['id']}-*.jpg"))
    return achados[-1] if achados else None


class Galeria:
    def __init__(self):
        self.acervo = {o["id"]: o for o in json.loads((BASE / "acervo.json").read_text(encoding="utf-8"))}
        self.cfg = ler_config()
        self.trava = threading.Lock()
        self.acordar = threading.Event()  # "Próxima obra": troca na hora
        self.recontar = threading.Event()  # intervalo mudou: recomeça a contagem sem trocar
        self.saindo = False
        self.icone = None

    # baralho: todas as obras passam uma vez antes de repetir
    def sortear(self):
        fila = [i for i in self.cfg["fila"] if i in self.acervo]
        if not fila:
            fila = list(self.acervo)
            random.shuffle(fila)
        obra_id = fila.pop()
        self.cfg["fila"] = fila
        return self.acervo[obra_id]

    def trocar(self):
        with self.trava:
            tela, area = tela_e_area()
            for _ in range(5):
                obra = self.sortear()
                try:
                    origem = baixar(obra, tela)
                except Exception:
                    origem = None
                if origem:
                    break
            else:
                # sem internet: roda o que estiver guardado
                guardadas = [o for o in self.acervo.values() if em_cache(o)]
                if not guardadas:
                    self.dizer(self.t("sem_internet"))
                    return
                obra = random.choice(guardadas)
                origem = em_cache(obra)
            self.mostrar(obra, origem, tela, area)

    def redesenhar(self):
        """Mesma obra, legenda em outra língua (quando a pessoa troca o idioma no menu)."""
        with self.trava:
            obra = self.atual()
            if not obra:
                return
            tela, area = tela_e_area()
            origem = em_cache(obra) or baixar(obra, tela)
            self.mostrar(obra, origem, tela, area)

    def mostrar(self, obra, origem, tela, area):
        # Em Imagens\Galeria, e não em AppData: no PC dele o Explorer respondia "arquivo não
        # encontrado" para imagem nova em AppData e lia normal de Imagens. Nome novo a cada obra,
        # porque o Windows reaproveita a cópia guardada de um caminho que ele já conhece.
        pasta = pasta_imagens() / NOME
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / f"galeria-{time.strftime('%Y%m%d-%H%M%S')}-{obra['id']}.jpg"
        compor(origem, self.legenda(obra), tela, area, destino)
        aplicar_papel(destino)
        for velho in sorted(pasta.glob("galeria-*.jpg"))[:-2]:  # fica a atual e a anterior
            velho.unlink(missing_ok=True)
        self.cfg["atual"] = obra["id"]
        gravar_config(self.cfg)
        self.atualizar_icone()

    # ---------- língua ----------
    def lingua(self):
        return self.cfg.get("lingua", textos.PADRAO)

    def t(self, chave):
        return textos.t(self.lingua(), chave)

    def legenda(self, obra):
        l = self.lingua()
        sep = textos.separador(l)
        autor = sep.join(textos.da_obra(a, l) for a in obra["artistas"]) or self.t("desconhecido")
        if obra.get("data"):
            autor += sep + obra["data"]
        return {"titulo": textos.da_obra(obra["titulo"], l), "autor": autor,
                "museu": textos.da_obra(obra.get("museu"), l), "lingua": l}

    def atual(self):
        return self.acervo.get(self.cfg.get("atual"))

    def dizer(self, texto):
        if self.icone:
            try:
                self.icone.notify(texto, NOME)
            except Exception:
                pass

    def atualizar_icone(self):
        if not self.icone:
            return
        o = self.atual()
        if o:
            leg = self.legenda(o)
            dica = f"{leg['titulo']} ({leg['autor']})"
        else:
            dica = NOME
        self.icone.title = dica[:127]
        self.icone.update_menu()

    # laço: troca a cada intervalo, ou na hora quando o menu pede
    def laco(self):
        if not self.cfg.get("atual") or not self.cfg["pausado"]:
            self.trocar_seguro()
        while not self.saindo:
            fim = time.time() + self.cfg["segundos"]
            while not (self.saindo or self.acordar.is_set()) and time.time() < fim:
                time.sleep(0.25)
                if self.recontar.is_set():
                    self.recontar.clear()
                    fim = time.time() + self.cfg["segundos"]
            if self.saindo:
                break
            pedido = self.acordar.is_set()
            self.acordar.clear()
            if pedido or not self.cfg["pausado"]:
                self.trocar_seguro()

    def seguro(self, funcao):
        try:
            funcao()
        except Exception as e:
            self.dizer(self.t("erro").format(erro=e))
            import traceback
            with open(PASTA / "erros.log", "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")

    def trocar_seguro(self):
        self.seguro(self.trocar)

    # ---------- menu ----------
    # Todo rótulo é função, para o menu mudar de língua na hora, sem reiniciar.
    def menu(self):
        def intervalo(i, segundos):
            def acao(icone, item):
                self.cfg["segundos"] = segundos
                gravar_config(self.cfg)
                self.recontar.set()  # o novo intervalo vale já, sem esperar o antigo acabar
            return pystray.MenuItem(lambda item: self.t("intervalos")[i], acao,
                                    checked=lambda item: self.cfg["segundos"] == segundos, radio=True)

        def lingua(codigo, nome):
            def acao(icone, item):
                self.cfg["lingua"] = codigo
                gravar_config(self.cfg)
                self.atualizar_icone()
                threading.Thread(target=self.seguro, args=(self.redesenhar,), daemon=True).start()
            return pystray.MenuItem(nome, acao, checked=lambda item: self.lingua() == codigo, radio=True)

        def titulo_atual(item):
            o = self.atual()
            return textos.da_obra(o["titulo"], self.lingua()) if o else self.t("nenhuma")

        def rotulo_lingua(item):
            # "Language" vai junto em toda língua, para quem caiu numa que não lê achar o caminho de volta
            nome = self.t("lingua")
            return nome if self.lingua() == "en" else f"{nome} (Language)"

        return pystray.Menu(
            pystray.MenuItem(titulo_atual, None, enabled=False),
            pystray.MenuItem(lambda item: self.t("sobre"), self.sobre, default=True),
            pystray.MenuItem(lambda item: self.t("proxima"), lambda i, it: self.acordar.set()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self.t("pausar"), self.pausar, checked=lambda item: self.cfg["pausado"]),
            pystray.MenuItem(lambda item: self.t("trocar"),
                             pystray.Menu(*[intervalo(i, s) for i, s in enumerate(INTERVALOS)])),
            pystray.MenuItem(rotulo_lingua, pystray.Menu(*[lingua(c, n) for c, n in textos.LINGUAS])),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self.t("sair"), self.sair),
        )

    def sobre(self, icone=None, item=None):
        o = self.atual()
        if o:
            webbrowser.open(textos.da_obra(o["links"], self.lingua()))

    def pausar(self, icone, item):
        self.cfg["pausado"] = not self.cfg["pausado"]
        gravar_config(self.cfg)

    def sair(self, icone, item):
        self.saindo = True
        self.acordar.set()
        icone.stop()

    def rodar(self):
        self.icone = pystray.Icon(NOME, desenhar_icone(), NOME, self.menu())
        threading.Thread(target=self.laco, daemon=True).start()
        self.icone.run()


def desenhar_icone():
    """Moldura dourada com uma paisagem dentro: o ícone da bandeja e do .exe."""
    t = 64
    im = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 6, 61, 57), radius=6, fill=(176, 132, 52))
    d.rectangle((9, 13, 54, 50), fill=(120, 170, 210))
    d.polygon([(9, 50), (24, 28), (36, 42), (44, 33), (54, 46), (54, 50)], fill=(62, 104, 66))
    d.ellipse((40, 17, 49, 26), fill=(250, 226, 140))
    return im


def main():
    if "--icone" in sys.argv:  # usado no build para gerar o .ico
        desenhar_icone().save(sys.argv[-1], sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        return
    if "--uma-vez" in sys.argv:  # troca uma vez e sai (teste)
        Galeria().trocar()
        return
    if not uma_instancia():
        return
    Galeria().rodar()


if __name__ == "__main__":
    main()
