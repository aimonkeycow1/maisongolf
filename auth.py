from __future__ import annotations

import os
import re
import unicodedata

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    abort,
    current_app,
    make_response,
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from round_storage import load_rounds_visible_to_user, get_in_progress_round_for_user
from web_helpers import get_global_round_stats, get_player_stats_table
from friends_service import list_friends
from avatar_service import (
    save_user_avatar,
    remove_user_avatar,
    avatar_disk_path,
    avatar_exists_on_disk,
    user_has_avatar,
)

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[\w.\-]{2,32}$", re.UNICODE)


def _normalize_username(raw: str) -> str:
    return unicodedata.normalize("NFKC", (raw or "").strip())


def _login_identifier_from_form() -> str:
    """相容舊版登入表單的 email 欄位與密碼管理器自動填入。"""
    for key in ("username", "email", "identifier"):
        val = _normalize_username(request.form.get(key) or "")
        if val:
            return val
    return ""


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


def _remember_from_form() -> bool:
    return (request.form.get("remember") or "").strip().lower() in (
        "1",
        "on",
        "true",
        "yes",
    )


def _login_secure(user: User, *, remember: bool = False) -> None:
    """登入前清空舊 Session，降低共用裝置／Session 固定風險。"""
    session.clear()
    login_user(user, remember=remember)


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
            _login_secure(user, remember=False)
            flash(f"歡迎加入，{nu}！", "ok")
            return redirect(url_for("index"))

    return render_template("auth_register.html", page="auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    login_identifier = ""

    if request.method == "POST":
        login_identifier = _login_identifier_from_form()
        password = request.form.get("password") or ""

        user = _find_user_for_login(login_identifier)
        if not user:
            flash("找不到此球友名稱或 Email，請確認後再試", "error")
        elif not (user.password_hash or "").strip():
            flash("此帳號無法使用密碼登入，請聯絡管理員", "error")
        elif not check_password_hash(user.password_hash, password):
            flash("密碼錯誤，請再試一次", "error")
        else:
            if not user.email_verified:
                user.email_verified = True
                user.email_verify_token = None
                db.session.commit()
            _login_secure(user, remember=_remember_from_form())
            next_url = (request.args.get("next") or "").strip()
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))

    return render_template(
        "auth_login.html",
        page="auth",
        login_identifier=login_identifier,
    )


def _parse_handicap(raw: str) -> float | None:
    s = (raw or "").strip()
    if not s:
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    if val < 0 or val > 54:
        return None
    return round(val, 1)


@auth_bp.route("/avatar/<int:user_id>")
def avatar_image(user_id: int):
    """本機備援頭像（未使用 Cloudinary 或舊資料）。"""
    user = db.session.get(User, user_id)
    if not user or not user_has_avatar(user):
        abort(404)
    if (user.avatar_url or "").strip().startswith("http"):
        from flask import redirect

        src = user.avatar_src()
        if not src:
            abort(404)
        return redirect(src)
    disk = avatar_disk_path(user_id)
    if not avatar_exists_on_disk(user_id):
        legacy = None
        path = (user.avatar_path or "").strip()
        if path and not path.startswith("http"):
            legacy = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "static",
                path,
            )
        if legacy and os.path.isfile(legacy):
            disk = legacy
        else:
            abort(404)
    return send_file(
        disk,
        mimetype="image/jpeg",
        max_age=86400,
        conditional=True,
    )


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    rounds = load_rounds_visible_to_user(current_user)
    global_stats = get_global_round_stats(rounds)
    player_rows = get_player_stats_table(rounds)[:5]
    friends_count = len(list_friends(current_user.id))

    if request.method == "POST":
        action = (request.form.get("action") or "settings").strip()

        if action == "avatar":
            upload = request.files.get("avatar")
            if not upload or not (upload.filename or "").strip():
                flash("請選擇要上傳的圖片", "error")
            else:
                meta, err = save_user_avatar(current_user.id, upload)
                if err:
                    flash(err, "error")
                elif not meta:
                    flash("頭像儲存失敗，請再試一次", "error")
                else:
                    current_user.avatar_url = meta.get("avatar_url")
                    current_user.avatar_public_id = meta.get("avatar_public_id")
                    current_user.avatar_path = meta.get("avatar_path")
                    current_user.avatar_revision = (current_user.avatar_revision or 0) + 1
                    db.session.commit()
                    db.session.refresh(current_user)
                    flash("頭像已更新", "ok")
        elif action == "avatar_remove":
            remove_user_avatar(
                current_user.id,
                avatar_public_id=current_user.avatar_public_id,
                current_path=current_user.avatar_path,
            )
            current_user.avatar_url = None
            current_user.avatar_public_id = None
            current_user.avatar_path = None
            current_user.avatar_revision = (current_user.avatar_revision or 0) + 1
            db.session.commit()
            flash("已移除頭像", "ok")
        elif action == "password":
            current_pw = request.form.get("current_password") or ""
            new_pw = request.form.get("new_password") or ""
            new_pw2 = request.form.get("new_password2") or ""

            if not check_password_hash(current_user.password_hash, current_pw):
                flash("目前密碼不正確", "error")
            elif len(new_pw) < 6:
                flash("新密碼至少 6 碼", "error")
            elif new_pw != new_pw2:
                flash("兩次輸入的新密碼不一致", "error")
            else:
                current_user.password_hash = generate_password_hash(new_pw)
                db.session.commit()
                flash("密碼已更新", "ok")
        else:
            handicap = _parse_handicap(request.form.get("handicap") or "")
            if request.form.get("handicap", "").strip() and handicap is None:
                flash("差點請填 0–54 之間的數字", "error")
            else:
                handedness = (request.form.get("handedness") or "").strip()
                if handedness and handedness not in ("right", "left"):
                    handedness = current_user.handedness
                current_user.handicap = handicap
                current_user.handedness = handedness or None
                current_user.home_course = (request.form.get("home_course") or "").strip()[:120] or None
                db.session.commit()
                flash("個人設置已儲存", "ok")

        return redirect(url_for("auth.profile") + "#settings")

    in_progress = get_in_progress_round_for_user(current_user.id)

    return render_template(
        "profile.html",
        page="profile",
        user=current_user,
        rounds_rev=list(reversed(rounds)),
        global_stats=global_stats,
        player_rows=player_rows,
        friends_count=friends_count,
        in_progress=in_progress,
    )


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """
    登出並徹底清除 Session /「記住我」Cookie。
    支援 GET（直接訪問 /logout 網址即可登出），方便在任何裝置強制清除登入狀態。
    """
    if current_user.is_authenticated:
        logout_user()
    session.clear()
    resp = make_response(redirect(url_for("auth.login")))
    # 明確清除所有已知 Session/Remember Cookie（路徑 / 和 /auth 都清）
    cookie_names = [
        current_app.config.get("SESSION_COOKIE_NAME", "session"),
        current_app.config.get("REMEMBER_COOKIE_NAME", "remember_token"),
        "session",
        "remember_token",
    ]
    for key in set(cookie_names):
        for path in ("/", "/auth"):
            resp.set_cookie(
                key, "", expires=0, max_age=0, path=path,
                httponly=True,
                samesite=current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
            )
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return resp
