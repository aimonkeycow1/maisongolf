"""差點挑戰 Blueprint — A1 社交競爭功能"""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required

from models import db, Challenge, User
from friends_service import are_friends
from round_storage import load_rounds_visible_to_user
from progress import compute_progress

challenges_bp = Blueprint("challenges", __name__, url_prefix="/challenge")

# ──────────────────────────────────────────────
# 輔助
# ──────────────────────────────────────────────

def _get_current_handicap(user: User) -> float | None:
    """即時從 round data 算出最新差點指數"""
    try:
        rounds = load_rounds_visible_to_user(user)
        prog = compute_progress(rounds, user)
        return prog["index"] if prog else None
    except Exception:
        return None


def _challenge_status_label(c: Challenge) -> str:
    if c.status == "pending":
        return "待接受"
    if c.status == "accepted":
        now = datetime.utcnow()
        if c.end_date and now > c.end_date:
            return "已結束"
        days_left = (c.end_date - now).days if c.end_date else 30
        return f"進行中（剩 {max(0, days_left)} 天）"
    if c.status == "rejected":
        return "已拒絕"
    if c.status in ("completed", "expired"):
        return "已結束"
    return c.status


def _challenge_result(c: Challenge):
    """計算挑戰結果（誰進步更多）"""
    if c.status not in ("accepted", "completed", "expired"):
        return None
    challenger_now = _get_current_handicap(c.challenger)
    challenged_now = _get_current_handicap(c.challenged)

    ch_start = c.start_handicap_challenger
    cd_start = c.start_handicap_challenged

    if ch_start is None or cd_start is None:
        return None

    ch_delta = (ch_start - challenger_now) if challenger_now is not None else None
    cd_delta = (cd_start - challenged_now) if challenged_now is not None else None

    winner_id = None
    if ch_delta is not None and cd_delta is not None:
        if ch_delta > cd_delta:
            winner_id = c.challenger_id
        elif cd_delta > ch_delta:
            winner_id = c.challenged_id
        # 平局 → winner_id = None

    return {
        "challenger_name": c.challenger.username,
        "challenged_name": c.challenged.username,
        "challenger_start": ch_start,
        "challenged_start": cd_start,
        "challenger_now": challenger_now,
        "challenged_now": challenged_now,
        "challenger_delta": ch_delta,
        "challenged_delta": cd_delta,
        "winner_id": winner_id,
        "is_draw": winner_id is None and ch_delta is not None,
        "in_progress": c.end_date and datetime.utcnow() <= c.end_date,
    }


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@challenges_bp.route("/send/<int:to_user_id>", methods=["POST"])
@login_required
def send_challenge(to_user_id: int):
    target = User.query.get_or_404(to_user_id)
    if not are_friends(current_user.id, to_user_id):
        return jsonify({"ok": False, "error": "只能向好友發起挑戰"}), 400

    # 避免重複挑戰（pending / accepted 中的）
    existing = Challenge.query.filter(
        Challenge.status.in_(["pending", "accepted"]),
        db.or_(
            db.and_(Challenge.challenger_id == current_user.id, Challenge.challenged_id == to_user_id),
            db.and_(Challenge.challenger_id == to_user_id, Challenge.challenged_id == current_user.id),
        ),
    ).first()
    if existing:
        return jsonify({"ok": False, "error": "你們之間已有進行中的挑戰"}), 400

    c = Challenge(
        challenger_id=current_user.id,
        challenged_id=to_user_id,
        status="pending",
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"ok": True, "challenge_id": c.id, "message": f"已向 {target.username} 發出挑戰！"})


@challenges_bp.route("/accept/<int:challenge_id>", methods=["POST"])
@login_required
def accept_challenge(challenge_id: int):
    c = Challenge.query.get_or_404(challenge_id)
    if c.challenged_id != current_user.id:
        return jsonify({"ok": False, "error": "無權限"}), 403
    if c.status != "pending":
        return jsonify({"ok": False, "error": "此挑戰已處理"}), 400

    now = datetime.utcnow()
    c.status = "accepted"
    c.start_date = now
    c.end_date = now + timedelta(days=30)
    c.start_handicap_challenger = _get_current_handicap(c.challenger)
    c.start_handicap_challenged = _get_current_handicap(current_user)
    db.session.commit()
    return jsonify({"ok": True, "message": "挑戰已接受！30 天進步競賽開始！"})


@challenges_bp.route("/reject/<int:challenge_id>", methods=["POST"])
@login_required
def reject_challenge(challenge_id: int):
    c = Challenge.query.get_or_404(challenge_id)
    if c.challenged_id != current_user.id:
        return jsonify({"ok": False, "error": "無權限"}), 403
    if c.status != "pending":
        return jsonify({"ok": False, "error": "此挑戰已處理"}), 400
    c.status = "rejected"
    db.session.commit()
    return jsonify({"ok": True, "message": "已拒絕挑戰"})


@challenges_bp.route("/my")
@login_required
def my_challenges():
    """API：取得我的所有挑戰（JSON）"""
    uid = current_user.id
    challenges = Challenge.query.filter(
        db.or_(Challenge.challenger_id == uid, Challenge.challenged_id == uid)
    ).order_by(Challenge.created_at.desc()).all()

    result = []
    for c in challenges:
        res = _challenge_result(c)
        result.append({
            "id": c.id,
            "challenger": c.challenger.username,
            "challenged": c.challenged.username,
            "status": c.status,
            "status_label": _challenge_status_label(c),
            "start_date": c.start_date.strftime("%Y-%m-%d") if c.start_date else None,
            "end_date": c.end_date.strftime("%Y-%m-%d") if c.end_date else None,
            "is_challenger": c.challenger_id == uid,
            "result": res,
        })

    return jsonify({"ok": True, "challenges": result})
