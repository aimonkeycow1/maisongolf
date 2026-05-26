# 匯出精美 HTML 記分卡（圖示、圖例、易懂版面）

import os
import subprocess
import sys

from course_data import PARS, YARDAGES_WHITE, PAR_FRONT, PAR_BACK, YARDAGE_TOTAL

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 南場真實照片（背景用，與 HTML 放同一資料夾）
HERO_PHOTO = "south_course_hole12.jpg"

FALLBACK_HERO = (
    "https://images.unsplash.com/photo-1587174482993-4eccc5aa6169"
    "?auto=format&fit=crop&w=1400&q=80"
)

def hero_background_url():
    path = os.path.join(SCRIPT_DIR, HERO_PHOTO)
    if os.path.isfile(path):
        return HERO_PHOTO
    return FALLBACK_HERO

def diff_class(diff):
    if diff <= -1:
        return "birdie"
    if diff == 0:
        return "par"
    if diff == 1:
        return "bogey"
    return "bad"

def diff_label_zh(diff, name):
    labels = {
        -3: "🦅 信天翁",
        -2: "🦅 老鷹",
        -1: "🐦 鳥擊",
        0: "✅ Par",
        1: "⚠️ 柏忌",
        2: "❌ 雙柏忌",
        3: "❌ 三柏忌",
    }
    if diff in labels:
        return labels[diff]
    if diff > 3:
        return f"❌ +{diff}"
    return name

def player_avatar(name):
    return name[0] if name else "?"

def build_legend_html():
    return """
    <section class="legend-box">
      <h2>📖 怎麼看懂這張記分卡？</h2>
      <div class="legend-grid">
        <div class="legend-item"><span class="swatch birdie"></span>
          <div><strong>綠色</strong><br>比標準桿少 · 鳥擊／老鷹</div></div>
        <div class="legend-item"><span class="swatch par"></span>
          <div><strong>灰色</strong><br>剛好 Par · 標準桿</div></div>
        <div class="legend-item"><span class="swatch bogey"></span>
          <div><strong>黃色</strong><br>比標準桿多 1 · 柏忌</div></div>
        <div class="legend-item"><span class="swatch bad"></span>
          <div><strong>紅色</strong><br>比標準桿多 2 以上</div></div>
      </div>
      <p class="legend-tip">💡 每格顯示：<b>洞號</b> → <b>你打的桿數</b> → <b>與 Par 差幾桿</b></p>
    </section>"""

def build_podium_html(ranked):
    cards = ""
    for rank, p in enumerate(ranked, start=1):
        medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"第{rank}名"
        tp = p["to_par"]
        tp_str = f"+{tp}" if tp > 0 else ("平標準桿 E" if tp == 0 else str(tp))
        rank_cls = f"rank-{rank}" if rank <= 3 else "rank-other"
        cards += f"""
        <div class="podium-card {rank_cls}">
          <div class="podium-medal">{medal}</div>
          <div class="avatar">{player_avatar(p['name'])}</div>
          <h3>{p['name']}</h3>
          <div class="big-number">{p['total']}</div>
          <div class="big-label">總桿數</div>
          <div class="to-par-chip">{tp_str}</div>
          <div class="mini-stats">
            <span>⛳ 前九 {p['front9']}</span>
            <span>⛳ 後九 {p['back9']}</span>
          </div>
        </div>"""
    return f'<section class="podium"><h2>🏆 今日排名（桿數越少越好）</h2><div class="podium-row">{cards}</div></section>'

def build_hole_bars_html(hole_results):
    """每洞相對 Par 的簡易長條圖"""
    bars = ""
    for h in hole_results:
        d = h["diff"]
        cls = diff_class(d)
        height = min(100, 20 + abs(d) * 18)
        if d < 0:
            height = min(100, 20 + abs(d) * 18)
        bars += f'<div class="bar {cls}" style="height:{height}%" title="第{h["hole"]}洞"></div>'
    return f'<div class="bar-chart" aria-label="18洞走勢">{bars}</div>'

