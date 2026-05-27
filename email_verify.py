"""註冊驗證信：SMTP 或未設定 SMTP 時改為記錄連結（模擬）"""

from __future__ import annotations

import os
from urllib.parse import urljoin

from flask import current_app, request, url_for, has_request_context
from flask_mail import Message

from extensions import mail


def build_verify_link(token: str) -> str:
    """含目前請求網域的絕對網址；無請求內容時退回環境變數。"""
    path = url_for("auth.verify_email", token=token, _external=False)
    if has_request_context() and request.url_root:
        base = request.url_root.rstrip("/")
        return urljoin(base + "/", path.lstrip("/"))
    base = (os.environ.get("PUBLIC_APP_URL") or "http://127.0.0.1:5000").rstrip("/")
    return urljoin(base + "/", path.lstrip("/"))


def send_verification_email(email: str, username: str, token: str) -> None:
    link = build_verify_link(token)
    subject = "[Maison Golf] 請驗證您的 Email"

    suppress = bool(current_app.config.get("MAIL_SUPPRESS_SEND"))
    body_plain = (
        f"您好 {username}，\n\n"
        f"請點擊以下連結完成 Email 驗證，啟用帳號：\n{link}\n\n"
        "若不是你本人註冊，請忽略此信。\n"
    )
    html = (
        f"<p>您好 <strong>{username}</strong>，</p>"
        f"<p>請點擊連結完成 Email 驗證：<p>"
        f'<p><a href="{link}">{link}</a></p>'
        "<p>若不是你本人註冊，請忽略此信。</p>"
    )

    if suppress:
        current_app.logger.warning(
            "[EMAIL SIMULATED] to=%s subject=%s link=%s", email, subject, link
        )
        print(f"\n{'=' * 48}\n[模擬驗證信] 收件人: {email}\n{body_plain}\n{'=' * 48}\n")
        return

    msg = Message(
        subject,
        recipients=[email],
        body=body_plain,
        html=html,
    )
    mail.send(msg)
