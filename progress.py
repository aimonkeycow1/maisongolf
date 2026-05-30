"""
我的進步引擎 — 從既有場次即時計算個人成長指標。

純函式：不新增資料表、不改寫任何場次。產出：
- 差點指數（WHS 簡化版，依最佳差值平均）
- 趨勢圖座標（最近 N 場 to-par，已算好 SVG path）
- 個人紀錄牆（最佳總桿 / 最佳 to-par / 最低單九 / 最多小鳥 / 勝場 / 連續週）
- 桿數分布（老鷹 / 小鳥 / Par / Bogey / Double+）
- 里程碑（破百 / 破90 / 破80）
"""

from __future__ import annotations

from datetime import date, datetime

from round_storage import get_player_in_round_for_user
from web_helpers import _player_to_par, _round_par_total


# WHS 簡化版：依場次數決定取「最佳幾個差值」與調整值
_WHS_TABLE = {
    3: (1, -2.0), 4: (1, -1.0), 5: (1, 0.0), 6: (2, -1.0),
    7: (2, 0.0), 8: (2, 0.0), 9: (3, 0.0), 10: (3, 0.0), 11: (3, 0.0),
    12: (4, 0.0), 13: (4, 0.0), 14: (4, 0.0), 15: (5, 0.0), 16: (5, 0.0),
    17: (6, 0.0), 18: (6, 0.0), 19: (7, 0.0), 20: (8, 0.0),
}
_MIN_ROUNDS_FOR_INDEX = 3

# 破百 / 破90 / 破80（以總桿計，符合球友語境）
_MILESTONES = [
    (100, "破百", "🎯"),
    (90, "破 90", "🔥"),
    (80, "破 80", "💎"),
]


def _fmt_to_par(n):
    if n is None:
        return "—"
    if n > 0:
        return f"+{n}"
    if n == 0:
        return "E"
    return str(n)


