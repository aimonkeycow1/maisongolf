"""網頁錄分：驗證與寫入 rounds.json"""

from courses import resolve_course_tee
from golf_utils import calc_player_stats

MAX_PLAYERS = 8
MIN_SCORE = 1
MAX_SCORE = 20


def validate_score_submission(data):
    """
    驗證 POST JSON，回傳 (result_dict, error_message)。
    """
    if not isinstance(data, dict):
        return None, "需要 JSON 物件"

    course_id = data.get("course_id", "")
    tee_id = data.get("tee_id", "")
    tee, err = resolve_course_tee(course_id, tee_id)
    if err:
        return None, err

    players = data.get("players")
    if not isinstance(players, list):
        return None, "缺少 players"
    if not 1 <= len(players) <= MAX_PLAYERS:
        return None, f"球友人數需 1～{MAX_PLAYERS} 人"

    note = data.get("note", "")
    if not isinstance(note, str):
        return None, "備註格式錯誤"

    pars = tee["pars"]
    players_stats = []
    for i, p in enumerate(players):
        if not isinstance(p, dict):
            return None, f"第 {i + 1} 位球友資料錯誤"
        name = str(p.get("name", "")).strip() or f"球友{i + 1}"
        scores = p.get("scores")
        if not isinstance(scores, list) or len(scores) != 18:
            return None, f"{name} 需要恰好 18 洞的桿數"
        try:
            scores = [int(s) for s in scores]
        except (TypeError, ValueError):
            return None, f"{name} 桿數必須是整數"
        for hole, s in enumerate(scores, start=1):
            if not MIN_SCORE <= s <= MAX_SCORE:
                return None, f"{name} 第 {hole} 洞桿數需在 {MIN_SCORE}～{MAX_SCORE} 之間"
        stats = calc_player_stats(scores, pars=pars)
        stats["name"] = name
        players_stats.append(stats)

    return {
        "players_stats": players_stats,
        "note": note.strip(),
        "course_id": course_id,
        "tee_id": tee_id,
    }, None
