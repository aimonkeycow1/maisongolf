"""
AI 教練總結：深度數據分析 + Grok (xAI) API
環境變數：XAI_API_KEY / GROK_API_KEY、GROK_MODEL（預設 grok-3-mini）
"""

import json
import os
import re
import urllib.error
import urllib.request

from web_helpers import _player_to_par, _round_par_total

XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("GROK_MODEL", "grok-3-mini")


def _to_par_label(n):
    if n is None:
        return "—"
    if n == 0:
        return "E"
    return f"+{n}" if n > 0 else str(n)


def _normalize_analysis(data):
    return {
        "highlights": [str(x).strip() for x in (data.get("highlights") or []) if str(x).strip()][:5],
        "improvements": [str(x).strip() for x in (data.get("improvements") or []) if str(x).strip()][:5],
        "tips": [str(x).strip() for x in (data.get("tips") or []) if str(x).strip()][:5],
        "summary": (data.get("summary") or "").strip(),
    }


def _ensure_holes(target, round_data):
    holes = target.get("hole_results") or []
    if holes:
        return holes
    scores = target.get("scores") or []
    pars = round_data.get("pars") or [4] * 18
    return [
        {
            "hole": i + 1,
            "score": s,
            "par": pars[i] if i < len(pars) else 4,
            "diff": s - (pars[i] if i < len(pars) else 4),
            "name": "",
        }
        for i, s in enumerate(scores)
    ]


def _diff_name(diff):
    if diff <= -2:
        return "Eagle 或更好"
    if diff == -1:
        return "Birdie"
    if diff == 0:
        return "Par"
    if diff == 1:
        return "Bogey"
    if diff == 2:
        return "Double Bogey"
    return f"+{diff}（三柏忌以上）"


def _infer_blowup_mechanism(hole):
    """依洞型與桿數差推斷最可能的失分機制（教練語境）"""
    par = hole["par"]
    diff = hole["diff"]
    score = hole["score"]

    if diff <= 0:
        return None

    if par == 3:
        if diff >= 2:
            return (
                f"Par 3 打了 {score} 桿（+{diff}），通常代表開球未能把球放在進攻位置，"
                "後續切/推連續失誤，屬於「一桿沒到位、後面補不回來」的連鎖反應。"
            )
        return (
            f"Par 3 打了 {score} 桿（+{diff}），多半是開球距離/方向不理想，"
            "果嶺周圍第一桿沒有把球送到可一推進洞的位置。"
        )

    if par == 4:
        if diff >= 3:
            return (
                f"Par 4 第 {hole['hole']} 洞打出 {score} 桿（+{diff}），屬於典型爆洞："
                "開球若進入困難球位，第二桿仍強行攻果嶺，第三、第四桿容易變成救球+兩推，"
                "心理上是「想追回來」反而擴大損失。"
            )
        if diff == 2:
            return (
                f"Par 4 第 {hole['hole']} 洞 +{diff}，常見於：開球偏離球道後，"
                "第二桿沒有先「回到球道中央」，導致第三桿仍從困難位置進攻，最後兩推也難救。"
            )
        return (
            f"Par 4 第 {hole['hole']} 洞 +{diff}，多數是「兩推或鐵桿進攻不夠靠近」——"
            "不是大失誤，但攻果嶺一桿留太遠，讓推桿壓力變大。"
        )

    if par == 5:
        if diff >= 2:
            return (
                f"Par 5 第 {hole['hole']} 洞 +{diff}，問題通常在第二桿（木桿/長鐵）"
                "無法把球送到舒適的攻果嶺距離，或第三桿選桿過於激進造成罰桿/下水。"
            )
        return (
            f"Par 5 第 {hole['hole']} 洞 +{diff}，通常是第三桿進攻品質不足"
            "（距離、方向、選桿），或果嶺周圍切/推多耗一桿。"
        )

    return f"第 {hole['hole']} 洞 +{diff}，需回放該洞策略與選桿。"


