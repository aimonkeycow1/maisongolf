"""註冊驗證信：模擬模式（預設）或 Flask-Mail + SMTP"""

from __future__ import annotations

import os
from urllib.parse import urljoin

from flask import current_app, request, url_for, has_request_context
from flask_mail import Message

from extensions import mail


def email_verification_is_simulated() -> bool:
    """
    是否使用模擬驗證（不發真信）。
    預設 True；設 EMAIL_VERIFICATION_SIMULATE=false 且 MAIL_SERVER 已設定時才走 SMTP。
    """
    raw = os.environ.get("EMAIL_VERIFICATION_SIMULATE", "").strip().lower()
    if raw in ("0", "false", "no"):
        return False
    if raw in ("1", "true", "yes"):
        return True
    return not bool(os.environ.get("MAIL_SERVER", "").strip())


def build_verify_link(token: str) -> str:
    """含目前請求網域的絕對網址；無請求內容時退回環境變數。"""
    path = url_for("auth.verify_email", token=token, _external=False)
    if has_request_context() and request.url_root:
        base = request.url_root.rstrip("/")
        return urljoin(base + "/", path.lstrip("/"))
    base = (os.environ.get("PUBLIC_APP_URL") or "http://127.0.0.1:5000").rstrip("/")
    return urljoin(base + "/", path.lstrip("/"))


def validate_mail_config() -> None:
    """檢查正式 SMTP 設定是否完整。"""
    required_keys = (
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_DEFAULT_SENDER",
    )
    missing = [k for k in required_keys if not current_app.config.get(k)]
    if missing:
        raise RuntimeError(f"缺少郵件設定：{', '.join(missing)}")


def send_verification_email(email: str, username: str, token: str) -> None:
    link = build_verify_link(token)
    subject = "[Maison Golf] 請驗證您的 Email"
    body_plain = (
        f"您好 {username}，\n\n"
        f"請點擊以下連結完成 Email 驗證，啟用帳號：\n{link}\n\n"
        "若不是你本人註冊，請忽略此信。\n"
    )

    if email_verification_is_simulated():
        current_app.logger.info(
            "[EMAIL SIMULATED] to=%s subject=%s link=%s", email, subject, link
        )
        print(f"\n{'=' * 48}\n[模擬驗證信] 收件人: {email}\n{body_plain}\n{'=' * 48}\n")
        return

    validate_mail_config()
    html = (
        f"<p>您好 <strong>{username}</strong>，</p>"
        f"<p>請點擊連結完成 Email 驗證：</p>"
        f'<p><a href="{link}">{link}</a></p>'
        "<p>若不是你本人註冊，請忽略此信。</p>"
    )
    msg = Message(
        subject,
        recipients=[email],
        body=body_plain,
        html=html,
    )
    mail.send(msg)
