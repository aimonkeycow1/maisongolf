"""
本機／測試環境專用：訪客模式與一鍵切換帳戶（sim01–sim50）。
正式環境（Render）預設關閉；本機開發預設開啟。
"""

from __future__ import annotations

import os

from flask import Blueprint, abort, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from database_config import is_production_hosting
from models import User, db

dev_bp = Blueprint("dev", __name__, url_prefix="/dev")

SIM_PASSWORD = "golf1234"


def dev_tools_enabled() -> bool:
    """
    安全策略：預設關閉。
    - 本機開發：設定 DEV_TEST_MODE=1 開啟（或不設 DATABASE_URL 時自動開啟）
    - 線上環境：永遠關閉，除非明確設 DEV_TEST_MODE=1
    """
    explicit = os.environ.get("DEV_TEST_MODE", "").strip()
    if explicit == "1":
        return True
    if explicit == "0":
        return False
    # 未設 DEV_TEST_MODE：只有在本機（無 DATABASE_URL 且無 RENDER）才自動開啟
    if is_production_hosting():
        return False
    if os.environ.get("DATABASE_URL"):   # 設了外部 DB → 視為生產
        return False
    return True  # 純本機開發（無 DB_URL、無 RENDER）


def _require_dev():
    if not dev_tools_enabled():
        abort(404)


def _clear_session_cookies(resp):
    from flask import current_app

    for key in (
        current_app.config.get("SESSION_COOKIE_NAME", "session"),
        current_app.config.get("REMEMBER_COOKIE_NAME", "remember_token"),
    ):
        resp.set_cookie(key, "", expires=0, max_age=0)
    return resp


@dev_bp.route("/test")
def test_hub():
    """測試控制台：訪客模式 + sim01–50 一鍵登入。"""
    _require_dev()
    sim_users = (
        User.query.filter(User.username.like("sim%"))
        .order_by(User.username)
        .all()
    )
    others = (
        User.query.filter(~User.username.like("sim%"))
        .order_by(User.username)
        .limit(30)
        .all()
    )
    return render_template(
        "dev_test.html",
        page="dev",
        sim_users=sim_users,
        other_users=others,
        sim_password=SIM_PASSWORD,
        current_username=current_user.username if current_user.is_authenticated else None,
    )


@dev_bp.route("/guest")
def guest_mode():
    """訪客模式：清除登入狀態，回到公開首頁（無需登入）。"""
    _require_dev()
    from flask import make_response

    if current_user.is_authenticated:
        logout_user()
    session.clear()
    resp = make_response(redirect(url_for("index")))
    _clear_session_cookies(resp)
    flash("已切換為訪客模式（未登入）", "ok")
    return resp


@dev_bp.route("/login-as/<username>")
def login_as(username):
    """一鍵登入指定帳戶（不勾選記住我，方便手動切換測試）。"""
    _require_dev()
    un = (username or "").strip()
    user = User.query.filter(func.lower(User.username) == un.lower()).first()
    if not user:
        flash(f"找不到帳戶「{un}」", "error")
        return redirect(url_for("dev.test_hub"))

    session.clear()
    login_user(user, remember=False)
    flash(f"已登入：{user.display_label}", "ok")
    return redirect(url_for("index"))
