"""
使用者黏著／習慣養成引擎。

純函式：僅從既有場次資料即時計算，不新增資料表、不改寫任何場次。
指標對應 docs/ENGAGEMENT_DESIGN.md 的心理槓桿：
連續週數（損失厭惡）、等級稱號（身份認同）、成就牆（完成欲）、
里程碑進度（目標漸進）、本月目標（稀缺）、破紀錄差距（進步可視化）。
"""

from __future__ import annotations

from datetime import date, datetime

from round_storage import get_player_in_round_for_user
from web_helpers import _player_to_par, _round_par_total


# —— 等級制（依個人最佳 to_par，越低越強） ——
# (門檻上限, 等級, 稱號, emoji)；由強到弱比對
_LEVELS = [
    (0, 6, "Scratch 殺手", "🏆"),
    (5, 5, "巡迴賽水準", "🦅"),
    (12, 4, "單位數差點", "🎯"),
    (20, 3, "進階球手", "⛳"),
    (30, 2, "穩定成長", "🌱"),
    (9999, 1, "歡樂高球", "😄"),
]
_MAX_LEVEL = 6

# 本月場次目標（稀缺/FOMO）
_MONTHLY_GOAL = 4
# 場次里程碑
_ROUND_MILESTONES = [1, 5, 10, 25, 50, 100]


def _parse_date(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(s)[:10], fmt).date()
        except ValueError:
            continue
    return None


def _week_index(d: date) -> int:
    """以 ISO 週為單位的連續可比較整數。"""
    iso = d.isocalendar()
    return iso[0] * 53 + iso[1]


def _hole_diffs(player, round_par_list):
    """取得逐洞 diff 列表（優先 hole_results，否則由 scores 推算）。"""
    holes = player.get("hole_results") or []
    if holes:
        return [h.get("diff", 0) for h in holes if isinstance(h, dict)]
    scores = player.get("scores") or []
    pars = round_par_list or [4] * 18
    out = []
    for i, s in enumerate(scores):
        if isinstance(s, int) and s >= 1:
            out.append(s - (pars[i] if i < len(pars) else 4))
    return out


def _level_for(best_to_par):
    if best_to_par is None:
        return _LEVELS[-1]
    for threshold, lvl, title, icon in _LEVELS:
        if best_to_par <= threshold:
            return (threshold, lvl, title, icon)
    return _LEVELS[-1]


def _level_progress(best_to_par, level):
    """回傳朝下一等級的百分比與「還差幾桿」。"""
    if best_to_par is None or level >= _MAX_LEVEL:
        return 100, 0
    # 找出目前等級門檻與下一等級門檻
    ordered = sorted(_LEVELS, key=lambda x: x[1])  # 由弱到強
    cur = next((x for x in ordered if x[1] == level), ordered[0])
    nxt = next((x for x in ordered if x[1] == level + 1), None)
    if not nxt:
        return 100, 0
    cur_cap = cur[0]      # 目前等級的 to_par 上限（較大）
    next_cap = nxt[0]     # 下一等級門檻（較小，較難）
    span = cur_cap - next_cap
    if span <= 0:
        return 100, 0
    done = cur_cap - best_to_par
    pct = max(0, min(100, int(done / span * 100)))
    remaining = max(0, best_to_par - next_cap)
    return pct, remaining


def _build_achievements(stats):
    """成就牆：已解鎖（earned）與未解鎖（含進度）。"""
    tr = stats["total_rounds"]

    def pct(n, target):
        return max(0, min(100, int(n / target * 100))) if target else 0

    items = [
        {
            "id": "first_round", "icon": "🚩", "name": "首場登場",
            "desc": "完成你的第一場記分", "earned": tr >= 1,
            "progress": pct(tr, 1), "hint": "完成 1 場",
        },
        {
            "id": "rounds_10", "icon": "📅", "name": "常客球手",
            "desc": "累積 10 場記分", "earned": tr >= 10,
            "progress": pct(tr, 10), "hint": f"{tr}/10 場",
        },
        {
            "id": "rounds_25", "icon": "🗓️", "name": "資深會員",
            "desc": "累積 25 場記分", "earned": tr >= 25,
            "progress": pct(tr, 25), "hint": f"{tr}/25 場",
        },
        {
            "id": "birdie", "icon": "🐦", "name": "Birdie 獵人",
            "desc": "在任一洞抓下 Birdie", "earned": stats["has_birdie"],
            "progress": 100 if stats["has_birdie"] else 0,
            "hint": "抓 1 隻小鳥",
        },
        {
            "id": "eagle", "icon": "🦅", "name": "Eagle 時刻",
            "desc": "在任一洞抓下 Eagle 或更好", "earned": stats["has_eagle"],
            "progress": 100 if stats["has_eagle"] else 0,
            "hint": "抓 1 隻老鷹",
        },
        {
            "id": "champion", "icon": "👑", "name": "同組之王",
            "desc": "在多人同組中奪得冠軍", "earned": stats["wins"] >= 1,
            "progress": 100 if stats["wins"] >= 1 else 0,
            "hint": "贏 1 場同組",
        },
        {
            "id": "steady", "icon": "🛡️", "name": "穩定大師",
            "desc": "打出一場零爆洞（無 Double+）", "earned": stats["has_clean_round"],
            "progress": 100 if stats["has_clean_round"] else 0,
            "hint": "整場無 Double+",
        },
        {
            "id": "comeback", "icon": "🔥", "name": "後九逆襲",
            "desc": "後九比前九少 3 桿以上", "earned": stats["has_comeback"],
            "progress": 100 if stats["has_comeback"] else 0,
            "hint": "後九大反攻",
        },
        {
            "id": "break_threshold", "icon": "💎", "name": "突破 +10",
            "desc": "單場成績優於標準桿 +10", "earned": stats["broke_threshold"],
            "progress": (
                100 if stats["broke_threshold"]
                else (pct(max(0, 30 - (stats["best_to_par"] or 30)), 20))
            ),
            "hint": "best ≤ +10",
        },
        {
            "id": "streak_4", "icon": "📈", "name": "四週不斷",
            "desc": "連續 4 週出場記分", "earned": stats["streak_weeks"] >= 4,
            "progress": pct(stats["streak_weeks"], 4),
            "hint": f"{stats['streak_weeks']}/4 週",
        },
    ]
    return items


