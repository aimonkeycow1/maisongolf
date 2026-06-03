"""
滘西洲南場 · 網頁版記分查詢
執行：python3 app.py
"""

import os
import shutil
import socket

from flask import Flask, render_template, abort, request, jsonify, redirect, url_for, flash
from flask_login import (
    LoginManager,
    login_required,
    current_user,
)

from course_data import PAR_TOTAL, COURSE_NAME
from courses import (
    list_courses_for_web,
    courses_catalog_full,
    list_courses_by_country,
    list_hero_carousel_slides,
)
from course_images import ensure_course_images
from round_storage import (
    save_rounds,
    add_round,
    BASE_DIR,
    load_rounds_visible_to_user,
    get_round_visible_to_user,
    migrate_legacy_round_user_ids,
    migrate_rounds_participant_fields,
    repair_stuck_in_progress_rounds,
    merge_rounds_by_id,
    get_in_progress_round_for_user,
    upsert_in_progress_round,
    complete_in_progress_round,
    abandon_in_progress_rounds,
    init_round_storage,
)
from web_helpers import (
    get_player_stats_table,
    get_hardest_holes,
    get_global_round_stats,
)
from web_score import validate_score_submission
from friends_service import list_friends, get_friend_activity_feed
from ai_coach import generate_coach_analysis
from courses import resolve_course_tee
from ai_coach import build_next_hole_strategy
from share_media import (
    build_share_meta,
    generate_photo_variants,
    generate_share_video,
    list_music_tracks,
    save_upload,
    PHOTO_STYLES,
)
from engagement import compute_user_engagement, compute_round_celebration
from progress import compute_progress, compute_friends_leaderboard, compute_newly_earned
from hole_analysis import compute_hole_analysis, compute_course_comparison
from year_review import compute_year_review
from models import db, User
import round_models  # noqa: F401 — 註冊 golf_rounds 資料表
from auth import auth_bp
from friends import friends_bp
from challenges import challenges_bp
from dev_tools import dev_bp, dev_tools_enabled
from user_migrations import migrate_users_auth_columns
from security_config import apply_security_config
from database_config import resolve_database_uri, is_render_hosting

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 85 * 1024 * 1024

# 正式環境：Render 注入 DATABASE_URL → PostgreSQL；本機開發：sqlite:///.../app.db
_database_url = (os.environ.get("DATABASE_URL") or "").strip()
if _database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = resolve_database_uri(BASE_DIR)
else:
    _sqlite_path = os.path.join(BASE_DIR, "app.db").replace("\\", "/")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_sqlite_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# 本機開發（無 DATABASE_URL）：模板自動重載，改 HTML 不必重啟伺服器
if not _database_url:
    app.config["TEMPLATES_AUTO_RELOAD"] = True
apply_security_config(app)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
# basic：避免手機網路切換導致 cookie 失效；帳號安全仍靠密碼與 HTTPS
login_manager.session_protection = "basic"


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


@app.after_request
def _prevent_cached_private_pages(response):
    """
    所有回應都加 Vary: Cookie，確保 Render/CDN 代理依 Cookie 分別快取，
    不會把已登入用戶的 HTML 送給下一個訪客。
    已登入頁面進一步加 no-store 防止任何形式的快取。
    """
    response.headers["Vary"] = "Cookie"
    if current_user.is_authenticated:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
    else:
        # 未登入頁面（登入頁、Landing）也不快取，確保跳轉後是新鮮狀態
        existing_cc = response.headers.get("Cache-Control", "")
        if "no-store" not in existing_cc:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
    return response


def _current_user_rounds():
    """目前登入使用者建立或參與的已完成場次"""
    return load_rounds_visible_to_user(current_user)


def _current_user_round(round_id):
    """取得使用者可查看的單場（建立者或參與者）"""
    return get_round_visible_to_user(round_id, current_user)


STATIC_IMG = os.path.join(BASE_DIR, "static", "img")
HERO_SRC = os.path.join(BASE_DIR, "south_course_hole12.jpg")
HERO_DST = os.path.join(STATIC_IMG, "hero.jpg")


def ensure_hero_image():
    os.makedirs(STATIC_IMG, exist_ok=True)
    if os.path.isfile(HERO_SRC) and (
        not os.path.isfile(HERO_DST)
        or os.path.getmtime(HERO_SRC) > os.path.getmtime(HERO_DST)
    ):
        shutil.copy2(HERO_SRC, HERO_DST)


from avatar_service import ensure_avatar_upload_dir, migrate_local_avatars_to_cloudinary

