from course_data import PARS, PAR_TOTAL, YARDAGES_WHITE, HANDICAP
from golf_utils import to_par_str
from round_storage import load_rounds
from golf_display import print_title, print_success, style, DIM, GREEN, CYAN, YELLOW
from golf_html import export_round_html, open_in_browser

def show_player_stats(rounds):
    """依所有存檔，統計每位球員的成績"""
    players = {}

    for r in rounds:
        for p in r["players"]:
            name = p["name"]
            if name not in players:
                players[name] = {
                    "totals": [],
                    "to_pars": [],
                    "dates": [],
                    "wins": 0,
                }
            players[name]["totals"].append(p["total"])
            players[name]["to_pars"].append(p["to_par"])
            players[name]["dates"].append(r["date"])

            best = min(r["players"], key=lambda x: x["total"])
            if best["name"] == name:
                players[name]["wins"] += 1

    print_title("球員歷史統計")
    print(style(f"{'球員':<8} {'場次':>4} {'冠軍':>4} {'平均桿':>6} {'最佳':>4} {'平均+/-':>8}", DIM))
    print(style("-" * 60, DIM))

    rows = []
    for name, data in players.items():
        n = len(data["totals"])
        avg_total = sum(data["totals"]) / n
        avg_to_par = sum(data["to_pars"]) / n
        best_total = min(data["totals"])
        rows.append((avg_total, name, n, data["wins"], avg_total, best_total, avg_to_par))

    rows.sort()
    for i, (_, name, n, wins, avg_total, best_total, avg_to_par) in enumerate(rows):
        color = GREEN if i == 0 else ""
        line = (f"{name:<8} {n:>4} {wins:>4} {avg_total:>6.1f} {best_total:>4} "
                f"{to_par_str(round(avg_to_par)):>8}")
        print(style(line, color) if color else line)

    print(style("（場次越多，平均越能反映真實水準）", DIM))


def show_hardest_holes(rounds):
    """分析哪些洞平均最難打"""
    hole_diffs = [[] for _ in range(18)]

    for r in rounds:
        for p in r["players"]:
            for i, score in enumerate(p["scores"]):
                hole_diffs[i].append(score - PARS[i])

    print_title("球場難洞分析 TOP 5")
    print(style(f"{'排名':<4} {'洞':>3} {'Par':>4} {'碼':>5} {'差點':>4} {'平均+/-':>8} {'樣本':>4}", DIM))
    print(style("-" * 60, DIM))

    hole_avg = []
    for i in range(18):
        if hole_diffs[i]:
            avg = sum(hole_diffs[i]) / len(hole_diffs[i])
            hole_avg.append((avg, i))

    hole_avg.sort(reverse=True)

    for rank, (avg, i) in enumerate(hole_avg[:5], start=1):
        sign = f"+{avg:.1f}" if avg > 0 else f"{avg:.1f}"
        line = (f"{rank:<4} {i + 1:>3} {PARS[i]:>4} {YARDAGES_WHITE[i]:>5} "
                f"{HANDICAP[i]:>4} {sign:>8} {len(hole_diffs[i]):>4}")
        print(style(line, YELLOW if rank <= 3 else ""))

    print(style("（平均+/− 越高 = 這洞越常打超過 Par）", DIM))


def show_latest_round_summary(rounds):
    r = rounds[-1]
    print(f"\n最近一場：{r['date']} {r['time']}")
    if r.get("note"):
        print(f"備註：{r['note']}")
    ranked = sorted(r["players"], key=lambda p: p["total"])
    print("排名：", end="")
    print(" · ".join(f"{i}.{p['name']} {p['total']}桿" for i, p in enumerate(ranked, 1)))


def export_latest_round():
    rounds = load_rounds()
    if not rounds:
        print("\n沒有資料可匯出。")
        return

    r = rounds[-1]
    filename = f"成績_{r['id']}.txt"
    ranked = sorted(r["players"], key=lambda p: p["total"])

    lines = [
        f"{r['course']}",
        f"日期：{r['date']} {r['time']}",
        f"標準桿：Par {r['par_total']}（{r.get('tee', '白梯')}）",
    ]
    if r.get("note"):
        lines.append(f"備註：{r['note']}")
    lines.append("")
    lines.append("【排名】")
    for i, p in enumerate(ranked, start=1):
        lines.append(
            f"{i}. {p['name']}  總桿 {p['total']} ({to_par_str(p['to_par'])})  "
            f"前九 {p['front9']} / 後九 {p['back9']}"
        )
    lines.append("")
    lines.append("【逐洞成績】")

    for p in ranked:
        lines.append(f"\n{p['name']}:")
        for h in p["hole_results"]:
            sign = f"+{h['diff']}" if h["diff"] > 0 else str(h["diff"])
            lines.append(f"  第{h['hole']:2d}洞 Par{h['par']}  {h['score']}桿 ({sign}) {h['name']}")

    text = "\n".join(lines) + "\n"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)

    print_success(f"已匯出：{filename}")
    print(style("   可把這個檔案傳給朋友留存。", DIM))


def show_analytics_menu():
    rounds = load_rounds()
    if not rounds:
        print("\n還沒有任何存檔，請先記一場球。")
        return

    show_latest_round_summary(rounds)
    show_player_stats(rounds)
    show_hardest_holes(rounds)

    if input("\n要匯出最近一場文字檔給朋友嗎？(y/n) ").strip().lower() == "y":
        export_latest_round()
    if input("要匯出 HTML 精美記分卡嗎？(y/n) ").strip().lower() == "y":
        path = export_round_html(rounds[-1])
        print_success(f"已產生：{path}")
        open_in_browser(path)
