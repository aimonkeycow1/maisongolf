"""
記分場次儲存 — 優先 PostgreSQL（Render DATABASE_URL），本機可用 SQLite。
對外 API 與舊版 rounds.json dict 格式相容。
"""

from __future__ import annotations

import json
import os
import unicodedata
import uuid
from datetime import datetime

from courses import DEFAULT_COURSE_ID, DEFAULT_TEE_ID, course_meta_for_round
from golf_utils import calc_player_stats

from round_db import (
    BASE_DIR,
    JSON_FILE as FILE,
    load_all_round_dicts,
    load_round_dict_by_external_id,
    upsert_round_dict,
    migrate_rounds_json_to_database,
    merge_rounds_by_id_db,
    query_rounds_for_user_broad,
)

def load_rounds():
    """載入全部場次 dict 列表（從資料庫）。"""
    return load_all_round_dicts()


def save_rounds(rounds):
    """將多筆場次寫入資料庫（依 id upsert）。不再寫入 rounds.json。"""
    for item in rounds:
        if isinstance(item, dict) and item.get("id"):
            upsert_round_dict(item)


def normalize_player_name(name: str) -> str:
    return unicodedata.normalize("NFKC", (name or "").strip()).lower()


def user_match_names(user) -> set[str]:
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


def is_round_listable(round_dict) -> bool:
    if not round_dict.get("players"):
        return False
    st = round_dict.get("status")
    if st == "completed":
        return True
    if st in (None, ""):
        return True
    if st in ("in_progress", "abandoned"):
        return False
    return True


def collect_participant_user_ids(round_dict, creator_user_id=None) -> list[int]:
    ids: set[int] = set()
    for raw in (
        creator_user_id,
        round_dict.get("user_id"),
        round_dict.get("creator_user_id"),
    ):
        if raw is not None:
            try:
                ids.add(int(raw))
            except (TypeError, ValueError):
                pass
    for raw in round_dict.get("participant_user_ids") or []:
        try:
            ids.add(int(raw))
        except (TypeError, ValueError):
            pass
    for p in round_dict.get("players") or []:
        if isinstance(p, dict):
            pid = _player_linked_user_id(p)
            if pid is not None:
                ids.add(pid)
    return sorted(ids)


def enrich_players_with_user_ids(players_stats: list, *, creator_user_id=None) -> list:
    if not players_stats:
        return players_stats
    try:
        from models import User
    except Exception:
        User = None  # type: ignore

    name_to_uid: dict[str, int] = {}
    if User is not None:
        for u in User.query.all():
            for n in user_match_names(u):
                name_to_uid[n] = int(u.id)

    creator_names: set[str] = set()
    cid = None
    if creator_user_id is not None:
        try:
            cid = int(creator_user_id)
            if User is not None:
                creator = User.query.get(cid)
                if creator:
                    creator_names = user_match_names(creator)
        except (TypeError, ValueError):
            cid = None

    creator_linked = False
    for row in players_stats:
        if not isinstance(row, dict):
            continue
        key = normalize_player_name(row.get("name", ""))
        if key and key in name_to_uid:
            row["participant_user_id"] = name_to_uid[key]
            if cid is not None and int(row["participant_user_id"]) == cid:
                creator_linked = True
        elif cid is not None and key and key in creator_names:
            row["participant_user_id"] = cid
            creator_linked = True

    if cid is not None and not creator_linked:
        if len(players_stats) == 1 and isinstance(players_stats[0], dict):
            players_stats[0]["participant_user_id"] = cid
        else:
            for row in players_stats:
                if not isinstance(row, dict):
                    continue
                key = normalize_player_name(row.get("name", ""))
                if key and key in creator_names:
                    row["participant_user_id"] = cid
                    break
    return players_stats