def compute_round_celebration(round_data, user, all_rounds=None):
    """打完一場後的慶祝資料：本場高光事蹟、是否破個人紀錄、主標。

    僅在使用者為該場參與者時回傳；否則 None（不彈窗）。
    """
    if not user or getattr(user, "id", None) is None or not round_data:
        return None

    p = get_player_in_round_for_user(round_data, user)
    if not p:
        return None

    rp = _round_par_total(round_data)
    total = p.get("total", 0)
    to_par = _player_to_par(p, rp)
    diffs = _hole_diffs(p, round_data.get("pars"))

    birdies = sum(1 for d in diffs if d == -1)
    eagles = sum(1 for d in diffs if d <= -2)
    full_round = len(diffs) >= 18
    clean = full_round and all(d <= 1 for d in diffs)

    players = round_data.get("players") or []
    is_champion = False
    if len(players) > 1:
        champ = min(players, key=lambda x: x.get("total", 999))
        is_champion = champ is p or champ.get("name") == p.get("name")

    f = p.get("front_to_par")
    b = p.get("back_to_par")
    comeback = isinstance(f, int) and isinstance(b, int) and b <= f - 3

    # 個人紀錄判定（與使用者其他「已完成」場次比較）
    is_personal_best = False
    is_first_round = False
    if all_rounds is not None:
        others = []
        for r in all_rounds:
            if r.get("id") == round_data.get("id"):
                continue
            op = get_player_in_round_for_user(r, user)
            if op and isinstance(op.get("total"), int):
                others.append(op["total"])
        if not others:
            is_first_round = True
        elif total <= min(others):
            is_personal_best = True

    feats = []
    if is_personal_best:
        feats.append({"icon": "💎", "label": "個人最佳成績"})
    if is_first_round:
        feats.append({"icon": "🚩", "label": "完成首場記分"})
    if eagles:
        feats.append({"icon": "🦅", "label": f"老鷹 ×{eagles}"})
    if birdies:
        feats.append({"icon": "🐦", "label": f"小鳥 ×{birdies}"})
    if is_champion:
        feats.append({"icon": "👑", "label": "同組冠軍"})
    if clean:
        feats.append({"icon": "🛡️", "label": "零爆洞"})
    if comeback:
        feats.append({"icon": "🔥", "label": "後九逆襲"})
    if to_par <= 10:
        feats.append({"icon": "⭐", "label": "突破 +10"})

    # 主標：挑最有份量的
    if is_personal_best:
        headline = "新的個人最佳！"
    elif eagles:
        headline = "抓到老鷹，太精彩了！"
    elif is_champion:
        headline = "恭喜奪得同組冠軍！"
    elif is_first_round:
        headline = "完成你的第一場！"
    elif birdies:
        headline = "漂亮的一場好球！"
    else:
        headline = "完成一場，記錄下來了！"

    # 下一個最接近達成的成就（把成就牆鉤子接進慶祝時刻）
    next_goal = None
    if all_rounds is not None:
        eng = compute_user_engagement(all_rounds, user)
        if eng and eng.get("next_goal"):
            ng = eng["next_goal"]
            next_goal = {
                "icon": ng["icon"],
                "name": ng["name"],
                "hint": ng["hint"],
                "progress": ng["progress"],
            }

    return {
        "player_name": p.get("name", ""),
        "total": total,
        "to_par": to_par,
        "headline": headline,
        "feats": feats[:6],
        "is_personal_best": is_personal_best,
        "next_goal": next_goal,
    }


