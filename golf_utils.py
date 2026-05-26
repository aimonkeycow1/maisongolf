from course_data import PARS as DEFAULT_PARS, PAR_TOTAL as DEFAULT_PAR_TOTAL
from course_data import PAR_FRONT as DEFAULT_PAR_FRONT, PAR_BACK as DEFAULT_PAR_BACK

def score_name(diff):
    names = {
        -3: "信天翁",
        -2: "老鷹",
        -1: "鳥擊",
        0: "Par",
        1: "柏忌",
        2: "雙柏忌",
        3: "三柏忌",
    }
    if diff in names:
        return names[diff]
    if diff > 3:
        return f"+{diff}"
    return str(diff)

def to_par_str(diff):
    if diff == 0:
        return "E"
    if diff > 0:
        return f"+{diff}"
    return str(diff)

def calc_player_stats(scores, pars=None):
    """依 18 洞桿數清單，計算統計數據；pars 可指定 Tee 的標準桿"""
    if pars is None:
        pars = DEFAULT_PARS
    par_total = sum(pars)
    par_front = sum(pars[:9])
    par_back = sum(pars[9:])

    total = sum(scores)
    front9 = sum(scores[:9])
    back9 = sum(scores[9:])
    to_par = total - par_total
    front_to_par = front9 - par_front
    back_to_par = back9 - par_back

    birdies = pars_count = bogeys = double_plus = 0
    hole_results = []
    for i, s in enumerate(scores):
        d = s - pars[i]
        hole_results.append({"hole": i + 1, "score": s, "par": pars[i], "diff": d, "name": score_name(d)})
        if d <= -1:
            birdies += 1
        elif d == 0:
            pars_count += 1
        elif d == 1:
            bogeys += 1
        else:
            double_plus += 1

    return {
        "scores": scores,
        "total": total,
        "to_par": to_par,
        "front9": front9,
        "back9": back9,
        "front_to_par": front_to_par,
        "back_to_par": back_to_par,
        "birdies": birdies,
        "pars": pars_count,
        "bogeys": bogeys,
        "double_plus": double_plus,
        "hole_results": hole_results,
    }

def ask_score(prompt):
    while True:
        try:
            score = int(input(prompt))
            if score > 0:
                return score
            print("⚠️ 桿數必須大於 0，請重新輸入")
        except ValueError:
            print("⚠️ 請輸入數字！")
