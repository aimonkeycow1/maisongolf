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

    # password（Email/電話註冊）或 oauth（Google/Apple）
    auth_provider = db.Column(db.String(32), nullable=False, default="password", index=True)
    oauth_provider = db.Column(db.String(32), nullable=True, index=True)  # google / apple
    oauth_subject = db.Column(db.String(255), nullable=True, index=True)  # provider user id

    password_hash = db.Column(db.String(255), nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

