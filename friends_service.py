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


def pending_outgoing(user_id: int) -> list[FriendRequest]:
    return (
        FriendRequest.query.filter_by(from_user_id=user_id, status=STATUS_PENDING)
        .order_by(FriendRequest.created_at.desc())
        .all()
    )
