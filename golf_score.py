# === 滘西洲南場 高爾夫記分器（單人 / 多人存檔）===

from course_data import (
    COURSE_NAME,
    PARS,
    YARDAGES_WHITE,
    HANDICAP,
    PAR_TOTAL,
    YARDAGE_TOTAL,
)
from golf_utils import score_name, calc_player_stats, ask_score
from round_storage import load_rounds, add_round
from golf_stats import show_analytics_menu
from golf_html import export_round_html, open_in_browser
from golf_display import (
    print_banner,
    print_menu_box,
    print_title,
    print_success,
    print_warning,
    print_hole_box,
    score_style,
    print_leaderboard,
    print_player_card,
    style,
    DIM,
)

def print_hole_header(hole):
    par = PARS[hole - 1]
    yard = YARDAGES_WHITE[hole - 1]
    hcp = HANDICAP[hole - 1]
    print_hole_box(hole, par, yard, hcp)

def play_single():
    print_title(f"單人記分 · {COURSE_NAME}")
    print(style(f"白梯 · {YARDAGE_TOTAL} 碼 · Par {PAR_TOTAL}\n", DIM))
    name = input(style("你的名字： ", DIM)) or "球員"
    scores = []
    for hole in range(1, 19):
        print_hole_header(hole)
        score = ask_score(style("你的桿數: ", DIM))
        diff = score - PARS[hole - 1]
        print(f"    → {score_style(diff, score_name(diff))}")
        scores.append(score)
    stats = calc_player_stats(scores)
    print_player_card(name, stats)
    if input("\n要存入歷史紀錄嗎？(y/n) ").strip().lower() == "y":
        note = input("備註（可留空）: ")
        rid = add_round([{"name": name, **stats}], note)
        print_success(f"已存檔！編號 {rid}")

def play_group():
    print_title(f"多人同組記分 · {COURSE_NAME}")
    print(style(f"白梯 · Par {PAR_TOTAL}\n", DIM))

    while True:
        try:
            n = int(input("今天幾位球友？ "))
            if 1 <= n <= 8:
                break
            print_warning("請輸入 1～8 之間的數字")
        except ValueError:
            print_warning("請輸入數字！")

    names = []
    for i in range(n):
        name = input(f"第 {i + 1} 位球友名字： ").strip()
        names.append(name if name else f"球友{i + 1}")

    all_scores = {name: [] for name in names}

    for hole in range(1, 19):
        print_hole_header(hole)
        par = PARS[hole - 1]
        for name in names:
            score = ask_score(f"  {style(name, DIM)} (Par {par}): ")
            all_scores[name].append(score)
            diff = score - par
            print(f"      → {score_style(diff, score_name(diff))}")

    players_stats = []
    for name in names:
        stats = calc_player_stats(all_scores[name])
        stats["name"] = name
        players_stats.append(stats)

    ranked = sorted(players_stats, key=lambda p: p["total"])
    print_leaderboard(ranked)

    for p in ranked:
        print_player_card(p["name"], p)

    note = input("\n這場球備註（可留空）: ")
    rid = add_round(players_stats, note)
    print_success("整組成績已存入 rounds.json")
    record = load_rounds()[-1]
    print(style(f"   編號：{rid}", DIM))
    print(style(f"   日期：{record['date']} {record['time']}", DIM))
    print(style(f"   球員：{', '.join(p['name'] for p in players_stats)}", DIM))

    if input("\n要順便產生 HTML 精美記分卡嗎？(y/n) ").strip().lower() == "y":
        path = export_round_html(record)
        print_success(f"已產生：{path}")
        open_in_browser(path)

def show_history():
    rounds = load_rounds()
    if not rounds:
        print_warning("還沒有任何存檔。請先使用「多人同組記分」。")
        return

    print_title("歷史紀錄")
    for i, r in enumerate(rounds, start=1):
        names = "、".join(p["name"] for p in r["players"])
        best = min(r["players"], key=lambda p: p["total"])
        note = f" · {r['note']}" if r.get("note") else ""
        print(style(f"{i}. [{r['id']}] {r['date']} {r['time']}  {names}", DIM))
        print(f"   冠軍 {style(best['name'], DIM)} {best['total']} 桿{note}")

    try:
        pick = int(input("\n要看第幾場詳細？（0=返回） "))
        if pick == 0:
            return
        if 1 <= pick <= len(rounds):
            r = rounds[pick - 1]
            print_title(f"{r['course']} · {r['date']} {r['time']}")
            if r.get("note"):
                print(f"備註：{r['note']}")
            ranked = sorted(r["players"], key=lambda p: p["total"])
            print_leaderboard(ranked)
            for p in ranked:
                print_player_card(p["name"], p)
            if input("\n匯出這場 HTML 記分卡？(y/n) ").strip().lower() == "y":
                path = export_round_html(r)
                print_success(f"已產生：{path}")
                open_in_browser(path)
        else:
            print_warning("編號超出範圍。")
    except ValueError:
        pass

def export_latest_html():
    rounds = load_rounds()
    if not rounds:
        print_warning("還沒有存檔。")
        return
    path = export_round_html(rounds[-1])
    print_success("HTML 記分卡已產生！")
    print(style(f"   檔案：{path}", DIM))
    if open_in_browser(path):
        print_success("已自動用瀏覽器打開（若沒跳出，請看下方路徑手動雙擊）")
    else:
        print_warning("無法自動開啟，請在 Finder 雙擊該 HTML 檔。")

def main_menu():
    while True:
        print_banner()
        print_menu_box("高爾夫記分器", [
            "1. 單人記分",
            "2. 多人同組記分並存檔",
            "3. 查看歷史紀錄",
            "4. 球員統計與難洞分析",
            "5. 匯出 HTML 精美記分卡 🎨",
            "0. 離開",
        ])
        choice = input(style("請選擇 (0～5)： ", DIM)).strip()

        if choice == "1":
            play_single()
        elif choice == "2":
            play_group()
        elif choice == "3":
            show_history()
        elif choice == "4":
            show_analytics_menu()
        elif choice == "5":
            export_latest_html()
        elif choice == "0":
            print_success("再見，祝你下場打出好成績！⛳")
            break
        else:
            print_warning("沒有這個選項。")

if __name__ == "__main__":
    main_menu()
