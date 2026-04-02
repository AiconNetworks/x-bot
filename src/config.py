import os
from dotenv import load_dotenv

load_dotenv()

X_CLIENT_ID = os.environ["X_CLIENT_ID"]
X_CLIENT_SECRET = os.environ["X_CLIENT_SECRET"]

OPENCLAW_URL = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
OPENCLAW_TOKEN = os.environ["OPENCLAW_TOKEN"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
