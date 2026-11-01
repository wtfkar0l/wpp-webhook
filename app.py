import hashlib
import hmac
import logging
import os
import threading

import requests
from flask import Flask, abort, request

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("whatsapp-webhook")

app = Flask(__name__)

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
APP_SECRET = os.environ["APP_SECRET"].encode()
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v21.0")
AUTO_REPLY = os.environ.get("AUTO_REPLY", "false").lower() == "true"

# Deduplicacao simples em memoria. Em producao real, use Redis ou banco.
_seen_ids: set[str] = set()
_lock = threading.Lock()


def send_text(to: str, body: str) -> None:
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PHONE_NUMBER_ID}/messages"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        },
        timeout=10,
    )
    log.info("send_text -> %s %s", resp.status_code, resp.text)


def handle_payload(payload: dict) -> None:
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for status in value.get("statuses", []):
                log.info("status: %s", status)

            for msg in value.get("messages", []):
                msg_id = msg.get("id")
                with _lock:
                    if msg_id in _seen_ids:
                        continue
                    _seen_ids.add(msg_id)

                sender = msg.get("from")
                text = msg.get("text", {}).get("body") if msg.get("type") == "text" else None
                log.info("mensagem de %s (%s): %s", sender, msg.get("type"), text)

                if AUTO_REPLY and ACCESS_TOKEN and PHONE_NUMBER_ID and text:
                    send_text(sender, f"Recebi: {text}")


@app.get("/")
def health():
    return "ok", 200


@app.get("/webhooks")
def verify():
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge", ""), 200
    abort(403)


@app.post("/webhooks")
def receive():
    sig = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(APP_SECRET, request.get_data(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        abort(403)

    payload = request.get_json(silent=True) or {}
    threading.Thread(target=handle_payload, args=(payload,), daemon=True).start()
    return "", 200