def build_holes_html(hole_results):
    front = ""
    back = ""
    for h in hole_results:
        cls = diff_class(h["diff"])
        sign = f"+{h['diff']}" if h["diff"] > 0 else str(h["diff"])
        label = diff_label_zh(h["diff"], h["name"])
        yard = YARDAGES_WHITE[h["hole"] - 1]
        cell = f"""
        <div class="hole {cls}">
          <div class="hole-icon">⛳ 第 {h['hole']} 洞</div>
          <div class="hole-yard">{yard} 碼</div>
          <div class="hole-score">{h['score']}</div>
          <div class="hole-par-text">標準桿 Par {h['par']}</div>
          <div class="hole-diff">{sign} · {label}</div>
        </div>"""
        if h["hole"] <= 9:
            front += cell
        else:
            back += cell
    return f"""
    <div class="nine-block">
      <h4>🌅 前九洞（Out）· 標準桿 {PAR_FRONT}</h4>
      <div class="holes">{front}</div>
    </div>
    <div class="nine-block">
      <h4>🌇 後九洞（In）· 標準桿 {PAR_BACK}</h4>
      <div class="holes">{back}</div>
    </div>"""

def build_player_html(rank, p):
    medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"
    tp = p["to_par"]
    tp_str = f"+{tp}" if tp > 0 else ("E" if tp == 0 else str(tp))
    return f"""
    <section class="player-card" id="player-{rank}">
      <div class="player-top">
        <div class="player-id">
          <span class="medal-lg">{medal}</span>
          <div class="avatar-lg">{player_avatar(p['name'])}</div>
          <div>
            <h2>{p['name']}</h2>
            <p class="player-sub">完整 18 洞成績</p>
          </div>
        </div>
        <div class="score-panel">
          <div class="score-panel-item">
            <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='28' fill='%23fff' stroke='%232e7d32' stroke-width='3'/%3E%3Cpath d='M20 40 Q32 10 44 40' fill='none' stroke='%232e7d32' stroke-width='2'/%3E%3C/svg%3E" alt="" class="icon-golf" width="48" height="48">
            <span class="num">{p['total']}</span>
            <span class="lbl">總桿</span>
          </div>
          <div class="score-panel-item highlight">
            <span class="num">{tp_str}</span>
            <span class="lbl">比標準桿</span>
          </div>
        </div>
      </div>
      <div class="stat-chips">
        <span class="chip">🐦 鳥擊+ <b>{p['birdies']}</b></span>
        <span class="chip">✅ Par <b>{p['pars']}</b></span>
        <span class="chip">⚠️ 柏忌 <b>{p['bogeys']}</b></span>
        <span class="chip">❌ 雙柏忌+ <b>{p['double_plus']}</b></span>
        <span class="chip">🌅 前九 <b>{p['front9']}</b></span>
        <span class="chip">🌇 後九 <b>{p['back9']}</b></span>
      </div>
      <p class="chart-label">📊 走勢圖（格子越高 = 該洞相對 Par 落差越大）</p>
      {build_hole_bars_html(p['hole_results'])}
      {build_holes_html(p['hole_results'])}
    </section>"""

