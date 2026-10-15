"""Monta a imagem do papel de parede: a obra inteira no tamanho da tela, fundo desfocado da
própria obra quando o formato não bate, e a legenda (nome, artista, data, museu) num canto."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTES = Path("C:/Windows/Fonts")
# Formato quase igual ao da tela: preenche cortando um pouco, em vez de deixar faixa fina de fundo.
TOLERANCIA_CORTE = 0.06


def _fonte(nome, tamanho):
    try:
        return ImageFont.truetype(str(FONTES / nome), tamanho)
    except OSError:
        return ImageFont.load_default(tamanho)


def _quebrar(texto, fonte, largura_max, desenho):
    """Quebra o texto em linhas que caibam na largura; no máximo duas, a segunda com reticências."""
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if desenho.textlength(teste, font=fonte) <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    if len(linhas) > 2:
        resto = " ".join(linhas[1:])
        while resto and desenho.textlength(resto + "…", font=fonte) > largura_max:
            resto = resto[:-1]
        linhas = [linhas[0], resto.rstrip() + "…"]
    return linhas


def compor(origem, obra, tela, area_util, destino):
    """origem: arquivo da obra baixada. tela: (largura, altura) do monitor em pixels.
    area_util: (esq, topo, dir, baixo) da área sem a barra de tarefas. destino: arquivo de saída."""
    W, H = tela
    faixa = 0  # largura da faixa de fundo à direita da obra, onde a legenda pode ficar sem cobrir a pintura
    img = Image.open(origem).convert("RGB")
    w, h = img.size
    proporcao_obra, proporcao_tela = w / h, W / H

    if abs(proporcao_obra / proporcao_tela - 1) <= TOLERANCIA_CORTE:
        escala = max(W / w, H / h)
        nova = img.resize((round(w * escala), round(h * escala)), Image.LANCZOS)
        x, y = (nova.width - W) // 2, (nova.height - H) // 2
        quadro = nova.crop((x, y, x + W, y + H))
    else:
        # fundo: a obra ampliada até cobrir a tela, borrada e escurecida (feita pequena, que é mais rápido)
        escala_fundo = max(W / w, H / h) / 8
        fundo = img.resize((max(1, round(w * escala_fundo)), max(1, round(h * escala_fundo))), Image.BILINEAR)
        fundo = fundo.filter(ImageFilter.GaussianBlur(6)).resize(
            (round(w * escala_fundo * 8), round(h * escala_fundo * 8)), Image.BILINEAR)
        x, y = (fundo.width - W) // 2, (fundo.height - H) // 2
        quadro = fundo.crop((x, y, x + W, y + H))
        quadro = Image.blend(quadro, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
        escala = min(W / w, H / h)
        frente = img.resize((round(w * escala), round(h * escala)), Image.LANCZOS)
        quadro.paste(frente, ((W - frente.width) // 2, (H - frente.height) // 2))
        faixa = (W - frente.width) // 2

    _legenda(quadro, obra, area_util, faixa)
    quadro.save(destino, "JPEG", quality=93)


def _legenda(quadro, obra, area_util, faixa=0):
    W, H = quadro.size
    u = H / 1080  # unidade: tudo proporcional à altura da tela
    f_titulo = _fonte("segoeuib.ttf", round(26 * u))
    f_linha = _fonte("segoeui.ttf", round(19 * u))
    f_museu = _fonte("segoeuii.ttf", round(16 * u))
    rascunho = ImageDraw.Draw(quadro)
    largura_max = round(520 * u)
    pad = round(18 * u)
    margem = round(28 * u)
    # cabe na faixa lateral, mesmo quebrando o título em mais linhas? então fica lá
    na_faixa = faixa - 2 * margem - 2 * pad >= round(200 * u)
    if na_faixa:
        largura_max = faixa - 2 * margem - 2 * pad

    linhas = [(l, f_titulo, (255, 255, 255)) for l in _quebrar(obra["titulo"], f_titulo, largura_max, rascunho)]
    autor = obra["artista"] + (f", {obra['data']}" if obra.get("data") else "")
    linhas += [(l, f_linha, (225, 225, 225)) for l in _quebrar(autor, f_linha, largura_max, rascunho)]
    if obra.get("museu"):
        linhas += [(l, f_museu, (185, 185, 185)) for l in _quebrar(obra["museu"], f_museu, largura_max, rascunho)]

    espaco = round(6 * u)
    alturas = [rascunho.textbbox((0, 0), t, font=f)[3] for t, f, _ in linhas]
    larg = max(rascunho.textlength(t, font=f) for t, f, _ in linhas)
    caixa_w = round(larg) + 2 * pad
    caixa_h = sum(alturas) + espaco * (len(linhas) - 1) + 2 * pad

    _, _, dir_util, baixo_util = area_util
    x1, y1 = dir_util - margem, baixo_util - margem
    x0, y0 = x1 - caixa_w, y1 - caixa_h

    camada = Image.new("RGBA", quadro.size, (0, 0, 0, 0))
    ImageDraw.Draw(camada).rounded_rectangle((x0, y0, x1, y1), radius=round(10 * u), fill=(0, 0, 0, 150))
    base = quadro.convert("RGBA")
    base.alpha_composite(camada)
    d = ImageDraw.Draw(base)
    y = y0 + pad
    for (t, f, cor), a in zip(linhas, alturas):
        d.text((x0 + pad, y), t, font=f, fill=cor)
        y += a + espaco
    quadro.paste(base.convert("RGB"))
