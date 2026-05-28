"""
打球場次 · PostgreSQL / SQLite 持久化層
對外仍回傳與舊 rounds.json 相同結構的 dict，供模板與 web_helpers 使用。
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from flask import has_app_context
from sqlalchemy import or_

from models import db, User
from round_models import GolfRound, RoundParticipant, HoleScore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "rounds.json")


def _player_dict_from_row(participant: RoundParticipant) -> dict:
    hole_results = [
        {
            "hole": h.hole_number,
            "score": h.score,
            "par": h.par,
            "diff": h.diff,
            "name": h.label or "",
        }
        for h in participant.hole_scores
    ]
    scores = [h.score for h in participant.hole_scores]
    row = {
        "name": participant.player_name,
        "scores": scores,
        "total": participant.total_score or (sum(scores) if scores else 0),
        "to_par": participant.to_par,
        "front9": participant.front9,
        "back9": participant.back9,
        "front_to_par": participant.front_to_par,
        "back_to_par": participant.back_to_par,
        "birdies": participant.birdies or 0,
        "pars": participant.pars_count or 0,
        "bogeys": participant.bogeys or 0,
        "double_plus": participant.double_plus or 0,
        "hole_results": hole_results,
    }
    if participant.user_id:
        row["participant_user_id"] = int(participant.user_id)
    return row


def round_orm_to_dict(gr: GolfRound) -> dict:
    """ORM → 舊版 rounds.json 相容 dict。"""
    data = {
        "id": gr.external_id,
        "status": gr.status,
        "user_id": gr.creator_user_id,
        "creator_user_id": gr.creator_user_id,
        "date": gr.played_date or "",
        "time": gr.played_time or "",
        "course_id": gr.course_id,
        "course": gr.course_name,
        "tee_id": gr.tee_id,
        "tee": gr.tee_name,
        "par_total": gr.par_total,
        "yardage_total": gr.yardage_total,
        "pars": gr.pars_json or [],
        "note": gr.note or "",
        "participant_user_ids": gr.participant_user_ids(),
    }
    if gr.user_email:
        data["user_email"] = gr.user_email
    if gr.status == "in_progress":
        data["draft_players"] = gr.draft_players_json or []
        data["draft_scores"] = gr.draft_scores_json or []
        data["draft_hole_index"] = gr.draft_hole_index or 0
    if gr.participants:
        data["players"] = [_player_dict_from_row(p) for p in gr.participants]
    else:
        data["players"] = []
    return data


def _apply_player_stats_to_participant(participant: RoundParticipant, stats: dict, pars: list[int]) -> None:
    participant.player_name = str(stats.get("name") or "球友").strip() or "球友"
    uid = stats.get("participant_user_id")
    participant.user_id = int(uid) if uid is not None else None
    participant.total_score = stats.get("total")
    participant.to_par = stats.get("to_par")
    participant.front9 = stats.get("front9")
    participant.back9 = stats.get("back9")
    participant.front_to_par = stats.get("front_to_par")
    participant.back_to_par = stats.get("back_to_par")
    participant.birdies = stats.get("birdies")
    participant.pars_count = stats.get("pars")
    participant.bogeys = stats.get("bogeys")
    participant.double_plus = stats.get("double_plus")

    participant.hole_scores.clear()
    hole_results = stats.get("hole_results") or []
    if hole_results:
        for h in hole_results:
            participant.hole_scores.append(
                HoleScore(
                    hole_number=int(h["hole"]),
                    score=int(h["score"]),
                    par=int(h.get("par", pars[int(h["hole"]) - 1] if pars else 4)),
                    diff=int(h.get("diff", 0)),
                    label=h.get("name"),
                )
            )
    else:
        scores = stats.get("scores") or []
        for i, s in enumerate(scores):
            par = pars[i] if i < len(pars) else 4
            diff = int(s) - par
            participant.hole_scores.append(
                HoleScore(
                    hole_number=i + 1,
                    score=int(s),
                    par=par,
                    diff=diff,
                    label=None,
                )
            )


def upsert_round_dict(data: dict) -> GolfRound | None:
    """將 dict（舊 JSON 格式）寫入資料庫；無 Flask context 時寫入 rounds.json。"""
    if not has_app_context():
        rounds = _load_json_file_only()
        merged = {r["id"]: r for r in rounds if r.get("id")}
        if data.get("id"):
            merged[data["id"]] = data
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(list(merged.values()), f, ensure_ascii=False, indent=2)
        return None

    ext_id = data.get("id")
    if not ext_id:
        raise ValueError("場次缺少 id")

    gr = GolfRound.query.filter_by(external_id=ext_id).first()
    if not gr:
        gr = GolfRound(external_id=ext_id)
        db.session.add(gr)

    gr.creator_user_id = data.get("creator_user_id") or data.get("user_id")
    gr.status = data.get("status") or "completed"
    gr.course_id = data.get("course_id")
    gr.tee_id = data.get("tee_id")
    gr.course_name = data.get("course")
    gr.tee_name = data.get("tee")
    gr.par_total = data.get("par_total")
    gr.yardage_total = data.get("yardage_total")
    gr.pars_json = data.get("pars")
    gr.note = (data.get("note") or "").strip()
    gr.played_date = data.get("date")
    gr.played_time = data.get("time")
    gr.user_email = data.get("user_email")

    if gr.status == "in_progress":
        gr.draft_players_json = data.get("draft_players")
        gr.draft_scores_json = data.get("draft_scores")
        gr.draft_hole_index = int(data.get("draft_hole_index") or 0)
        gr.participants.clear()
    else:
        gr.draft_players_json = None
        gr.draft_scores_json = None
        gr.draft_hole_index = 0
        pars = gr.pars_json or []
        gr.participants.clear()
        for idx, pstats in enumerate(data.get("players") or []):
            if not isinstance(pstats, dict):
                continue
            part = RoundParticipant(sort_index=idx)
            _apply_player_stats_to_participant(part, pstats, pars)
            gr.participants.append(part)

    db.session.commit()
    return gr


def _load_json_file_only() -> list[dict]:
    if not os.path.isfile(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def load_all_round_dicts() -> list[dict]:
    if not has_app_context():
        return _load_json_file_only()
    rows = (
        GolfRound.query.order_by(
            GolfRound.played_date.desc(),
            GolfRound.played_time.desc(),
            GolfRound.id.desc(),
        ).all()
    )
    return [round_orm_to_dict(r) for r in rows]


def load_round_dict_by_external_id(external_id: str) -> dict | None:
    gr = GolfRound.query.filter_by(external_id=external_id).first()
    return round_orm_to_dict(gr) if gr else None


def query_rounds_for_user_broad(user: User) -> list[GolfRound]:
    """SQL 層篩選：建立者或 participants.user_id 相符。"""
    uid = int(user.id)
    return (
        GolfRound.query.filter(
            or_(
                GolfRound.creator_user_id == uid,
                GolfRound.participants.any(RoundParticipant.user_id == uid),
            )
        )
        .order_by(
            GolfRound.played_date.desc(),
            GolfRound.played_time.desc(),
            GolfRound.id.desc(),
        )
        .all()
    )


def delete_round_by_external_id(external_id: str) -> None:
    gr = GolfRound.query.filter_by(external_id=external_id).first()
    if gr:
        db.session.delete(gr)
        db.session.commit()


def migrate_rounds_json_to_database() -> int:
    """一次性：將 rounds.json 匯入 PostgreSQL / SQLite（略過已存在 external_id）。"""
    if not os.path.isfile(JSON_FILE):
        return 0
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0
    if not isinstance(raw, list):
        return 0

    imported = 0
    for item in raw:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        if GolfRound.query.filter_by(external_id=item["id"]).first():
            continue
        try:
            upsert_round_dict(item)
            imported += 1
        except Exception as exc:
            print(f"⚠️ 遷移場次 {item.get('id')} 失敗: {exc}")
    return imported


def merge_rounds_by_id_db(incoming_rounds: list[dict]) -> int:
    """管理員同步：依 external_id 合併寫入資料庫。"""
    n = 0
    for item in incoming_rounds:
        if item.get("id"):
            upsert_round_dict(item)
            n += 1
    return n
