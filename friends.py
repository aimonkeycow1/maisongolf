"""好友系統路由"""

from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from models import User
from friends_service import (
    search_users,
    send_friend_request,
    accept_friend_request,
    reject_friend_request,
    list_friends,
    pending_incoming,
    pending_outgoing,
    can_view_user_data,
)
from round_storage import load_rounds_for_user, get_round_for_user
from course_data import PAR_TOTAL

friends_bp = Blueprint("friends", __name__, url_prefix="/friends")


@friends_bp.route("/")
@login_required
def friends_home():
    q = request.args.get("q", "").strip()
    results = search_users(q, current_user.id) if q else []
    return render_template(
        "friends.html",
        page="friends",
        friends=list_friends(current_user.id),
        incoming=pending_incoming(current_user.id),
        outgoing=pending_outgoing(current_user.id),
        search_q=q,
        search_results=results,
    )


@friends_bp.route("/request/<int:user_id>", methods=["POST"])
@login_required
def friends_request(user_id):
    ok, msg = send_friend_request(current_user.id, user_id)
    flash(msg, "ok" if ok else "error")
    return redirect(url_for("friends.friends_home", q=request.form.get("q", "")))


@friends_bp.route("/accept/<int:request_id>", methods=["POST"])
@login_required
def friends_accept(request_id):
    ok, msg = accept_friend_request(request_id, current_user.id)
    flash(msg, "ok" if ok else "error")
    return redirect(url_for("friends.friends_home"))


@friends_bp.route("/reject/<int:request_id>", methods=["POST"])
@login_required
def friends_reject(request_id):
    ok, msg = reject_friend_request(request_id, current_user.id)
    flash(msg, "ok" if ok else "error")
    return redirect(url_for("friends.friends_home"))


@friends_bp.route("/user/<int:user_id>")
@login_required
def friend_rounds(user_id):
    friend = User.query.get(user_id)
    if not friend:
        abort(404)
    if not can_view_user_data(current_user.id, user_id):
        abort(403)
    if user_id == current_user.id:
        return redirect(url_for("index"))

    rounds = load_rounds_for_user(user_id)
    return render_template(
        "friend_rounds.html",
        page="friends",
        friend=friend,
        rounds_rev=list(reversed(rounds)),
        par_total=PAR_TOTAL,
        is_self=False,
    )


@friends_bp.route("/user/<int:user_id>/round/<round_id>")
@login_required
def friend_round_detail(user_id, round_id):
    friend = User.query.get(user_id)
    if not friend:
        abort(404)
    if not can_view_user_data(current_user.id, user_id):
        abort(403)

    r = get_round_for_user(round_id, user_id)
    if not r:
        abort(404)

    rp = r.get("par_total") or PAR_TOTAL
    ranked = []
    for p in sorted(r["players"], key=lambda x: x["total"]):
        row = dict(p)
        if row.get("to_par") is None:
            row["to_par"] = row.get("total", 0) - rp
        ranked.append(row)

    return render_template(
        "friend_round.html",
        page="friends",
        friend=friend,
        round=r,
        ranked=ranked,
    )
