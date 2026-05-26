"""
AI 教練總結：Grok (xAI) API + 本機規則模擬回退
環境變數：
  XAI_API_KEY 或 GROK_API_KEY — xAI API 金鑰
  GROK_MODEL — 模型名稱（預設 grok-3-mini）
"""

import json
import os
import re
import urllib.error
import urllib.request

from web_helpers import _player_to_par, _round_par_total

XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("GROK_MODEL", "grok-3-mini")


def _normalize_analysis(data):
    """確保回傳結構一致"""
    return {
        "highlights": list(data.get("highlights") or [])[:5],
        "improvements": list(data.get("improvements") or [])[:5],
        "tips": list(data.get("tips") or [])[:5],
        "summary": (data.get("summary") or "").strip(),
    }


def build_round_context(round_data, player_name=None):
    """整理單場球員資料供 AI 或模擬分析使用"""
    players = round_data.get("players") or []
    if not players:
        return None

    rp = _round_par_total(round_data)
    ranked = sorted(players, key=lambda p: p["total"])

    if player_name:
        target = next((p for p in players if p["name"] == player_name), None)
        if not target:
            return None
    else:
        target = ranked[0]

    holes = target.get("hole_results") or []
    if not holes and target.get("scores"):
        pars = round_data.get("pars") or [4] * 18
        holes = [
            {
                "hole": i + 1,
                "score": s,
                "par": pars[i] if i < len(pars) else 4,
                "diff": s - (pars[i] if i < len(pars) else 4),
            }
            for i, s in enumerate(target["scores"])
        ]

    hole_lines = []
    for h in holes:
        d = h.get("diff", 0)
        sign = f"+{d}" if d > 0 else str(d)
        hole_lines.append(f"第{h['hole']}洞 Par{h['par']} 打{h['score']} ({sign})")

    worst = sorted(holes, key=lambda h: h.get("diff", 0), reverse=True)[:3]
    best = sorted(holes, key=lambda h: h.get("diff", 0))[:3]

    return {
        "round_id": round_data.get("id", ""),
        "course": round_data.get("course", ""),
        "tee": round_data.get("tee", ""),
        "par_total": rp,
        "yardage_total": round_data.get("yardage_total"),
        "date": round_data.get("date", ""),
        "note": round_data.get("note", ""),
        "player_name": target["name"],
        "total": target["total"],
        "to_par": _player_to_par(target, rp),
        "front9": target.get("front9"),
        "back9": target.get("back9"),
        "front_to_par": target.get("front_to_par"),
        "back_to_par": target.get("back_to_par"),
        "birdies": target.get("birdies", 0),
        "pars": target.get("pars", 0),
        "bogeys": target.get("bogeys", 0),
        "double_plus": target.get("double_plus", 0),
        "rank": ranked.index(target) + 1,
        "field_size": len(players),
        "hole_lines": hole_lines,
        "worst_holes": worst,
        "best_holes": best,
        "all_players": [
            {"name": p["name"], "total": p["total"], "to_par": _player_to_par(p, rp)}
            for p in ranked
        ],
    }


def _to_par_label(n):
    if n == 0:
        return "E"
    return f"+{n}" if n > 0 else str(n)


