# 🤖 Robô de Coleta de Preços

Robô em Python que **percorre todas as páginas de um catálogo online e coleta os dados dos produtos** (nome, preço, avaliação, estoque e link), salvando tudo em **Excel e CSV** prontos para análise.

## O problema

Acompanhar preços de concorrentes ou montar uma base de produtos copiando item por item de um site leva dias e é cheio de erros.

## A solução

- navega **sozinho** por todas as páginas do catálogo (paginação automática);
- extrai nome, preço, nota (1 a 5), disponibilidade e link de cada produto;
- **filtra** por nota mínima e preço máximo;
- salva Excel (com filtros e colunas ajustadas) e CSV que abre certinho no Excel em português;
- pausa entre páginas e tenta de novo se a conexão falhar, para não sobrecarregar o site.

```
Iniciando coleta...
  ✓ Página 1: 20 produtos
  ✓ Página 2: 20 produtos
  ...
Pronto! 1000 produtos salvos em:
  saida/produtos_2026-11-15_1725.xlsx
  saida/produtos_2026-11-15_1725.csv
```

## Como usar

```bash
pip install -r requirements.txt

python coletar.py                                # catálogo inteiro
python coletar.py --paginas 3                    # só 3 páginas
python coletar.py --nota-minima 4 --preco-maximo 30
```

## Testes

Os testes simulam o site com HTML falso, então rodam sem internet:

```bash
python -m unittest discover tests
```

## Como adaptar para outro site

Os seletores CSS ficam concentrados em `extrair_produtos` e `proxima_pagina`. Para outro site, basta ajustar esses seletores e a `URL_INICIAL`.

> **Uso responsável:** a demonstração usa o [books.toscrape.com](https://books.toscrape.com), um site criado para treino de coleta de dados. Em projetos reais, verifique os termos de uso e o `robots.txt` do site, e não colete dados pessoais sem base legal (LGPD).

## Tecnologias

Python · requests · BeautifulSoup · pandas · openpyxl · unittest
