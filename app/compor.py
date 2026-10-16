"""Monta a imagem do papel de parede: a obra inteira no tamanho da tela, fundo desfocado da
própria obra quando o formato não bate, e a legenda (nome, artista, data, museu) num canto."""
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from textos import DIREITA_PARA_ESQUERDA, FONTES as FONTES_LINGUA, FONTES_PADRAO

FONTES = Path("C:/Windows/Fonts")
# Formato quase igual ao da tela: preenche cortando um pouco, em vez de deixar faixa fina de fundo.
TOLERANCIA_CORTE = 0.06


def _fonte(nome, tamanho):
    try:
        return ImageFont.truetype(str(FONTES / nome), tamanho)
    except OSError:
        return ImageFont.load_default(tamanho)


def _visual(texto, rtl):
    """Árabe: o Pillow sem a libraqm não junta as letras nem inverte a ordem; o arabic_reshaper
    junta (forma inicial, medial, final) e o python-bidi põe na ordem em que se desenha."""
    if not rtl:
        return texto
    import arabic_reshaper
    from bidi import get_display
    v = get_display(arabic_reshaper.reshape(texto))
    # o python-bidi não espelha parêntese: no texto todo em árabe, "(" desenhado à esquerda tem de ser ")"
    if not re.search("[A-Za-z]", texto):
        v = v.translate(str.maketrans("()[]{}«»", ")(][}{»«"))
    return v


def _quebrar(texto, fonte, largura_max, desenho, rtl=False):
    """Quebra o texto em linhas que caibam na largura; no máximo duas, a segunda com reticências.
    Palavra que sozinha não cabe (título em chinês ou japonês não tem espaço) quebra por caractere."""
    medir = lambda t: desenho.textlength(_visual(t, rtl), font=fonte)
    pedacos = []
    for p in texto.split():
        while medir(p) > largura_max and len(p) > 1:
            k = len(p)
            while k > 1 and medir(p[:k]) > largura_max:
                k -= 1
            pedacos.append(p[:k])
            p = p[k:]
        pedacos.append(p)
    sep = " " if " " in texto.strip() else ""  # sem espaço no texto (chinês, japonês), sem espaço ao juntar
    juntar = lambda a, b: f"{a}{sep}{b}" if a else b
    linhas, atual = [], ""
    for p in pedacos:
        teste = juntar(atual, p)
        if medir(teste) <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    if len(linhas) > 2:
        resto = sep.join(linhas[1:])
        while resto and medir(resto + "…") > largura_max:
            resto = resto[:-1]
        linhas = [linhas[0], resto.rstrip() + "…"]
    return [_visual(l, rtl) for l in linhas]


def compor(origem, legenda, tela, area_util, destino):
    """origem: arquivo da obra baixada. legenda: {"titulo", "autor", "museu", "lingua"}, já na língua.
    tela: (largura, altura) do monitor em pixels. area_util: (esq, topo, dir, baixo) da área sem a
    barra de tarefas. destino: arquivo de saída."""
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

    _legenda(quadro, legenda, area_util, faixa)
    quadro.save(destino, "JPEG", quality=93)


def _legenda(quadro, legenda, area_util, faixa=0):
    W, H = quadro.size
    u = H / 1080  # unidade: tudo proporcional à altura da tela
    lingua = legenda.get("lingua", "en")
    rtl = lingua in DIREITA_PARA_ESQUERDA
    n_titulo, n_linha, n_museu = FONTES_LINGUA.get(lingua, FONTES_PADRAO)
    f_titulo = _fonte(n_titulo, round(26 * u))
    f_linha = _fonte(n_linha, round(19 * u))
    f_museu = _fonte(n_museu, round(16 * u))
    rascunho = ImageDraw.Draw(quadro)
    largura_max = round(520 * u)
    pad = round(18 * u)
    margem = round(28 * u)
    # cabe na faixa lateral, mesmo quebrando o título em mais linhas? então fica lá
    na_faixa = faixa - 2 * margem - 2 * pad >= round(200 * u)
    if na_faixa:
        largura_max = faixa - 2 * margem - 2 * pad

    linhas = [(l, f_titulo, (255, 255, 255)) for l in _quebrar(legenda["titulo"], f_titulo, largura_max, rascunho, rtl)]
    linhas += [(l, f_linha, (225, 225, 225)) for l in _quebrar(legenda["autor"], f_linha, largura_max, rascunho, rtl)]
    if legenda.get("museu"):
        linhas += [(l, f_museu, (185, 185, 185)) for l in _quebrar(legenda["museu"], f_museu, largura_max, rascunho, rtl)]

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
        x = x1 - pad - d.textlength(t, font=f) if rtl else x0 + pad  # árabe alinha pela direita
        d.text((x, y), t, font=f, fill=cor)
        y += a + espaco
    quadro.paste(base.convert("RGB"))