def sync_round_participant_fields(round_dict, creator_user_id=None) -> None:
    cid = creator_user_id
    if cid is None:
        cid = round_dict.get("creator_user_id") or round_dict.get("user_id")
    if cid is not None:
        cid = int(cid)
        round_dict["user_id"] = cid
        round_dict["creator_user_id"] = cid
    if round_dict.get("players"):
        round_dict["players"] = enrich_players_with_user_ids(
            round_dict["players"],
            creator_user_id=cid,
        )
    round_dict["participant_user_ids"] = collect_participant_user_ids(round_dict, cid)


def user_participated_in_round(round_dict, user) -> bool:
    if not user or getattr(user, "id", None) is None:
        return False
    uid = int(user.id)
    for pid in round_dict.get("participant_user_ids") or []:
        try:
            if int(pid) == uid:
                return True
        except (TypeError, ValueError):
            pass
    for p in round_dict.get("players") or []:
        if isinstance(p, dict) and _player_linked_user_id(p) == uid:
            return True
    match_names = user_match_names(user)
    if not match_names:
        return False
    return bool(_round_player_names(round_dict) & match_names)


def round_belongs_to_user(round_dict, user_id) -> bool:
    if user_id is None:
        return False
    uid = round_dict.get("user_id") or round_dict.get("creator_user_id")
    if uid is None:
        return False
    return int(uid) == int(user_id)


def round_belongs_to_user_account(round_dict, user) -> bool:
    if not user or getattr(user, "id", None) is None:
        return False
    if round_belongs_to_user(round_dict, user.id):
        return True
    legacy_email = round_dict.get("user_email")
    if legacy_email and getattr(user, "email", None):
        return legacy_email == user.email
    return False


def round_visible_to_user(round_dict, user) -> bool:
    if not user or getattr(user, "id", None) is None:
        return False
    if not is_round_listable(round_dict):
        return False
    if round_belongs_to_user_account(round_dict, user):
        return True
    if user_participated_in_round(round_dict, user):
        return True
    return False


def get_player_in_round_for_user(round_dict, user):
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


def load_rounds_visible_to_user(user):
    if not user or getattr(user, "id", None) is None:
        return []
    try:
        from round_db import round_orm_to_dict

        broad = query_rounds_for_user_broad(user)
        out = []
        for gr in broad:
            d = round_orm_to_dict(gr)
            if round_visible_to_user(d, user):
                out.append(d)
        return out
    except Exception:
        return [r for r in load_rounds() if round_visible_to_user(r, user)]


def load_rounds_for_user(user_id, *, include_participation: bool = True):
    try:
        from models import User

        user = User.query.get(int(user_id))
    except Exception:
        user = None
    if not user:
        return []
    if include_participation:
        return load_rounds_visible_to_user(user)
    return [
        r
        for r in load_rounds()
        if is_round_listable(r) and round_belongs_to_user(r, user_id)
    ]


def load_rounds_involving_user(user):
    return load_rounds_visible_to_user(user)


def load_rounds_for_user_account(user):
    return load_rounds_visible_to_user(user)


def get_round_by_id(rounds, round_id):
    for r in rounds:
        if r.get("id") == round_id:
            return r
    return None


def get_round_visible_to_user(round_id, user):
    if not user:
        return None
    d = load_round_dict_by_external_id(round_id)
    if d and round_visible_to_user(d, user):
        return d
    return None


def get_round_for_user(round_id, user_id, *, include_participation: bool = True):
    try:
        from models import User

        user = User.query.get(int(user_id))
    except Exception:
        user = None
    if not user:
        return None
    if include_participation:
        return get_round_visible_to_user(round_id, user)
    d = load_round_dict_by_external_id(round_id)
    if d and round_belongs_to_user(d, user_id):
        return d
    return None


def get_round_for_user_account(round_id, user):
    return get_round_visible_to_user(round_id, user)


def merge_rounds_by_id(incoming_rounds):
    merge_rounds_by_id_db(incoming_rounds)
    return load_rounds()