def _parse_dt(r):
    d = str(r.get("date") or "")
    t = str(r.get("time") or "")
    try:
        return datetime.strptime(f"{d[:10]} {t[:5] or '00:00'}", "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            return datetime.strptime(d[:10], "%Y-%m-%d")
        except ValueError:
            return datetime.min


def _week_index(d: date) -> int:
    iso = d.isocalendar()
    return iso[0] * 53 + iso[1]


def _whs_index(diffs):
    """diffs 為各場 to-par（越低越強）。回傳 (index, used_count) 或 (None, 0)。"""
    n = len(diffs)
    if n < _MIN_ROUNDS_FOR_INDEX:
        return None, 0
    recent = diffs[-20:]
    n = len(recent)
    count, adj = _WHS_TABLE.get(n, (8, 0.0))
    lowest = sorted(recent)[:count]
    if not lowest:
        return None, 0
    idx = sum(lowest) / len(lowest) * 0.96 + adj
    return round(idx, 1), count


def _build_chart(entries, limit=12):
    """產出趨勢圖（最近 limit 場 to-par）的 SVG 座標。"""
    pts = entries[-limit:]
    if not pts:
        return None

    W, H = 1000.0, 300.0
    pad_x, pad_top, pad_bottom = 36.0, 34.0, 34.0
    vals = [e["to_par"] for e in pts]
    vmin, vmax = min(vals), max(vals)
    span = (vmax - vmin) or 1

    n = len(pts)

    def x_of(i):
        if n == 1:
            return W / 2
        return pad_x + i * (W - 2 * pad_x) / (n - 1)

    def y_of(v):
        # 越低（越強）越靠上
        return pad_top + (v - vmin) / span * (H - pad_top - pad_bottom)

    points = []
    for i, e in enumerate(pts):
        x = round(x_of(i), 1)
        y = round(y_of(e["to_par"]), 1)
        points.append({
            "x": x, "y": y,
            "to_par": e["to_par"],
            "to_par_label": _fmt_to_par(e["to_par"]),
            "total": e["total"],
            "date": e["date"],
            "is_best": e["to_par"] == vmin,
        })

    line = "M " + " L ".join(f"{p['x']} {p['y']}" for p in points)
    base_y = H - pad_bottom
    area = line + f" L {points[-1]['x']} {base_y} L {points[0]['x']} {base_y} Z"

    par_y = None
    if vmin <= 0 <= vmax:
        par_y = round(y_of(0), 1)

    return {
        "w": W, "h": H,
        "line": line, "area": area,
        "points": points,
        "par_y": par_y,
        "base_y": base_y,
    }


def compute_friends_leaderboard(friends, current_user, current_progress):
    """
    回傳好友差點排行榜（含自己）。
    friends: list[User] — 好友列表（已是 User ORM 物件）
    current_progress: 已算好的 compute_progress 結果（self 的那份）
    """
    from round_storage import load_rounds_visible_to_user

    entries = []

    # 自己
    my_index = current_progress["index"] if current_progress else None
    entries.append({
        "user_id": current_user.id,
        "name": getattr(current_user, "display_label", None) or getattr(current_user, "username", "我"),
        "index": my_index,
        "total_rounds": current_progress["total_rounds"] if current_progress else 0,
        "best_total": current_progress["records"]["best_total"]["value"] if current_progress else None,
        "is_self": True,
    })

    # 好友
    for friend in friends:
        try:
            friend_rounds = load_rounds_visible_to_user(friend)
            fp = compute_progress(friend_rounds, friend)
            entries.append({
                "user_id": friend.id,
                "name": getattr(friend, "display_label", None) or getattr(friend, "username", f"球友{friend.id}"),
                "index": fp["index"] if fp else None,
                "total_rounds": fp["total_rounds"] if fp else 0,
                "best_total": fp["records"]["best_total"]["value"] if fp else None,
                "is_self": False,
            })
        except Exception:
            entries.append({
                "user_id": friend.id,
                "name": getattr(friend, "display_label", None) or f"球友{friend.id}",
                "index": None,
                "total_rounds": 0,
                "best_total": None,
                "is_self": False,
            })

    # 排序：有指數者優先（越低越好），無指數排末
    entries.sort(key=lambda e: (e["index"] is None, e["index"] if e["index"] is not None else 999))

    # 標注名次 & 自己相對位置
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    self_rank = next((e["rank"] for e in entries if e["is_self"]), 1)
    total = len(entries)

    return {
        "entries": entries,
        "self_rank": self_rank,
        "total": total,
        "has_friends": total > 1,
    }


def compute_newly_earned(prev_total_rounds, current_progress):
    """
    比對「上一場之前」vs「現在」，找出剛達成的里程碑。
    prev_total_rounds: URL ?prev_rounds 帶入的整數，代表進入進步頁前的場次數。
    current_progress: compute_progress 的回傳結果。
    回傳 None 表示不需彈窗。
    """
    if not current_progress or prev_total_rounds is None:
        return None

    prev = int(prev_total_rounds)
    now = current_progress["total_rounds"]
    if now <= prev:
        return None  # 場次沒增加，不彈窗

    # 找剛達成的里程碑（任何已達成、且前一次場次數不足以達成的）
    achieved_milestones = [m for m in current_progress["milestones"] if m["achieved"]]
    if not achieved_milestones:
        return None

    # 取最「有份量」的首個里程碑慶祝
    milestone = achieved_milestones[0]
    headline = f"🏆 達成里程碑：{milestone['label']}！"

    return {
        "headline": headline,
        "icon": milestone["icon"],
        "achievement": None,
        "milestone": milestone,
        "index": current_progress["index"],
        "total_rounds": now,
    }


def compute_progress(rounds, user):
    """主函式：回傳個人進步資料；無任何場次回傳 None。"""
    if not user or getattr(user, "id", None) is None:
        return None

    entries = []
    for r in rounds:
        p = get_player_in_round_for_user(r, user)
        if not p:
            continue
        rp = _round_par_total(r)
        tp = _player_to_par(p, rp)
        diffs = [h.get("diff", 0) for h in (p.get("hole_results") or []) if isinstance(h, dict)]
        players = r.get("players") or []
        rank = 1
        if players:
            ordered = sorted(players, key=lambda x: x.get("total", 999))
            rank = next(
                (i + 1 for i, x in enumerate(ordered) if x.get("name") == p.get("name")),
                1,
            )
        entries.append({
            "dt": _parse_dt(r),
            "date": r.get("date", ""),
            "course": r.get("course", ""),
            "round_id": r.get("id", ""),
            "total": p.get("total", 0),
            "to_par": tp,
            "front9": p.get("front9"),
            "back9": p.get("back9"),
            "hole_diffs": diffs,
            "rank": rank,
            "player_count": len(players),
        })

    if not entries:
        return None

    entries.sort(key=lambda e: e["dt"])
    total_rounds = len(entries)
    diffs_series = [e["to_par"] for e in entries]

    # —— 差點指數 ——
    index, used = _whs_index(diffs_series)
    prev_index = None
    delta = None
    if index is not None and total_rounds >= _MIN_ROUNDS_FOR_INDEX + 2:
        prev_index, _ = _whs_index(diffs_series[:-2])
        if prev_index is not None:
            delta = round(index - prev_index, 1)

    rounds_needed = max(0, _MIN_ROUNDS_FOR_INDEX - total_rounds)

    # —— 個人紀錄 ——
    best_total_e = min(entries, key=lambda e: e["total"])
    best_topar_e = min(entries, key=lambda e: e["to_par"])
    nine_vals = []
    for e in entries:
        for v in (e["front9"], e["back9"]):
            if isinstance(v, int) and v > 0:
                nine_vals.append((v, e))
    lowest_nine = min(nine_vals, key=lambda x: x[0]) if nine_vals else None

    def birdie_plus(e):
        return sum(1 for d in e["hole_diffs"] if d <= -1)

    most_birdies_e = max(entries, key=birdie_plus)
    most_birdies = birdie_plus(most_birdies_e)
    wins = sum(1 for e in entries if e["player_count"] > 1 and e["rank"] == 1)

    # 連續週數
    played_weeks = sorted({_week_index(e["dt"].date()) for e in entries if e["dt"] != datetime.min})
    streak_weeks = 0
    if played_weeks:
        streak_weeks = 1
        for i in range(len(played_weeks) - 1, 0, -1):
            if played_weeks[i] - played_weeks[i - 1] == 1:
                streak_weeks += 1
            else:
                break

    # —— 桿數分布 ——
    dist = {"eagle": 0, "birdie": 0, "par": 0, "bogey": 0, "double": 0}
    total_holes = 0
    for e in entries:
        for d in e["hole_diffs"]:
            total_holes += 1
            if d <= -2:
                dist["eagle"] += 1
            elif d == -1:
                dist["birdie"] += 1
            elif d == 0:
                dist["par"] += 1
            elif d == 1:
                dist["bogey"] += 1
            else:
                dist["double"] += 1

    def pct(n):
        return round(n / total_holes * 100, 1) if total_holes else 0

    distribution = [
        {"key": "eagle", "label": "老鷹+", "icon": "🦅", "count": dist["eagle"], "pct": pct(dist["eagle"]), "color": "#3b82f6"},
        {"key": "birdie", "label": "小鳥", "icon": "🐦", "count": dist["birdie"], "pct": pct(dist["birdie"]), "color": "#22c55e"},
        {"key": "par", "label": "Par", "icon": "⛳", "count": dist["par"], "pct": pct(dist["par"]), "color": "#e5e7eb"},
        {"key": "bogey", "label": "Bogey", "icon": "•", "count": dist["bogey"], "pct": pct(dist["bogey"]), "color": "#f97316"},
        {"key": "double", "label": "Double+", "icon": "•", "count": dist["double"], "pct": pct(dist["double"]), "color": "#ef4444"},
    ]

    # —— 里程碑（破百 / 破90 / 破80）——
    best_total = best_total_e["total"]
    milestones = []
    next_milestone = None
    for thr, label, icon in _MILESTONES:
        achieved = best_total < thr
        gap = max(0, best_total - (thr - 1))
        milestones.append({"threshold": thr, "label": label, "icon": icon, "achieved": achieved, "gap": gap})
        if not achieved and next_milestone is None:
            next_milestone = {"threshold": thr, "label": label, "icon": icon, "gap": gap}

    # —— 近期表現 ——
    last5 = entries[-5:]
    recent_avg_topar = round(sum(e["to_par"] for e in last5) / len(last5), 1)
    avg_total = round(sum(e["total"] for e in entries) / total_rounds, 1)

    return {
        "total_rounds": total_rounds,
        "index": index,
        "index_used": used,
        "prev_index": prev_index,
        "delta": delta,
        "improving": delta is not None and delta < 0,
        "rounds_needed": rounds_needed,
        "min_rounds": _MIN_ROUNDS_FOR_INDEX,
        "chart": _build_chart(entries),
        "records": {
            "best_total": {"value": best_total, "date": best_total_e["date"], "course": best_total_e["course"], "round_id": best_total_e["round_id"]},
            "best_to_par": {"value": best_topar_e["to_par"], "label": _fmt_to_par(best_topar_e["to_par"]), "date": best_topar_e["date"], "round_id": best_topar_e["round_id"]},
            "lowest_nine": ({"value": lowest_nine[0], "date": lowest_nine[1]["date"]} if lowest_nine else None),
            "most_birdies": {"value": most_birdies, "date": most_birdies_e["date"]},
            "wins": wins,
            "streak_weeks": streak_weeks,
        },
        "distribution": distribution,
        "total_holes": total_holes,
        "milestones": milestones,
        "next_milestone": next_milestone,
        "recent_avg_topar": recent_avg_topar,
        "recent_avg_topar_label": _fmt_to_par(round(recent_avg_topar)),
        "avg_total": avg_total,
    }
