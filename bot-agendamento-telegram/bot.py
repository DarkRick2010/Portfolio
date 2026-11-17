"""
Bot de Agendamento no Telegram
------------------------------
Clientes da barbearia agendam, consultam e cancelam horários sozinhos,
pelo Telegram, 24h por dia. O dono recebe um aviso a cada agendamento.

Uso:
    1. Crie um bot com o @BotFather no Telegram e copie o token.
    2. Crie um arquivo .env com:  TELEGRAM_TOKEN=seu_token
       (opcional) ADMIN_CHAT_ID=seu_id  -> para receber os avisos
    3. python bot.py
"""
import os
import time
from datetime import date
from pathlib import Path

import requests

from agenda import ENDERECO, HORARIOS, NOME_NEGOCIO, SERVICOS, Agenda

PASTA = Path(__file__).parent
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def carregar_env(caminho: Path = PASTA / ".env"):
    """Lê o arquivo .env (CHAVE=valor) sem precisar de biblioteca extra."""
    if caminho.exists():
        for linha in caminho.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.strip().startswith("#"):
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip())


def reais(valor: float) -> str:
    return f"R$ {valor:.2f}".replace(".", ",")


def data_br(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{DIAS_SEMANA[d.weekday()]} {d:%d/%m}"


def teclado(*linhas: list[tuple[str, str]]) -> dict:
    """Monta botões: cada linha é uma lista de (texto, dado_do_botão)."""
    return {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in linha]
                                for linha in linhas]}


MENU = teclado(
    [("📅 Agendar horário", "agendar")],
    [("💈 Serviços e preços", "servicos"), ("📋 Meus horários", "meus")],
    [("📍 Endereço", "endereco")],
)
VOLTAR = [("⬅️ Menu", "menu")]


class TelegramAPI:
    """Conversa com a API oficial do Telegram (https://core.telegram.org/bots/api)."""

    def __init__(self, token: str):
        self.url = f"https://api.telegram.org/bot{token}/"

    def chamar(self, metodo: str, **dados):
        resposta = requests.post(self.url + metodo, json=dados, timeout=40)
        resposta.raise_for_status()
        return resposta.json()["result"]

    def receber(self, offset: int) -> list[dict]:
        return self.chamar("getUpdates", offset=offset, timeout=30)

    def enviar(self, chat_id, texto, botoes=None):
        dados = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
        if botoes:
            dados["reply_markup"] = botoes
        return self.chamar("sendMessage", **dados)

    def editar(self, chat_id, message_id, texto, botoes=None):
        dados = {"chat_id": chat_id, "message_id": message_id,
                 "text": texto, "parse_mode": "HTML"}
        if botoes:
            dados["reply_markup"] = botoes
        return self.chamar("editMessageText", **dados)

    def responder_botao(self, callback_id, aviso=""):
        return self.chamar("answerCallbackQuery", callback_query_id=callback_id, text=aviso)


