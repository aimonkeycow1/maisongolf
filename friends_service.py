"""好友邀請與好友關係邏輯"""

from __future__ import annotations

import unicodedata

from sqlalchemy import or_, and_, func

from models import db, User, FriendRequest

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_REJECTED = "rejected"


def are_friends(user_id_a: int, user_id_b: int) -> bool:
    if user_id_a is None or user_id_b is None:
        return False
    if int(user_id_a) == int(user_id_b):
        return True
    return (
        FriendRequest.query.filter(
            FriendRequest.status == STATUS_ACCEPTED,
            or_(
                and_(
                    FriendRequest.from_user_id == user_id_a,
                    FriendRequest.to_user_id == user_id_b,
                ),
                and_(
                    FriendRequest.from_user_id == user_id_b,
                    FriendRequest.to_user_id == user_id_a,
                ),
            ),
        ).first()
        is not None
    )


def can_view_user_data(viewer_id: int, owner_id: int) -> bool:
    """本人或好友才可查看對方成績"""
    return are_friends(viewer_id, owner_id)


def _normalize_search_query(query: str) -> str:
    return unicodedata.normalize("NFKC", (query or "").strip())


def search_users(query: str, current_user_id: int, limit: int = 10) -> list[User]:
    """依球友名稱或 Email 搜尋（忽略大小寫，部分符合）。"""
    q = _normalize_search_query(query)
    if len(q) < 2:
        return []
    pattern = f"%{q.lower()}%"

    return (
        User.query.filter(
            User.id != current_user_id,
            or_(
                func.lower(User.username).like(pattern),
                func.lower(User.email).like(pattern),
            ),
        )
        .order_by(User.username)
        .limit(limit)
        .all()
    )


def _existing_request_between(a_id: int, b_id: int) -> FriendRequest | None:
    return FriendRequest.query.filter(
        or_(
            and_(FriendRequest.from_user_id == a_id, FriendRequest.to_user_id == b_id),
            and_(FriendRequest.from_user_id == b_id, FriendRequest.to_user_id == a_id),
        )
    ).first()


def send_friend_request(from_user_id: int, to_user_id: int) -> tuple[bool, str]:
    if from_user_id == to_user_id:
        return False, "不能加自己為好友"
    target = User.query.get(to_user_id)
    if target is None:
        return False, "找不到該使用者"
    if are_friends(from_user_id, to_user_id):
        return False, "你們已經是好友"

    existing = _existing_request_between(from_user_id, to_user_id)
    if existing:
        if existing.status == STATUS_PENDING:
            if existing.from_user_id == from_user_id:
                return False, "已送出邀請，等待對方回應"
            return False, "對方已向你發送邀請，請到「待處理邀請」接受"
        if existing.status == STATUS_ACCEPTED:
            return False, "你們已經是好友"
        if existing.status == STATUS_REJECTED:
            existing.from_user_id = from_user_id
            existing.to_user_id = to_user_id
            existing.status = STATUS_PENDING
            db.session.commit()
            return True, "已重新發送好友邀請"

    req = FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id, status=STATUS_PENDING)
    db.session.add(req)
    db.session.commit()
    return True, "好友邀請已送出"


def accept_friend_request(request_id: int, user_id: int) -> tuple[bool, str]:
    req = FriendRequest.query.get(request_id)
    if not req or req.to_user_id != user_id:
        return False, "找不到邀請或無權限"
    if req.status != STATUS_PENDING:
        return False, "此邀請已處理"
    req.status = STATUS_ACCEPTED
    db.session.commit()
    return True, "已接受好友邀請"


def reject_friend_request(request_id: int, user_id: int) -> tuple[bool, str]:
    req = FriendRequest.query.get(request_id)
    if not req or req.to_user_id != user_id:
        return False, "找不到邀請或無權限"
    if req.status != STATUS_PENDING:
        return False, "此邀請已處理"
    req.status = STATUS_REJECTED
    db.session.commit()
    return True, "已拒絕好友邀請"