def migrate_legacy_round_user_ids():
    try:
        from models import User

        users = User.query.all()
    except Exception:
        return 0

    email_to_id = {u.email: u.id for u in users if u.email}
    changed = 0
    for r in load_rounds():
        if r.get("user_id") is not None:
            continue
        email = r.get("user_email")
        if email and email in email_to_id:
            r["user_id"] = int(email_to_id[email])
            r["creator_user_id"] = int(email_to_id[email])
            upsert_round_dict(r)
            changed += 1
    return changed


def migrate_rounds_participant_fields():
    changed = 0
    for r in load_rounds():
        if not is_round_listable(r):
            continue
        before = json.dumps(
            (r.get("participant_user_ids"), r.get("creator_user_id"), r.get("players")),
            sort_keys=True,
            default=str,
        )
        sync_round_participant_fields(r, r.get("user_id"))
        after = json.dumps(
            (r.get("participant_user_ids"), r.get("creator_user_id"), r.get("players")),
            sort_keys=True,
            default=str,
        )
        if before != after:
            upsert_round_dict(r)
            changed += 1
    return changed


def _draft_scores_complete(draft_scores, num_players: int) -> bool:
    if not isinstance(draft_scores, list) or len(draft_scores) < num_players:
        return False
    for row in draft_scores[:num_players]:
        if not isinstance(row, list) or len(row) < 18:
            return False
        for s in row[:18]:
            if s is None:
                return False
            if isinstance(s, str) and not str(s).strip():
                return False
    return True


def repair_stuck_in_progress_rounds():
    from web_score import normalize_scores_list

    changed = 0
    for r in load_rounds():
        if r.get("status") != "in_progress":
            continue
        uid = r.get("user_id") or r.get("creator_user_id")
        if uid is None:
            continue
        players = r.get("draft_players") or []
        draft_scores = r.get("draft_scores") or []
        if not players or not _draft_scores_complete(draft_scores, len(players)):
            continue
        pars = r.get("pars") or []
        built_stats = []
        try:
            for i, name in enumerate(players):
                pname = str(name).strip() or f"球友{i + 1}"
                row = draft_scores[i] if i < len(draft_scores) else []
                scores_int, err = normalize_scores_list(row, player_name=pname)
                if err:
                    raise ValueError(err)
                stats = calc_player_stats(scores_int, pars=pars)
                stats["name"] = pname
                built_stats.append(stats)
        except ValueError:
            continue
        r["players"] = built_stats
        r["status"] = "completed"
        r.pop("draft_players", None)
        r.pop("draft_scores", None)
        r.pop("draft_hole_index", None)
        sync_round_participant_fields(r, uid)
        upsert_round_dict(r)
        changed += 1
    return changed


def build_round_record(
    players_stats, note="", course_id=None, tee_id=None, user_id=None,
    pars=None, course_name=None,
):
    if user_id is None:
        raise ValueError("新增場次必須提供 user_id")

    now = datetime.now()
    # 極簡記分：優先用自訂 pars（拍照/模板），不依賴球場資料庫
    meta = course_meta_for_round(course_id, tee_id, pars=pars, course_name=course_name)
    if not meta:
        cid = course_id or DEFAULT_COURSE_ID
        tid = tee_id or DEFAULT_TEE_ID
        meta = course_meta_for_round(cid, tid)
    if not meta:
        meta = course_meta_for_round(DEFAULT_COURSE_ID, DEFAULT_TEE_ID)

    players_stats = enrich_players_with_user_ids(players_stats, creator_user_id=user_id)
    # 唯一場次 ID：秒級時間戳 + 微秒 + 隨機碼，避免同秒（甚至跨使用者並發）完成造成 ID 衝突與互相覆蓋
    record = {
        "id": f"{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond:06d}{uuid.uuid4().hex[:4]}",
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
        "creator_user_id": int(user_id),
        "status": "completed",
    }
    sync_round_participant_fields(record, user_id)
    return record


