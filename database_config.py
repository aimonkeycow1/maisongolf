"""資料庫 URI 與 Render 環境偵測（供 app.py、security_config.py 使用）"""

from __future__ import annotations

import os


def is_render_hosting() -> bool:
    return bool(
        os.environ.get("RENDER")
        or os.environ.get("RENDER_SERVICE_ID")
        or os.environ.get("RENDER_EXTERNAL_URL")
    )


def is_production_hosting() -> bool:
    return is_render_hosting() or os.environ.get("FLASK_ENV", "").lower() == "production"


def normalize_database_url(url: str) -> str:
    """Render / Heroku 的 postgres:// 轉為 SQLAlchemy + psycopg2 可用格式。"""
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def resolve_database_uri(base_dir: str) -> str:
    """
    有 DATABASE_URL → PostgreSQL（Render 持久化帳號）
    無 DATABASE_URL → 本機 SQLite（app.db）
    """
    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if database_url:
        return normalize_database_url(database_url)
    db_path = os.path.join(base_dir, "app.db").replace("\\", "/")
    return f"sqlite:///{db_path}"