def _analyze_scoring_profile(holes):
    """深度統計：依洞型、九洞、連續性、推斷弱項"""
    if not holes:
        return {}

    by_par = {3: [], 4: [], 5: []}
    for h in holes:
        p = h.get("par", 4)
        if p in by_par:
            by_par[p].append(h)

    def _cat_summary(cat_holes, label):
        if not cat_holes:
            return None
        diffs = [h["diff"] for h in cat_holes]
        scores = [h["score"] for h in cat_holes]
        total_par = sum(h["par"] for h in cat_holes)
        total_score = sum(scores)
        over = total_score - total_par
        hole_nums = [h["hole"] for h in cat_holes]
        bogey_only = sum(1 for d in diffs if d == 1)
        double_plus = sum(1 for d in diffs if d >= 2)
        birdie_plus = sum(1 for d in diffs if d <= -1)
        return {
            "label": label,
            "count": len(cat_holes),
            "holes": hole_nums,
            "avg_diff": round(sum(diffs) / len(diffs), 2),
            "strokes_over": over,
            "bogey_only": bogey_only,
            "double_plus": double_plus,
            "birdie_plus": birdie_plus,
            "worst": max(cat_holes, key=lambda x: x["diff"]),
            "best": min(cat_holes, key=lambda x: x["diff"]),
        }

    par3 = _cat_summary(by_par[3], "Par 3 三桿洞")
    par4 = _cat_summary(by_par[4], "Par 4 四桿洞")
    par5 = _cat_summary(by_par[5], "Par 5 五桿洞")

    front = [h for h in holes if h["hole"] <= 9]
    back = [h for h in holes if h["hole"] > 9]
    front_diff = sum(h["diff"] for h in front)
    back_diff = sum(h["diff"] for h in back)

    blowups = sorted([h for h in holes if h["diff"] >= 2], key=lambda x: -x["diff"])
    excellent = [h for h in holes if h["diff"] <= -1]
    clean_pars = [h for h in holes if h["diff"] == 0]
    soft_bogeys = [h for h in holes if h["diff"] == 1]

    # 連續失分 / 連續穩定
    streaks_bad = []
    streaks_good = []
    cur_bad, cur_good = [], []
    for h in sorted(holes, key=lambda x: x["hole"]):
        if h["diff"] >= 1:
            cur_bad.append(h)
            if len(cur_good) >= 3:
                streaks_good.append(list(cur_good))
            cur_good = []
        else:
            cur_good.append(h)
            if len(cur_bad) >= 2:
                streaks_bad.append(list(cur_bad))
            cur_bad = []
    if len(cur_bad) >= 2:
        streaks_bad.append(cur_bad)
    if len(cur_good) >= 3:
        streaks_good.append(cur_good)

    # 推斷最弱環節（依「相對該洞型標準桿」的總超桿數）
    category_loss = []
    for cat in (par3, par4, par5):
        if cat and cat["strokes_over"] > 0:
            category_loss.append((cat["strokes_over"], cat["avg_diff"], cat))
    category_loss.sort(reverse=True)

    # 鐵桿/木桿/短桿/推桿 代理指標（無逐桿類型時用洞型+桿數差推斷）
    weakness_guess = []
    if par4 and par4["strokes_over"] >= (par3 or {}).get("strokes_over", 0) and par4["strokes_over"] > 2:
        weakness_guess.append(
            f"四桿洞共超標 {par4['strokes_over']} 桿（洞號 {par4['holes']}），"
            f"其中 {par4['bogey_only']} 洞是「小一號柏忌」、{par4['double_plus']} 洞爆洞——"
            "鐵桿進攻與果嶺周圍控制是主要失分來源。"
        )
    if par3 and par3["avg_diff"] >= 1.0:
        weakness_guess.append(
            f"三桿洞平均 +{par3['avg_diff']:.1f}（洞 {par3['holes']}），"
            "顯示開球上果嶺率或短桿精準度不足，常把 Par 3 打成「兩推還不夠」的局面。"
        )
    if par5 and par5["strokes_over"] > 2:
        weakness_guess.append(
            f"五桿洞超標 {par5['strokes_over']} 桿，長桿（木桿/長鐵）距離與第三桿攻果嶺決策需優先檢討。"
        )
    if len(soft_bogeys) >= 6 and not blowups:
        weakness_guess.append(
            f"全場 {len(soft_bogeys)} 洞是「僅 +1」的柏忌，代表沒有天天爆洞，"
            "但推桿或攻果嶺一桿經常差「最後 6 米」——屬於可快速進步的區間。"
        )

    # 九洞節奏
    nine_insight = None
    if front_diff < back_diff - 2:
        nine_insight = (
            f"前九僅 +{front_diff}、後九 +{back_diff}，後九多丟 {back_diff - front_diff} 桿；"
            "常見原因是體力下降、節奏加快，或對後九難洞準備不足。"
        )
    elif back_diff < front_diff - 2:
        nine_insight = (
            f"前九 +{front_diff}、後九 +{back_diff}，開局較緊但後九找回節奏，"
            "顯示調整能力與心理恢復力不錯。"
        )

    return {
        "par3": par3,
        "par4": par4,
        "par5": par5,
        "front_diff": front_diff,
        "back_diff": back_diff,
        "nine_insight": nine_insight,
        "blowups": blowups,
        "excellent": excellent,
        "clean_pars": clean_pars,
        "soft_bogeys": soft_bogeys,
        "streaks_bad": streaks_bad,
        "streaks_good": streaks_good,
        "category_loss": category_loss,
        "weakness_guess": weakness_guess,
    }


