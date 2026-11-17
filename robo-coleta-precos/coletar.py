"""
Robô de Coleta de Preços
------------------------
Percorre todas as páginas de um catálogo online, coleta nome, preço,
avaliação e estoque de cada produto e salva tudo em Excel e CSV.

Site usado na demonstração: https://books.toscrape.com
(um site FEITO para treinar coleta de dados — uso liberado).

Uso:
    python coletar.py                       # coleta tudo (50 páginas)
    python coletar.py --paginas 3           # só as 3 primeiras páginas
    python coletar.py --nota-minima 4 --preco-maximo 30
"""
import argparse
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_INICIAL = "https://books.toscrape.com/catalogue/page-1.html"
PASTA_SAIDA = Path(__file__).parent / "saida"
NOTAS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
CABECALHOS = {"User-Agent": "Mozilla/5.0 (robo-coleta-portfolio)"}
PAUSA_ENTRE_PAGINAS = 1.0  # segundos — educação com o servidor


def baixar_pagina(url: str, tentativas: int = 3) -> BeautifulSoup:
    """Baixa a página, tentando de novo se a internet falhar."""
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(url, headers=CABECALHOS, timeout=15)
            resposta.raise_for_status()
            return BeautifulSoup(resposta.content, "html.parser")
        except requests.RequestException as erro:
            print(f"  ! Falha ({tentativa}/{tentativas}) em {url}: {erro}")
            time.sleep(2 * tentativa)
    raise RuntimeError(f"Não foi possível acessar {url}")


def extrair_produtos(pagina: BeautifulSoup, url_base: str) -> list[dict]:
    """Lê os cartões de produto de uma página do catálogo."""
    produtos = []
    for cartao in pagina.select("article.product_pod"):
        link = cartao.select_one("h3 a")
        preco_texto = cartao.select_one("p.price_color").get_text(strip=True)
        classes_nota = cartao.select_one("p.star-rating")["class"]
        estoque = cartao.select_one("p.availability").get_text(strip=True)

        produtos.append({
            "titulo": link["title"],
            "preco": float(preco_texto.replace("£", "").replace("Â", "")),
            "nota": next((NOTAS[c] for c in classes_nota if c in NOTAS), None),
            "em_estoque": "In stock" in estoque,
            "link": urljoin(url_base, link["href"]),
        })
    return produtos


def proxima_pagina(pagina: BeautifulSoup, url_atual: str) -> str | None:
    botao = pagina.select_one("li.next a")
    return urljoin(url_atual, botao["href"]) if botao else None


def coletar(max_paginas: int | None = None) -> pd.DataFrame:
    url, numero, todos = URL_INICIAL, 1, []
    while url and (max_paginas is None or numero <= max_paginas):
        pagina = baixar_pagina(url)
        produtos = extrair_produtos(pagina, url)
        todos.extend(produtos)
        print(f"  ✓ Página {numero}: {len(produtos)} produtos")
        url = proxima_pagina(pagina, url)
        numero += 1
        if url:
            time.sleep(PAUSA_ENTRE_PAGINAS)
    return pd.DataFrame(todos)


def salvar(df: pd.DataFrame) -> Path:
    PASTA_SAIDA.mkdir(exist_ok=True)
    carimbo = datetime.now().strftime("%Y-%m-%d_%H%M")
    caminho_excel = PASTA_SAIDA / f"produtos_{carimbo}.xlsx"

    tabela = df.rename(columns={"titulo": "Título", "preco": "Preço (£)",
                                "nota": "Nota (1-5)", "em_estoque": "Em estoque",
                                "link": "Link"})
    tabela["Em estoque"] = tabela["Em estoque"].map({True: "Sim", False: "Não"})
    tabela.to_csv(caminho_excel.with_suffix(".csv"), index=False,
                  sep=";", encoding="utf-8-sig")  # abre certinho no Excel BR

    with pd.ExcelWriter(caminho_excel, engine="openpyxl") as writer:
        tabela.to_excel(writer, sheet_name="Produtos", index=False)
        ws = writer.sheets["Produtos"]
        larguras = {"A": 60, "B": 12, "C": 12, "D": 12, "E": 70}
        for coluna, largura in larguras.items():
            ws.column_dimensions[coluna].width = largura
        ws.auto_filter.ref = ws.dimensions  # filtros no cabeçalho
        ws.freeze_panes = "A2"
    return caminho_excel


def main():
    parser = argparse.ArgumentParser(description="Coleta produtos de um catálogo online.")
    parser.add_argument("--paginas", type=int, help="limite de páginas (padrão: todas)")
    parser.add_argument("--nota-minima", type=int, default=1, help="filtra nota >= N")
    parser.add_argument("--preco-maximo", type=float, help="filtra preço <= valor")
    args = parser.parse_args()

    print("Iniciando coleta...")
    df = coletar(args.paginas)

    df = df[df["nota"] >= args.nota_minima]
    if args.preco_maximo is not None:
        df = df[df["preco"] <= args.preco_maximo]
    df = df.sort_values(["nota", "preco"], ascending=[False, True])

    caminho = salvar(df)
    print(f"\nPronto! {len(df)} produtos salvos em:\n  {caminho}\n  {caminho.with_suffix('.csv')}")
    if len(df):
        print(f"Preço médio: £{df['preco'].mean():.2f} | "
              f"Mais barato: {df.loc[df['preco'].idxmin(), 'titulo']}")


if __name__ == "__main__":
    main()
