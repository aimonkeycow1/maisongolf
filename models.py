from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    # 登入識別：Email / 電話 / 第三方 OAuth（Google/Apple）
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(40), unique=True, nullable=True, index=True)

    # 認證方式
    auth_provider = db.Column(db.String(32), nullable=False, default="password", index=True)
    oauth_provider = db.Column(db.String(32), nullable=True, index=True)   # google / apple
    oauth_subject = db.Column(db.String(255), nullable=True, index=True)   # provider uid

    password_hash = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 個人資料
    nickname   = db.Column(db.String(60), nullable=True)
    handicap   = db.Column(db.Float, nullable=True)          # 差點 0.0–54.0
    handedness = db.Column(db.String(10), nullable=True)     # right / left
    home_course = db.Column(db.String(120), nullable=True)   # 常用球場

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

    @property
    def display_name(self) -> str:
        return self.nickname or self.email or self.phone or "球友"

    @property
    def profile_complete(self) -> bool:
        """是否已完善基本資料（最低要求：有暱稱）"""
        return bool(self.nickname)