def export_round_html(round_data, filename=None):
    if filename is None:
        filename = f"記分卡_{round_data['id']}.html"

    ranked = sorted(round_data["players"], key=lambda p: p["total"])
    note = round_data.get("note", "")
    winner = ranked[0]
    hero_bg = hero_background_url()

    players_html = ""
    for rank, p in enumerate(ranked, start=1):
        players_html += build_player_html(rank, p)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{round_data['course']} · {round_data['date']}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
      background: #0a1f18;
      color: #f1f8f4;
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1000px; margin: 0 auto; padding: 0 16px 48px; }}

    .hero {{
      position: relative;
      border-radius: 0 0 28px 28px;
      overflow: hidden;
      margin: 0 -16px 28px;
      min-height: 280px;
      display: flex;
      align-items: flex-end;
    }}
    .hero-bg {{
      position: absolute; inset: 0;
      background: url('{hero_bg}') center/cover no-repeat;
    }}
    .hero-bg::after {{
      content: "";
      position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(8,30,22,0.95) 0%, rgba(8,30,22,0.4) 60%);
    }}
    .hero-content {{
      position: relative; z-index: 1;
      padding: 32px 24px 36px;
      width: 100%;
    }}
    .hero-badge {{
      display: inline-block;
      background: #2e7d32;
      color: #fff;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.85rem;
      margin-bottom: 12px;
    }}
    .hero h1 {{ font-size: clamp(1.4rem, 4vw, 2rem); margin-bottom: 6px; }}
    .hero .sub {{ opacity: 0.9; font-size: 1rem; }}
    .hero-meta {{
      display: flex; flex-wrap: wrap; gap: 10px;
      margin-top: 18px;
    }}
    .meta-pill {{
      background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.25);
      padding: 8px 14px;
      border-radius: 12px;
      font-size: 0.9rem;
    }}
    .winner-banner {{
      background: linear-gradient(90deg, #ffd54f, #ffb300);
      color: #1a1a1a;
      padding: 14px 20px;
      border-radius: 14px;
      margin-bottom: 24px;
      font-size: 1.05rem;
      font-weight: 600;
      text-align: center;
    }}

    .legend-box {{
      background: #fff;
      color: #1a1a1a;
      border-radius: 16px;
      padding: 22px;
      margin-bottom: 28px;
    }}
    .legend-box h2 {{ font-size: 1.15rem; margin-bottom: 16px; }}
    .legend-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 14px;
    }}
    .legend-item {{ display: flex; gap: 12px; align-items: center; font-size: 0.9rem; }}
    .swatch {{
      width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0;
    }}
    .swatch.birdie {{ background: #2e7d32; }}
    .swatch.par {{ background: #607d8b; }}
    .swatch.bogey {{ background: #ffca28; }}
    .swatch.bad {{ background: #e53935; }}
    .legend-tip {{ margin-top: 14px; font-size: 0.9rem; color: #555; }}

    .podium {{ margin-bottom: 32px; }}
    .podium h2 {{ text-align: center; margin-bottom: 20px; font-size: 1.2rem; }}
    .podium-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px;
    }}
    .podium-card {{
      background: rgba(255,255,255,0.08);
      border: 2px solid rgba(255,255,255,0.12);
      border-radius: 20px;
      padding: 20px 16px;
      text-align: center;
    }}
    .podium-card.rank-1 {{ border-color: #ffd54f; background: rgba(255,213,79,0.12); }}
    .podium-card.rank-2 {{ border-color: #b0bec5; }}
    .podium-card.rank-3 {{ border-color: #ffab91; }}
    .podium-medal {{ font-size: 2rem; }}
    .avatar {{
      width: 56px; height: 56px; line-height: 56px;
      background: #2e7d32; border-radius: 50%;
      font-size: 1.5rem; font-weight: bold;
      margin: 10px auto;
    }}
    .podium-card h3 {{ margin: 8px 0; font-size: 1.1rem; }}
    .big-number {{ font-size: 2.8rem; font-weight: 800; color: #a5d6a7; line-height: 1; }}
    .big-label {{ font-size: 0.85rem; opacity: 0.8; margin: 4px 0 10px; }}
    .to-par-chip {{
      display: inline-block;
      background: rgba(0,0,0,0.25);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.95rem;
    }}
    .mini-stats {{
      display: flex; justify-content: center; gap: 12px;
      margin-top: 12px; font-size: 0.8rem; opacity: 0.85;
    }}

    .player-card {{
      background: rgba(255,255,255,0.06);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 28px;
      border: 1px solid rgba(255,255,255,0.1);
    }}
    .player-top {{
      display: flex; flex-wrap: wrap;
      justify-content: space-between; align-items: center;
      gap: 16px; margin-bottom: 16px;
    }}
    .player-id {{ display: flex; align-items: center; gap: 14px; }}
    .medal-lg {{ font-size: 2rem; }}
    .avatar-lg {{
      width: 64px; height: 64px; line-height: 64px;
      text-align: center; background: #388e3c;
      border-radius: 50%; font-size: 1.8rem; font-weight: bold;
    }}
    .player-sub {{ opacity: 0.75; font-size: 0.9rem; }}
    .score-panel {{ display: flex; gap: 16px; }}
    .score-panel-item {{
      text-align: center; padding: 12px 20px;
      background: rgba(0,0,0,0.2);
      border-radius: 14px; min-width: 100px;
    }}
    .score-panel-item.highlight {{ background: rgba(46,125,50,0.4); }}
    .score-panel-item .num {{ display: block; font-size: 2rem; font-weight: 800; }}
    .score-panel-item .lbl {{ font-size: 0.8rem; opacity: 0.85; }}
    .icon-golf {{ display: block; margin: 0 auto 4px; }}

    .stat-chips {{
      display: flex; flex-wrap: wrap; gap: 8px;
      margin-bottom: 16px;
    }}
    .chip {{
      background: rgba(255,255,255,0.1);
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.85rem;
    }}
    .chart-label {{ font-size: 0.9rem; opacity: 0.85; margin-bottom: 8px; }}
    .bar-chart {{
      display: flex; align-items: flex-end; gap: 4px;
      height: 80px; margin-bottom: 20px;
      padding: 8px; background: rgba(0,0,0,0.2);
      border-radius: 12px;
    }}
    .bar {{ flex: 1; border-radius: 4px 4px 0 0; min-height: 8px; }}
    .bar.birdie {{ background: #66bb6a; }}
    .bar.par {{ background: #90a4ae; }}
    .bar.bogey {{ background: #ffca28; }}
    .bar.bad {{ background: #ef5350; }}

    .nine-block {{ margin-bottom: 20px; }}
    .nine-block h4 {{
      font-size: 1rem; margin-bottom: 12px;
      padding: 8px 12px;
      background: rgba(46,125,50,0.35);
      border-radius: 8px;
    }}
    .holes {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
      gap: 10px;
    }}
    .hole {{
      border-radius: 12px;
      padding: 12px 8px;
      text-align: center;
      border: 2px solid rgba(255,255,255,0.15);
    }}
    .hole-icon {{ font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; }}
    .hole-yard {{ font-size: 0.7rem; opacity: 0.85; }}
    .hole-score {{ font-size: 2rem; font-weight: 800; margin: 6px 0; }}
    .hole-par-text {{ font-size: 0.75rem; opacity: 0.9; }}
    .hole-diff {{ font-size: 0.8rem; margin-top: 6px; font-weight: 600; }}
    .hole.birdie {{ background: #1b5e20; border-color: #81c784; }}
    .hole.par {{ background: #37474f; }}
    .hole.bogey {{ background: #f9a825; color: #1a1a1a; }}
    .hole.bad {{ background: #c62828; }}

    footer {{
      text-align: center; padding: 24px;
      opacity: 0.6; font-size: 0.85rem;
    }}
    @media (max-width: 600px) {{
      .holes {{ grid-template-columns: repeat(3, 1fr); }}
      .big-number {{ font-size: 2.2rem; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <div class="hero-bg" role="img" aria-label="高爾夫球場"></div>
      <div class="hero-content">
        <span class="hero-badge">🏌️ 滘西洲 · 南場官方 Par 數據</span>
        <h1>⛳ {round_data['course']}</h1>
        <p class="sub">Kau Sai Chau South · 白梯 {YARDAGE_TOTAL} 碼 · 標準桿 Par {round_data['par_total']}</p>
        <div class="hero-meta">
          <span class="meta-pill">📅 {round_data['date']} {round_data['time']}</span>
          <span class="meta-pill">👥 {len(ranked)} 位球友</span>
          {"<span class='meta-pill'>📝 " + note + "</span>" if note else ""}
        </div>
      </div>
    </header>

    <div class="winner-banner">
      🏆 今日冠軍：<b>{winner['name']}</b> · 總桿 <b>{winner['total']}</b> 桿
      （{("+" + str(winner['to_par'])) if winner['to_par'] > 0 else "平標準桿 E" if winner['to_par'] == 0 else str(winner['to_par'])}）
    </div>

    {build_legend_html()}
    {build_podium_html(ranked)}
    {players_html}

    <footer>
      <p>由 Python 高爾夫記分器產生</p>
      <p>碼數與 Par 參考滘西洲南場白梯公開記分卡</p>
      <p>背景照片：滘西洲南場第 12 洞（Wikimedia Commons）</p>
    </footer>
  </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as file:
        file.write(html)

    return os.path.abspath(filename)


def open_in_browser(filepath):
    abs_path = os.path.abspath(filepath)
    if not os.path.isfile(abs_path):
        return False
    if sys.platform == "darwin":
        subprocess.run(["open", abs_path], check=False)
        return True
    if sys.platform.startswith("win"):
        os.startfile(abs_path)  # type: ignore[attr-defined]
        return True
    return False
