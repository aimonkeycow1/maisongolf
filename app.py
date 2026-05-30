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
    """避免代理/瀏覽器快取已登入頁面，減少他人裝置看到舊畫面。"""
    if current_user.is_authenticated:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Vary"] = "Cookie"
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
app.register_blueprint(friends_bp)
app.register_blueprint(challenges_bp)
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
    if is_render_hosting() and not _database_url:
        import logging

        logging.warning(
            "Render 未設定 DATABASE_URL：帳號使用容器內 SQLite，部署後會清空。"
            "請建立 PostgreSQL 並在 Environment 設定 DATABASE_URL。"
        )


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
    # 訪客預覽：未登入者先看到公開落地頁（含範例記分卡與 AI 教練預告），先嚐甜頭再註冊
    if not current_user.is_authenticated:
        return render_template("landing.html", page="home")
    rounds = _current_user_rounds()
    engagement = compute_user_engagement(rounds, current_user)
    friend_feed = get_friend_activity_feed(current_user, limit=8)
    return render_template(
        "index.html",
        page="home",
        rounds_rev=list(reversed(rounds)),
        par_total=PAR_TOTAL,
        course_name=COURSE_NAME,
        hero_slides=list_hero_carousel_slides(),
        engagement=engagement,
        friend_feed=friend_feed,
    )


@app.route("/preview")
def preview_gallery():
    return render_template("preview_index.html")


@app.route("/preview/<variant>")
def preview_variant(variant):
    allowed = {
        "masters": "preview_masters.html",
        "dusk": "preview_dusk.html",
        "pro": "preview_pro.html",
        "bplus": "preview_bplus.html",
    }
    tpl = allowed.get(variant)
    if not tpl:
        abort(404)
    return render_template(tpl)


@app.route("/round/<round_id>")
@login_required
def round_detail(round_id):
    r = _current_user_round(round_id)
    if not r:
        abort(404)
    rp = r.get("par_total") or PAR_TOTAL
    ranked = []
    for p in sorted(r["players"], key=lambda x: x["total"]):
        row = dict(p)
        if row.get("to_par") is None:
            row["to_par"] = row.get("total", 0) - rp
        ranked.append(row)

    celebration = None
    if request.args.get("celebrate"):
        celebration = compute_round_celebration(
            r, current_user, _current_user_rounds()
        )

    # B3 — 同球場跨場次比較
    all_rounds = _current_user_rounds()
    course_id = r.get("course_id") or r.get("course") or ""
    course_cmp = compute_course_comparison(all_rounds, current_user, course_id) if course_id else None

    return render_template(
        "round.html",
        page="home",
        round=r,
        ranked=ranked,
        celebration=celebration,
        course_cmp=course_cmp,
    )


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


@app.route("/score", methods=["GET", "POST"])
@login_required
def score_entry():
    """網頁多人同組錄分（雲端需 SYNC_SECRET）"""
    secret_required = bool(os.environ.get("SYNC_SECRET", ""))

    in_progress = get_in_progress_round_for_user(current_user.id)
    if request.method == "GET":
        friend_users = list_friends(current_user.id)
        return render_template(
            "score.html",
            page="score",
            courses_catalog=list_courses_for_web(),
            courses_by_country=list_courses_by_country(),
            courses_full=courses_catalog_full(),
            secret_required=secret_required,
            resume_draft=in_progress,
            friends=[
                {"username": u.username, "label": u.display_label}
                for u in friend_users
            ],
            current_username=current_user.username or "",
        )

    if not _sync_secret_ok():
        return jsonify({"ok": False, "error": "管理員密鑰錯誤或未填寫"}), 403

    data = request.get_json(force=True, silent=True)
    result, err = validate_score_submission(data)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    draft_round_id = data.get("round_id") or current_user.current_round_id
    if draft_round_id:
        done, done_err = complete_in_progress_round(
            draft_round_id,
            current_user.id,
            note=result["note"],
            players_stats=result["players_stats"],
        )
        if done_err:
            rid = add_round(
                result["players_stats"],
                result["note"],
                course_id=result["course_id"],
                tee_id=result["tee_id"],
                user_id=current_user.id,
            )
        else:
            rid = done["id"]
    else:
        rid = add_round(
            result["players_stats"],
            result["note"],
            course_id=result["course_id"],
            tee_id=result["tee_id"],
            user_id=current_user.id,
        )
    current_user.current_round_id = None
    db.session.commit()
    return jsonify({
        "ok": True,
        "id": rid,
        "redirect": request.url_root.rstrip("/") + f"/round/{rid}?ai=1&share=1&celebrate=1",
    })


