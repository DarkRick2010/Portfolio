"""
Gera planilhas de vendas FICTÍCIAS para demonstrar o consolidador.

Simula um problema real: cada loja manda sua planilha de um jeito
(nomes de colunas diferentes, linhas em branco, valores como texto).
"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PASTA_ENTRADA = Path(__file__).parent / "entrada"
PRODUTOS = {
    "Camiseta": 49.90,
    "Calça Jeans": 129.90,
    "Tênis": 249.90,
    "Boné": 39.90,
    "Jaqueta": 199.90,
}
VENDEDORES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio"]

# Cada loja usa nomes de colunas um pouco diferentes (como na vida real)
LOJAS = {
    "Centro": ["Data", "Produto", "Quantidade", "Preço Unitário", "Vendedor"],
    "Norte": ["DATA", "PRODUTO", "QTD", "VALOR UNIT", "VENDEDOR"],
    "Sul": ["data venda", "produto", "qtde", "preco", "vendedor"],
}


def gerar_loja(nome_loja: str, colunas: list[str], seed: int) -> pd.DataFrame:
    random.seed(seed)
    linhas = []
    inicio = date(2026, 1, 1)
    for _ in range(random.randint(120, 180)):
        produto = random.choice(list(PRODUTOS))
        linhas.append([
            inicio + timedelta(days=random.randint(0, 180)),
            produto,
            random.randint(1, 5),
            PRODUTOS[produto],
            random.choice(VENDEDORES[:4] if nome_loja == "Centro" else VENDEDORES[2:]),
        ])
    df = pd.DataFrame(linhas, columns=colunas)

    # "Sujeira" típica: linhas vazias e preço digitado como texto "R$ 49,90"
    if nome_loja == "Sul":
        df[colunas[3]] = df[colunas[3]].map(lambda v: f"R$ {v:.2f}".replace(".", ","))
    vazias = pd.DataFrame([[None] * len(colunas)] * 3, columns=colunas)
    return pd.concat([df.iloc[:50], vazias, df.iloc[50:]], ignore_index=True)


def main():
    PASTA_ENTRADA.mkdir(exist_ok=True)
    for i, (loja, colunas) in enumerate(LOJAS.items()):
        caminho = PASTA_ENTRADA / f"vendas_loja_{loja.lower()}.xlsx"
        gerar_loja(loja, colunas, seed=i).to_excel(caminho, index=False)
        print(f"Criado: {caminho.name}")


if __name__ == "__main__":
    main()
