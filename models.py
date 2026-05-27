from __future__ import annotations

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    基礎使用者：username、email、密碼；需完成 Email 驗證後才可登入使用功能。

    記分場次（Round）儲存於 rounds.json，每筆資料以 user_id 欄位關聯本表的 id。
    查詢場次請一律透過 round_storage.load_rounds_for_user(user.id)。
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verify_token = db.Column(db.String(128), nullable=True, index=True)
    current_round_id = db.Column(db.String(64), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

    @property
    def is_active(self) -> bool:
        """Flask-Login：未驗證 Email 視為無法使用之帳號"""
        return bool(self.email_verified)

    def load_rounds(self):
        """僅載入屬於此使用者的記分場次"""
        from round_storage import load_rounds_for_user
        return load_rounds_for_user(self.id)

    @property
    def display_label(self) -> str:
        """列表顯示用（優先球友名稱）"""
        if self.username:
            return self.username
        if self.email and "@" in self.email:
            return self.email.split("@")[0]
        return self.email or f"球友{self.id}"


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