def list_friends(user_id: int) -> list[User]:
    accepted = FriendRequest.query.filter(
        FriendRequest.status == STATUS_ACCEPTED,
        or_(FriendRequest.from_user_id == user_id, FriendRequest.to_user_id == user_id),
    ).all()
    friend_ids = []
    for r in accepted:
        fid = r.to_user_id if r.from_user_id == user_id else r.from_user_id
        friend_ids.append(fid)
    if not friend_ids:
        return []
    return User.query.filter(User.id.in_(friend_ids)).order_by(User.username).all()


def pending_incoming(user_id: int) -> list[FriendRequest]:
    return (
        FriendRequest.query.filter_by(to_user_id=user_id, status=STATUS_PENDING)
        .order_by(FriendRequest.created_at.desc())
        .all()
    )


def get_friend_activity_feed(user, limit: int = 10) -> list[dict]:
    """
    返回好友最近的動態列表，每條包含：
    {type, name, headline, sub, icon, date, round_id}
    """
    from round_storage import load_rounds_visible_to_user
    from progress import compute_progress

    friends = list_friends(user.id)
    if not friends:
        return []

    items: list[dict] = []
    for friend in friends:
        try:
            rnds = load_rounds_visible_to_user(friend)
        except Exception:
            continue
        # 只取最近 5 場，避免太慢
        recent = sorted(rnds, key=lambda r: r.get("date", ""), reverse=True)[:5]
        for r in recent:
            players = r.get("players", [])
            # 找這個好友在這場的成績
            p = next((pl for pl in players if pl.get("name") == friend.username), None)
            total = p.get("total") if p else None
            par_total = r.get("par_total") or 72
            to_par = (total - par_total) if total else None
            date = r.get("date", "")

            headline = ""
            icon = "⛳"
            if total and to_par is not None:
                if total <= 80:
                    icon = "🦅"
                    headline = f"打出 {total} 桿！破80！"
                elif total <= 90:
                    icon = "🏆"
                    headline = f"打出 {total} 桿！破90！"
                elif total <= 100:
                    icon = "🎯"
                    headline = f"打出 {total} 桿，破百！"
                else:
                    to_str = f"+{to_par}" if to_par > 0 else str(to_par)
                    icon = "⛳"
                    headline = f"完成一場 {total} 桿（{to_str}）"
            else:
                headline = "完成一場新記錄"

            course = r.get("course") or r.get("course_name") or "球場"
            items.append({
                "type": "round",
                "user_id": friend.id,
                "name": friend.username,
                "headline": headline,
                "sub": f"{date} · {course}",
                "icon": icon,
                "date": date,
                "round_id": r.get("id"),
            })

        # 里程碑
        try:
            prog = compute_progress(rnds, friend)
            if prog:
                for m in prog.get("milestones", []):
                    if m["achieved"]:
                        items.append({
                            "type": "milestone",
                            "user_id": friend.id,
                            "name": friend.username,
                            "headline": f"達成里程碑：{m['label']}！",
                            "sub": f"{prog['total_rounds']} 場累積",
                            "icon": m["icon"],
                            "date": "",
                            "round_id": None,
                        })
                        break  # 一人只顯示最大里程碑一條
        except Exception:
            pass

    # 按日期排序，去重，取最新 limit 條
    seen_keys: set = set()
    deduped = []
    for it in sorted(items, key=lambda x: x["date"], reverse=True):
        k = (it["user_id"], it.get("round_id") or it["headline"])
        if k not in seen_keys:
            seen_keys.add(k)
            deduped.append(it)
    return deduped[:limit]


def pending_outgoing(user_id: int) -> list[FriendRequest]:
    return (
        FriendRequest.query.filter_by(from_user_id=user_id, status=STATUS_PENDING)
        .order_by(FriendRequest.created_at.desc())
        .all()
    )
