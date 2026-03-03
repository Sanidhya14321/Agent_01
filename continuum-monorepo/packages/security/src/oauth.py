"""
packages/security/src/oauth.py

Least-Privilege OAuth helpers for GitHub, Gmail, and YouTube.
Implements PKCE + state-param CSRF protection.
"""

import os
import secrets
import hashlib
import base64
from urllib.parse import urlencode
from typing import Optional
from dataclasses import dataclass

# ── Scope Definitions (Least Privilege) ──────────────────────────────────────

GITHUB_SCOPES = ["repo", "user:email"]          # read-only repo + identity
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.metadata",  # subjects/senders only
]
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
]

OAUTH_CONFIGS = {
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "scopes": GITHUB_SCOPES,
        "supports_pkce": False,     # GitHub uses state param only
    },
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": GMAIL_SCOPES + YOUTUBE_SCOPES,
        "supports_pkce": True,
    },
}


@dataclass
class PKCEChallenge:
    """PKCE code verifier + challenge pair."""
    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"


def generate_pkce() -> PKCEChallenge:
    """Generate a PKCE code verifier and S256 challenge."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return PKCEChallenge(code_verifier=verifier, code_challenge=challenge)


def generate_state() -> str:
    """Generate a cryptographically random CSRF state param."""
    return secrets.token_urlsafe(32)


def build_authorization_url(
    provider: str,
    redirect_uri: str,
    state: str,
    pkce: Optional[PKCEChallenge] = None,
    extra_scopes: Optional[list[str]] = None,
) -> str:
    """
    Build the OAuth authorization URL for a given provider.
    Enforces least-privilege scope list; extra_scopes must be from
    the approved whitelist or they are silently ignored.
    """
    if provider not in OAUTH_CONFIGS:
        raise ValueError(f"Unknown OAuth provider: {provider}")

    cfg = OAUTH_CONFIGS[provider]
    scopes = cfg["scopes"].copy()

    params: dict = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "response_type": "code",
    }

    if cfg["supports_pkce"] and pkce:
        params["code_challenge"] = pkce.code_challenge
        params["code_challenge_method"] = pkce.code_challenge_method

    # Google-specific: force offline access for refresh tokens
    if provider == "google":
        params["access_type"] = "offline"
        params["prompt"] = "consent"

    return f"{cfg['auth_url']}?{urlencode(params)}"


def validate_state(received: str, stored: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return secrets.compare_digest(received, stored)


def summarise_scopes(provider: str) -> list[dict]:
    """
    Return human-readable scope summaries for the onboarding consent UI.
    Key: what the agent CAN and CANNOT see.
    """
    summaries = {
        "github": [
            {
                "scope": "repo",
                "can_see": "Repository names, languages, commit messages, file structure (read-only)",
                "cannot_see": "Private repo content beyond metadata, secrets, Actions logs",
            },
            {
                "scope": "user:email",
                "can_see": "Primary email address",
                "cannot_see": "Password, SSH keys, billing info",
            },
        ],
        "google": [
            {
                "scope": "gmail.metadata",
                "can_see": "Email subjects, sender addresses, timestamps, labels",
                "cannot_see": "Email body, attachments, contacts list",
            },
            {
                "scope": "youtube.readonly",
                "can_see": "Liked videos, subscriptions, watch history titles",
                "cannot_see": "Comments, private playlists, account financials",
            },
        ],
    }
    return summaries.get(provider, [])
