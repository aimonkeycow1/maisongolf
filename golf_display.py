# 終端機「美工」：顏色與版面（Mac / Linux 終端機適用）

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BLUE = "\033[94m"
WHITE = "\033[97m"
BG_GREEN = "\033[42m\033[30m"
BG_BLUE = "\033[44m\033[97m"

def style(text, *codes):
    return "".join(codes) + str(text) + RESET

def print_banner():
    line = "═" * 52
    print()
    print(style(line, CYAN))
    print(style("     ⛳  滘西洲高爾夫球場 · 南場  ⛳", BOLD, CYAN))
    print(style("     Kau Sai Chau South Course", DIM, CYAN))
    print(style("     Par 69  ·  白梯 5906 碼", CYAN))
    print(style(line, CYAN))
    print()

def print_menu_box(title, items):
    width = 44
    print(style("┌" + "─" * width + "┐", BLUE))
    print(style(f"│ {title:^{width - 2}} │", BOLD, BLUE))
    print(style("├" + "─" * width + "┤", BLUE))
    for item in items:
        print(style(f"│  {item:<{width - 4}}│", WHITE))
    print(style("└" + "─" * width + "┘", BLUE))
    print()

def print_title(text):
    print(style(f"\n▎ {text}", BOLD, CYAN))

def print_success(text):
    print(style(f"✅ {text}", GREEN))

def print_warning(text):
    print(style(f"⚠️  {text}", YELLOW))

def print_hole_box(hole, par, yard, hcp):
    print(style(f"\n┏━━ 第 {hole:2d} 洞 ━━", BOLD, CYAN), end="")
    print(style(f" Par {par} ", BG_BLUE, BOLD), end="")
    print(style(f" {yard}碼 ", CYAN), end="")
    print(style(f" 差點 {hcp} ━━┓", CYAN))

def score_style(diff, name):
    if diff <= -1:
        return style(name, BOLD, GREEN)
    if diff == 0:
        return style(name, BOLD, WHITE)
    if diff == 1:
        return style(name, YELLOW)
    return style(name, RED)

def rank_medal(rank):
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    return medals.get(rank, f"{rank}.")

def print_leaderboard(ranked_players):
    print_title("今日成績排名")
    print(style("─" * 55, DIM))
    print(style(f"{'':3} {'球員':<10} {'總桿':>5} {'+/-':>6}  {'前九':>3}/{'後九':<3}", BOLD))
    print(style("─" * 55, DIM))
    for rank, p in enumerate(ranked_players, start=1):
        medal = rank_medal(rank)
        to_par = p["to_par"]
        tp = f"+{to_par}" if to_par > 0 else (str(to_par) if to_par < 0 else "E")
        line = f"{medal:3} {p['name']:<10} {p['total']:5d} {tp:>6}  {p['front9']:3d}/{p['back9']:<3d}"
        if rank == 1:
            print(style(line, BOLD, GREEN))
        else:
            print(line)
    print(style("─" * 55, DIM))

def print_player_card(name, stats):
    print()
    print(style(f"  ╔══ {name} ══╗", BOLD, GREEN if stats["to_par"] <= 10 else CYAN))
    print(style(f"{'洞':>4} {'Par':>4} {'桿':>4} {'+/−':>5}  成績", DIM))
    print(style("  " + "─" * 48, DIM))
    for h in stats["hole_results"]:
        d = h["diff"]
        sign = f"+{d}" if d > 0 else str(d)
        result = score_style(d, h["name"])
        print(f"  {h['hole']:4d} {h['par']:4d} {h['score']:4d} {sign:>5}  {result}")
    print(style("  " + "─" * 48, DIM))
    tp = stats["to_par"]
    total_str = f"+{tp}" if tp > 0 else ("E" if tp == 0 else str(tp))
    print(
        f"  前九 {stats['front9']}  後九 {stats['back9']}  "
        + style(f"總桿 {stats['total']} ({total_str})", BOLD, CYAN)
    )
    print(
        style(
            f"  鳥擊+ {stats['birdies']} · Par {stats['pars']} · "
            f"柏忌 {stats['bogeys']} · 雙柏忌+ {stats['double_plus']}",
            DIM,
        )
    )
