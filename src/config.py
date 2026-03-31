import os
from dotenv import load_dotenv

load_dotenv()

X_API_KEY = os.environ["X_API_KEY"]
X_API_SECRET = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_SECRET = os.environ["X_ACCESS_SECRET"]

OPENCLAW_URL = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
OPENCLAW_TOKEN = os.environ["OPENCLAW_TOKEN"]
