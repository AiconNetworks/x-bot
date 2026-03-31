"""One-time OAuth 2.0 PKCE setup for X/Twitter.

Run this once to authorize and save your user access token:
    poetry run python src/x_oauth_setup.py
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import urllib.parse
import webbrowser

import requests
from config import X_CLIENT_ID, X_CLIENT_SECRET

CALLBACK_PORT = 3000
REDIRECT_URI = f"http://127.0.0.1:{CALLBACK_PORT}/callback"
SCOPES = "tweet.read tweet.write users.read offline.access"
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", ".x_tokens.json")


def _generate_pkce():
    verifier = secrets.token_urlsafe(64)[:128]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def _save_tokens(data: dict):
    path = os.path.normpath(TOKEN_FILE)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Tokens saved to {path}")


def main():
    verifier, challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": X_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print(f"Opening browser for X authorization...\n")
    webbrowser.open(url)

    # Wait for callback
    auth_code = None
    returned_state = None

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code, returned_state
            query = urllib.parse.urlparse(self.path).query
            qs = urllib.parse.parse_qs(query)
            auth_code = qs.get("code", [None])[0]
            returned_state = qs.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization complete. You can close this tab.</h1>")

        def log_message(self, format, *args):
            pass  # suppress logs

    server = http.server.HTTPServer(("127.0.0.1", CALLBACK_PORT), Handler)
    print(f"Waiting for callback on http://127.0.0.1:{CALLBACK_PORT}/callback ...")
    server.handle_request()

    if not auth_code:
        print("No authorization code received. Aborting.")
        return

    if returned_state != state:
        print("State mismatch. Possible CSRF. Aborting.")
        return

    print("Authorization code received. Exchanging for tokens...")

    # Exchange code for tokens
    auth_header = base64.b64encode(
        f"{X_CLIENT_ID}:{X_CLIENT_SECRET}".encode()
    ).decode()

    token_response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        },
        timeout=15,
    )
    token_response.raise_for_status()
    tokens = token_response.json()

    _save_tokens(tokens)
    print(f"Access token: {tokens['access_token'][:20]}...")
    if "refresh_token" in tokens:
        print("Refresh token saved.")
    print("\nDone. You can now run the main app.")


if __name__ == "__main__":
    main()
