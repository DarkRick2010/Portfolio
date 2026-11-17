# 💈 Bot de Agendamento no Telegram

Bot que permite aos clientes de uma barbearia **agendar, consultar e cancelar horários sozinhos, pelo Telegram, 24 horas por dia**. O dono recebe um aviso a cada novo agendamento ou cancelamento, e todos os horários ficam numa planilha que abre no Excel.

## O problema

Pequenos negócios perdem tempo (e clientes) respondendo mensagem por mensagem para marcar horário, e a agenda no papel gera horários duplicados.

## A solução

Atendimento por botões, sem o cliente precisar digitar nada:

```
Olá, Carlos! 👋 Bem-vindo à Barbearia do Zé.
[📅 Agendar horário]
[💈 Serviços e preços] [📋 Meus horários]
[📍 Endereço]

→ Corte de cabelo → Ter 17/11 → 14:00 → ✅ Confirmar

✅ Agendado!
Corte de cabelo — Ter 17/11 às 14:00
```

**Funcionalidades**

- escolha de serviço, dia e horário por botões;
- mostra **só horários livres** (e, no dia de hoje, só os que ainda não passaram);
- **impede horário duplicado**, mesmo com dois clientes clicando ao mesmo tempo;
- domingo fechado (configurável);
- o cliente vê e cancela os próprios horários;
- aviso automático ao dono;
- agendamentos salvos em `agendamentos.csv`, que abre no Excel.

## Como usar

1. No Telegram, fale com o **@BotFather**, envie `/newbot` e copie o token.
2. Copie `.env.exemplo` para `.env` e cole o token:
   ```
   TELEGRAM_TOKEN=123456:ABC...
   ADMIN_CHAT_ID=seu_id   # opcional: para receber avisos (descubra com o @userinfobot)
   ```
3. Instale e rode:
   ```bash
   pip install -r requirements.txt
   python bot.py
   ```
4. Abra o seu bot no Telegram e mande qualquer mensagem.

## Como adaptar para outro negócio

Tudo fica no começo do arquivo `agenda.py`: nome, endereço, serviços e preços, horários e dias fechados. Funciona para salão, clínica, estúdio, pet shop…

## Testes

Os testes usam um Telegram "falso", então rodam sem internet e sem token:

```bash
python -m unittest discover tests
```

## Tecnologias

Python · API oficial de Bots do Telegram · requests · CSV · unittest

> Negócio fictício, criado para demonstração.
