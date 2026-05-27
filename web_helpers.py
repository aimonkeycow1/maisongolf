"""網頁版用的資料整理（不印終端機）"""

from course_data import PARS, YARDAGES_WHITE, HANDICAP, PAR_TOTAL as DEFAULT_PAR_TOTAL
from golf_utils import to_par_str


def _round_pars(r):
    """優先使用場次儲存的 pars，否則用預設球場"""
    if r.get("pars") and len(r["pars"]) == 18:
        return r["pars"]
    return PARS


def _round_yardages(r):
    if r.get("yardages") and len(r.get("yardages", [])) == 18:
        return r["yardages"]
    return YARDAGES_WHITE

def get_round_by_id(rounds, round_id):
    for r in rounds:
        if r["id"] == round_id:
            return r
    return None


def user_owns_round(round_dict, user) -> bool:
    """判斷場次是否屬於目前登入使用者（委派 round_storage）"""
    from round_storage import round_belongs_to_user_account
    return round_belongs_to_user_account(round_dict, user)


def filter_rounds_for_user(rounds, user):
    from round_storage import round_belongs_to_user_account
    return [r for r in rounds if round_belongs_to_user_account(r, user)]


def _player_to_par(player, round_par):
    if player.get("to_par") is not None:
        return player["to_par"]
    return player["total"] - round_par


def _round_par_total(r):
    return r.get("par_total") or DEFAULT_PAR_TOTAL


def get_global_round_stats(rounds):
    """全站統計摘要（統計頁卡片與趨勢圖）"""
    if not rounds:
        return None

    entries = []
    for r in rounds:
        rp = _round_par_total(r)
        for p in r["players"]:
            entries.append({
                "total": p["total"],
                "to_par": _player_to_par(p, rp),
                "date": r.get("date", ""),
                "time": r.get("time", ""),
                "course": r.get("course", ""),
                "player": p.get("name", ""),
                "round_id": r.get("id", ""),
            })

    totals = [e["total"] for e in entries]
    to_pars = [e["to_par"] for e in entries]
    avg_to_par_val = sum(to_pars) / len(to_pars)

    best = min(entries, key=lambda e: e["total"])
    worst = max(entries, key=lambda e: e["total"])

    sorted_rounds = sorted(rounds, key=lambda r: (r.get("date", ""), r.get("time", "")))
    recent = []
    for r in sorted_rounds[-5:]:
        rp = _round_par_total(r)
        champ = min(r["players"], key=lambda x: x["total"])
        tp = _player_to_par(champ, rp)
        date = r.get("date", "")
        recent.append({
            "date": date,
            "label": date[5:] if len(date) >= 10 else date,
            "to_par": tp,
            "to_par_label": to_par_str(tp),
            "total": champ["total"],
            "course": r.get("course", ""),
            "player": champ.get("name", ""),
        })

    trend_max = max((abs(item["to_par"]) for item in recent), default=1)
    if trend_max < 1:
        trend_max = 1

    return {
        "total_rounds": len(rounds),
        "player_rounds": len(entries),
        "avg_score": round(sum(totals) / len(totals), 1),
        "avg_to_par": to_par_str(round(avg_to_par_val)),
        "avg_to_par_num": round(avg_to_par_val, 1),
        "best": best,
        "worst": worst,
        "recent_trend": recent,
        "trend_max": trend_max,
    }

def get_player_stats_table(rounds):
    players = {}
    for r in rounds:
        for p in r["players"]:
            name = p["name"]
            if name not in players:
                players[name] = {"totals": [], "to_pars": [], "wins": 0}
            players[name]["totals"].append(p["total"])
            players[name]["to_pars"].append(p["to_par"])
            if min(r["players"], key=lambda x: x["total"])["name"] == name:
                players[name]["wins"] += 1

    rows = []
    for name, data in players.items():
        n = len(data["totals"])
        rows.append({
            "name": name,
            "rounds": n,
            "wins": data["wins"],
            "avg_total": round(sum(data["totals"]) / n, 1),
            "best_total": min(data["totals"]),
            "avg_to_par": to_par_str(round(sum(data["to_pars"]) / n)),
        })
    rows.sort(key=lambda x: x["avg_total"])
    return rows

def get_hardest_holes(rounds, top_n=5):
    hole_diffs = [[] for _ in range(18)]
    hole_pars = list(PARS)
    hole_yards = list(YARDAGES_WHITE)

    for r in rounds:
        rp = _round_pars(r)
        ry = _round_yardages(r)
        hole_pars = rp
        hole_yards = ry
        for p in r["players"]:
            if p.get("hole_results") and len(p["hole_results"]) == 18:
                for h in p["hole_results"]:
                    i = h["hole"] - 1
                    hole_diffs[i].append(h["diff"])
            else:
                for i, score in enumerate(p["scores"]):
                    hole_diffs[i].append(score - rp[i])

    hole_avg = []
    for i in range(18):
        if hole_diffs[i]:
            avg = sum(hole_diffs[i]) / len(hole_diffs[i])
            hole_avg.append({
                "hole": i + 1,
                "par": hole_pars[i],
                "yard": hole_yards[i] if i < len(hole_yards) else 0,
                "hcp": HANDICAP[i],
                "avg_diff": round(avg, 1),
                "samples": len(hole_diffs[i]),
            })
    hole_avg.sort(key=lambda x: x["avg_diff"], reverse=True)
    return hole_avg[:top_n]