@app.route("/score/progress", methods=["POST"])
@login_required
def score_progress():
    data = request.get_json(force=True, silent=True) or {}
    round_id = data.get("round_id") or current_user.current_round_id
    course_id = data.get("course_id")
    tee_id = data.get("tee_id")
    players = data.get("players") or []
    scores = data.get("scores") or []
    hole_index = int(data.get("hole_index") or 0)
    note = data.get("note") or ""
    if not isinstance(players, list) or not isinstance(scores, list):
        return jsonify({"ok": False, "error": "草稿格式錯誤"}), 400
    if data.get("force_new"):
        abandon_in_progress_rounds(current_user.id)
        round_id = None
        current_user.current_round_id = None
    draft = upsert_in_progress_round(
        current_user.id,
        round_id=round_id,
        course_id=course_id,
        tee_id=tee_id,
        players=players,
        scores=scores,
        hole_index=hole_index,
        note=note,
    )
    current_user.current_round_id = draft["id"]
    db.session.commit()
    return jsonify({"ok": True, "round_id": draft["id"]})


@app.route("/score/next-hole-strategy", methods=["POST"])
@login_required
def score_next_hole_strategy():
    data = request.get_json(force=True, silent=True) or {}
    course_id = data.get("course_id")
    tee_id = data.get("tee_id")
    next_hole = int(data.get("next_hole") or 1)
    scores = data.get("scores") or []
    players = data.get("players") or []
    tee, err = resolve_course_tee(course_id, tee_id)
    if err:
        return jsonify({"ok": False, "error": err}), 400
    strategy = build_next_hole_strategy(
        tee=tee,
        next_hole=next_hole,
        players=players,
        scores=scores,
    )
    return jsonify({"ok": True, "strategy": strategy})


@app.route("/ai_analysis", methods=["POST"])
@login_required
def ai_analysis():
    """AI 教練賽後總結（Grok API 或本機模擬）"""
    data = request.get_json(force=True, silent=True) or {}
    round_id = data.get("round_id")
    player_name = data.get("player_name") or None

    if not round_id:
        return jsonify({"ok": False, "error": "缺少 round_id"}), 400

    r = _current_user_round(round_id)
    if not r:
        return jsonify({"ok": False, "error": "找不到該場次"}), 404

    analysis, source = generate_coach_analysis(r, player_name=player_name)
    if not analysis:
        return jsonify({"ok": False, "error": "無法產生分析（球員資料不足）"}), 400

    return jsonify({
        "ok": True,
        "analysis": analysis,
        "source": source,
        "player_name": player_name or sorted(r["players"], key=lambda p: p["total"])[0]["name"],
    })


@app.route("/share/meta/<round_id>")
@login_required
def share_meta(round_id):
    """分享疊字用場次中繼資料"""
    r = _current_user_round(round_id)
    if not r:
        return jsonify({"ok": False, "error": "找不到該場次"}), 404

    player_name = request.args.get("player_name")
    meta = build_share_meta(r, player_name=player_name)
    if not meta:
        return jsonify({"ok": False, "error": "場次無球員資料"}), 400

    # 帶上目前使用者的差點指數（社交炫耀點）
    prog = compute_progress(_current_user_rounds(), current_user)
    meta["index"] = prog["index"] if prog else None

    players = sorted(r["players"], key=lambda p: p["total"])
    return jsonify({
        "ok": True,
        "meta": meta,
        "players": [{"name": p["name"], "total": p["total"]} for p in players],
        "photo_styles": list(PHOTO_STYLES),
        "music_tracks": list_music_tracks(),
    })


