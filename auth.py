from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth_bp = Blueprint("auth", __name__)


def _looks_like_phone(s: str) -> bool:
    digits = "".join(ch for ch in s if ch.isdigit())
    return 8 <= len(digits) <= 15


def _profile_setup_or_home():
    """註冊/登入後的導向邏輯：未完善資料先去完善頁，否則首頁"""
    if not current_user.profile_complete:
        return redirect(url_for("auth.profile_setup"))
    return redirect(url_for("index"))


# ─── 註冊 ────────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _profile_setup_or_home()

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password   = request.form.get("password")  or ""
        password2  = request.form.get("password2") or ""

        is_email = "@" in identifier
        is_phone = (not is_email) and _looks_like_phone(identifier)

        error = None
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
                if User.query.filter_by(email=identifier.lower()).first():
                    error = "此 Email 已被註冊，請直接登入"
            else:
                if User.query.filter_by(phone=identifier).first():
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
            return redirect(url_for("auth.profile_setup"))   # 先完善資料

    return render_template("auth_register.html", page="auth")


# ─── 登入 ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _profile_setup_or_home()

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password   = request.form.get("password") or ""

        user = None
        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            user = User.query.filter_by(phone=identifier).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("帳號或密碼錯誤", "error")
        else:
            login_user(user, remember=True)
            next_url = request.args.get("next") or None
            if next_url:
                return redirect(next_url)
            return _profile_setup_or_home()

    return render_template("auth_login.html", page="auth")


# ─── 完善個人資料 ─────────────────────────────────────────────────────────────

@auth_bp.route("/profile/setup", methods=["GET", "POST"])
@login_required
def profile_setup():
    if request.method == "POST":
        nickname   = (request.form.get("nickname") or "").strip()
        handicap_s = (request.form.get("handicap") or "").strip()
        handedness = request.form.get("handedness") or ""
        home_course = (request.form.get("home_course") or "").strip()

        error = None
        if not nickname:
            error = "暱稱為必填，其餘可稍後再填"
        if error:
            flash(error, "error")
        else:
            current_user.nickname = nickname[:60]
            current_user.home_course = home_course[:120] or None
            current_user.handedness = handedness if handedness in ("right", "left") else None
            if handicap_s:
                try:
                    hc = float(handicap_s)
                    current_user.handicap = max(0.0, min(54.0, hc))
                except ValueError:
                    pass
            db.session.commit()
            flash("個人資料已儲存！開始記錄你的高爾夫之旅吧。", "ok")
            return redirect(url_for("index"))

    return render_template("auth_profile_setup.html", page="auth", user=current_user)


# ─── 編輯個人資料（登入後可修改）───────────────────────────────────────────────

@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    if request.method == "POST":
        nickname   = (request.form.get("nickname") or "").strip()
        handicap_s = (request.form.get("handicap") or "").strip()
        handedness = request.form.get("handedness") or ""
        home_course = (request.form.get("home_course") or "").strip()

        error = None
        if not nickname:
            error = "暱稱為必填"
        if error:
            flash(error, "error")
        else:
            current_user.nickname = nickname[:60]
            current_user.home_course = home_course[:120] or None
            current_user.handedness = handedness if handedness in ("right", "left") else None
            if handicap_s:
                try:
                    hc = float(handicap_s)
                    current_user.handicap = max(0.0, min(54.0, hc))
                except ValueError:
                    pass
            else:
                current_user.handicap = None
            db.session.commit()
            flash("個人資料已更新。", "ok")
            return redirect(url_for("auth.profile_edit"))

    return render_template("auth_profile_edit.html", page="auth", user=current_user)


# ─── 登出 ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
