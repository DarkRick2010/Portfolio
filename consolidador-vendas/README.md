# 📊 Consolidador de Planilhas de Vendas

Automação em Python que **junta várias planilhas de vendas em um único relatório Excel**, já limpo, padronizado e com resumos e gráfico.

## O problema

Uma empresa com várias lojas recebe uma planilha de cada filial. Cada uma vem de um jeito: nomes de colunas diferentes (`Quantidade`, `QTD`, `qtde`), linhas em branco e preços digitados como texto (`R$ 49,90`). Juntar tudo à mão leva horas e gera erros.

## A solução

Um script que, em segundos:

- lê **todas** as planilhas `.xlsx` de uma pasta;
- reconhece as colunas automaticamente, mesmo com nomes diferentes;
- limpa os dados (linhas vazias, valores em texto, datas);
- gera um relatório Excel formatado com as abas:
  - **Resumo por loja** (com gráfico)
  - **Resumo por produto**
  - **Resumo por vendedor**
  - **Faturamento por mês** (por loja)
  - **Dados consolidados** (todas as vendas juntas)

```
Lendo planilhas de: entrada
  ✓ vendas_loja_centro.xlsx: 174 vendas
  ✓ vendas_loja_norte.xlsx: 128 vendas
  ✓ vendas_loja_sul.xlsx: 175 vendas

Pronto! 477 vendas consolidadas | Faturamento: R$ 181.865,90
Relatório salvo em: saida/relatorio_vendas.xlsx
```

## Como usar

```bash
pip install -r requirements.txt

# 1. (opcional) gerar planilhas de exemplo na pasta "entrada"
python gerar_dados_exemplo.py

# 2. consolidar
python consolidar.py
```

Para usar outra pasta ou outro nome de arquivo:

```bash
python consolidar.py --entrada "C:/Vendas/Novembro" --saida "relatorio_novembro.xlsx"
```

## Como adaptar para um cliente

- **Nova variação de nome de coluna?** Adicione o apelido no dicionário `APELIDOS_COLUNAS` em `consolidar.py`.
- **Outras métricas?** Ajuste a função `montar_resumos`.

## Tecnologias

Python · pandas · openpyxl

> Os dados de exemplo são fictícios.
