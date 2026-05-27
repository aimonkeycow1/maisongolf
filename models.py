from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    基礎使用者：id + email + 密碼雜湊。

    記分場次（Round）儲存於 rounds.json，每筆資料以 user_id 欄位關聯本表的 id。
    查詢場次請一律透過 round_storage.load_rounds_for_user(user.id)。
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

    def load_rounds(self):
        """僅載入屬於此使用者的記分場次"""
        from round_storage import load_rounds_for_user
        return load_rounds_for_user(self.id)
