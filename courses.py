"""
多球場 · 多 Tee 資料庫
新增球場：在 COURSES 加入一筆，並設定 tees 內的 pars / yardages / handicap
"""

DEFAULT_COURSE_ID = "ksc-south"
DEFAULT_TEE_ID = "white"

# 滘西洲南場 · 白梯（公開記分卡）
_KSC_SOUTH_PARS = [4, 3, 4, 4, 3, 4, 4, 4, 4, 4, 3, 4, 4, 4, 5, 3, 4, 4]
_KSC_SOUTH_HCP = [5, 11, 1, 17, 7, 15, 9, 13, 3, 16, 14, 4, 10, 2, 8, 6, 18, 12]
_KSC_SOUTH_WHITE = [
    341, 149, 429, 285, 134, 301, 307, 315, 362,
    317, 159, 417, 377, 464, 577, 198, 375, 399,
]
# 藍梯：較白梯為長（參考公開資料估算，Par 相同）
_KSC_SOUTH_BLUE = [
    365, 162, 455, 310, 148, 325, 330, 338, 385,
    340, 175, 440, 400, 490, 605, 215, 400, 425,
]

COURSES = {
    "ksc-south": {
        "id": "ksc-south",
        "name": "滘西洲高爾夫球場 · 南場",
        "name_en": "Kau Sai Chau Public Golf Course - South",
        "description": "香港西貢離島名場，臨海球道與山景交織，南場白梯全長約 5906 碼、Par 69。",
        "location": "香港 · 西貢滘西洲",
        "hero_image": "/static/img/hero.jpg",
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
            "hero_image": c.get("hero_image", "/static/img/hero.jpg"),
            "tees": tees,
        })
    return out


def courses_catalog_full():
    """完整 18 洞數據給記分 JS"""
    catalog = {}
    for cid, c in COURSES.items():
        catalog[cid] = {
            "id": cid,
            "name": c["name"],
            "hero_image": c.get("hero_image", "/static/img/hero.jpg"),
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