def _format_hole_line(h):
    return (
        f"第{h['hole']:>2}洞 Par{h['par']} 實際{h['score']}桿 "
        f"({_diff_name(h['diff'])}, {_to_par_label(h['diff'])})"
    )


def build_round_context(round_data, player_name=None):
    players = round_data.get("players") or []
    if not players:
        return None

    rp = _round_par_total(round_data)
    ranked = sorted(players, key=lambda p: p["total"])
    target = (
        next((p for p in players if p["name"] == player_name), None)
        if player_name
        else ranked[0]
    )
    if not target:
        return None

    holes = _ensure_holes(target, round_data)
    profile = _analyze_scoring_profile(holes)

    yardages = round_data.get("yardages") or []
    hole_detail = []
    for h in holes:
        idx = h["hole"] - 1
        yd = yardages[idx] if idx < len(yardages) else None
        row = dict(h)
        if yd:
            row["yardage"] = yd
        hole_detail.append(row)

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
        "holes": hole_detail,
        "profile": profile,
        "all_players": [
            {"name": p["name"], "total": p["total"], "to_par": _player_to_par(p, rp)}
            for p in ranked
        ],
    }


def build_coach_data_brief(ctx):
    """產生給 Grok / 規則引擎用的結構化賽後數據簡報"""
    p = ctx["profile"]
    holes = ctx["holes"]
    lines = []

    lines.append("=== 基本資訊 ===")
    lines.append(f"球員：{ctx['player_name']}｜球場：{ctx['course']}｜{ctx['tee']}")
    lines.append(f"總桿 {ctx['total']}（{_to_par_label(ctx['to_par'])}）｜前九 {ctx['front9']}({_to_par_label(ctx['front_to_par'])}) 後九 {ctx['back9']}({_to_par_label(ctx['back_to_par'])})")
    lines.append(
        f"成績分布：Birdie+ {ctx['birdies']}｜Par {ctx['pars']}｜Bogey {ctx['bogeys']}｜Double+ {ctx['double_plus']}"
    )
    lines.append(f"同組排名：第 {ctx['rank']}/{ctx['field_size']} 名")

    lines.append("\n=== 逐洞明細 ===")
    for h in holes:
        extra = f"｜{h['yardage']}碼" if h.get("yardage") else ""
        lines.append(_format_hole_line(h) + extra)

    lines.append("\n=== 洞型統計（數據結論，分析時必須引用） ===")
    for key in ("par3", "par4", "par5"):
        cat = p.get(key)
        if not cat:
            continue
        lines.append(
            f"{cat['label']}：{cat['count']} 洞、合計超標 {cat['strokes_over']} 桿、"
            f"平均 +{cat['avg_diff']:.2f}｜爆洞 {cat['double_plus']}｜僅+1柏忌 {cat['bogey_only']}｜"
            f"洞號 {cat['holes']}"
        )

    if p.get("nine_insight"):
        lines.append(f"\n九洞節奏：{p['nine_insight']}")

    if p.get("weakness_guess"):
        lines.append("\n=== 數據推斷的技術弱項（請在分析中呼應或修正） ===")
        for w in p["weakness_guess"]:
            lines.append(f"- {w}")

    if p.get("blowups"):
        lines.append("\n=== 爆洞清單（diff≥+2，必須逐洞點名） ===")
        for h in p["blowups"]:
            mech = _infer_blowup_mechanism(h)
            lines.append(f"- {_format_hole_line(h)}")
            if mech:
                lines.append(f"  機制：{mech}")

    if p.get("excellent"):
        lines.append("\n=== 優異洞（Birdie 或更好） ===")
        for h in p["excellent"]:
            lines.append(f"- {_format_hole_line(h)}")

    if p.get("clean_pars"):
        lines.append(f"\n=== Par 洞共 {len(p['clean_pars'])} 個 ===")
        lines.append("洞號：" + ", ".join(str(h["hole"]) for h in p["clean_pars"]))

    if p.get("streaks_bad"):
        lines.append("\n=== 連續失分區間 ===")
        for streak in p["streaks_bad"]:
            nums = ", ".join(f"第{h['hole']}洞(+{h['diff']})" for h in streak)
            lines.append(f"- {nums}")

    if p.get("streaks_good"):
        lines.append("\n=== 連續穩定區間 ===")
        for streak in p["streaks_good"]:
            nums = ", ".join(f"第{h['hole']}洞({_to_par_label(h['diff'])})" for h in streak)
            lines.append(f"- {nums}")

    return "\n".join(lines)


