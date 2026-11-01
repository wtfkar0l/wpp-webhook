# Webhook WhatsApp Business (Cloud API)

## Rodar local

    cp .env.example .env      # preencha os valores
    docker build -t wa-webhook .
    docker run --env-file .env -p 8000:8000 wa-webhook

Exponha com `ngrok http 8000` e use `https://SEU-DOMINIO.ngrok-free.app/webhooks` como Callback URL.

## Deploy no Render

1. Suba esta pasta em um repositorio no GitHub.
2. Render > New > Blueprint (ou Web Service com Docker) e escolha o repo.
3. Preencha VERIFY_TOKEN e APP_SECRET nas variaveis de ambiente.
4. Callback URL: `https://SEUAPP.onrender.com/webhooks`

## Painel da Meta

WhatsApp > Configuration > Webhook > Edit
- Callback URL: a URL acima
- Verify token: o mesmo valor de VERIFY_TOKEN
- Verify and save, depois assine o campo `messages`

## Responder mensagens

Preencha ACCESS_TOKEN (token permanente do usuario do sistema), PHONE_NUMBER_ID
(painel WhatsApp > API Setup) e defina AUTO_REPLY=true.

## Testar a verificacao

    curl "http://localhost:8000/webhooks?hub.mode=subscribe&hub.verify_token=SEU_TOKEN&hub.challenge=123"

Deve devolver `123`.
