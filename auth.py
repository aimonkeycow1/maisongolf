from __future__ import annotations

import re
import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from email_verify import send_verification_email
from models import db, User

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[\w.\-]{2,32}$", re.UNICODE)


def _normalize_username(raw: str) -> str:
    return (raw or "").strip()


def _validate_username(username: str) -> tuple[str | None, str | None]:
    u = _normalize_username(username)
    if len(u) < 2:
        return None, "球友名稱至少 2 個字元"
    if len(u) > 32:
        return None, "球友名稱不可超過 32 字元"
    if not USERNAME_RE.match(u):
        return (
            None,
            "球友名稱僅可使用英數、底線、中文、句點、連字號",
        )
    return u, None


def _username_taken(norm_username: str, exclude_id: int | None = None) -> bool:
    q = User.query.filter(func.lower(User.username) == norm_username.lower())
    if exclude_id is not None:
        q = q.filter(User.id != exclude_id)
    return q.first() is not None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username") or ""
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""

        nu, um_err = _validate_username(username)
        error = um_err

        if not error and nu and _username_taken(nu):
            error = "此球友名稱已被使用，請換一個"

        if not error:
            if not email or "@" not in email:
                error = "請輸入有效的 Email"
            elif len(password) < 6:
                error = "密碼長度至少 6 碼"
            elif password != password2:
                error = "兩次輸入的密碼不一致"
            else:
                existing = User.query.filter_by(email=email).first()
                if existing:
                    if existing.email_verified:
                        error = "此 Email 已被註冊，請直接登入"
                    else:
                        error = "此 Email 已註冊但尚未驗證，請使用「重送驗證信」。"

        if error:
            flash(error, "error")
        else:
            token = secrets.token_urlsafe(32)
            user = User(
                username=nu,
                email=email,
                password_hash=generate_password_hash(password),
                email_verified=False,
                email_verify_token=token,
            )
            db.session.add(user)
            db.session.commit()
            send_verification_email(email, nu, token)
            return redirect(url_for("auth.register_sent", email=email))

    return render_template("auth_register.html", page="auth")


@auth_bp.route("/register/sent")
def register_sent():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    email = (request.args.get("email") or "").strip()
    return render_template("auth_register_sent.html", page="auth", email=email)


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    user = User.query.filter_by(email_verify_token=token).first()
    if not user:
        flash("驗證連結無效或已使用，請重新註冊或重送驗證信。", "error")
        return redirect(url_for("auth.login"))

    user.email_verified = True
    user.email_verify_token = None
    db.session.commit()
    flash("Email 驗證成功，請登入。", "ok")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("若該 Email 已註冊且仍未驗證，已寄出驗證信。", "ok")
            return redirect(url_for("auth.login"))
        if user.email_verified:
            flash("此帳號已驗證，請直接登入。", "ok")
            return redirect(url_for("auth.login"))

        user.email_verify_token = secrets.token_urlsafe(32)
        db.session.commit()
        send_verification_email(user.email, user.username, user.email_verify_token)
        flash("已重新寄送驗證信，請查看信箱。", "ok")
        return redirect(url_for("auth.login"))

    return render_template("auth_resend_verification.html", page="auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Email 或密碼錯誤", "error")
        elif not user.email_verified:
            flash(
                "此帳號尚未完成 Email 驗證。請開啟信中的連結，或重送驗證信。",
                "error",
            )
        else:
            login_user(user, remember=True)
            next_url = (request.args.get("next") or "").strip()
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))

    return render_template("auth_login.html", page="auth")


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for("auth.login"))

