"""Testes offline do bot: usam uma API falsa no lugar do Telegram.

Rodar:  python -m unittest discover tests
"""
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agenda import HORARIOS, Agenda  # noqa: E402
from bot import BotBarbearia  # noqa: E402


class APIFalsa:
    def __init__(self):
        self.enviadas = []

    def enviar(self, chat_id, texto, botoes=None):
        self.enviadas.append((chat_id, texto))

    def editar(self, *a, **k):
        pass

    def responder_botao(self, *a, **k):
        pass


def dados_dos_botoes(botoes: dict) -> list[str]:
    return [b["callback_data"] for linha in botoes["inline_keyboard"] for b in linha]


class TestAgenda(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.agenda = Agenda(Path(self.tmp.name) / "ag.csv")

    def tearDown(self):
        self.tmp.cleanup()

    def test_nao_permite_horario_duplicado(self):
        dia = date(2030, 1, 7)  # segunda-feira
        self.assertIsNotNone(self.agenda.agendar(1, "Ana", "corte", dia, "10:00"))
        self.assertIsNone(self.agenda.agendar(2, "Bia", "corte", dia, "10:00"))
        self.assertNotIn("10:00", self.agenda.horarios_livres(dia))

    def test_domingo_fechado(self):
        dias = self.agenda.dias_disponiveis(hoje=date(2030, 1, 5))  # sábado
        self.assertNotIn(6, [d.weekday() for d in dias])

    def test_hoje_so_mostra_horarios_futuros(self):
        dia = date(2030, 1, 7)
        livres = self.agenda.horarios_livres(dia, agora=datetime(2030, 1, 7, 14, 30))
        self.assertEqual(livres, [h for h in HORARIOS if h > "14:30"])

    def test_so_o_dono_cancela(self):
        ag = self.agenda.agendar(1, "Ana", "barba", date(2030, 1, 7), "09:00")
        self.assertIsNone(self.agenda.cancelar(999, ag["id"]))
        self.assertIsNotNone(self.agenda.cancelar(1, ag["id"]))


class TestFluxoDoBot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.api = APIFalsa()
        self.bot = BotBarbearia(self.api, Agenda(Path(self.tmp.name) / "ag.csv"),
                                admin_chat_id="dono")

    def tearDown(self):
        self.tmp.cleanup()

    def test_fluxo_completo_agendar_e_cancelar(self):
        # cliente clica: Agendar -> Corte -> primeiro dia -> primeiro horário -> Confirmar
        _, b = self.bot.tela("agendar", 42, "Carlos")
        self.assertIn("servico:corte", dados_dos_botoes(b))
        _, b = self.bot.tela("servico:corte", 42, "Carlos")
        dia = dados_dos_botoes(b)[0]
        _, b = self.bot.tela(dia, 42, "Carlos")
        hora = dados_dos_botoes(b)[0]
        _, b = self.bot.tela(hora, 42, "Carlos")
        confirmar = dados_dos_botoes(b)[0]
        texto, _ = self.bot.tela(confirmar, 42, "Carlos")

        self.assertIn("Agendado", texto)
        self.assertEqual(self.api.enviadas[-1][0], "dono")  # dono foi avisado

        texto, b = self.bot.tela("meus", 42, "Carlos")
        self.assertIn("Corte de cabelo", texto)
        cancelar = [d for d in dados_dos_botoes(b) if d.startswith("cancelar:")][0]
        texto, _ = self.bot.tela(cancelar, 42, "Carlos")
        self.assertIn("cancelado", texto)

    def test_mensagem_de_texto_mostra_menu(self):
        self.bot.tratar({"message": {"chat": {"id": 7}, "from": {"first_name": "Ana"},
                                     "text": "oi"}})
        self.assertIn("Ana", self.api.enviadas[0][1])

    def test_callback_data_cabe_no_limite_do_telegram(self):
        _, b = self.bot.tela("servico:combo", 1, "X")
        dia = dados_dos_botoes(b)[0]
        _, b = self.bot.tela(dia, 1, "X")
        for d in dados_dos_botoes(b):
            self.assertLessEqual(len(d.encode()), 64)


if __name__ == "__main__":
    unittest.main()
