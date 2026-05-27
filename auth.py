from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth_bp = Blueprint("auth", __name__)

def _looks_like_phone(s: str) -> bool:
    digits = "".join(ch for ch in s if ch.isdigit())
    return 8 <= len(digits) <= 15


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""

        error = None
        is_email = "@" in identifier
        is_phone = (not is_email) and _looks_like_phone(identifier)

        if not identifier:
            error = "請輸入 Email 或電話號碼"
        elif not (is_email or is_phone):
            error = "請輸入有效的 Email 或電話號碼"
        elif not password or len(password) < 6:
            error = "密碼長度至少 6 碼"
        elif password != password2:
            error = "兩次輸入的密碼不一致"
        else:
            if is_email:
                email = identifier.lower()
                if User.query.filter_by(email=email).first():
                    error = "此 Email 已被註冊，請直接登入"
            else:
                phone = identifier
                if User.query.filter_by(phone=phone).first():
                    error = "此電話已被註冊，請直接登入"

        if error:
            flash(error, "error")
        else:
            user = User(
                email=identifier.lower() if is_email else None,
                phone=identifier if is_phone else None,
                auth_provider="password",
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("index"))

    return render_template("auth_register.html", page="auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""

        user = None
        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            user = User.query.filter_by(phone=identifier).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("帳號或密碼錯誤", "error")
        else:
            login_user(user, remember=True)
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)

    return render_template("auth_login.html", page="auth")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