def add_round(
    players_stats, note="", course_id=None, tee_id=None, user_id=None,
    pars=None, course_name=None,
):
    record = build_round_record(
        players_stats, note, course_id, tee_id, user_id=user_id,
        pars=pars, course_name=course_name,
    )
    upsert_round_dict(record)
    return record["id"]


def _new_round_id(prefix="round"):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def get_in_progress_round_for_user(user_id):
    try:
        from round_db import round_orm_to_dict
        from round_models import GolfRound

        gr = (
            GolfRound.query.filter_by(creator_user_id=int(user_id), status="in_progress")
            .order_by(GolfRound.updated_at.desc())
            .first()
        )
        return round_orm_to_dict(gr) if gr else None
    except Exception:
        for r in reversed(load_rounds()):
            if round_belongs_to_user(r, user_id) and r.get("status") == "in_progress":
                return r
        return None


def abandon_in_progress_rounds(user_id):
    from models import db

    try:
        from round_models import GolfRound

        rows = GolfRound.query.filter_by(
            creator_user_id=int(user_id), status="in_progress"
        ).all()
        for gr in rows:
            gr.status = "abandoned"
        if rows:
            db.session.commit()
    except Exception:
        for r in load_rounds():
            if round_belongs_to_user(r, user_id) and r.get("status") == "in_progress":
                r["status"] = "abandoned"
                upsert_round_dict(r)


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
    pars=None,
    course_name=None,
):
    from models import db

    if user_id is None:
        raise ValueError("保存草稿必須提供 user_id")

    has_custom_pars = isinstance(pars, (list, tuple)) and len(pars) == 18
    if not has_custom_pars and (not course_id or not tee_id):
        raise ValueError("保存草稿需要 18 洞 Par 或 course_id 與 tee_id")

    meta = course_meta_for_round(course_id, tee_id, pars=pars, course_name=course_name)
    if not meta:
        raise ValueError("找不到球場/發球台資料")

    target_dict = None
    if round_id:
        target_dict = load_round_dict_by_external_id(round_id)
        if target_dict and not round_belongs_to_user(target_dict, user_id):
            target_dict = None
    if target_dict is None:
        target_dict = get_in_progress_round_for_user(user_id)

    now = datetime.now()
    if target_dict is None:
        target_dict = {
            "id": round_id or _new_round_id("draft"),
            "status": "in_progress",
            "user_id": int(user_id),
            "creator_user_id": int(user_id),
        }

    target_dict.update({
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
        "user_id": int(user_id),
        "creator_user_id": int(user_id),
    })
    upsert_round_dict(target_dict)
    return target_dict


def complete_in_progress_round(round_id, user_id, note="", players_stats=None):
    from web_score import normalize_scores_list

    target = load_round_dict_by_external_id(round_id)
    if not target or not round_belongs_to_user(target, user_id):
        return None, "找不到進行中的場次"
    if target.get("status") == "completed" and target.get("players"):
        sync_round_participant_fields(target, user_id)
        upsert_round_dict(target)
        return target, None
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
        target["players"] = enrich_players_with_user_ids(
            final_stats, creator_user_id=user_id
        )
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
        target["players"] = enrich_players_with_user_ids(
            built_stats, creator_user_id=user_id
        )

    target["note"] = (note or target.get("note") or "").strip()
    target["status"] = "completed"
    target.pop("draft_players", None)
    target.pop("draft_scores", None)
    target.pop("draft_hole_index", None)
    sync_round_participant_fields(target, user_id)
    upsert_round_dict(target)
    return target, None


def init_round_storage():
    """啟動時：從 rounds.json 遷移至資料庫（若存在且尚未匯入）。"""
    n = migrate_rounds_json_to_database()
    if n:
        print(f"✅ 已將 {n} 場次從 rounds.json 遷移至資料庫")
