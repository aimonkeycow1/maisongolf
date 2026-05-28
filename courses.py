"""
多球場 · 多 Tee 資料庫
新增球場：在 COURSES 加入一筆，並設定 tees 內的 pars / yardages / handicap
數據來源：球會官網 / GolfPass 公開記分卡（白梯 White Tee）
"""

from kl_courses import KL_COURSES

DEFAULT_COURSE_ID = "ksc-south"
DEFAULT_TEE_ID = "white"

_IMG = "/static/img"
_HERO = f"{_IMG}/hero.jpg"

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

# —— 泰國 · Alpine Golf · 白梯 6048 碼（GolfPass）——
_ALPINE_PARS = [4, 4, 3, 4, 5, 3, 5, 4, 4, 4, 4, 3, 4, 5, 3, 4, 5, 4]
_ALPINE_HCP = [17, 3, 13, 15, 5, 7, 9, 1, 11, 2, 6, 14, 16, 8, 12, 18, 4, 10]
_ALPINE_WHITE = [
    334, 374, 165, 334, 506, 190, 471, 370, 344,
    378, 349, 157, 325, 469, 160, 272, 521, 329,
]
_ALPINE_BLUE = [
    382, 399, 185, 357, 528, 210, 507, 425, 361,
    417, 387, 173, 345, 493, 179, 311, 555, 365,
]

# —— 泰國 · Thai Country Club · 白梯 6034 碼（Golfify / 官網）——
_TCC_TH_PARS = [4, 4, 3, 5, 4, 3, 5, 4, 4, 4, 3, 4, 4, 5, 4, 3, 5, 4]
_TCC_TH_HCP = [18, 12, 16, 4, 6, 8, 2, 14, 10, 9, 11, 3, 7, 1, 13, 17, 5, 15]
_TCC_TH_WHITE = [
    314, 337, 157, 443, 356, 167, 449, 365, 371,
    324, 124, 381, 347, 547, 352, 145, 522, 333,
]
_TCC_TH_BLUE = [
    353, 366, 176, 466, 393, 197, 476, 386, 413,
    337, 142, 410, 365, 579, 391, 166, 539, 365,
]

# —— 泰國 · Thana City · 白梯 6342 碼（Thai Golf Booking / 18Birdies）——
_THANA_PARS = [5, 4, 3, 4, 4, 4, 5, 3, 4, 4, 4, 5, 3, 5, 4, 3, 4, 4]
_THANA_HCP = [6, 18, 16, 10, 12, 8, 2, 14, 4, 11, 17, 5, 13, 1, 9, 15, 7, 3]
_THANA_WHITE = [
    562, 377, 154, 374, 307, 391, 540, 166, 396,
    349, 272, 450, 124, 482, 360, 206, 412, 420,
]

# —— 泰國 · Summit Windmill · 白梯 6211 碼（GolfPass）——
_SUMMIT_PARS = [5, 3, 4, 3, 4, 4, 5, 4, 4, 4, 4, 3, 4, 5, 4, 4, 3, 5]
_SUMMIT_HCP = [3, 17, 9, 15, 7, 1, 11, 13, 5, 10, 6, 18, 2, 14, 8, 12, 16, 4]
_SUMMIT_WHITE = [
    550, 134, 325, 181, 372, 419, 452, 305, 400,
    352, 358, 129, 403, 453, 363, 312, 160, 543,
]
_SUMMIT_BLUE = [
    618, 163, 378, 212, 413, 453, 504, 378, 438,
    385, 398, 154, 438, 493, 398, 371, 193, 577,
]

# —— 泰國 · Panya Indra Lagoon + Palm · 白梯 6744 碼（官網 A/B 九）——
_PANYA_PARS = [4, 4, 3, 5, 4, 4, 5, 3, 4, 5, 4, 4, 3, 4, 5, 4, 3, 4]
_PANYA_HCP = [9, 2, 8, 7, 1, 6, 5, 3, 4, 9, 8, 1, 7, 3, 5, 6, 4, 2]
_PANYA_WHITE = [
    370, 421, 155, 526, 437, 363, 511, 210, 390,
    528, 385, 420, 139, 398, 544, 371, 176, 400,
]

