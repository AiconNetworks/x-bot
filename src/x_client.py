import json
import os

import requests
from config import X_CLIENT_ID, X_CLIENT_SECRET

TWEET_URL = "https://api.x.com/2/tweets"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", ".x_tokens.json")
TOKEN_URL = "https://api.x.com/2/oauth2/token"

import base64


def _load_tokens() -> dict:
    path = os.path.normpath(TOKEN_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            "No tokens found. Run 'poetry run python src/x_oauth_setup.py' first."
        )
    with open(path) as f:
        return json.load(f)


def _save_tokens(data: dict):
    path = os.path.normpath(TOKEN_FILE)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _refresh_access_token(refresh_token: str) -> dict:
    """Use refresh token to get a new access token."""
    auth_header = base64.b64encode(
        f"{X_CLIENT_ID}:{X_CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def post_tweet(text: str) -> dict:
    """Post a tweet to X and return the API response."""
    tokens = _load_tokens()
    access_token = tokens["access_token"]

    response = requests.post(
        TWEET_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"text": text},
        timeout=15,
    )

    # If token expired, try refreshing
    if response.status_code == 401 and "refresh_token" in tokens:
        new_tokens = _refresh_access_token(tokens["refresh_token"])
        _save_tokens(new_tokens)
        response = requests.post(
            TWEET_URL,
            headers={
                "Authorization": f"Bearer {new_tokens['access_token']}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=15,
        )

    response.raise_for_status()
    return response.json()
