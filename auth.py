from __future__ import annotations

import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

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


def _find_user_for_login(identifier: str) -> User | None:
    """球友名稱登入；舊帳號仍可用 Email 登入。"""
    u = _normalize_username(identifier)
    if not u:
        return None
    user = User.query.filter(func.lower(User.username) == u.lower()).first()
    if user:
        return user
    if "@" in u:
        return User.query.filter(func.lower(User.email) == u.lower()).first()
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""

        nu, um_err = _validate_username(username)
        error = um_err

        if not error and nu and _username_taken(nu):
            error = "此球友名稱已被使用，請換一個"

        if not error:
            if len(password) < 6:
                error = "密碼長度至少 6 碼"

        if error:
            flash(error, "error")
        else:
            user = User(
                username=nu,
                email=User.placeholder_email(nu),
                password_hash=generate_password_hash(password),
                email_verified=True,
                email_verify_token=None,
            )
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=True)
            flash(f"歡迎加入，{nu}！", "ok")
            return redirect(url_for("index"))

    return render_template("auth_register.html", page="auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""

        user = _find_user_for_login(username)
        if not user or not check_password_hash(user.password_hash, password):
            flash("球友名稱或密碼錯誤", "error")
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
