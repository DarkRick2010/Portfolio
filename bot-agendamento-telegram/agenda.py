"""
Regras de agendamento da barbearia, salvas em uma planilha CSV
(o dono pode abrir no Excel a qualquer momento).
"""
import csv
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

# ---- Configuração do negócio (fácil de trocar para outro cliente) ----
NOME_NEGOCIO = "Barbearia do Zé (fictícia)"
ENDERECO = "Rua Exemplo, 123 — Centro"
SERVICOS = {
    "corte": {"nome": "Corte de cabelo", "preco": 40.0, "minutos": 30},
    "barba": {"nome": "Barba", "preco": 30.0, "minutos": 30},
    "combo": {"nome": "Corte + Barba", "preco": 60.0, "minutos": 60},
}
HORARIOS = ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
DIAS_FECHADO = {6}       # 6 = domingo (segunda = 0)
DIAS_A_FRENTE = 6        # quantos dias de funcionamento oferecer
# -----------------------------------------------------------------------

COLUNAS = ["id", "chat_id", "cliente", "servico", "data", "hora", "criado_em"]


class Agenda:
    def __init__(self, arquivo: Path):
        self.arquivo = Path(arquivo)
        if not self.arquivo.exists():
            with self.arquivo.open("w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f, delimiter=";").writerow(COLUNAS)

    # --- leitura/escrita da planilha ---
    def _ler(self) -> list[dict]:
        with self.arquivo.open(newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f, delimiter=";"))

    def _gravar(self, linhas: list[dict]):
        with self.arquivo.open("w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
            escritor.writeheader()
            escritor.writerows(linhas)

    # --- regras ---
    def dias_disponiveis(self, hoje: date | None = None) -> list[date]:
        dia, dias = hoje or date.today(), []
        while len(dias) < DIAS_A_FRENTE:
            if dia.weekday() not in DIAS_FECHADO and self.horarios_livres(dia):
                dias.append(dia)
            dia += timedelta(days=1)
            if (dia - (hoje or date.today())).days > 30:
                break
        return dias

    def horarios_livres(self, dia: date, agora: datetime | None = None) -> list[str]:
        agora = agora or datetime.now()
        ocupados = {a["hora"] for a in self._ler() if a["data"] == dia.isoformat()}
        livres = [h for h in HORARIOS if h not in ocupados]
        if dia == agora.date():  # hoje: só horários que ainda não passaram
            livres = [h for h in livres if h > agora.strftime("%H:%M")]
        return livres

    def agendar(self, chat_id: int, cliente: str, servico: str,
                dia: date, hora: str) -> dict | None:
        """Retorna o agendamento criado, ou None se o horário já foi ocupado."""
        if servico not in SERVICOS or hora not in self.horarios_livres(dia):
            return None
        novo = {
            "id": uuid.uuid4().hex[:6],
            "chat_id": str(chat_id),
            "cliente": cliente,
            "servico": servico,
            "data": dia.isoformat(),
            "hora": hora,
            "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._gravar(self._ler() + [novo])
        return novo

    def do_cliente(self, chat_id: int, hoje: date | None = None) -> list[dict]:
        hoje = (hoje or date.today()).isoformat()
        meus = [a for a in self._ler()
                if a["chat_id"] == str(chat_id) and a["data"] >= hoje]
        return sorted(meus, key=lambda a: (a["data"], a["hora"]))

    def cancelar(self, chat_id: int, id_agendamento: str) -> dict | None:
        linhas = self._ler()
        for a in linhas:
            if a["id"] == id_agendamento and a["chat_id"] == str(chat_id):
                linhas.remove(a)
                self._gravar(linhas)
                return a
        return None
