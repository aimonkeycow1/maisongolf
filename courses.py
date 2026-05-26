"""
多球場 · 多 Tee 資料庫
新增球場：在 COURSES 加入一筆，並設定 tees 內的 pars / yardages / handicap
數據來源：球會官網 / GolfPass 公開記分卡（白梯 White Tee）
"""

DEFAULT_COURSE_ID = "ksc-south"
DEFAULT_TEE_ID = "white"

_HERO = "/static/img/hero.jpg"

# —— 東場 Par 72 · 白梯 6025 碼 ——
_KSC_EAST_PARS = [5, 4, 3, 4, 3, 5, 4, 3, 4, 5, 4, 4, 3, 4, 3, 5, 4, 5]
_KSC_EAST_HCP = [11, 5, 17, 9, 15, 1, 13, 7, 3, 8, 12, 16, 14, 4, 18, 10, 2, 6]
_KSC_EAST_WHITE = [
    500, 352, 157, 304, 125, 507, 329, 199, 403,
    466, 370, 259, 137, 347, 130, 496, 411, 533,
]

# —— 南場 Par 69 · 白梯 5906 碼 ——
_KSC_SOUTH_PARS = [4, 3, 4, 4, 3, 4, 4, 4, 4, 4, 3, 4, 4, 4, 5, 3, 4, 4]
_KSC_SOUTH_HCP = [5, 11, 1, 17, 7, 15, 9, 13, 3, 16, 14, 4, 10, 2, 8, 6, 18, 12]
_KSC_SOUTH_WHITE = [
    341, 149, 429, 285, 134, 301, 307, 315, 362,
    317, 159, 417, 377, 464, 577, 198, 375, 399,
]
_KSC_SOUTH_BLUE = [
    365, 162, 455, 310, 148, 325, 330, 338, 385,
    340, 175, 440, 400, 490, 605, 215, 400, 425,
]

# —— 北場 Par 72 · 白梯 6357 碼 ——
_KSC_NORTH_PARS = [5, 4, 3, 4, 4, 4, 3, 5, 4, 4, 3, 5, 4, 3, 4, 4, 5, 4]
_KSC_NORTH_HCP = [5, 11, 9, 3, 13, 15, 17, 7, 1, 4, 12, 2, 18, 6, 14, 16, 8, 10]
_KSC_NORTH_WHITE = [
    523, 335, 166, 379, 330, 317, 143, 541, 452,
    450, 166, 508, 303, 168, 344, 308, 551, 373,
]

# —— 馬來西亞 · Templer Park · 白梯 6343 碼（官網記分卡）——
_TPCC_PARS = [5, 3, 4, 4, 4, 4, 5, 3, 4, 4, 3, 5, 4, 4, 5, 3, 4, 4]
_TPCC_HCP = [11, 15, 1, 7, 5, 17, 13, 9, 3, 16, 12, 6, 10, 14, 2, 18, 4, 8]
_TPCC_WHITE = [
    505, 145, 370, 340, 385, 363, 542, 143, 370,
    355, 155, 520, 360, 370, 535, 125, 380, 380,
]
_TPCC_BLUE = [
    535, 160, 400, 365, 410, 382, 554, 169, 395,
    370, 180, 530, 385, 385, 540, 145, 425, 395,
]

# —— 馬來西亞 · 雲頂 Awana · 白梯 5884 碼（GolfPass）——
_GENTING_PARS = [4, 4, 4, 3, 5, 3, 4, 5, 3, 4, 4, 5, 5, 4, 3, 4, 3, 4]
_GENTING_HCP = [1, 17, 7, 15, 5, 13, 9, 3, 11, 4, 14, 12, 6, 16, 10, 2, 18, 8]
_GENTING_WHITE = [
    399, 350, 314, 151, 503, 180, 325, 529, 132,
    422, 353, 443, 506, 334, 177, 326, 137, 303,
]
_GENTING_BLUE = [
    413, 385, 355, 176, 516, 207, 348, 560, 189,
    433, 375, 469, 527, 354, 221, 363, 155, 361,
]

