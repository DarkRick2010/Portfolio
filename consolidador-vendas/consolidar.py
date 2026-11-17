"""
Consolidador de Planilhas de Vendas
-----------------------------------
Junta todas as planilhas .xlsx da pasta "entrada", padroniza as colunas,
limpa os dados e gera um relatório Excel pronto, com resumos e gráfico.

Uso:
    python consolidar.py
    python consolidar.py --entrada minha_pasta --saida relatorio.xlsx
"""
import argparse
import re
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

PASTA = Path(__file__).parent

# Mapa de "apelidos" -> nome padrão. Para aceitar um novo formato de
# planilha, basta adicionar o apelido aqui.
APELIDOS_COLUNAS = {
    "data": ["data", "data venda", "dt", "dia"],
    "produto": ["produto", "item", "descricao", "descrição"],
    "quantidade": ["quantidade", "qtd", "qtde", "quant"],
    "preco_unitario": ["preço unitário", "preco unitario", "valor unit",
                       "preco", "preço", "valor"],
    "vendedor": ["vendedor", "vendedora", "atendente"],
}


def padronizar_colunas(df: pd.DataFrame, arquivo: str) -> pd.DataFrame:
    """Renomeia as colunas para o padrão, ignorando maiúsculas/espaços."""
    renomear = {}
    for coluna in df.columns:
        nome_limpo = str(coluna).strip().lower()
        for padrao, apelidos in APELIDOS_COLUNAS.items():
            if nome_limpo in apelidos:
                renomear[coluna] = padrao
    df = df.rename(columns=renomear)

    faltando = set(APELIDOS_COLUNAS) - set(df.columns)
    if faltando:
        raise ValueError(f"{arquivo}: colunas não reconhecidas -> {sorted(faltando)}")
    return df[list(APELIDOS_COLUNAS)]


def converter_dinheiro(valor) -> float:
    """Aceita 49.9, '49,90', 'R$ 1.234,56' e devolve número."""
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = re.sub(r"[^\d,.-]", "", str(valor))
    if "," in texto:  # formato brasileiro: 1.234,56
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto)


def ler_planilhas(pasta_entrada: Path) -> pd.DataFrame:
    arquivos = sorted(pasta_entrada.glob("*.xlsx"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhuma planilha .xlsx encontrada em {pasta_entrada}")

    partes = []
    for arquivo in arquivos:
        df = pd.read_excel(arquivo)
        df = padronizar_colunas(df, arquivo.name)
        df = df.dropna(how="all")  # remove linhas totalmente vazias
        # Nome da loja vem do nome do arquivo: vendas_loja_centro.xlsx -> Centro
        df["loja"] = arquivo.stem.replace("vendas_loja_", "").replace("_", " ").title()
        partes.append(df)
        print(f"  ✓ {arquivo.name}: {len(df)} vendas")
    return pd.concat(partes, ignore_index=True)


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    df["data"] = pd.to_datetime(df["data"], errors="coerce", dayfirst=True)
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    df["preco_unitario"] = df["preco_unitario"].map(converter_dinheiro)
    df["produto"] = df["produto"].astype(str).str.strip()
    df["vendedor"] = df["vendedor"].astype(str).str.strip()

    invalidas = df[["data", "quantidade", "preco_unitario"]].isna().any(axis=1)
    if invalidas.any():
        print(f"  ! {invalidas.sum()} linha(s) com dados inválidos foram ignoradas")
    df = df[~invalidas].copy()

    df["total"] = df["quantidade"] * df["preco_unitario"]
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.sort_values("data").reset_index(drop=True)


def montar_resumos(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    def resumo(por: str) -> pd.DataFrame:
        return (df.groupby(por)
                  .agg(vendas=("total", "size"),
                       itens=("quantidade", "sum"),
                       faturamento=("total", "sum"))
                  .sort_values("faturamento", ascending=False)
                  .reset_index()
                  .rename(columns={por: por.title(), "vendas": "Vendas",
                                   "itens": "Itens", "faturamento": "Faturamento"}))

    por_mes = df.pivot_table(index="mes", columns="loja", values="total",
                             aggfunc="sum", fill_value=0).reset_index()
    por_mes = por_mes.rename(columns={"mes": "Mês"})
    por_mes.columns.name = None
    return {
        "Resumo por loja": resumo("loja"),
        "Resumo por produto": resumo("produto"),
        "Resumo por vendedor": resumo("vendedor"),
        "Faturamento por mês": por_mes,
    }


def formatar_excel(caminho: Path):
    """Deixa o relatório com cara profissional: cabeçalho, larguras, R$, gráfico."""
    wb = load_workbook(caminho)
    cabecalho = PatternFill("solid", fgColor="1F4E78")
    formato_reais = 'R$ #,##0.00'

    for ws in wb.worksheets:
        for celula in ws[1]:
            celula.font = Font(bold=True, color="FFFFFF")
            celula.fill = cabecalho
            celula.alignment = Alignment(horizontal="center")
        ws.freeze_panes = "A2"
        for i, coluna in enumerate(ws.columns, start=1):
            titulo = str(coluna[0].value or "").lower()
            largura = max(len(str(c.value or "")) for c in coluna) + 3
            ws.column_dimensions[get_column_letter(i)].width = min(largura, 30)
            if any(p in titulo for p in ("total", "faturamento", "preco")) or \
               ws.title == "Faturamento por mês" and i > 1:
                for c in coluna[1:]:
                    c.number_format = formato_reais
            if titulo == "data":
                for c in coluna[1:]:
                    c.number_format = "DD/MM/YYYY"

    # Gráfico de barras: faturamento por loja
    ws = wb["Resumo por loja"]
    grafico = BarChart()
    grafico.title = "Faturamento por loja"
    grafico.y_axis.title = "R$"
    grafico.y_axis.scaling.min = 0  # eixo começa no zero (não distorce)
    grafico.legend = None
    dados = Reference(ws, min_col=4, min_row=1, max_row=ws.max_row)
    nomes = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
    grafico.add_data(dados, titles_from_data=True)
    grafico.set_categories(nomes)
    grafico.height, grafico.width = 8, 14
    ws.add_chart(grafico, "G2")

    wb.save(caminho)


def main():
    parser = argparse.ArgumentParser(description="Consolida planilhas de vendas.")
    parser.add_argument("--entrada", default=PASTA / "entrada", type=Path)
    parser.add_argument("--saida", default=PASTA / "saida" / "relatorio_vendas.xlsx", type=Path)
    args = parser.parse_args()

    print(f"Lendo planilhas de: {args.entrada}")
    df = limpar(ler_planilhas(args.entrada))
    resumos = montar_resumos(df)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    colunas_finais = {"data": "Data", "loja": "Loja", "produto": "Produto",
                      "vendedor": "Vendedor", "quantidade": "Quantidade",
                      "preco_unitario": "Preco unitario", "total": "Total"}
    with pd.ExcelWriter(args.saida, engine="openpyxl") as writer:
        for nome, tabela in resumos.items():
            tabela.to_excel(writer, sheet_name=nome, index=False)
        df[list(colunas_finais)].rename(columns=colunas_finais) \
            .to_excel(writer, sheet_name="Dados consolidados", index=False)
    formatar_excel(args.saida)

    total = df["total"].sum()
    print(f"\nPronto! {len(df)} vendas consolidadas | Faturamento: "
          f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Relatório salvo em: {args.saida}")


if __name__ == "__main__":
    main()
