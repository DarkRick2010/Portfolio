"""Testes offline: simulam o site com HTML falso, sem precisar de internet.

Rodar:  python -m unittest discover tests
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import coletar  # noqa: E402

PAGINA_1 = """
<html><body><ol class="row">
<li><article class="product_pod">
  <h3><a href="livro-a_1/index.html" title="Livro A">Livro A</a></h3>
  <p class="star-rating Three"></p>
  <div class="product_price"><p class="price_color">£51.77</p>
  <p class="instock availability"><i class="icon-ok"></i> In stock</p></div>
</article></li>
<li><article class="product_pod">
  <h3><a href="livro-b_2/index.html" title="Livro B">Livro B</a></h3>
  <p class="star-rating Five"></p>
  <div class="product_price"><p class="price_color">£12.50</p>
  <p class="instock availability"> In stock</p></div>
</article></li>
</ol>
<ul class="pager"><li class="next"><a href="page-2.html">next</a></li></ul>
</body></html>
"""

PAGINA_2 = """
<html><body><ol class="row">
<li><article class="product_pod">
  <h3><a href="livro-c_3/index.html" title="Livro C">Livro C</a></h3>
  <p class="star-rating One"></p>
  <div class="product_price"><p class="price_color">£20.00</p>
  <p class="availability"> Out of stock</p></div>
</article></li>
</ol></body></html>
"""


def resposta_falsa(url, **kwargs):
    r = mock.Mock()
    r.content = (PAGINA_2 if "page-2" in url else PAGINA_1).encode("utf-8")
    r.raise_for_status = lambda: None
    return r


class TestColeta(unittest.TestCase):
    @mock.patch.object(coletar.time, "sleep", lambda s: None)
    @mock.patch.object(coletar.requests, "get", side_effect=resposta_falsa)
    def test_percorre_todas_as_paginas(self, _get):
        df = coletar.coletar()
        self.assertEqual(list(df["titulo"]), ["Livro A", "Livro B", "Livro C"])
        self.assertEqual(list(df["preco"]), [51.77, 12.50, 20.00])
        self.assertEqual(list(df["nota"]), [3, 5, 1])
        self.assertEqual(list(df["em_estoque"]), [True, True, False])
        self.assertEqual(df["link"][0],
                         "https://books.toscrape.com/catalogue/livro-a_1/index.html")

    @mock.patch.object(coletar.time, "sleep", lambda s: None)
    @mock.patch.object(coletar.requests, "get", side_effect=resposta_falsa)
    def test_respeita_limite_de_paginas(self, _get):
        df = coletar.coletar(max_paginas=1)
        self.assertEqual(len(df), 2)


if __name__ == "__main__":
    unittest.main()
