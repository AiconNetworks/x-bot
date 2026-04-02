"""Thin Telegram listener. Receives source text, runs the pipeline."""

import time
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from telegram_approval import send_message, choose_tweet_option
from pipeline import run_pipeline

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _poll_for_source_text():
    """Block until a text message arrives from the authorized chat."""
    last_update_id = None

    # Flush old updates
    resp = requests.post(f"{API_BASE}/getUpdates", json={"timeout": 0}, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("result", [])
    if results:
        last_update_id = results[-1]["update_id"] + 1

    send_message("Ready. Send me text and I'll generate tweet options.")

    while True:
        params = {"timeout": 30}
        if last_update_id is not None:
            params["offset"] = last_update_id

        resp = requests.post(f"{API_BASE}/getUpdates", json=params, timeout=40)
        resp.raise_for_status()
        results = resp.json().get("result", [])

        for update in results:
            last_update_id = update["update_id"] + 1
            msg = update.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "").strip()

            if chat_id != TELEGRAM_CHAT_ID:
                continue
            if not text or text.startswith("/"):
                continue

            return text


def main():
    print("Telegram bot starting...")
    while True:
        try:
            source_text = _poll_for_source_text()
            run_pipeline(
                source_text=source_text,
                approve_fn=choose_tweet_option,
                notify_fn=send_message,
            )
        except KeyboardInterrupt:
            print("\nStopping.")
            break
        except Exception as e:
            print(f"Error: {e}")
            try:
                send_message(f"Error: {e}")
            except Exception:
                pass
            time.sleep(5)


if __name__ == "__main__":
    main()
