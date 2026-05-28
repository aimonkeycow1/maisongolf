from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

PLACEHOLDER_EMAIL_DOMAIN = "maison.local"


class User(UserMixin, db.Model):
    """
    測試版使用者：球友名稱 + 密碼登入。
    email 欄位保留供舊資料相容，新帳號使用內部占位信箱。

    記分場次（Round）儲存於 rounds.json，每筆資料以 user_id 欄位關聯本表的 id。
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=True, nullable=False)
    email_verify_token = db.Column(db.String(128), nullable=True, index=True)
    current_round_id = db.Column(db.String(64), nullable=True, index=True)
    handicap = db.Column(db.Float, nullable=True)
    handedness = db.Column(db.String(10), nullable=True)
    home_course = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

    @property
    def is_active(self) -> bool:
        return True

    @staticmethod
    def placeholder_email(username: str) -> str:
        """新帳號內部信箱（滿足 DB unique / not null，不對外使用）"""
        safe = (username or "user").strip().lower()
        return f"{safe}@{PLACEHOLDER_EMAIL_DOMAIN}"

    def load_rounds(self):
        """僅載入屬於此使用者的記分場次"""
        from round_storage import load_rounds_for_user
        return load_rounds_for_user(self.id)

    @property
    def display_label(self) -> str:
        return self.username or f"球友{self.id}"

    @property
    def public_email(self) -> str | None:
        """對外顯示用 Email（隱藏內部占位信箱）。"""
        if not self.email or self.email.endswith(f"@{PLACEHOLDER_EMAIL_DOMAIN}"):
            return None
        return self.email


class FriendRequest(db.Model):
    """好友邀請：接受後雙方可查看彼此歷史成績"""

    __tablename__ = "friend_requests"

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    from_user = db.relationship("User", foreign_keys=[from_user_id], backref="sent_friend_requests")
    to_user = db.relationship("User", foreign_keys=[to_user_id], backref="received_friend_requests")