ensure_hero_image()
ensure_course_images()
ensure_avatar_upload_dir()

app.register_blueprint(auth_bp)
# 極簡版：好友／挑戰功能已隱藏（藍圖不註冊，檔案保留供日後啟用）
if dev_tools_enabled():
    app.register_blueprint(dev_bp)


@app.context_processor
def inject_dev_tools():
    return {"dev_tools_enabled": dev_tools_enabled()}

def _init_database():
    """僅建立缺少的資料表與欄位，絕不 drop 或清空既有資料。"""
    db.create_all()
    migrate_users_auth_columns()
    init_round_storage()
    migrate_legacy_round_user_ids()
    repair_stuck_in_progress_rounds()
    migrate_rounds_participant_fields()
    n = migrate_local_avatars_to_cloudinary()
    if n:
        print(f"✅ 已將 {n} 個本機頭像遷移至 Cloudinary")


with app.app_context():
    _init_database()


def _boot_banner():
    """部署資訊：import 時即印出，gunicorn（Render Logs）與本機皆可見。"""
    try:
        from scorecard_vision import describe_mode
        ocr_mode = describe_mode()
    except Exception:
        ocr_mode = "未知"
    storage = "PostgreSQL" if _database_url else "容器內 SQLite（暫存，不保存場次）"
    print("\n".join([
        "",
        "=" * 58,
        "  ⛳ Maison Golf · 極簡測試版（零登入 + 本地儲存）",
        "=" * 58,
        "  場次與成績：存在使用者瀏覽器 localStorage（伺服器不保存）",
        f"  伺服器資料庫：{storage}",
        f"  拍照讀 Par：{ocr_mode}",
        "  切換真實 OCR：在 Render 設 XAI_API_KEY，並把 OCR_MOCK 設為 false",
        "=" * 58,
        "",
    ]), flush=True)


_boot_banner()


@app.route("/admin/sync", methods=["POST"])
def admin_sync():
    """本機錄分後，用 sync_rounds.py 把 rounds.json 上傳到雲端"""
    secret = os.environ.get("SYNC_SECRET", "")
    if not secret or request.headers.get("X-Sync-Key") != secret:
        abort(403)
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "需要 JSON 陣列"}), 400
    merge_rounds_by_id(data)
    return jsonify({"ok": True, "rounds": len(data)})


@app.route("/")
def index():
    # 零登入：首頁為空殼，最近場次由前端從 localStorage 渲染
    return render_template("index.html", page="home")


@app.route("/history")
def history():
    # 零登入：歷史由前端從 localStorage 渲染
    return render_template("history.html", page="history")


@app.route("/round/<round_id>")
def round_detail(round_id):
    # 零登入：總結頁為空殼，依 round_id 由前端從 localStorage 渲染
    return render_template("round.html", page="home", round_id=round_id)


def _sync_secret_ok():
    secret = os.environ.get("SYNC_SECRET", "")
    if not secret:
        return True
    key = request.headers.get("X-Sync-Key") or ""
    if not key and request.is_json:
        data = request.get_json(silent=True) or {}
        key = data.get("sync_key", "")
    if not key:
        key = request.form.get("sync_key", "")
    return key == secret


@app.route("/score")
def score_entry():
    # 零登入：記分頁為空殼，草稿與儲存全部由前端 localStorage 管理
    return render_template("score.html", page="score")


@app.route("/score/read-scorecard", methods=["POST"])
def score_read_scorecard():
    """拍照讀 Par：上傳記分卡照片 → Grok Vision 回傳 18 洞 Par。"""
    from scorecard_vision import read_scorecard_pars

    file = request.files.get("photo")
    if not file:
        return jsonify({"ok": False, "error": "沒有收到圖片"}), 400
    image_bytes = file.read()
    if not image_bytes:
        return jsonify({"ok": False, "error": "圖片是空的"}), 400

    result, err = read_scorecard_pars(image_bytes)
    if err:
        return jsonify({"ok": False, "error": err}), 422
    return jsonify({"ok": True, **result})


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


if __name__ == "__main__":
    # 本機開發用；Render 以 gunicorn app:app 啟動，不會進入這裡
    port = int(os.environ.get("PORT", 5050))
    ip = local_ip()
    print(f"  本機打開：  http://127.0.0.1:{port}")
    print(f"  手機同 WiFi： http://{ip}:{port}（零登入，打開即用）")
    print("  按 Ctrl+C 停止伺服器\n")
    app.run(host="0.0.0.0", port=port, debug=False)