# 國家分類（選球場頁依此分組）
COUNTRY_ORDER = ["香港", "馬來西亞", "泰國"]
COUNTRY_META = {
    "香港": {"flag": "🇭🇰", "subtitle": "Hong Kong SAR"},
    "馬來西亞": {"flag": "🇲🇾", "subtitle": "Malaysia · KL & Klang Valley"},
    "泰國": {"flag": "🇹🇭", "subtitle": "Thailand · Bangkok"},
}

COURSES = {
    "ksc-east": {
        "id": "ksc-east",
        "name": "滘西洲高爾夫球場 · 東場",
        "name_en": "Kau Sai Chau - East",
        "description": "Nelson & Haworth 設計，山丘臨海、景觀最美的一場。白梯 Par 72、6025 碼，需乘球車。",
        "location": "西貢滘西洲",
        "country": "香港",
        "hero_image": f"{_IMG}/ksc-east.jpg",
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
        "location": "西貢滘西洲",
        "country": "香港",
        "hero_image": f"{_IMG}/ksc-south.jpg",
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
        "location": "西貢滘西洲",
        "country": "香港",
        "hero_image": f"{_IMG}/ksc-north.jpg",
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
        "location": "雪蘭莪 Rawang",
        "country": "馬來西亞",
        "hero_image": f"{_IMG}/my-templer.jpg",
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
        "location": "彭亨雲頂",
        "country": "馬來西亞",
        "hero_image": f"{_IMG}/my-genting.jpg",
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
    "th-alpine": {
        "id": "th-alpine",
        "name": "Alpine Golf & Sports Club",
        "name_en": "Alpine Golf & Sports Club",
        "description": "Ron Garl 設計，曼谷北郊 Pathum Thani 名場，曾舉辦泰國公開賽。白梯 Par 72、6048 碼，水障與沙坑策略性強。",
        "location": "曼谷 Pathum Thani",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-alpine.jpg",
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _ALPINE_PARS,
                "yardages": _ALPINE_WHITE,
                "handicap": _ALPINE_HCP,
            },
            "blue": {
                "id": "blue",
                "name": "藍梯",
                "name_en": "Blue Tee",
                "pars": _ALPINE_PARS,
                "yardages": _ALPINE_BLUE,
                "handicap": _ALPINE_HCP,
            },
        },
    },
    "th-tcc": {
        "id": "th-tcc",
        "name": "Thai Country Club",
        "name_en": "Thai Country Club",
        "description": "Denis Griffiths 設計，1997 亞洲本田經典賽 Tiger Woods 奪冠球場。白梯 Par 72、6034 碼，水景與起伏果嶺。",
        "location": "曼谷 Chachoengsao",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-tcc.jpg",
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _TCC_TH_PARS,
                "yardages": _TCC_TH_WHITE,
                "handicap": _TCC_TH_HCP,
            },
            "blue": {
                "id": "blue",
                "name": "藍梯",
                "name_en": "Blue Tee",
                "pars": _TCC_TH_PARS,
                "yardages": _TCC_TH_BLUE,
                "handicap": _TCC_TH_HCP,
            },
        },
    },
    "th-thana": {
        "id": "th-thana",
        "name": "Thana City Country Club",
        "name_en": "Thana City Country Club",
        "description": "Greg Norman 設計，泰國唯一由其操刀的 18 洞錦標場。白梯 Par 72、6342 碼，多座島嶼果嶺，近素萬那普機場。",
        "location": "曼谷 Samut Prakan",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-thana.jpg",
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _THANA_PARS,
                "yardages": _THANA_WHITE,
                "handicap": _THANA_HCP,
            },
        },
    },
    "th-summit": {
        "id": "th-summit",
        "name": "Summit Windmill Golf Club",
        "name_en": "Summit Windmill Golf Club",
        "description": "Nick Faldo 設計，機場旁度假式球場，湖泊與園景交錯。白梯 Par 72、6211 碼，可日間／夜間擊球。",
        "location": "曼谷 Samut Prakan",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-summit.jpg",
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _SUMMIT_PARS,
                "yardages": _SUMMIT_WHITE,
                "handicap": _SUMMIT_HCP,
            },
            "blue": {
                "id": "blue",
                "name": "藍梯",
                "name_en": "Blue Tee",
                "pars": _SUMMIT_PARS,
                "yardages": _SUMMIT_BLUE,
                "handicap": _SUMMIT_HCP,
            },
        },
    },
    "th-panya": {
        "id": "th-panya",
        "name": "Panya Indra · Lagoon + Palm",
        "name_en": "Panya Indra Golf Club (A+B)",
        "description": "Ronald Fream 設計 27 洞名場，此組合為 Lagoon 與 Palm 兩九。白梯 Par 72、6744 碼，水障與棕櫚球道，曾辦 LPGA。",
        "location": "曼谷 Khan Na Yao",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-panya.jpg",
        "tees": {
            "white": {
                "id": "white",
                "name": "白梯",
                "name_en": "White Tee",
                "pars": _PANYA_PARS,
                "yardages": _PANYA_WHITE,
                "handicap": _PANYA_HCP,
            },
        },
    },
    **KL_COURSES,
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
            tee_row = {
                "id": t["id"],
                "name": t["name"],
                "name_en": t.get("name_en", ""),
                "par_total": totals["par_total"],
                "yardage_total": totals["yardage_total"],
            }
            if t.get("course_rating") is not None:
                tee_row["course_rating"] = t["course_rating"]
            if t.get("slope_rating") is not None:
                tee_row["slope_rating"] = t["slope_rating"]
            tees.append(tee_row)
        out.append({
            "id": c["id"],
            "name": c["name"],
            "name_en": c.get("name_en", ""),
            "description": c.get("description", ""),
            "location": c.get("location", ""),
            "city": c.get("city", ""),
            "address": c.get("address", ""),
            "country": c.get("country", ""),
            "architect": c.get("architect", ""),
            "visitor_policy": c.get("visitor_policy", ""),
            "features": c.get("features", []),
            "photos": c.get("photos", []),
            "hero_image": c.get("hero_image", _HERO),
            "tees": tees,
        })
    return out