def compute_user_engagement(rounds, user):
    """從使用者可見場次，計算成長儀表板所需的所有指標。"""
    if not user or getattr(user, "id", None) is None:
        return None

    today = date.today()
    entries = []
    has_birdie = has_eagle = has_clean_round = has_comeback = False
    wins = 0

    for r in rounds:
        p = get_player_in_round_for_user(r, user)
        if not p:
            continue
        rp = _round_par_total(r)
        d = _parse_date(r.get("date"))
        tp = _player_to_par(p, rp)
        entries.append({
            "date": d,
            "total": p.get("total", 0),
            "to_par": tp,
        })

        diffs = _hole_diffs(p, r.get("pars"))
        if diffs:
            if any(x <= -1 for x in diffs):
                has_birdie = True
            if any(x <= -2 for x in diffs):
                has_eagle = True
            if all(x <= 1 for x in diffs) and len(diffs) >= 18:
                has_clean_round = True

        f = p.get("front_to_par")
        b = p.get("back_to_par")
        if isinstance(f, int) and isinstance(b, int) and b <= f - 3:
            has_comeback = True

        players = r.get("players") or []
        if len(players) > 1:
            champ = min(players, key=lambda x: x.get("total", 999))
            if champ is p or champ.get("name") == p.get("name"):
                wins += 1

    if not entries:
        return None

    total_rounds = len(entries)
    best_entry = min(entries, key=lambda e: e["total"])
    best_to_par = best_entry["to_par"]
    best_total = best_entry["total"]

    # —— 連續週數（損失厭惡） ——
    played_weeks = sorted({_week_index(e["date"]) for e in entries if e["date"]})
    streak_weeks = 0
    streak_status = "broken"
    last_played = max((e["date"] for e in entries if e["date"]), default=None)
    days_since = (today - last_played).days if last_played else None

    if played_weeks:
        cur_week = _week_index(today)
        most_recent = played_weeks[-1]
        # 從最近一個有出場的週往前數連續週
        streak_weeks = 1
        for i in range(len(played_weeks) - 1, 0, -1):
            if played_weeks[i] - played_weeks[i - 1] == 1:
                streak_weeks += 1
            else:
                break
        if most_recent == cur_week:
            streak_status = "active"
        elif most_recent == cur_week - 1:
            streak_status = "at_risk"
        else:
            streak_status = "broken"
            streak_weeks = 0

    # —— 本月場次目標（稀缺） ——
    month_rounds = sum(
        1 for e in entries
        if e["date"] and e["date"].year == today.year and e["date"].month == today.month
    )
    # 當月剩餘天數
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    days_left_in_month = (next_month - today).days
    month_goal_pct = max(0, min(100, int(month_rounds / _MONTHLY_GOAL * 100)))

    # —— 等級／身份 ——
    cap, level, title, icon = _level_for(best_to_par)
    level_pct, level_remaining = _level_progress(best_to_par, level)
    next_title = None
    if level < _MAX_LEVEL:
        ordered = sorted(_LEVELS, key=lambda x: x[1])
        nxt = next((x for x in ordered if x[1] == level + 1), None)
        next_title = nxt[2] if nxt else None

    # —— 下一個里程碑（場次） ——
    next_milestone = next((m for m in _ROUND_MILESTONES if m > total_rounds), None)

    stats = {
        "total_rounds": total_rounds,
        "best_to_par": best_to_par,
        "has_birdie": has_birdie,
        "has_eagle": has_eagle,
        "has_clean_round": has_clean_round,
        "has_comeback": has_comeback,
        "broke_threshold": best_to_par is not None and best_to_par <= 10,
        "wins": wins,
        "streak_weeks": streak_weeks,
    }
    achievements = _build_achievements(stats)
    earned = [a for a in achievements if a["earned"]]
    locked = [a for a in achievements if not a["earned"]]
    # 「最接近達成」的下一個目標（目標漸進效應）
    next_goal = max(locked, key=lambda a: a["progress"]) if locked else None

    return {
        "total_rounds": total_rounds,
        "level": level,
        "level_title": title,
        "level_icon": icon,
        "level_pct": level_pct,
        "level_remaining": level_remaining,
        "next_title": next_title,
        "is_max_level": level >= _MAX_LEVEL,
        "best_total": best_total,
        "best_to_par": best_to_par,
        "streak_weeks": streak_weeks,
        "streak_status": streak_status,
        "days_since_last": days_since,
        "month_rounds": month_rounds,
        "month_goal": _MONTHLY_GOAL,
        "month_goal_pct": month_goal_pct,
        "days_left_in_month": days_left_in_month,
        "next_milestone": next_milestone,
        "achievements": achievements,
        "earned_count": len(earned),
        "total_achievements": len(achievements),
        "next_goal": next_goal,
        "wins": wins,
    }