COURSES = {
    "ksc-east": {
        "id": "ksc-east",
        "name": "滘西洲高爾夫球場 · 東場",
        "name_en": "Kau Sai Chau - East",
        "description": "Nelson & Haworth 設計，山丘臨海、景觀最美的一場。白梯 Par 72、6025 碼，需乘球車。",
        "location": "香港 · 西貢滘西洲",
        "region": "香港",
        "hero_image": _HERO,
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _KSC_EAST_PARS,
                "yardages": _KSC_EAST_WHITE,
                "handicap": _KSC_EAST_HCP,
            },
        },
    },
    "ksc-south": {
        "id": "ksc-south",
        "name": "滘西洲高爾夫球場 · 南場",
        "name_en": "Kau Sai Chau - South",
        "description": "Gary Player 設計，三場中最親和。白梯 Par 69、5906 碼，可步行或乘車。",
        "location": "香港 · 西貢滘西洲",
        "region": "香港",
        "hero_image": _HERO,
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _KSC_SOUTH_PARS,
                "yardages": _KSC_SOUTH_WHITE,
                "handicap": _KSC_SOUTH_HCP,
            },
            "blue": {
                "id": "blue",
                "name": "藍梯",
                "name_en": "Blue Tee",
                "pars": _KSC_SOUTH_PARS,
                "yardages": _KSC_SOUTH_BLUE,
                "handicap": _KSC_SOUTH_HCP,
            },
        },
    },
    "ksc-north": {
        "id": "ksc-north",
        "name": "滘西洲高爾夫球場 · 北場",
        "name_en": "Kau Sai Chau - North",
        "description": "Gary Player 設計，競賽級球道。白梯 Par 72、6357 碼，僅限步行。",
        "location": "香港 · 西貢滘西洲",
        "region": "香港",
        "hero_image": _HERO,
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _KSC_NORTH_PARS,
                "yardages": _KSC_NORTH_WHITE,
                "handicap": _KSC_NORTH_HCP,
            },
        },
    },
    "my-templer": {
        "id": "my-templer",
        "name": "Templer Park Country Club",
        "name_en": "Templer Park Country Club",
        "description": "Jumbo Ozaki & Kentaro Sato 設計，石灰岩山景與森林環繞。白梯 Par 72、6343 碼，吉隆坡近郊名場。",
        "location": "馬來西亞 · 雪蘭莪 Rawang",
        "region": "馬來西亞",
        "hero_image": _HERO,
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _TPCC_PARS,
                "yardages": _TPCC_WHITE,
                "handicap": _TPCC_HCP,
            },
            "blue": {
                "id": "blue",
                "name": "藍梯",
                "name_en": "Blue Tee",
                "pars": _TPCC_PARS,
                "yardages": _TPCC_BLUE,
                "handicap": _TPCC_HCP,
            },
        },
    },
    "my-genting": {
        "id": "my-genting",
        "name": "雲頂高原 · Awana 球場",
        "name_en": "Awana Genting Highlands",
        "description": "Ronald Fream 設計，海拔約 3100 呎，雲霧與雨林球道。白梯 Par 71、5884 碼，清涼高地體驗。",
        "location": "馬來西亞 · 彭亨雲頂",
        "region": "馬來西亞",
        "hero_image": _HERO,
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _GENTING_PARS,
                "yardages": _GENTING_WHITE,
                "handicap": _GENTING_HCP,
            },
            "blue": {
                "id": "blue",
                "name": "藍梯",
                "name_en": "Blue Tee",
                "pars": _GENTING_PARS,
                "yardages": _GENTING_BLUE,
                "handicap": _GENTING_HCP,
            },
        },
    },
}


def _tee_totals(tee):
    pars = tee["pars"]
    yardages = tee["yardages"]
    return {
        "par_total": sum(pars),
        "par_front": sum(pars[:9]),
        "par_back": sum(pars[9:]),
        "yardage_total": sum(yardages),
    }


def get_course(course_id):
    return COURSES.get(course_id)


def get_tee(course_id, tee_id):
    course = get_course(course_id)
    if not course:
        return None
    tee = course["tees"].get(tee_id)
    if not tee:
        return None
    return {**tee, **_tee_totals(tee), "course_id": course_id, "course_name": course["name"]}


def list_courses_for_web():
    """供前端選擇頁使用的精簡列表"""
    out = []
    for c in COURSES.values():
        tees = []
        for t in c["tees"].values():
            totals = _tee_totals(t)
            tees.append({
                "id": t["id"],
                "name": t["name"],
                "name_en": t.get("name_en", ""),
                "par_total": totals["par_total"],
                "yardage_total": totals["yardage_total"],
            })
        out.append({
            "id": c["id"],
            "name": c["name"],
            "name_en": c.get("name_en", ""),
            "description": c.get("description", ""),
            "location": c.get("location", ""),
            "region": c.get("region", ""),
            "hero_image": c.get("hero_image", _HERO),
            "tees": tees,
        })
    return out


def list_course_regions():
    """依 COURSES 順序回傳不重複地區標籤"""
    seen = []
    for c in COURSES.values():
        r = c.get("region", "")
        if r and r not in seen:
            seen.append(r)
    return seen


def courses_catalog_full():
    """完整 18 洞數據給記分 JS"""
    catalog = {}
    for cid, c in COURSES.items():
        catalog[cid] = {
            "id": cid,
            "name": c["name"],
            "hero_image": c.get("hero_image", _HERO),
            "tees": {},
        }
        for tid, t in c["tees"].items():
            totals = _tee_totals(t)
            catalog[cid]["tees"][tid] = {
                "id": tid,
                "name": t["name"],
                "pars": t["pars"],
                "yardages": t["yardages"],
                "handicap": t["handicap"],
                "par_total": totals["par_total"],
                "yardage_total": totals["yardage_total"],
            }
    return catalog


def resolve_course_tee(course_id, tee_id):
    """回傳 (tee_dict, error_message)"""
    if not course_id or not tee_id:
        return None, "請選擇球場與發球台"
    tee = get_tee(course_id, tee_id)
    if not tee:
        return None, "無效的球場或發球台"
    return tee, None


def course_meta_for_round(course_id, tee_id):
    """寫入 rounds.json 的球場資訊"""
    tee, err = resolve_course_tee(course_id, tee_id)
    if err:
        return None
    return {
        "course_id": course_id,
        "course": tee["course_name"],
        "tee_id": tee_id,
        "tee": tee["name"],
        "par_total": tee["par_total"],
        "yardage_total": tee["yardage_total"],
        "pars": tee["pars"],
    }