def deep_coach_analysis(ctx):
    """依深度統計產生具體教練分析（本機，保證可執行且針對性強）"""
    p = ctx["profile"]
    holes = ctx["holes"]
    highlights = []
    improvements = []
    tips = []

    # —— 亮點：必須具名洞號與數據 ——
    if p.get("excellent"):
        for h in p["excellent"]:
            highlights.append(
                f"第 {h['hole']} 洞 Par {h['par']} 打出 {h['score']} 桿（{_diff_name(h['diff'])}），"
                f"在當日 {_to_par_label(ctx['to_par'])} 的基調下，這洞證明你具備抓住機會的能力。"
            )

    if p.get("clean_pars") and len(p["clean_pars"]) >= 3:
        nums = "、".join(str(h["hole"]) for h in p["clean_pars"][:6])
        more = f"等共 {len(p['clean_pars'])} 洞" if len(p["clean_pars"]) > 6 else ""
        highlights.append(
            f"第 {nums}{more} 洞守住 Par，佔全場 {len(p['clean_pars'])}/18——"
            "代表多數時間球道策略尚可，問題集中在少數「爆洞」而非全程失控。"
        )

    for cat_key, label in (("par3", "三桿洞"), ("par4", "四桿洞"), ("par5", "五桿洞")):
        cat = p.get(cat_key)
        if cat and cat["birdie_plus"] > 0:
            best = cat["best"]
            if best["diff"] <= -1:
                highlights.append(
                    f"{label}最佳：第 {best['hole']} 洞 {best['score']} 桿完成（Par {best['par']}），"
                    f"該洞型平均僅 +{cat['avg_diff']:.1f}，顯示這類球洞並非你的絕對弱項。"
                )

    if p.get("nine_insight") and ctx.get("back_to_par", 99) < ctx.get("front_to_par", 99):
        highlights.append(p["nine_insight"])

    if ctx["rank"] == 1 and ctx["field_size"] > 1:
        gap = ctx["all_players"][-1]["to_par"] - ctx["to_par"] if ctx["all_players"] else 0
        highlights.append(
            f"同組 {ctx['field_size']} 人中以 {ctx['total']} 桿奪冠"
            + (f"（領先末位 {gap} 桿）" if gap > 0 else "")
            + "，關鍵洞的抗壓選擇優於其他球友。"
        )

    if not highlights:
        best_h = min(holes, key=lambda x: x["diff"])
        highlights.append(
            f"相對最佳為第 {best_h['hole']} 洞（Par {best_h['par']} 打 {best_h['score']}，{_to_par_label(best_h['diff'])}），"
            "建議以此洞的選桿與節奏作為下場模板。"
        )

    # —— 改進：爆洞 + 洞型弱項 + 連續失分 ——
    for h in p.get("blowups") or []:
        mech = _infer_blowup_mechanism(h)
        improvements.append(
            f"第 {h['hole']} 洞 Par {h['par']} 打 {h['score']} 桿（{_diff_name(h['diff'])}）——本場主要失分點。"
            + (f" {mech}" if mech else "")
        )

    if p.get("category_loss"):
        top = p["category_loss"][0][2]
        improvements.append(
            f"數據顯示「{top['label']}」是主要失分來源：{top['count']} 洞合計超標 {top['strokes_over']} 桿、"
            f"平均 +{top['avg_diff']:.2f}（洞號 {top['holes']}）。"
            f"其中 {top['double_plus']} 洞爆洞、{top['bogey_only']} 洞為小幅柏忌。"
        )

    for w in p.get("weakness_guess") or []:
        if w not in " ".join(improvements):
            improvements.append(w)

    for streak in p.get("streaks_bad") or []:
        if len(streak) >= 2:
            nums = "→".join(f"{h['hole']}(+{h['diff']})" for h in streak)
            improvements.append(
                f"第 {streak[0]['hole']}–{streak[-1]['hole']} 洞連續失分（{nums}），"
                "顯示第一洞出錯後節奏變快、選桿變冒進，需建立「止損打」習慣。"
            )

    if len(p.get("soft_bogeys") or []) >= 8:
        improvements.append(
            f"全場 {len(p['soft_bogeys'])} 洞是「+1 柏忌」——代表常差在最後一桿或最後兩推，"
            "攻果嶺距離常落在 8–15 米，推桿壓力累積成總桿數。"
        )

    if not improvements:
        worst = max(holes, key=lambda x: x["diff"])
        improvements.append(
            f"最需檢討第 {worst['hole']} 洞（+{worst['diff']}），"
            "建議回放該洞每一桿的目標與實際執行是否一致。"
        )

    # —— 建議：對應具體洞與練習 ——
    if p.get("blowups"):
        h = p["blowups"][0]
        if h["par"] == 4 and h["diff"] >= 3:
            tips.append(
                f"針對第 {h['hole']} 洞型（Par 4）練習「開球偏離後的止損」："
                "下一桿只用 7 號以內把球放回球道寬處，禁止第二桿直接攻旗。"
                "練習場連續 10 球：故意打偏開球，測試第三桿能否穩定 Par。"
            )
        elif h["par"] == 3:
            tips.append(
                f"第 {h['hole']} 洞（Par 3）爆洞後，下場 Par 3 策略改為："
                "果嶺前一律以「洞中央」為目標，選大一號桿確保上果嶺，"
                "接受兩推 Par 而非高風險切球過洞。"
            )
        else:
            tips.append(
                f"為第 {h['hole']} 洞建立專屬賽前計畫：寫下開球目標區、第二桿目標距離、"
                "「超過 Par+2 就改打保守」的止損線，洞邊實際執行。"
            )

    if p.get("par4") and p["par4"]["strokes_over"] >= 4:
        tips.append(
            f"四桿洞（洞 {p['par4']['holes']}）練習：球道中央 100–130 碼內用同一支鐵桿（如 8 號）"
            "連打 15 球，記錄落點散布；目標散布半徑 < 12 米，直接提升攻果嶺品質。"
        )

    if p.get("par3") and p["par3"]["avg_diff"] >= 0.8:
        tips.append(
            f"三桿洞（洞 {p['par3']['holes']}）加練：TEE 用同一顆桿建立固定距離，"
            "果嶺邊 20–30 碼內切杆各 10 球，記錄上果嶺率；目標 7/10 進入 2 推圈。"
        )

    if ctx.get("front_to_par", 0) > ctx.get("back_to_par", 0) + 3:
        tips.append(
            "前九失分較多：開球前 3 洞採「開球桿 + 3/4 揮桿」節奏，"
            "第 4 洞起再恢復全揮；熱身多打 5 顆模擬開球，避免開局倉促。"
        )
    elif ctx.get("back_to_par", 0) > ctx.get("front_to_par", 0) + 3:
        tips.append(
            "後九失分較多：第 10 洞前補充水分+2 分鐘揮桿節奏練習，"
            "後九鐵桿目標改為果嶺「安全區」而非旗桿，保存體力。"
        )

    if len(p.get("soft_bogeys") or []) >= 6:
        tips.append(
            "針對大量「+1」：練習 1.5m / 3m / 5m 三個距離各 10 推，"
            "記錄進洞數；下場若攻果嶺剩 5 米內，心態目標改為「穩定兩推」而非追鳥。"
        )

    if not tips:
        tips.append(
            f"下場前針對 {ctx['course']} 標記 3 個最難洞（參考今日爆洞："
            f"{', '.join(str(h['hole']) for h in (p.get('blowups') or [])[:3]) or '待標記'}），"
            "每洞寫一句「開球目標 + 止損策略」，洞前 10 秒默念執行。"
        )

    # —— 總評 ——
    blowup_nums = ", ".join(f"第{h['hole']}洞" for h in (p.get("blowups") or [])[:2])
    main_weak = p["category_loss"][0][2]["label"] if p.get("category_loss") else "整體穩定度"
    if p.get("blowups") and ctx["to_par"] > 10:
        summary = (
            f"{ctx['player_name']}，這場 {ctx['total']} 桿（{_to_par_label(ctx['to_par'])}）"
            f"並非全程崩潰，而是 {blowup_nums} 等少數洞拉高總數；"
            f"數據指向「{main_weak}」是主要失分來源。"
            f"下場優先目標：爆洞洞號採止損策略，其餘洞守住柏忌即可明顯降桿。"
        )
    elif ctx["to_par"] <= 5:
        summary = (
            f"這場 {ctx['total']} 桿（{_to_par_label(ctx['to_par'])}）具競爭力；"
            f"{main_weak}仍有小幅超標，但 Par 洞與關鍵洞把握度不錯。"
            "再壓縮 2–3 個柏忌洞，就有機會穩定進入個人最佳區間。"
        )
    else:
        summary = (
            f"總桿 {ctx['total']}（{_to_par_label(ctx['to_par'])}），"
            f"全場 {len(p.get('soft_bogeys') or [])} 洞小幅柏忌 + {len(p.get('blowups') or [])} 洞爆洞；"
            f"優先處理 {blowup_nums or '爆洞洞'}，同時把攻果嶺距離控制在兩推範圍內，"
            "下一場有明確進步空間。"
        )

    return _normalize_analysis({
        "highlights": highlights[:4],
        "improvements": improvements[:4],
        "tips": tips[:4],
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


def _validate_analysis_quality(analysis, ctx):
    """過濾過於空泛的句子（若全為空則回退）"""
    generic_phrases = (
        "保持開球穩定",
        "繼續加油",
        "整體不錯",
        "有待提升",
        "多練習",
        "設定目標",
    )

    def _ok_list(items):
        good = []
        for item in items:
            if len(item) < 20:
                continue
            if not any(g in item for g in ("第", "洞", "Par", "桿", "+", "Birdie", "柏忌", "三桿", "四桿", "五桿")):
                if any(g in item for g in generic_phrases):
                    continue
            good.append(item)
        return good

    h = _ok_list(analysis.get("highlights", []))
    i = _ok_list(analysis.get("improvements", []))
    t = _ok_list(analysis.get("tips", []))
    s = analysis.get("summary", "")

    if len(h) >= 1 and len(i) >= 1 and len(t) >= 1 and len(s) >= 40:
        return _normalize_analysis({
            "highlights": h,
            "improvements": i,
            "tips": t,
            "summary": s,
        })
    return None


def call_grok_analysis(ctx):
    api_key = os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")
    if not api_key:
        return None

    brief = build_coach_data_brief(ctx)

    system = """你是擁有 12 年巡迴賽教學經驗的 PGA 私人教練，正在為學員做「一對一賽後講評」。
語言：繁體中文（香港高球用語）。語氣：專業、直接、親切，像教練坐在會所酒吧旁拿著記分卡講解。

【硬性規則 — 違反即不合格】
1. 禁止空泛建議（如「多練習」「保持心態」「繼續加油」「注意開球」而不附洞號與數據）。
2. highlights / improvements / tips 每一條必須包含：具體洞號 或 洞型(Par3/4/5) + 桿數/差桿數據。
3. improvements 必須解釋「問題本質」（開球/鐵桿/短桿/推桿/策略/心理連鎖），不可只描述結果。
4. tips 必須是可立刻執行的練習或下場策略（含距離、桿數、次數、止損條件等）。
5. 優先使用「數據簡報」中已算好的結論；可修正但不可忽略爆洞清單與洞型統計。
6. 只輸出 JSON，無 markdown：
{"highlights":["..."],"improvements":["..."],"tips":["..."],"summary":"..."}
7. 陣列各 3–4 條；summary 3–4 句，須點名最關鍵洞號與主要失分來源。"""

    user = f"""請根據以下「已完成的數據分析簡報」撰寫教練講評。
你的任務不是重新算數，而是把數據轉成有溫度的專業洞察。

{brief}
"""

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.45,
        "max_tokens": 1400,
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        if parsed:
            validated = _validate_analysis_quality(_normalize_analysis(parsed), ctx)
            if validated:
                return validated
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        pass
    return None


def generate_coach_analysis(round_data, player_name=None):
    ctx = build_round_context(round_data, player_name)
    if not ctx:
        return None, None

    grok = call_grok_analysis(ctx)
    if grok:
        return grok, "grok"

    return deep_coach_analysis(ctx), "mock"


def build_next_hole_strategy(tee, next_hole, players, scores):
    """
    逐洞策略：輸入下一洞洞號，輸出可直接顯示在 UI 的教練卡片內容。
    """
    idx = max(1, min(18, int(next_hole))) - 1
    pars = tee.get("pars") or [4] * 18
    yardages = tee.get("yardages") or [0] * 18
    handicaps = tee.get("handicap") or [0] * 18
    par = pars[idx] if idx < len(pars) else 4
    yard = yardages[idx] if idx < len(yardages) else 0
    hcp = handicaps[idx] if idx < len(handicaps) else 0
    hole_no = idx + 1

    avg_diff = 0
    valid = []
    for row in scores or []:
        if not isinstance(row, list):
            continue
        played = [v for v in row[:idx] if isinstance(v, int) and v >= 1]
        if not played:
            continue
        rel = 0
        for h_i, s in enumerate(played):
            rel += s - (pars[h_i] if h_i < len(pars) else 4)
        valid.append(rel / len(played))
    if valid:
        avg_diff = round(sum(valid) / len(valid), 2)

    if par == 5:
        shot_plan = "開球以球道中左/中右安全區為第一目標；第二桿優先把球送到 80–120 碼舒適攻果嶺距離，第三桿再進攻旗位。"
        club_plan = "開球可用 Driver 或 3W（依你今天命中率）；第二桿若球位不理想，改用長鐵做位置球，避免硬攻下水或 OB。"
    elif par == 3:
        shot_plan = "這洞重點是『一桿上果嶺或安全前緣』，目標先對準果嶺中央，不追旗桿。"
        club_plan = "選大一號桿，節奏 80–90% 揮桿；寧可留長推，不要短桿進沙坑。"
    else:
        shot_plan = "開球先拿球道，再用第二桿攻果嶺安全區（優先中間，不硬攻邊旗）。"
        club_plan = "若今天開球偏右/左，改用 3W 或混血桿保守開球；第二桿以『可兩推』距離為目標。"

    risk_line = "右側 OB / 左側長草風險較高，失誤方向一律選擇可救球的安全側。"
    if hcp and hcp <= 6:
        risk_line = "此洞為高難度洞（差點靠前），請把策略設定為『Bogey 可接受，Double 禁止』。"

    momentum = (
        f"目前平均表現約 {avg_diff:+.2f} 桿/洞，相比標準桿"
        if valid else
        "目前資料不足，建議先用保守策略建立節奏"
    )
    coach_tone = (
        f"第 {hole_no} 洞（Par {par}，{yard} 碼）請你用『先穩再攻』。"
        "第一桿只求進入可打第二桿的位置，第二桿才決定是否進攻旗位。"
    )

    return {
        "title": f"第 {hole_no} 洞策略建議",
        "subtitle": f"Par {par} · {yard} 碼 · 差點 {hcp}",
        "summary": coach_tone,
        "shot_plan": shot_plan,
        "club_plan": club_plan,
        "risk_control": risk_line,
        "momentum": momentum,
    }
