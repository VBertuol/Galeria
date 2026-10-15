"""Monta a lista curada de obras da galeria.

Fonte: Wikidata (o que a obra é, quem pintou, quando, onde está) e Wikimedia Commons
(a imagem e o tamanho dela). Critério de "obra conhecida": número de Wikipédias que têm
artigo sobre ela (sitelinks). Critério de domínio público: autor morto até 1955 (70 anos
depois da morte, regra do Brasil e da maior parte do mundo) ou, sem autor conhecido, obra
anterior a 1900. Critério de 4K: a imagem cobre pelo menos 75% de uma tela 3840x2160 no
encaixe inteiro, ou seja, ampliação de no máximo 1,33x.

Uso: python tools/curar.py [--min-sitelinks 12] [--saida app/acervo.json]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

UA = {"User-Agent": "Galeria/1.0 (curadoria de obras em dominio publico; viniciusbertuol6@gmail.com)"}
AQUI = Path(__file__).resolve().parent
SAIDA_PADRAO = AQUI.parent / "app" / "acervo.json"

# Explícita demais para papel de parede de qualquer pessoa.
BLOQUEADAS = {"Q334138"}  # A Origem do Mundo, Courbet

# Pintura, afresco (duas classes), tríptico, díptico, políptico, mural, grupo e série de pinturas.
# A Torre de Babel de Bruegel é "grupo de pinturas": o artigo cobre a de Viena e a de Roterdã.
# Uma consulta por tipo: todas juntas estouram o tempo do servidor.
TIPOS = ["Q3305213", "Q134194", "Q22669139", "Q79218", "Q475476", "Q1278452",
         "Q219423", "Q18573970", "Q15727816"]

CONSULTA = """
SELECT ?item ?sl WHERE {
  ?item wdt:P31 wd:%(tipo)s; wdt:P18 ?image; wikibase:sitelinks ?sl.
  FILTER(?sl >= %(min)d)
}
"""


def sparql(consulta):
    for tentativa in range(4):
        try:
            r = requests.get("https://query.wikidata.org/sparql",
                             params={"query": consulta, "format": "json"}, headers=UA, timeout=300)
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            erro = r.status_code
        except requests.RequestException as e:  # o servidor às vezes corta a resposta no meio
            erro = type(e).__name__
        print(f"wikidata falhou ({erro}), tentativa {tentativa + 1}", file=sys.stderr)
        time.sleep(15)
    sys.exit("wikidata não respondeu em 4 tentativas")


def entidades(ids, props="labels|claims|sitelinks"):
    """wbgetentities, 50 por pedido. A consulta SPARQL com tudo junto estoura o tempo do servidor."""
    out = {}
    ids = list(ids)
    for i in range(0, len(ids), 50):
        r = requests.get("https://www.wikidata.org/w/api.php", headers=UA, timeout=120, params={
            "action": "wbgetentities", "format": "json", "ids": "|".join(ids[i:i + 50]),
            "props": props, "languages": "pt-br|pt|en", "sitefilter": "ptwiki|enwiki"})
        r.raise_for_status()
        out.update(r.json().get("entities", {}))
        time.sleep(0.3)
    return out


def rotulo(e):
    lb = e.get("labels", {})
    for lang in ("pt-br", "pt", "en"):
        if lang in lb:
            return lb[lang]["value"]
    return None


def valores(e, prop):
    out = []
    for c in e.get("claims", {}).get(prop, []):
        if c.get("rank") == "deprecated":
            continue
        dv = c["mainsnak"].get("datavalue")
        if dv:
            out.append(dv["value"])
    return out


def colecao_atual(e):
    """A coleção onde a obra está hoje: descarta a que tem data de fim (P582), prefere a marcada como preferida."""
    vivas = [c for c in e.get("claims", {}).get("P195", [])
             if c.get("rank") != "deprecated" and "P582" not in c.get("qualifiers", {})
             and c["mainsnak"].get("datavalue")]
    vivas.sort(key=lambda c: c.get("rank") != "preferred")
    return vivas[0]["mainsnak"]["datavalue"]["value"]["id"] if vivas else None


def ano_de(v):
    # {"time": "+1563-00-00T00:00:00Z", "precision": 9}
    try:
        t = v["time"]
        a = int(t[1:].split("-")[0])
        return -a if t.startswith("-") else a
    except (KeyError, TypeError, ValueError):
        return None


def agrupar(linhas):
    sl = {b["item"]["value"].rsplit("/", 1)[-1]: int(b["sl"]["value"]) for b in linhas}
    ents = entidades(sl)
    criadores, colecoes = set(), set()
    for e in ents.values():
        criadores.update(v["id"] for v in valores(e, "P170"))
        if colecao_atual(e):
            colecoes.add(colecao_atual(e))
    ce = entidades(criadores, "labels|claims")
    co = entidades(colecoes, "labels")
    obras = {}
    for q, e in ents.items():
        imgs = valores(e, "P18")
        if not imgs:
            continue
        crs = {}
        for v in valores(e, "P170"):
            c = ce.get(v["id"], {})
            mortes = [m for m in (ano_de(x) for x in valores(c, "P570")) if m is not None]
            crs[v["id"]] = {"nome": rotulo(c), "morte": max(mortes) if mortes else None}
        col = colecao_atual(e)
        site = e.get("sitelinks", {})
        lb = e.get("labels", {})
        obras[q] = {
            "id": q, "sitelinks": sl[q], "imagem": imgs[0], "criadores": crs,
            "anos": {a for a in (ano_de(x) for x in valores(e, "P571")) if a is not None},
            "colecoes": {col: rotulo(co.get(col, {}))} if col else {},
            "titulo_pt": (lb.get("pt-br") or lb.get("pt") or {}).get("value"),
            "titulo_en": (lb.get("en") or {}).get("value"),
            "ptwiki": "https://pt.wikipedia.org/wiki/" + site["ptwiki"]["title"].replace(" ", "_") if "ptwiki" in site else None,
            "enwiki": "https://en.wikipedia.org/wiki/" + site["enwiki"]["title"].replace(" ", "_") if "enwiki" in site else None,
        }
    return obras


def dominio_publico(o):
    if o["criadores"]:
        mortes = [c["morte"] for c in o["criadores"].values()]
        if all(m is not None for m in mortes):
            return max(mortes) <= 1955
        # autor sem data de morte (anônimo, "mestre de...", oficina): vale a data da obra
    return bool(o["anos"]) and max(o["anos"]) < 1900


def tamanhos(arquivos):
    """Largura e altura no Commons, 50 por pedido."""
    out = {}
    lista = list(arquivos)
    for i in range(0, len(lista), 50):
        lote = lista[i:i + 50]
        r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=120, params={
            "action": "query", "format": "json", "prop": "imageinfo", "iiprop": "size|mime",
            "titles": "|".join("File:" + a for a in lote)})
        r.raise_for_status()
        dados = r.json()["query"]
        normal = {n["to"]: n["from"] for n in dados.get("normalized", [])}
        for p in dados["pages"].values():
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]
            nome = normal.get(p["title"], p["title"])[5:]
            out[nome] = (ii["width"], ii["height"], ii["mime"])
        time.sleep(0.5)
    return out


def nome_arquivo(nome):
    return nome.replace("_", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-sitelinks", type=int, default=12)
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = ap.parse_args()

    linhas = []
    for tipo in TIPOS:
        linhas += sparql(CONSULTA % {"tipo": tipo, "min": args.min_sitelinks})
    obras = agrupar(linhas)
    print(f"{len(obras)} pinturas com imagem e >= {args.min_sitelinks} wikipédias")

    motivos = {"bloqueada": 0, "sem domínio público": 0, "sem tamanho": 0, "não é jpeg/png": 0,
               "resolução baixa": 0, "sem título": 0}
    candidatas = []
    for o in obras.values():
        if o["id"] in BLOQUEADAS:
            motivos["bloqueada"] += 1
        elif not dominio_publico(o):
            motivos["sem domínio público"] += 1
        else:
            o["arquivo"] = nome_arquivo(o["imagem"])
            candidatas.append(o)

    info = tamanhos({o["arquivo"] for o in candidatas})
    acervo = []
    for o in candidatas:
        t = info.get(o["arquivo"])
        if not t:
            motivos["sem tamanho"] += 1
            continue
        w, h, mime = t
        if mime not in ("image/jpeg", "image/png"):
            motivos["não é jpeg/png"] += 1
            continue
        if min(3840 / w, 2160 / h) > 1 / 0.75:
            motivos["resolução baixa"] += 1
            continue
        titulo = o["titulo_pt"] or o["titulo_en"]
        if not titulo or titulo == o["id"]:
            motivos["sem título"] += 1
            continue
        nomes = [c["nome"] for c in o["criadores"].values() if c["nome"]]
        anos = sorted(o["anos"])
        data = None
        if anos:
            data = str(anos[0]) if anos[0] == anos[-1] else f"{anos[0]}–{anos[-1]}"
        acervo.append({
            "id": o["id"],
            "titulo": titulo,
            "artista": " e ".join(nomes) if nomes else "Autor desconhecido",
            "data": data,
            "museu": next(iter(o["colecoes"].values()), None),
            "arquivo": o["arquivo"],
            "largura": w,
            "altura": h,
            "link": o["ptwiki"] or o["enwiki"] or f"https://www.wikidata.org/wiki/{o['id']}",
            "fama": o["sitelinks"],
        })
    acervo.sort(key=lambda a: -a["fama"])
    # Mesmo título de uma obra mais famosa e autor desconhecido: é cópia (a "Mona Lisa" do Prado)
    # e na tela parece erro de cadastro. Mesmo título com outro autor conhecido fica (Adão e Eva).
    vistos, final = set(), []
    for a in acervo:
        if a["titulo"].casefold() in vistos and a["artista"] == "Autor desconhecido":
            motivos["cópia anônima de título famoso"] = motivos.get("cópia anônima de título famoso", 0) + 1
            continue
        vistos.add(a["titulo"].casefold())
        final.append(a)
    acervo = final

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(acervo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(acervo)} obras na lista -> {args.saida}")
    for k, v in motivos.items():
        print(f"  fora por {k}: {v}")


if __name__ == "__main__":
    main()