@app.route("/share/photo", methods=["POST"])
@login_required
def share_photo():
    """上傳照片並生成多風格分享圖"""
    round_id = request.form.get("round_id")
    if not round_id:
        return jsonify({"ok": False, "error": "缺少 round_id"}), 400

    r = _current_user_round(round_id)
    if not r:
        return jsonify({"ok": False, "error": "找不到該場次"}), 404

    path, err = save_upload(request.files.get("photo"), "image")
    if err:
        return jsonify({"ok": False, "error": err}), 400

    meta = build_share_meta(r, player_name=request.form.get("player_name"))
    styles_raw = request.form.get("styles", "")
    styles = [s.strip() for s in styles_raw.split(",") if s.strip()] or None

    images, gen_err = generate_photo_variants(path, meta, styles=styles)
    if gen_err:
        return jsonify({"ok": False, "error": gen_err}), 500
    if not images:
        return jsonify({"ok": False, "error": "無法生成分享圖"}), 500

    return jsonify({
        "ok": True,
        "images": images,
        "meta": meta,
    })


@app.route("/share/video", methods=["POST"])
@login_required
def share_video():
    """上傳短視頻並合成抖音風格短片"""
    round_id = request.form.get("round_id")
    if not round_id:
        return jsonify({"ok": False, "error": "缺少 round_id"}), 400

    r = _current_user_round(round_id)
    if not r:
        return jsonify({"ok": False, "error": "找不到該場次"}), 404

    path, err = save_upload(request.files.get("video"), "video")
    if err:
        return jsonify({"ok": False, "error": err}), 400

    meta = build_share_meta(r, player_name=request.form.get("player_name"))
    music_id = request.form.get("music_id") or None
    try:
        duration = int(request.form.get("duration", "25"))
    except (TypeError, ValueError):
        duration = 25

    url, gen_err = generate_share_video(path, meta, music_id=music_id, duration_sec=duration)
    if gen_err:
        return jsonify({"ok": False, "error": gen_err}), 500

    return jsonify({
        "ok": True,
        "video_url": url,
        "meta": meta,
        "duration_sec": max(15, min(30, duration)),
    })


@app.route("/stats")
@login_required
def stats():
    rounds = _current_user_rounds()
    return render_template(
        "stats.html",
        page="stats",
        player_rows=get_player_stats_table(rounds),
        hard_holes=get_hardest_holes(rounds),
        global_stats=get_global_round_stats(rounds),
    )


@app.route("/progress")
@login_required
def progress():
    rounds = _current_user_rounds()
    data = compute_progress(rounds, current_user)

    # 好友差點排行榜
    friends = list_friends(current_user.id)
    leaderboard = compute_friends_leaderboard(friends, current_user, data) if data else None

    # 剛解鎖成就／里程碑慶祝（URL 帶 ?prev_rounds=N 時觸發，由前端在新場次完成後設定）
    prev_rounds_raw = request.args.get("prev_rounds")
    try:
        prev_rounds = int(prev_rounds_raw) if prev_rounds_raw is not None else None
    except (TypeError, ValueError):
        prev_rounds = None
    newly_earned = compute_newly_earned(prev_rounds, data)

    hole_data = compute_hole_analysis(rounds, current_user)

    return render_template(
        "progress.html",
        page="progress",
        progress=data,
        leaderboard=leaderboard,
        newly_earned=newly_earned,
        hole_data=hole_data,
    )


@app.route("/year-review")
@app.route("/year-review/<int:year>")
@login_required
def year_review(year: int | None = None):
    rounds = _current_user_rounds()
    data = compute_year_review(rounds, current_user, year)
    available_years = sorted(set(
        int(r["date"][:4]) for r in rounds if r.get("date") and len(r["date"]) >= 4
    ), reverse=True) if rounds else []
    return render_template(
        "year_review.html",
        page="progress",
        review=data,
        available_years=available_years,
    )


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
    port = int(os.environ.get("PORT", 5050))
    ip = local_ip()
    print("\n" + "=" * 50)
    print("  ⛳ Maison Golf · 網頁版已啟動")
    print("=" * 50)
    print(f"  本機打開：  http://127.0.0.1:{port}")
    print(f"  手機同 WiFi： http://{ip}:{port}")
    print("  把第二條網址貼到 WhatsApp 群即可分享（訪客需各自登入，不會共用帳號）")
    print("  按 Ctrl+C 停止伺服器")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
