"""
滘西洲南場 · 網頁版記分查詢
執行：python3 app.py
"""

import os
import shutil
import socket

from flask import Flask, render_template, abort, request, jsonify

from course_data import PAR_TOTAL, COURSE_NAME
from courses import (
    list_courses_for_web,
    courses_catalog_full,
    list_courses_by_country,
    list_hero_carousel_slides,
)
from course_images import ensure_course_images
from round_storage import load_rounds, save_rounds, add_round, BASE_DIR
from web_helpers import (
    get_round_by_id,
    get_player_stats_table,
    get_hardest_holes,
    get_global_round_stats,
)
from web_score import validate_score_submission
from ai_coach import generate_coach_analysis

app = Flask(__name__)

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


ensure_hero_image()
ensure_course_images()


@app.route("/admin/sync", methods=["POST"])
def admin_sync():
    """本機錄分後，用 sync_rounds.py 把 rounds.json 上傳到雲端"""
    secret = os.environ.get("SYNC_SECRET", "")
    if not secret or request.headers.get("X-Sync-Key") != secret:
        abort(403)
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "需要 JSON 陣列"}), 400
    save_rounds(data)
    return jsonify({"ok": True, "rounds": len(data)})


@app.route("/")
def index():
    rounds = load_rounds()
    return render_template(
        "index.html",
        page="home",
        rounds_rev=list(reversed(rounds)),
        par_total=PAR_TOTAL,
        course_name=COURSE_NAME,
        hero_slides=list_hero_carousel_slides(),
    )


@app.route("/round/<round_id>")
def round_detail(round_id):
    rounds = load_rounds()
    r = get_round_by_id(rounds, round_id)
    if not r:
        abort(404)
    ranked = sorted(r["players"], key=lambda p: p["total"])
    return render_template(
        "round.html",
        page="home",
        round=r,
        ranked=ranked,
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
def score_entry():
    """網頁多人同組錄分（雲端需 SYNC_SECRET）"""
    secret_required = bool(os.environ.get("SYNC_SECRET", ""))

    if request.method == "GET":
        return render_template(
            "score.html",
            page="score",
            courses_catalog=list_courses_for_web(),
            courses_by_country=list_courses_by_country(),
            courses_full=courses_catalog_full(),
            secret_required=secret_required,
        )

    if not _sync_secret_ok():
        return jsonify({"ok": False, "error": "管理員密鑰錯誤或未填寫"}), 403

    data = request.get_json(force=True, silent=True)
    result, err = validate_score_submission(data)
    if err:
        return jsonify({"ok": False, "error": err}), 400

    rid = add_round(
        result["players_stats"],
        result["note"],
        course_id=result["course_id"],
        tee_id=result["tee_id"],
    )
    return jsonify({
        "ok": True,
        "id": rid,
        "redirect": request.url_root.rstrip("/") + f"/round/{rid}?ai=1",
    })


@app.route("/ai_analysis", methods=["POST"])
def ai_analysis():
    """AI 教練賽後總結（Grok API 或本機模擬）"""
    data = request.get_json(force=True, silent=True) or {}
    round_id = data.get("round_id")
    player_name = data.get("player_name") or None

    if not round_id:
        return jsonify({"ok": False, "error": "缺少 round_id"}), 400

    rounds = load_rounds()
    r = get_round_by_id(rounds, round_id)
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


@app.route("/stats")
def stats():
    rounds = load_rounds()
    return render_template(
        "stats.html",
        page="stats",
        player_rows=get_player_stats_table(rounds),
        hard_holes=get_hardest_holes(rounds),
        global_stats=get_global_round_stats(rounds),
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
    print("  ⛳ 滘西洲南場 · 網頁版已啟動")
    print("=" * 50)
    print(f"  本機打開：  http://127.0.0.1:{port}")
    print(f"  手機同 WiFi： http://{ip}:{port}")
    print("  把第二條網址貼到 WhatsApp 群即可分享")
    print("  按 Ctrl+C 停止伺服器")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
