import hashlib
import hmac
import time
import base64
import urllib.parse
import uuid

import requests
from config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET

TWEET_URL = "https://api.twitter.com/2/tweets"


def _oauth_header(method: str, url: str, body_params: dict | None = None) -> str:
    """Build an OAuth 1.0a Authorization header."""
    oauth_params = {
        "oauth_consumer_key": X_API_KEY,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": X_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }

    all_params = {**oauth_params}
    if body_params:
        all_params.update(body_params)

    param_string = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(all_params.items())
    )

    base_string = (
        f"{method.upper()}&"
        f"{urllib.parse.quote(url, safe='')}&"
        f"{urllib.parse.quote(param_string, safe='')}"
    )

    signing_key = (
        f"{urllib.parse.quote(X_API_SECRET, safe='')}&"
        f"{urllib.parse.quote(X_ACCESS_SECRET, safe='')}"
    )

    signature = base64.b64encode(
        hmac.new(
            signing_key.encode(), base_string.encode(), hashlib.sha1
        ).digest()
    ).decode()

    oauth_params["oauth_signature"] = signature

    header = "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return header


def post_tweet(text: str) -> dict:
    """Post a tweet to X and return the API response."""
    response = requests.post(
        TWEET_URL,
        headers={
            "Authorization": _oauth_header("POST", TWEET_URL),
            "Content-Type": "application/json",
        },
        json={"text": text},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()
