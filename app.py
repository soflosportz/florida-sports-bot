import os
import secrets
import hashlib
import base64
import requests

from flask import Flask, redirect, request

app = Flask(__name__)

CLIENT_ID = os.environ["X_CLIENT_ID"]
REDIRECT_URI = "https://florida-sports-bot.onrender.com/callback"

# Temporary storage for the login attempt
oauth_state = None
code_verifier = None


def create_code_verifier():
    return secrets.token_urlsafe(64)


def create_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@app.route("/")
def home():
    return """
    <h1>Florida Sports Bot</h1>
    <p>My sports bot is running.</p>
    <p><a href="/login">Connect my X account</a></p>
    """


@app.route("/login")
def login():
    global oauth_state, code_verifier

    oauth_state = secrets.token_urlsafe(32)
    code_verifier = create_code_verifier()
    challenge = create_code_challenge(code_verifier)

    authorization_url = (
        "https://twitter.com/i/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=tweet.read%20tweet.write%20users.read%20offline.access"
        f"&state={oauth_state}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )

    return redirect(authorization_url)


@app.route("/callback")
def callback():
    global oauth_state, code_verifier

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or state != oauth_state:
        return "Login failed: invalid state or missing code.", 400

    token_response = requests.post(
        "https://api.x.com/2/oauth2/token",
        data={
            "code": code,
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        timeout=30,
    )

    if token_response.status_code != 200:
        return f"Token exchange failed: {token_response.text}", 400

    token_data = token_response.json()

    return f"""
    <h1>Success!</h1>
    <p>Your X account is connected.</p>
    <p>Your bot now has authorization to use your X account.</p>
    <p>Do not share these credentials.</p>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
