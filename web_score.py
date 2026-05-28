"""網頁錄分：驗證與寫入資料庫（round_storage）"""

from courses import resolve_course_tee
from golf_utils import calc_player_stats

MAX_PLAYERS = 8
MIN_SCORE = 1
MAX_SCORE = 20
HOLES = 18


def coerce_hole_score(raw, *, hole: int, player_name: str) -> tuple[int | None, str | None]:
    """將單洞桿數轉為 int；失敗回傳 (None, error)。"""
    label = f"{player_name} 第 {hole} 洞"
    if raw is None:
        return None, f"{label} 尚未填寫"
    if isinstance(raw, bool):
        return None, f"{player_name} 的桿數格式錯誤"

    v: int
    if isinstance(raw, int):
        v = raw
    elif isinstance(raw, float):
        if not raw.is_integer():
            return None, f"{player_name} 的桿數格式錯誤"
        v = int(raw)
    elif isinstance(raw, str):
        s = raw.strip()
        if not s:
            return None, f"{label} 尚未填寫"
        try:
            if "." in s:
                f = float(s)
                if not f.is_integer():
                    return None, f"{player_name} 的桿數格式錯誤"
                v = int(f)
            else:
                v = int(s)
        except ValueError:
            return None, f"{player_name} 的桿數格式錯誤"
    else:
        return None, f"{player_name} 的桿數格式錯誤"

    if not MIN_SCORE <= v <= MAX_SCORE:
        return None, f"{label} 桿數需在 {MIN_SCORE}～{MAX_SCORE} 之間"
    return v, None


def normalize_scores_list(
    scores,
    *,
    player_name: str,
    holes: int = HOLES,
) -> tuple[list[int] | None, str | None]:
    """將 18 洞桿數列表轉為整數列表。"""
    if not isinstance(scores, list):
        return None, f"{player_name} 需要恰好 {holes} 洞的桿數"
    if len(scores) != holes:
        return None, f"{player_name} 需要恰好 {holes} 洞的桿數"

    out: list[int] = []
    for i, raw in enumerate(scores):
        v, err = coerce_hole_score(raw, hole=i + 1, player_name=player_name)
        if err:
            return None, err
        out.append(v)
    return out, None


def parse_player_entry(entry, index: int, pars: list[int]) -> tuple[dict | None, str | None]:
    """解析單一位球友的 name + scores，回傳 calc_player_stats 結果。"""
    if not isinstance(entry, dict):
        return None, f"第 {index + 1} 位球友資料錯誤"
    name = str(entry.get("name", "")).strip() or f"球友{index + 1}"
    scores_int, err = normalize_scores_list(entry.get("scores"), player_name=name)
    if err:
        return None, err
    stats = calc_player_stats(scores_int, pars=pars)
    stats["name"] = name
    return stats, None


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
        stats, p_err = parse_player_entry(p, i, pars)
        if p_err:
            return None, p_err
        players_stats.append(stats)

    return {
        "players_stats": players_stats,
        "note": note.strip(),
        "course_id": course_id,
        "tee_id": tee_id,
    }, None
