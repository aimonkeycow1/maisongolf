"""
記分場次儲存（rounds.json）
所有讀寫皆支援依 user_id 隔離。
"""

import json
import os
import unicodedata
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


def normalize_player_name(name: str) -> str:
    """比對球友名稱用（與登入 username 比對，忽略大小寫與全半形）。"""
    return unicodedata.normalize("NFKC", (name or "").strip()).lower()


def user_match_names(user) -> set[str]:
    """使用者可能被記在場次裡的名稱集合（username、顯示名、Email 本地段）。"""
    names: set[str] = set()
    if not user:
        return names
    for raw in (
        getattr(user, "username", None),
        getattr(user, "display_label", None),
    ):
        n = normalize_player_name(str(raw or ""))
        if n:
            names.add(n)
    email = getattr(user, "email", None) or ""
    if "@" in email:
        local = normalize_player_name(email.split("@", 1)[0])
        if local:
            names.add(local)
    return names


def _round_player_names(round_dict) -> set[str]:
    names: set[str] = set()
    for p in round_dict.get("players") or []:
        if isinstance(p, dict):
            n = normalize_player_name(p.get("name", ""))
            if n:
                names.add(n)
    for raw in round_dict.get("draft_players") or []:
        n = normalize_player_name(str(raw))
        if n:
            names.add(n)
    return names


def _player_linked_user_id(player: dict) -> int | None:
    raw = player.get("participant_user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def enrich_players_with_user_ids(players_stats: list) -> list:
    """若球友名稱對應已註冊帳號，寫入 participant_user_id 供好友戰績查詢。"""
    if not players_stats:
        return players_stats
    try:
        from models import User
    except Exception:
        return players_stats

    name_to_uid: dict[str, int] = {}
    for u in User.query.all():
        for n in user_match_names(u):
            name_to_uid[n] = int(u.id)

    for row in players_stats:
        if not isinstance(row, dict):
            continue
        key = normalize_player_name(row.get("name", ""))
        if key and key in name_to_uid:
            row["participant_user_id"] = name_to_uid[key]
    return players_stats


def user_participated_in_round(round_dict, user) -> bool:
    """使用者是否參與場次：建立者，或 players 內有名稱／participant_user_id 相符。"""
    if not user or getattr(user, "id", None) is None:
        return False
    uid = int(user.id)
    if round_belongs_to_user(round_dict, uid):
        return True
    for p in round_dict.get("players") or []:
        if isinstance(p, dict) and _player_linked_user_id(p) == uid:
            return True
    match_names = user_match_names(user)
    if not match_names:
        return False
    return bool(_round_player_names(round_dict) & match_names)


def get_player_in_round_for_user(round_dict, user):
    """取得該使用者在單場中的成績列（players 內 dict），無則 None。"""
    if not user or getattr(user, "id", None) is None:
        return None
    uid = int(user.id)
    match_names = user_match_names(user)
    for p in round_dict.get("players") or []:
        if not isinstance(p, dict):
            continue
        if _player_linked_user_id(p) == uid:
            return p
        if match_names and normalize_player_name(p.get("name", "")) in match_names:
            return p
    return None


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


def load_rounds_for_user(user_id, *, include_participation: bool = False):
    """
    載入使用者的已完成場次。
    include_participation=False：僅 user_id 為本人的場次（個人頁、首頁）。
    include_participation=True：含本人建立或 players 內有其名稱的場次（好友戰績）。
    """
    user = None
    if include_participation:
        try:
            from models import User

            user = User.query.get(int(user_id))
        except Exception:
            user = None

    out = []
    for r in load_rounds():
        if r.get("status", "completed") != "completed":
            continue
        if include_participation and user:
            if user_participated_in_round(r, user):
                out.append(r)
        elif round_belongs_to_user(r, user_id):
            out.append(r)
    return out


def load_rounds_involving_user(user):
    """載入使用者建立或參與過的已完成場次（好友戰績、公開統計用）。"""
    if not user or getattr(user, "id", None) is None:
        return []
    return load_rounds_for_user(user.id, include_participation=True)


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


def get_round_for_user(round_id, user_id, *, include_participation: bool = False):
    """取得單一場次；預設僅建立者。include_participation 時含參與場次。"""
    if include_participation:
        try:
            from models import User

            user = User.query.get(int(user_id))
        except Exception:
            user = None
        if not user:
            return None
        for r in load_rounds():
            if r.get("id") == round_id and user_participated_in_round(r, user):
                return r
        return None

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
        enrich_players_with_user_ids(players_stats),
        note,
        course_id,
        tee_id,
        user_id=user_id,
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


def abandon_in_progress_rounds(user_id):
    """放棄使用者所有進行中草稿（開始全新場次時用）"""
    rounds = load_rounds()
    changed = False
    for r in rounds:
        if round_belongs_to_user(r, user_id) and r.get("status") == "in_progress":
            r["status"] = "abandoned"
            changed = True
    if changed:
        save_rounds(rounds)


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
    if round_id:
        for r in rounds:
            if r.get("id") == round_id and round_belongs_to_user(r, user_id):
                target = r
                break
    elif round_id is None:
        for r in reversed(rounds):
            if round_belongs_to_user(r, user_id) and r.get("status") == "in_progress":
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


def complete_in_progress_round(round_id, user_id, note="", players_stats=None):
    """
    完成進行中場次。
    players_stats：若前端已驗證並傳入（建議），優先使用，避免草稿缺最後一洞。
    """
    from web_score import normalize_scores_list

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

    pars = target.get("pars") or []

    if players_stats is not None:
        if not players_stats:
            return None, "成績資料不完整"
        final_stats = []
        for i, row in enumerate(players_stats):
            if not isinstance(row, dict):
                return None, f"第 {i + 1} 位球友成績格式錯誤"
            final_stats.append(row)
        target["players"] = enrich_players_with_user_ids(final_stats)
    else:
        players = target.get("draft_players") or []
        draft_scores = target.get("draft_scores") or []
        if not players or not draft_scores:
            return None, "草稿資料不完整"

        if len(draft_scores) < len(players):
            return None, "草稿球友分數列數不一致"

        built_stats = []
        for i, name in enumerate(players):
            pname = str(name).strip() or f"球友{i + 1}"
            row = draft_scores[i] if i < len(draft_scores) else []
            scores_int, err = normalize_scores_list(row, player_name=pname)
            if err:
                return None, err
            stats = calc_player_stats(scores_int, pars=pars)
            stats["name"] = pname
            built_stats.append(stats)
        target["players"] = enrich_players_with_user_ids(built_stats)
    target["note"] = (note or target.get("note") or "").strip()
    target["status"] = "completed"
    target.pop("draft_players", None)
    target.pop("draft_scores", None)
    target.pop("draft_hole_index", None)
    save_rounds(rounds)
    return target, None
