"""Flask 會員 Session / Cookie 安全設定"""

from __future__ import annotations

import os
from datetime import timedelta

DEFAULT_DEV_SECRET = "dev-secret-change-me"


def is_production_hosting() -> bool:
    return bool(
        os.environ.get("RENDER")
        or os.environ.get("FLASK_ENV", "").lower() == "production"
    )


def resolve_secret_key() -> str:
    secret = (os.environ.get("SECRET_KEY") or "").strip()
    if is_production_hosting():
        if not secret or secret == DEFAULT_DEV_SECRET:
            raise RuntimeError(
                "Production requires a unique SECRET_KEY in environment variables. "
                "Set SECRET_KEY on Render (Environment) to a long random string."
            )
        return secret
    if secret and secret != DEFAULT_DEV_SECRET:
        return secret
    return DEFAULT_DEV_SECRET


def apply_security_config(app) -> None:
    app.config["SECRET_KEY"] = resolve_secret_key()
    use_secure_cookies = is_production_hosting() or os.environ.get(
        "FORCE_SECURE_COOKIES", ""
    ).strip() == "1"
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=use_secure_cookies,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=use_secure_cookies,
        REMEMBER_COOKIE_DURATION=timedelta(days=14),
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    )
