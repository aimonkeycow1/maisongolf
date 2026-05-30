"""
B1 — 弱點洞自動偵測
對每位用戶分析 18 洞的歷史平均表現，找出強/弱洞與規律。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Optional


def _player_in_round(r: dict, username: str) -> Optional[dict]:
    for p in r.get("players") or []:
        if (p.get("name") or "").strip() == username.strip():
            return p
    return None


def compute_hole_analysis(rounds: list[dict], user) -> Optional[dict]:
    """
    逐洞分析：返回每洞歷史統計 + 弱洞/強洞列表。

    返回格式:
    {
      "holes": [
        {"hole": 1, "par": 4, "avg": 4.8, "avg_to_par": +0.8, "count": N,
         "best": 3, "worst": 8, "class": "weak|strong|neutral", "eagle": %, "birdie": %, ...},
        ...
      ],
      "weak_holes": [洞號, ...],      # avg_to_par > +0.7
      "strong_holes": [洞號, ...],    # avg_to_par < -0.2
      "patterns": [...],              # 文字規律描述
      "total_holes_played": N,
      "has_data": bool,
    }
    """
    username = getattr(user, "username", "") or ""
    if not username:
        return None

    # 逐洞收集資料：hole_data[0..17] = list of (score, par)
    hole_data: list[list[tuple[int, int]]] = [[] for _ in range(18)]
    par_by_hole: list[int] = [4] * 18

    for r in rounds:
        p = _player_in_round(r, username)
        if not p:
            continue
        scores = p.get("scores") or p.get("hole_scores") or []
        pars = r.get("pars") or ([4] * 18)
        if len(scores) < 9:
            continue
        for hi in range(min(18, len(scores))):
            s = scores[hi]
            par = pars[hi] if hi < len(pars) else 4
            if isinstance(s, int) and 1 <= s <= 20:
                hole_data[hi].append((s, par))
                par_by_hole[hi] = par

    total_holes_played = sum(len(h) for h in hole_data)
    if total_holes_played < 18:
        return {"has_data": False, "total_holes_played": total_holes_played}

    holes_out = []
    for hi, entries in enumerate(hole_data):
        if not entries:
            holes_out.append({
                "hole": hi + 1, "par": par_by_hole[hi],
                "avg": None, "avg_to_par": None, "count": 0,
                "best": None, "worst": None,
                "eagle_pct": 0, "birdie_pct": 0, "par_pct": 0,
                "bogey_pct": 0, "double_pct": 0,
                "class": "neutral",
            })
            continue

        scores = [s for s, _ in entries]
        par = entries[0][1]
        avg = round(sum(scores) / len(scores), 2)
        avg_to_par = round(avg - par, 2)
        best = min(scores)
        worst = max(scores)
        n = len(scores)

        eagle_pct  = round(100 * sum(1 for s in scores if s <= par - 2) / n)
        birdie_pct = round(100 * sum(1 for s in scores if s == par - 1) / n)
        par_pct    = round(100 * sum(1 for s in scores if s == par) / n)
        bogey_pct  = round(100 * sum(1 for s in scores if s == par + 1) / n)
        double_pct = round(100 * sum(1 for s in scores if s >= par + 2) / n)

        if avg_to_par >= 0.8:
            cls = "weak"
        elif avg_to_par <= -0.2:
            cls = "strong"
        else:
            cls = "neutral"

        holes_out.append({
            "hole": hi + 1,
            "par": par,
            "avg": avg,
            "avg_to_par": avg_to_par,
            "count": n,
            "best": best,
            "worst": worst,
            "eagle_pct": eagle_pct,
            "birdie_pct": birdie_pct,
            "par_pct": par_pct,
            "bogey_pct": bogey_pct,
            "double_pct": double_pct,
            "class": cls,
        })

    weak_holes  = [h["hole"] for h in holes_out if h["class"] == "weak" and h["count"] > 0]
    strong_holes = [h["hole"] for h in holes_out if h["class"] == "strong" and h["count"] > 0]

    # 規律偵測
    patterns = []
    par3_diffs = [h["avg_to_par"] for h in holes_out if h["par"] == 3 and h["avg_to_par"] is not None]
    par5_diffs = [h["avg_to_par"] for h in holes_out if h["par"] == 5 and h["avg_to_par"] is not None]
    par4_diffs = [h["avg_to_par"] for h in holes_out if h["par"] == 4 and h["avg_to_par"] is not None]

    if par3_diffs and sum(par3_diffs)/len(par3_diffs) > 0.7:
        patterns.append({"icon": "🎯", "text": "短洞（Par 3）是你目前最大失分點，建議加強開球準確性"})
    elif par3_diffs and sum(par3_diffs)/len(par3_diffs) < 0:
        patterns.append({"icon": "💚", "text": "短洞（Par 3）是你的強項，平均低於標準桿"})

    if par5_diffs and sum(par5_diffs)/len(par5_diffs) > 0.8:
        patterns.append({"icon": "🌊", "text": "長洞（Par 5）失分較多，三桿上果嶺是關鍵"})
    elif par5_diffs and sum(par5_diffs)/len(par5_diffs) < 0.1:
        patterns.append({"icon": "💪", "text": "長洞（Par 5）表現穩定，善用你的距離優勢"})

    if par4_diffs and sum(par4_diffs)/len(par4_diffs) > 0.9:
        patterns.append({"icon": "⚠️", "text": "標準洞（Par 4）平均超標超過 +0.9，第二桿上果嶺是突破口"})

    # 後九 vs 前九比較
    front9 = [h["avg_to_par"] for h in holes_out[:9] if h["avg_to_par"] is not None]
    back9  = [h["avg_to_par"] for h in holes_out[9:] if h["avg_to_par"] is not None]
    if front9 and back9:
        f_avg = sum(front9)/len(front9)
        b_avg = sum(back9)/len(back9)
        if b_avg - f_avg > 0.4:
            patterns.append({"icon": "😓", "text": "後九（10-18 洞）明顯比前九差，可能是體力或專注力下滑"})
        elif f_avg - b_avg > 0.4:
            patterns.append({"icon": "🔥", "text": "你的後九表現反而更好 — 暖身後愈打愈準"})

    return {
        "has_data": True,
        "holes": holes_out,
        "weak_holes": weak_holes[:5],       # 最多顯示 5 個
        "strong_holes": strong_holes[:3],
        "patterns": patterns,
        "total_holes_played": total_holes_played,
    }


def compute_course_comparison(rounds: list[dict], user, course_id: str) -> Optional[dict]:
    """
    B3 — 同球場跨場次比較：返回最近兩次該球場的成績差異。
    """
    username = getattr(user, "username", "") or ""
    course_rounds = [
        r for r in sorted(rounds, key=lambda x: x.get("date", ""), reverse=True)
        if (r.get("course_id") or r.get("course") or "") and
           _player_in_round(r, username) is not None
    ]
    # 篩選同一 course_id 或 course name 的場次
    matching = []
    for r in course_rounds:
        cid = r.get("course_id") or ""
        cname = r.get("course") or ""
        if cid == course_id or course_id in cname or cname in course_id:
            p = _player_in_round(r, username)
            if p and p.get("total"):
                matching.append((r, p))

    if len(matching) < 2:
        return None

    current_r, current_p = matching[0]
    prev_r, prev_p = matching[1]

    curr_total = current_p.get("total", 0)
    prev_total = prev_p.get("total", 0)
    delta = curr_total - prev_total

    curr_par = current_r.get("par_total") or 72
    prev_par = prev_r.get("par_total") or 72
    curr_to_par = curr_total - curr_par
    prev_to_par = prev_total - prev_par

    # 逐洞比較
    curr_scores = current_p.get("scores") or []
    prev_scores = prev_p.get("scores") or []
    pars = current_r.get("pars") or ([4] * 18)

    hole_diffs = []
    for hi in range(min(len(curr_scores), len(prev_scores), 18)):
        cs, ps = curr_scores[hi], prev_scores[hi]
        if isinstance(cs, int) and isinstance(ps, int) and 1 <= cs <= 20 and 1 <= ps <= 20:
            hole_diffs.append({
                "hole": hi + 1,
                "par": pars[hi] if hi < len(pars) else 4,
                "current": cs,
                "prev": ps,
                "diff": cs - ps,   # 負 = 進步，正 = 退步
            })

    improved = [h for h in hole_diffs if h["diff"] < 0]
    declined = [h for h in hole_diffs if h["diff"] > 0]

    return {
        "course": current_r.get("course") or "該球場",
        "current_date": current_r.get("date", ""),
        "prev_date": prev_r.get("date", ""),
        "curr_total": curr_total,
        "prev_total": prev_total,
        "delta": delta,
        "improved": delta < 0,
        "curr_to_par": curr_to_par,
        "prev_to_par": prev_to_par,
        "hole_diffs": hole_diffs,
        "improved_holes": improved,
        "declined_holes": declined,
    }
