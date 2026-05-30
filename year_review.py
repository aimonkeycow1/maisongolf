"""D3 — 年度回顧引擎 (Year in Review)"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime


def compute_year_review(rounds: list[dict], user, year: int | None = None) -> dict | None:
    target_year = year or datetime.utcnow().year
    username = getattr(user, "username", "") or ""

    def _my_player(r):
        for p in r.get("players") or []:
            if (p.get("name") or "").strip() == username.strip():
                return p
        return None

    yr_rounds = [
        r for r in rounds
        if (r.get("date") or "").startswith(str(target_year))
        and _my_player(r) is not None
    ]

    if not yr_rounds:
        return {"year": target_year, "has_data": False, "total_rounds": 0}

    totals, to_pars, courses, months = [], [], [], []
    eagles = birdies = pars_count = bogeys = doubles = 0
    best_round = worst_round = None
    wins = 0

    for r in yr_rounds:
        p = _my_player(r)
        if not p:
            continue
        total = p.get("total")
        par_total = r.get("par_total") or 72
        if total:
            totals.append(total)
            to_pars.append(total - par_total)
            if best_round is None or total < best_round["total"]:
                best_round = {"total": total, "date": r.get("date"), "course": r.get("course", ""), "id": r.get("id")}
            if worst_round is None or total > worst_round["total"]:
                worst_round = {"total": total, "date": r.get("date"), "course": r.get("course", ""), "id": r.get("id")}

        course = r.get("course") or r.get("course_id") or "未知球場"
        courses.append(course)

        date = r.get("date", "")
        if len(date) >= 7:
            months.append(date[:7])

        # 洞分布
        scores = p.get("scores") or []
        pars = r.get("pars") or ([4] * 18)
        for hi, s in enumerate(scores):
            if not isinstance(s, int) or s < 1:
                continue
            par = pars[hi] if hi < len(pars) else 4
            diff = s - par
            if diff <= -2:
                eagles += 1
            elif diff == -1:
                birdies += 1
            elif diff == 0:
                pars_count += 1
            elif diff == 1:
                bogeys += 1
            else:
                doubles += 1

        # 冠軍？
        players = r.get("players") or []
        if players:
            best_in_round = min(players, key=lambda x: x.get("total") or 999)
            if (best_in_round.get("name") or "").strip() == username.strip():
                wins += 1

    total_rounds = len(yr_rounds)
    avg_total = round(sum(totals) / len(totals), 1) if totals else None
    avg_to_par = round(sum(to_pars) / len(to_pars), 1) if to_pars else None

    # 月份分布
    month_counts = Counter(months)
    month_data = []
    for m in range(1, 13):
        key = f"{target_year}-{m:02d}"
        month_data.append({"month": m, "label": f"{m}月", "count": month_counts.get(key, 0)})
    most_active_month = max(month_data, key=lambda x: x["count"]) if month_data else None

    # 最愛球場
    course_counts = Counter(courses)
    fav_course = course_counts.most_common(1)[0] if course_counts else None

    # 進步指標（首半年 vs 後半年）
    first_half = [r for r in yr_rounds if (r.get("date") or "")[:7] <= f"{target_year}-06"]
    second_half = [r for r in yr_rounds if (r.get("date") or "")[:7] >= f"{target_year}-07"]

    def _avg_total(rlist):
        vals = [_my_player(r).get("total") for r in rlist if _my_player(r) and _my_player(r).get("total")]
        return round(sum(vals) / len(vals), 1) if vals else None

    h1_avg = _avg_total(first_half)
    h2_avg = _avg_total(second_half)
    half_year_delta = round(h2_avg - h1_avg, 1) if h1_avg and h2_avg else None

    total_holes = eagles + birdies + pars_count + bogeys + doubles

    # 最佳月份
    best_month_scores = defaultdict(list)
    for r in yr_rounds:
        p2 = _my_player(r)
        date = r.get("date", "")
        if p2 and p2.get("total") and len(date) >= 7:
            best_month_scores[date[:7]].append(p2.get("total"))
    best_month_avg = None
    best_month_label = None
    for m, vals in best_month_scores.items():
        avg = sum(vals) / len(vals)
        if best_month_avg is None or avg < best_month_avg:
            best_month_avg = round(avg, 1)
            best_month_label = m

    return {
        "year": target_year,
        "has_data": True,
        "total_rounds": total_rounds,
        "total_holes": total_holes,
        "avg_total": avg_total,
        "avg_to_par": avg_to_par,
        "best_round": best_round,
        "worst_round": worst_round,
        "wins": wins,
        "eagles": eagles,
        "birdies": birdies,
        "pars": pars_count,
        "bogeys": bogeys,
        "doubles": doubles,
        "month_data": month_data,
        "most_active_month": most_active_month,
        "fav_course": fav_course,
        "h1_avg": h1_avg,
        "h2_avg": h2_avg,
        "half_year_delta": half_year_delta,
        "half_improved": half_year_delta is not None and half_year_delta < 0,
        "best_month_avg": best_month_avg,
        "best_month_label": best_month_label,
        "courses_visited": len(set(courses)),
    }
