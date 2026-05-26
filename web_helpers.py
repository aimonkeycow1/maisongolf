"""網頁版用的資料整理（不印終端機）"""

from course_data import PARS, YARDAGES_WHITE, HANDICAP
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