class BotBarbearia:
    def __init__(self, api, agenda: Agenda, admin_chat_id: str | None = None):
        self.api, self.agenda, self.admin = api, agenda, admin_chat_id

    # ---------- entrada ----------
    def tratar(self, update: dict):
        if "message" in update:
            msg = update["message"]
            nome = msg["from"].get("first_name", "cliente")
            self.api.enviar(msg["chat"]["id"],
                            f"Olá, {nome}! 👋 Bem-vindo à <b>{NOME_NEGOCIO}</b>.\n"
                            "Como posso ajudar?", MENU)
        elif "callback_query" in update:
            cb = update["callback_query"]
            self.api.responder_botao(cb["id"])
            texto, botoes = self.tela(cb["data"], cb["message"]["chat"]["id"],
                                      cb["from"].get("first_name", "Cliente"))
            self.api.editar(cb["message"]["chat"]["id"], cb["message"]["message_id"],
                            texto, botoes)

    # ---------- telas ----------
    def tela(self, dado: str, chat_id: int, nome: str) -> tuple[str, dict]:
        """Recebe o dado do botão clicado e devolve (texto, botões) da próxima tela."""
        acao, *partes = dado.split(":")

        if acao == "menu":
            return "Como posso ajudar?", MENU

        if acao == "servicos":
            linhas = [f"• {s['nome']} — {reais(s['preco'])} ({s['minutos']} min)"
                      for s in SERVICOS.values()]
            return "💈 <b>Serviços</b>\n\n" + "\n".join(linhas), teclado(VOLTAR)

        if acao == "endereco":
            return (f"📍 {ENDERECO}\n🕘 Seg a Sáb, {HORARIOS[0]} às {HORARIOS[-1]}",
                    teclado(VOLTAR))

        if acao == "agendar":
            botoes = [[(f"{s['nome']} — {reais(s['preco'])}", f"servico:{chave}")]
                      for chave, s in SERVICOS.items()]
            return "Qual serviço você quer?", teclado(*botoes, VOLTAR)

        if acao == "servico":
            servico = partes[0]
            dias = self.agenda.dias_disponiveis()
            if not dias:
                return "😕 Não há horários livres nos próximos dias.", teclado(VOLTAR)
            botoes = [[(data_br(d.isoformat()), f"dia:{servico}:{d.isoformat()}")]
                      for d in dias]
            return f"<b>{SERVICOS[servico]['nome']}</b> — escolha o dia:", \
                teclado(*botoes, [("⬅️ Voltar", "agendar")])

        if acao == "dia":
            servico, dia = partes
            livres = self.agenda.horarios_livres(date.fromisoformat(dia))
            if not livres:
                return "Esse dia acabou de lotar 😕 Escolha outro.", \
                    teclado([("⬅️ Voltar", f"servico:{servico}")])
            # 4 horários por linha
            botoes = [(h, f"hora:{servico}:{dia}:{h.replace(':', '')}") for h in livres]
            linhas = [botoes[i:i + 4] for i in range(0, len(botoes), 4)]
            return f"{data_br(dia)} — escolha o horário:", \
                teclado(*linhas, [("⬅️ Voltar", f"servico:{servico}")])

        if acao == "hora":
            servico, dia, hhmm = partes
            hora = f"{hhmm[:2]}:{hhmm[2:]}"
            s = SERVICOS[servico]
            return (f"Confirma?\n\n💈 {s['nome']} — {reais(s['preco'])}\n"
                    f"📅 {data_br(dia)} às {hora}",
                    teclado([("✅ Confirmar", f"ok:{servico}:{dia}:{hhmm}"),
                             ("⬅️ Voltar", f"dia:{servico}:{dia}")]))

        if acao == "ok":
            servico, dia, hhmm = partes
            hora = f"{hhmm[:2]}:{hhmm[2:]}"
            ag = self.agenda.agendar(chat_id, nome, servico, date.fromisoformat(dia), hora)
            if not ag:
                return "Ops, esse horário acabou de ser ocupado 😕 Escolha outro.", \
                    teclado([("Ver horários", f"dia:{servico}:{dia}")])
            self.avisar_dono(f"🆕 Novo agendamento: {nome} — {SERVICOS[servico]['nome']} "
                             f"em {data_br(dia)} às {hora}")
            return (f"✅ <b>Agendado!</b>\n\n{SERVICOS[servico]['nome']}\n"
                    f"{data_br(dia)} às {hora}\n📍 {ENDERECO}\n\nTe esperamos!",
                    teclado(VOLTAR))

        if acao == "meus":
            meus = self.agenda.do_cliente(chat_id)
            if not meus:
                return "Você não tem horários marcados.", \
                    teclado([("📅 Agendar", "agendar")], VOLTAR)
            linhas = [f"• {SERVICOS[a['servico']]['nome']} — {data_br(a['data'])} às {a['hora']}"
                      for a in meus]
            botoes = [[(f"❌ Cancelar {data_br(a['data'])} {a['hora']}", f"cancelar:{a['id']}")]
                      for a in meus]
            return "📋 <b>Seus horários</b>\n\n" + "\n".join(linhas), teclado(*botoes, VOLTAR)

        if acao == "cancelar":
            ag = self.agenda.cancelar(chat_id, partes[0])
            if not ag:
                return "Não encontrei esse agendamento.", teclado(VOLTAR)
            self.avisar_dono(f"❌ Cancelado: {nome} — {data_br(ag['data'])} às {ag['hora']}")
            return f"Horário de {data_br(ag['data'])} às {ag['hora']} cancelado.", \
                teclado([("📋 Meus horários", "meus")], VOLTAR)

        return "Não entendi 🤔", MENU

    def avisar_dono(self, texto: str):
        if self.admin:
            try:
                self.api.enviar(self.admin, texto)
            except requests.RequestException:
                pass  # aviso ao dono não pode derrubar o atendimento


def main():
    carregar_env()
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise SystemExit("Defina TELEGRAM_TOKEN no arquivo .env (veja o README).")

    bot = BotBarbearia(TelegramAPI(token), Agenda(PASTA / "agendamentos.csv"),
                       os.environ.get("ADMIN_CHAT_ID"))
    print("Bot rodando! Ctrl+C para parar.")
    offset = 0
    while True:
        try:
            for update in bot.api.receber(offset):
                offset = update["update_id"] + 1
                try:
                    bot.tratar(update)
                except Exception as erro:  # um erro num cliente não derruba o bot
                    print(f"Erro ao tratar mensagem: {erro}")
        except requests.RequestException as erro:
            print(f"Sem conexão ({erro}). Tentando de novo em 5s...")
            time.sleep(5)


if __name__ == "__main__":
    main()