def list_hero_carousel_slides():
    """首頁 Hero 走馬燈：各球場真實照片與文案（依國家順序）"""
    slides = []
    for country in COUNTRY_ORDER:
        for c in COURSES.values():
            if c.get("country") != country:
                continue
            tee = c["tees"].get("white") or next(iter(c["tees"].values()))
            totals = _tee_totals(tee)
            tee_label = tee.get("name_en") or tee["name"]
            slides.append({
                "id": c["id"],
                "name": c["name"],
                "badge": f"{tee_label.upper()} · PAR {totals['par_total']}",
                "subtitle": (
                    f"{c['country']} · {c['location']} · "
                    f"{tee['name']} · {totals['yardage_total']} 碼"
                ),
                "image": c.get("hero_image", _HERO),
            })
    return slides


def list_course_countries():
    """依 COUNTRY_ORDER 回傳國家列表（僅含實際有球場的國家）"""
    present = {c.get("country") for c in COURSES.values() if c.get("country")}
    return [name for name in COUNTRY_ORDER if name in present]


def list_courses_by_country():
    """選球場頁：按國家分組的球場列表"""
    catalog = list_courses_for_web()
    groups = []
    for country in list_course_countries():
        meta = COUNTRY_META.get(country, {})
        courses = [c for c in catalog if c["country"] == country]
        groups.append({
            "country": country,
            "flag": meta.get("flag", ""),
            "subtitle": meta.get("subtitle", ""),
            "count": len(courses),
            "courses": courses,
        })
    return groups


def list_course_regions():
    """向後相容"""
    return list_course_countries()


def courses_catalog_full():
    """完整 18 洞數據給記分 JS"""
    catalog = {}
    for cid, c in COURSES.items():
        catalog[cid] = {
            "id": cid,
            "name": c["name"],
            "name_en": c.get("name_en", ""),
            "description": c.get("description", ""),
            "country": c.get("country", ""),
            "location": c.get("location", ""),
            "city": c.get("city", ""),
            "address": c.get("address", ""),
            "hero_image": c.get("hero_image", _HERO),
            "photos": c.get("photos", []),
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
                "course_rating": t.get("course_rating"),
                "slope_rating": t.get("slope_rating"),
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
