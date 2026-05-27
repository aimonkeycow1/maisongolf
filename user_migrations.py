"""SQLite 使用者表欄位補齊（相容既有 app.db）"""

from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy import inspect, text, func

from models import db, User


def _sqlite_table_columns(table: str) -> set[str]:
    insp = inspect(db.engine)
    return {c["name"] for c in insp.get_columns(table)}


def _exec(sql: str) -> None:
    with db.engine.begin() as conn:
        conn.execute(text(sql))


def migrate_users_auth_columns() -> None:
    cols = _sqlite_table_columns("users")
    statements: list[str] = []
    if "username" not in cols:
        statements.append(
            'ALTER TABLE users ADD COLUMN username VARCHAR(80)'
        )
    if "email_verified" not in cols:
        # 勿加 DEFAULT：否則部分 SQLite 版本會把舊列填成 0，導致既有帳號無法登入
        statements.append("ALTER TABLE users ADD COLUMN email_verified BOOLEAN")
    if "email_verify_token" not in cols:
        statements.append(
            "ALTER TABLE users ADD COLUMN email_verify_token VARCHAR(128)"
        )
    if "current_round_id" not in cols:
        statements.append("ALTER TABLE users ADD COLUMN current_round_id VARCHAR(64)")
    for stmt in statements:
        _exec(stmt)

    backfill_existing_users_username_and_verified()

    with db.engine.begin() as conn:
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username)"))


def _unique_username_candidates(base: str, max_len: int = 80) -> Iterable[str]:
    if not base:
        base = "user"
    base = base[:max_len]
    yield base
    for i in range(1, 10_000):
        suffix = f"_{i}"
        yield (base[: max_len - len(suffix)] + suffix)[:max_len]


def backfill_existing_users_username_and_verified() -> None:
    """既有帳號：補 username、視為已驗證。"""
    for u in User.query.order_by(User.id).all():
        changed = False
        if not u.email_verified or u.email_verified is None:
            u.email_verified = True
            changed = True
        if not getattr(u, "username", None):
            local = ((u.email or "").split("@")[0]).strip()
            safe = re.sub(r"[^\w.-]", "_", local, flags=re.UNICODE).strip("_") or ""
            safe = safe[:72] if safe else ""
            existing_ids = set()
            for cand in _unique_username_candidates(safe or f"user{u.id}"):
                clash = User.query.filter(
                    func.lower(User.username) == cand.lower(),
                    User.id != u.id,
                ).first()
                if not clash:
                    u.username = cand
                    changed = True
                    break
            if not u.username:
                u.username = f"user{u.id}"
                changed = True
        if changed:
            db.session.add(u)
    db.session.commit()
