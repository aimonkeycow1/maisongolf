"""
記分場次儲存（rounds.json）
所有讀寫皆支援依 user_id 隔離。
"""

import json
import os
from datetime import datetime

from courses import DEFAULT_COURSE_ID, DEFAULT_TEE_ID, course_meta_for_round
from golf_utils import calc_player_stats

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "rounds.json")


def load_rounds():
    """載入全部場次（僅內部或管理同步使用）"""
    try:
        with open(FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("⚠️ 紀錄檔損壞，將從空白開始。")
        return []


def save_rounds(rounds):
    with open(FILE, "w", encoding="utf-8") as file:
        json.dump(rounds, file, ensure_ascii=False, indent=2)


def round_belongs_to_user(round_dict, user_id) -> bool:
    """場次是否屬於指定 user_id（嚴格：無 user_id 的舊資料不算任何人的）"""
    if user_id is None:
        return False
    uid = round_dict.get("user_id")
    if uid is None:
        return False
    return int(uid) == int(user_id)


def round_belongs_to_user_account(round_dict, user) -> bool:
    """場次是否屬於登入使用者（含舊版 user_email 相容）"""
    if not user or getattr(user, "id", None) is None:
        return False
    if round_belongs_to_user(round_dict, user.id):
        return True
    legacy_email = round_dict.get("user_email")
    if legacy_email and getattr(user, "email", None):
        return legacy_email == user.email
    return False


def load_rounds_for_user(user_id):
    """只載入屬於該使用者的場次"""
    return [
        r
        for r in load_rounds()
        if round_belongs_to_user(r, user_id) and r.get("status", "completed") == "completed"
    ]


def load_rounds_for_user_account(user):
    """依 Flask-Login 使用者物件過濾場次"""
    if not user or getattr(user, "id", None) is None:
        return []
    return [r for r in load_rounds() if round_belongs_to_user_account(r, user)]


def get_round_by_id(rounds, round_id):
    for r in rounds:
        if r.get("id") == round_id:
            return r
    return None


def get_round_for_user(round_id, user_id):
    """取得單一場次，且必須屬於該 user_id（嚴格比對，他人資料不可見）"""
    for r in load_rounds():
        if r.get("id") == round_id and round_belongs_to_user(r, user_id):
            return r
    return None


def get_round_for_user_account(round_id, user):
    """取得單一場次；優先 user_id，啟動遷移前相容 user_email"""
    if not user or getattr(user, "id", None) is None:
        return None
    r = get_round_for_user(round_id, user.id)
    if r:
        return r
    for rec in load_rounds():
        if rec.get("id") == round_id and round_belongs_to_user_account(rec, user):
            return rec
    return None


def merge_rounds_by_id(incoming_rounds):
    """合併同步資料：依 id 覆寫/新增，不刪除其他使用者的場次"""
    merged = {r["id"]: r for r in load_rounds() if r.get("id")}
    for r in incoming_rounds:
        if r.get("id"):
            merged[r["id"]] = r
    return list(merged.values())


def migrate_legacy_round_user_ids():
    """
    將舊資料（仅有 user_email）回填 user_id。
    啟動時呼叫一次即可。
    """
    try:
        from models import User
        users = User.query.all()
    except Exception:
        return 0

    email_to_id = {u.email: u.id for u in users if u.email}
    rounds = load_rounds()
    changed = 0
    for r in rounds:
        if r.get("user_id") is not None:
            continue
        email = r.get("user_email")
        if email and email in email_to_id:
            r["user_id"] = int(email_to_id[email])
            changed += 1
    if changed:
        save_rounds(rounds)
    return changed


def build_round_record(players_stats, note="", course_id=None, tee_id=None, user_id=None):
    if user_id is None:
        raise ValueError("新增場次必須提供 user_id")

    now = datetime.now()
    cid = course_id or DEFAULT_COURSE_ID
    tid = tee_id or DEFAULT_TEE_ID
    meta = course_meta_for_round(cid, tid)
    if not meta:
        meta = course_meta_for_round(DEFAULT_COURSE_ID, DEFAULT_TEE_ID)

    return {
        "id": now.strftime("%Y%m%d_%H%M%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "course_id": meta["course_id"],
        "course": meta["course"],
        "tee_id": meta["tee_id"],
        "tee": meta["tee"],
        "par_total": meta["par_total"],
        "yardage_total": meta["yardage_total"],
        "pars": meta["pars"],
        "note": note.strip(),
        "players": players_stats,
        "user_id": int(user_id),
        "status": "completed",
    }


def add_round(players_stats, note="", course_id=None, tee_id=None, user_id=None):
    """新增場次（強制綁定 user_id）"""
    rounds = load_rounds()
    record = build_round_record(
        players_stats, note, course_id, tee_id, user_id=user_id
    )
    rounds.append(record)
    save_rounds(rounds)
    return record["id"]


def _new_round_id(prefix="round"):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def get_in_progress_round_for_user(user_id):
    for r in reversed(load_rounds()):
        if (
            round_belongs_to_user(r, user_id)
            and r.get("status") == "in_progress"
        ):
            return r
    return None


def upsert_in_progress_round(
    user_id,
    *,
    round_id=None,
    course_id=None,
    tee_id=None,
    players=None,
    scores=None,
    hole_index=0,
    note="",
):
    if user_id is None:
        raise ValueError("保存草稿必須提供 user_id")
    if not course_id or not tee_id:
        raise ValueError("保存草稿需要 course_id 與 tee_id")

    rounds = load_rounds()
    target = None
    for r in rounds:
        if r.get("id") == round_id and round_belongs_to_user(r, user_id):
            target = r
            break
    if target is None:
        target = {
            "id": round_id or _new_round_id("draft"),
            "status": "in_progress",
            "user_id": int(user_id),
        }
        rounds.append(target)

    meta = course_meta_for_round(course_id, tee_id)
    if not meta:
        raise ValueError("找不到球場/發球台資料")

    now = datetime.now()
    target.update({
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "course_id": meta["course_id"],
        "course": meta["course"],
        "tee_id": meta["tee_id"],
        "tee": meta["tee"],
        "par_total": meta["par_total"],
        "yardage_total": meta["yardage_total"],
        "pars": meta["pars"],
        "note": (note or "").strip(),
        "draft_players": players or [],
        "draft_scores": scores or [],
        "draft_hole_index": int(hole_index),
        "status": "in_progress",
    })
    save_rounds(rounds)
    return target


def complete_in_progress_round(round_id, user_id, note=""):
    rounds = load_rounds()
    target = None
    for r in rounds:
        if r.get("id") == round_id and round_belongs_to_user(r, user_id):
            target = r
            break
    if not target:
        return None, "找不到進行中的場次"
    if target.get("status") != "in_progress":
        return None, "此場次已完成或不可編輯"

    players = target.get("draft_players") or []
    draft_scores = target.get("draft_scores") or []
    pars = target.get("pars") or []
    if not players or not draft_scores:
        return None, "草稿資料不完整"

    players_stats = []
    for i, name in enumerate(players):
        scores = draft_scores[i] if i < len(draft_scores) else []
        if not isinstance(scores, list) or len(scores) != 18:
            return None, f"{name} 的草稿資料不完整"
        try:
            scores_int = [int(s) for s in scores]
        except (TypeError, ValueError):
            return None, f"{name} 的桿數格式錯誤"
        if any(s < 1 or s > 20 for s in scores_int):
            return None, f"{name} 的桿數超出範圍"
        stats = calc_player_stats(scores_int, pars=pars)
        stats["name"] = name
        players_stats.append(stats)

    target["players"] = players_stats
    target["note"] = (note or target.get("note") or "").strip()
    target["status"] = "completed"
    target.pop("draft_players", None)
    target.pop("draft_scores", None)
    target.pop("draft_hole_index", None)
    save_rounds(rounds)
    return target, None