def mock_coach_analysis(ctx):
    """無 API 金鑰時的專業規則模擬教練總結"""
    highlights = []
    improvements = []
    tips = []

    if ctx["birdies"] > 0:
        highlights.append(
            f"全場錄得 {ctx['birdies']} 個 Birdie 或更好成績，進攻火力有亮點。"
        )
    if ctx["pars"] >= 9:
        highlights.append(f"完成 {ctx['pars']} 個 Par，整體穩定度值得肯定。")
    if ctx.get("front_to_par") is not None and ctx["front_to_par"] < ctx.get("back_to_par", 99):
        highlights.append(
            f"前九 {ctx['front9']} 桿（{_to_par_label(ctx['front_to_par'])}）優於後九，開局節奏掌握佳。"
        )
    elif ctx.get("back_to_par") is not None and ctx["back_to_par"] < ctx.get("front_to_par", 99):
        highlights.append(
            f"後九 {ctx['back9']} 桿（{_to_par_label(ctx['back_to_par'])}）收得更穩，關鍵時刻心理素質不錯。"
        )
    if ctx["rank"] == 1 and ctx["field_size"] > 1:
        highlights.append(f"在同組 {ctx['field_size']} 位球手中奪冠，表現最佳。")
    if not highlights:
        highlights.append("完整打完 18 洞並留下數據，有利後續追蹤進步軌跡。")

    if ctx["double_plus"] >= 2:
        improvements.append(
            f"出現 {ctx['double_plus']} 個 Double Bogey 或更差，大失分洞需優先檢討。"
        )
    if ctx["bogeys"] >= 8:
        improvements.append("柏忌洞偏多，鐵桿進攻與果嶺周圍的距離控制還可再加強。")

    for h in ctx["worst_holes"][:2]:
        if h.get("diff", 0) >= 2:
            improvements.append(
                f"第 {h['hole']} 洞（Par {h['par']} 打 {h['score']}）是主要失分點。"
            )

    if ctx["to_par"] > 12:
        improvements.append("總桿與標準桿差距較大，建議從開球穩定度與三桿洞策略著手。")
    if not improvements:
        improvements.append("整體表現均衡，可進一步壓縮柏忌並提升 Par 轉 Birdie 的轉換率。")

    tips.append("練習前先設定本場目標：例如「雙柏忌不超過 2 個」或「Par 3 平均 +1 以內」。")
    if ctx["double_plus"] > 0:
        tips.append("針對失分洞回放：是開球方向、第二桿距離還是短桿？分類後各練 15 分鐘。")
    if ctx.get("worst_holes"):
        tips.append("最難洞下次採保守策略：果嶺前寧可留短一點，避免爆洞。")
    tips.append("推桿練習以 1.5 米內連續 10 推進洞開始，建立推桿信心。")

    summary_parts = [
        f"{ctx['player_name']} 在 {ctx['course']}（{ctx['tee']}）",
        f"總桿 {ctx['total']}（比標準桿 {_to_par_label(ctx['to_par'])}）。",
    ]
    if ctx["birdies"] >= 2 and ctx["double_plus"] <= 1:
        summary = (
            f"這場整體節奏不錯，{' '.join(summary_parts)} "
            "推桿與短桿貢獻明顯，保持開球穩定就能再下一城。"
        )
    elif ctx["to_par"] <= 5:
        summary = (
            f"這是一場有競爭力的回合，{' '.join(summary_parts)} "
            "鐵桿距離控制佳，繼續減少非受迫性失誤即可。"
        )
    else:
        summary = (
            f"這場還有提升空間，{' '.join(summary_parts)} "
            "推桿若再穩一些、鐵桿選桿更果斷，下一場會明顯進步。"
        )

    return _normalize_analysis({
        "highlights": highlights,
        "improvements": improvements,
        "tips": tips,
        "summary": summary,
    })


def _extract_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def call_grok_analysis(ctx):
    """呼叫 xAI Grok Chat Completions，失敗時回傳 None"""
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not api_key:
        return None

    players_text = "\n".join(
        f"- {p['name']}: {p['total']} 桿 ({_to_par_label(p['to_par'])})"
        for p in ctx["all_players"]
    )
    holes_text = "\n".join(ctx["hole_lines"])

    system = (
        "你是專業 PGA 風格的高爾夫教練，用繁體中文（香港用語）撰寫簡潔、鼓勵但誠實的賽後總結。"
        "只回傳 JSON，不要 markdown，格式："
        '{"highlights":["..."],"improvements":["..."],"tips":["..."],"summary":"..."}'
        "每個陣列 2-4 條，summary 一段 2-3 句。"
    )
    user = f"""請為以下球員撰寫賽後教練分析：

球場：{ctx['course']} · {ctx['tee']} · Par {ctx['par_total']}
日期：{ctx['date']}
備註：{ctx['note'] or '無'}

分析對象：{ctx['player_name']}（本組第 {ctx['rank']}/{ctx['field_size']} 名）
總桿：{ctx['total']}（比標準桿 {_to_par_label(ctx['to_par'])}）
前九/後九：{ctx['front9']}/{ctx['back9']}（{_to_par_label(ctx.get('front_to_par', 0))} / {_to_par_label(ctx.get('back_to_par', 0))}）
Birdie+：{ctx['birdies']} · Par：{ctx['pars']} · Bogey：{ctx['bogeys']} · Double+：{ctx['double_plus']}

同組成績：
{players_text}

逐洞：
{holes_text}
"""

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.6,
        "max_tokens": 900,
    }

    req = urllib.request.Request(
        XAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        if parsed:
            return _normalize_analysis(parsed)
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None
    return None


def generate_coach_analysis(round_data, player_name=None):
    """
    回傳 (analysis_dict, source)
    source: 'grok' | 'mock'
    """
    ctx = build_round_context(round_data, player_name)
    if not ctx:
        return None, None

    grok = call_grok_analysis(ctx)
    if grok:
        return grok, "grok"

    return mock_coach_analysis(ctx), "mock"
