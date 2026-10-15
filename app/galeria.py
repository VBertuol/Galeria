"""Galeria: troca o papel de parede do Windows por obras de arte em domínio público.

Fica na bandeja (perto do relógio). Menu: próxima obra, sobre esta obra, pausar, intervalo, sair.
Abrir com o Windows é opção do instalador (atalho na pasta Inicializar), não do programa: um programa
que se registra sozinho para iniciar e troca o papel de parede imita ransomware, e o antivírus bloqueia. As obras vêm da lista curada `acervo.json` e as imagens são
baixadas do Wikimedia Commons na hora, no tamanho da tela, e guardadas num cache pequeno.
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
from ctypes import wintypes
from pathlib import Path
from urllib.parse import quote

import pystray
import requests
from PIL import Image, ImageDraw

from compor import TOLERANCIA_CORTE, compor

NOME = "Galeria"
VERSAO = "1.0.0"
UA = {"User-Agent": "Galeria/1.0 (papel de parede com arte em dominio publico)"}
BASE = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
PASTA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / NOME
CACHE = PASTA / "cache"
CONFIG = PASTA / "config.json"
MAX_CACHE = 40  # imagens guardadas para funcionar sem internet
INTERVALOS = [(5, "5 minutos"), (15, "15 minutos"), (30, "30 minutos"), (60, "1 hora"),
              (180, "3 horas"), (1440, "1 dia")]


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


def aplicar_papel(caminho):
    # A imagem já sai no tamanho exato da tela, então qualquer estilo do Windows (preencher, centralizar,
    # lado a lado) mostra igual; não mexer no estilo é uma alteração de sistema a menos.
    # SPI_SETDESKWALLPAPER, gravando no perfil e avisando as janelas
    if not ctypes.windll.user32.SystemParametersInfoW(20, 0, str(caminho), 3):
        raise OSError("o Windows recusou o papel de parede")


def uma_instancia():
    ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\GaleriaPapelDeParede")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


# ---------- estado ----------

def ler_config():
    padrao = {"intervalo": 30, "pausado": False, "fila": [], "atual": None}
    try:
        padrao.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
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
        self.acordar = threading.Event()
        self.saindo = False
        self.icone = None
        self.proxima_em = 0

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
                    self.dizer("Sem internet e nenhuma obra guardada ainda.")
                    return
                obra = random.choice(guardadas)
                origem = em_cache(obra)
            # o Windows guarda o papel pelo caminho: alternar o nome força a troca
            destino = PASTA / ("papel-a.jpg" if self.cfg.get("ultimo") != "papel-a.jpg" else "papel-b.jpg")
            compor(origem, obra, tela, area, destino)
            aplicar_papel(destino)
            self.cfg["ultimo"] = destino.name
            self.cfg["atual"] = obra["id"]
            gravar_config(self.cfg)
            self.atualizar_icone()

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
        dica = f"{o['titulo']} ({o['artista']})" if o else NOME
        self.icone.title = dica[:127]
        self.icone.update_menu()

    # laço: troca a cada intervalo, ou na hora quando o menu pede
    def laco(self):
        if not self.cfg.get("atual") or not self.cfg["pausado"]:
            self.trocar_seguro()
        while not self.saindo:
            self.proxima_em = time.time() + self.cfg["intervalo"] * 60
            pedido = self.acordar.wait(self.cfg["intervalo"] * 60)
            self.acordar.clear()
            if self.saindo:
                break
            if pedido or not self.cfg["pausado"]:
                self.trocar_seguro()

    def trocar_seguro(self):
        try:
            self.trocar()
        except Exception as e:
            self.dizer(f"Não consegui trocar a obra: {e}")

    # ---------- menu ----------
    def menu(self):
        def intervalo(minutos, rotulo):
            def acao(icone, item):
                self.cfg["intervalo"] = minutos
                gravar_config(self.cfg)
            return pystray.MenuItem(rotulo, acao, checked=lambda item: self.cfg["intervalo"] == minutos, radio=True)

        def titulo_atual(item):
            o = self.atual()
            return o["titulo"] if o else "Nenhuma obra ainda"

        return pystray.Menu(
            pystray.MenuItem(titulo_atual, None, enabled=False),
            pystray.MenuItem("Sobre esta obra", self.sobre, default=True),
            pystray.MenuItem("Próxima obra", lambda i, it: self.acordar.set()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pausar", self.pausar, checked=lambda item: self.cfg["pausado"]),
            pystray.MenuItem("Trocar a cada", pystray.Menu(*[intervalo(m, r) for m, r in INTERVALOS])),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sair", self.sair),
        )

    def sobre(self, icone=None, item=None):
        o = self.atual()
        if o:
            webbrowser.open(o["link"])

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
