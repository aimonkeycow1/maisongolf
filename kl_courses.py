"""
吉隆坡（Klang Valley）熱門球場資料
格式與 courses.py 的 COURSES 完全一致；由 courses.py 合併匯入。

資料來源：GolfPass / Golfify / 球會官網公開記分卡（2024–2026）。
照片：Unsplash 高爾夫主題 placeholder，之後可替換為球會授權圖片。
"""

from __future__ import annotations

_IMG = "/static/img"

# 通用高爾夫場景圖（placeholder，註明可替換）
_PHOTO_GOLF_1 = "https://images.unsplash.com/photo-1535131749006-b7f58c990b8e?auto=format&fit=crop&w=1600&q=80"
_PHOTO_GOLF_2 = "https://images.unsplash.com/photo-1587174482993-4eccc5aa6169?auto=format&fit=crop&w=1600&q=80"
_PHOTO_GOLF_3 = "https://images.unsplash.com/photo-1593111778420-763a58753d32?auto=format&fit=crop&w=1600&q=80"
_PHOTO_GOLF_4 = "https://images.unsplash.com/photo-1592919505780-303950717480?auto=format&fit=crop&w=1600&q=80"
_PHOTO_LAKE = "https://images.unsplash.com/photo-1596727147705-61a532a659b9?auto=format&fit=crop&w=1600&q=80"

# —— KLGCC West · Par 72（GolfPass 白梯 5606 yds）——
_KL_WEST_PARS = [4, 4, 5, 3, 5, 4, 4, 3, 4, 5, 3, 4, 4, 4, 3, 4, 4, 5]
_KL_WEST_HCP = [5, 3, 1, 17, 7, 11, 9, 15, 13, 4, 16, 6, 2, 12, 18, 8, 14, 10]
_KL_WEST_WHITE = [
    346, 411, 457, 120, 468, 388, 340, 170, 359,
    474, 173, 427, 365, 318, 155, 284, 291, 562,
]
_KL_WEST_BLUE = [
    384, 428, 489, 129, 500, 395, 375, 188, 384,
    516, 202, 448, 413, 338, 180, 294, 324, 618,
]
_KL_WEST_BLACK = [
    401, 444, 503, 140, 518, 420, 386, 203, 404,
    539, 226, 479, 459, 358, 199, 318, 336, 634,
]
_KL_WEST_RED = [
    337, 390, 419, 113, 447, 363, 322, 143, 314,
    421, 142, 388, 332, 299, 127, 264, 276, 521,
]

# —— KLGCC East · Par 71（白梯約 5815 yds）——
_KL_EAST_PARS = [4, 4, 4, 4, 3, 5, 3, 4, 4, 4, 4, 5, 4, 4, 3, 5, 3, 4]
_KL_EAST_HCP = [9, 13, 5, 11, 17, 1, 15, 7, 3, 12, 8, 4, 10, 14, 18, 2, 16, 6]
_KL_EAST_WHITE = [
    334, 377, 370, 321, 180, 528, 143, 360, 382,
    329, 356, 528, 343, 339, 133, 533, 169, 364,
]
_KL_EAST_BLUE = [
    361, 408, 400, 347, 195, 570, 154, 389, 413,
    355, 385, 570, 370, 366, 144, 575, 183, 393,
]

# —— The Mines · Par 71（Golfify 白梯 5275 yds）——
_MINES_PARS = [4, 3, 5, 4, 4, 4, 3, 4, 4, 4, 5, 4, 4, 3, 4, 3, 5, 4]
_MINES_HCP = [9, 11, 13, 1, 5, 17, 15, 3, 7, 16, 4, 2, 8, 12, 18, 10, 14, 6]
_MINES_WHITE = [
    280, 119, 431, 347, 349, 279, 114, 332, 334,
    292, 455, 378, 303, 143, 213, 146, 429, 331,
]
_MINES_BLUE = [
    307, 133, 454, 371, 374, 301, 142, 354, 376,
    328, 490, 409, 331, 154, 256, 153, 453, 363,
]
_MINES_GOLD = [
    359, 168, 447, 362, 168, 280, 167, 495, 397,
    336, 145, 497, 406, 409, 329, 155, 387, 411,
]

# —— Saujana Palm · Par 72（Golfify 白梯 6104 yds）——
_SAUJANA_PARS = [4, 3, 5, 4, 3, 4, 5, 4, 4, 4, 4, 3, 5, 4, 4, 3, 4, 5]
_SAUJANA_HCP = [11, 13, 7, 15, 17, 1, 9, 3, 5, 10, 6, 16, 18, 2, 4, 14, 12, 8]
_SAUJANA_WHITE = [
    295, 144, 548, 269, 147, 367, 514, 334, 338,
    345, 362, 162, 458, 402, 377, 148, 354, 540,
]
_SAUJANA_BLUE = [
    322, 172, 567, 308, 170, 439, 544, 375, 359,
    359, 388, 176, 503, 439, 400, 166, 366, 557,
]

# —— Glenmarie Valley · Par 72（GolfPass 白梯 5983 yds）——
_GLEN_PARS = [4, 5, 4, 3, 5, 4, 4, 3, 4, 4, 4, 3, 4, 5, 3, 4, 4, 5]
_GLEN_HCP = [1, 15, 13, 17, 7, 3, 5, 9, 11, 6, 16, 10, 4, 8, 12, 14, 2, 18]
_GLEN_WHITE = [
    347, 456, 287, 148, 482, 339, 339, 165, 317,
    352, 352, 210, 361, 481, 148, 329, 381, 489,
]
_GLEN_BLUE = [
    384, 490, 331, 157, 506, 371, 354, 190, 344,
    388, 370, 222, 395, 513, 170, 351, 414, 518,
]

# —— Tropicana East 18（East 1 + East 2 · 白梯 6201 yds）——
_TROP_PARS = [4, 4, 3, 5, 4, 5, 4, 3, 4, 4, 4, 4, 3, 5, 4, 4, 3, 5]
_TROP_HCP = [3, 9, 11, 13, 1, 15, 5, 17, 7, 12, 8, 14, 18, 6, 4, 2, 10, 16]
_TROP_WHITE = [
    345, 388, 164, 478, 353, 434, 379, 139, 328,
    371, 351, 349, 145, 518, 419, 387, 176, 477,
]
_TROP_BLUE = [
    375, 416, 186, 527, 401, 483, 397, 171, 362,
    390, 383, 386, 161, 568, 448, 429, 207, 495,
]


def _tee(
    tid: str,
    name: str,
    name_en: str,
    pars: list[int],
    yardages: list[int],
    handicap: list[int],
    *,
    course_rating: float | None = None,
    slope_rating: int | None = None,
) -> dict:
    row = {
        "id": tid,
        "name": name,
        "name_en": name_en,
        "pars": pars,
        "yardages": yardages,
        "handicap": handicap,
    }
    if course_rating is not None:
        row["course_rating"] = course_rating
    if slope_rating is not None:
        row["slope_rating"] = slope_rating
    return row


KL_COURSES = {
    "kl-gcc-west": {
        "id": "kl-gcc-west",
        "name": "吉隆坡高爾夫鄉村俱樂部 · 西場",
        "name_en": "KLGCC - West Course",
        "description": (
            "馬來西亞經典錦標場，曾舉辦歐巡與亞巡賽事。"
            "西場 Par 72、白梯約 5606 碼，球道寬敞、果嶺快速，適合進攻型球友。"
        ),
        "location": "吉隆坡 Bukit Kiara",
        "city": "Kuala Lumpur",
        "address": "10, Jalan 1/70D, Off Jalan Bukit Kiara, 60000 Kuala Lumpur",
        "country": "馬來西亞",
        "architect": "Original layout; TPC renovation",
        "visitor_policy": "訪客需預約；平日／假日球費分級（官網參考）",
        "features": ["錦標賽場", "TPC 規格", "電球車", "球僮"],
        "hero_image": f"{_IMG}/kl-gcc-west.jpg",
        "photos": [_PHOTO_GOLF_1, _PHOTO_GOLF_2, _PHOTO_LAKE, _PHOTO_GOLF_3],
        "tees": {
            "white": _tee(
                "white", "白梯", "White Tee",
                _KL_WEST_PARS, _KL_WEST_WHITE, _KL_WEST_HCP,
                course_rating=70.8, slope_rating=129,
            ),
            "blue": _tee(
                "blue", "藍梯", "Blue Tee",
                _KL_WEST_PARS, _KL_WEST_BLUE, _KL_WEST_HCP,
                course_rating=73.1, slope_rating=134,
            ),
            "black": _tee(
                "black", "黑梯", "Black Tee",
                _KL_WEST_PARS, _KL_WEST_BLACK, _KL_WEST_HCP,
                course_rating=74.8, slope_rating=137,
            ),
            "red": _tee(
                "red", "紅梯", "Red Tee",
                _KL_WEST_PARS, _KL_WEST_RED, _KL_WEST_HCP,
                course_rating=67.8, slope_rating=121,
            ),
        },
    },
    "kl-gcc-east": {
        "id": "kl-gcc-east",
        "name": "吉隆坡高爾夫鄉村俱樂部 · 東場",
        "name_en": "KLGCC - East Course",
        "description": (
            "Nelson & Wright 設計的園景球場，曾長期舉辦 LPGA 馬來西亞站。"
            "東場 Par 71、白梯約 5815 碼，濕地與水障策略性強，後九難度較高。"
        ),
        "location": "吉隆坡 Bukit Kiara",
        "city": "Kuala Lumpur",
        "address": "10, Jalan 1/70D, Off Jalan Bukit Kiara, 60000 Kuala Lumpur",
        "country": "馬來西亞",
        "architect": "Nelson & Wright",
        "visitor_policy": "訪客需預約；與西場共用俱樂部設施",
        "features": ["LPGA 賽事球場", "濕地景觀", "水障多", "電球車"],
        "hero_image": f"{_IMG}/kl-gcc-east.jpg",
        "photos": [_PHOTO_GOLF_2, _PHOTO_LAKE, _PHOTO_GOLF_4, _PHOTO_GOLF_1],
        "tees": {
            "white": _tee(
                "white", "白梯", "White Tee",
                _KL_EAST_PARS, _KL_EAST_WHITE, _KL_EAST_HCP,
                course_rating=68.1, slope_rating=124,
            ),
            "blue": _tee(
                "blue", "藍梯", "Blue Tee",
                _KL_EAST_PARS, _KL_EAST_BLUE, _KL_EAST_HCP,
                course_rating=71.2, slope_rating=130,
            ),
        },
    },
    "kl-mines": {
        "id": "kl-mines",
        "name": "The Mines 度假高爾夫俱樂部",
        "name_en": "The Mines Resort & Golf Club",
        "description": (
            "Robert Trent Jones Jr. 設計，從礦場廢址再造的園景球場。"
            "Par 71、白梯 5275 碼，前九較短、後九水障與峽谷洞精彩，距 KL 約 20 分鐘。"
        ),
        "location": "雪蘭莪 Seri Kembangan",
        "city": "Kuala Lumpur",
        "address": "Jalan Kelikir, Mines Wellness City, 43300 Seri Kembangan, Selangor",
        "country": "馬來西亞",
        "architect": "Robert Trent Jones Jr.",
        "visitor_policy": "訪客擊球需透過球會／代理預約",
        "features": ["礦場再造", "水障策略", "園景球道", "度假設施"],
        "hero_image": f"{_IMG}/kl-mines.jpg",
        "photos": [_PHOTO_LAKE, _PHOTO_GOLF_3, _PHOTO_GOLF_1, _PHOTO_GOLF_2],
        "tees": {
            "white": _tee(
                "white", "白梯", "White Tee",
                _MINES_PARS, _MINES_WHITE, _MINES_HCP,
                course_rating=68.5, slope_rating=124,
            ),
            "blue": _tee(
                "blue", "藍梯", "Blue Tee",
                _MINES_PARS, _MINES_BLUE, _MINES_HCP,
                course_rating=70.6, slope_rating=126,
            ),
            "gold": _tee(
                "gold", "金梯", "Gold Tee",
                _MINES_PARS, _MINES_GOLD, _MINES_HCP,
                course_rating=72.0, slope_rating=133,
            ),
        },
    },
    "kl-saujana-palm": {
        "id": "kl-saujana-palm",
        "name": "Saujana 高爾夫鄉村俱樂部 · Palm",
        "name_en": "Saujana Golf & CC - Palm Course",
        "description": (
            "Ronald Fream 設計，暱稱「Cobra」，馬來西亞公開賽多屆賽場。"
            "Par 72、白梯 6104 碼，棕櫚夾道、起伏大，被公認為全馬最具挑戰球場之一。"
        ),
        "location": "雪蘭莪 Shah Alam",
        "city": "Kuala Lumpur",
        "address": "Saujana Resort, Jalan Lapangan Terbang SAAS, 40150 Shah Alam, Selangor",
        "country": "馬來西亞",
        "architect": "Ronald Fream",
        "visitor_policy": "訪客歡迎；建議提前預約開球時間",
        "features": ["馬來西亞公開賽", "高難度", "水障", "棕櫚球道"],
        "hero_image": f"{_IMG}/kl-saujana-palm.jpg",
        "photos": [_PHOTO_GOLF_4, _PHOTO_GOLF_1, _PHOTO_GOLF_2, _PHOTO_LAKE],
        "tees": {
            "white": _tee(
                "white", "白梯", "White Tee",
                _SAUJANA_PARS, _SAUJANA_WHITE, _SAUJANA_HCP,
                course_rating=70.3, slope_rating=137,
            ),
            "blue": _tee(
                "blue", "藍梯", "Blue Tee",
                _SAUJANA_PARS, _SAUJANA_BLUE, _SAUJANA_HCP,
                course_rating=73.0, slope_rating=140,
            ),
        },
    },
    "kl-glenmarie-valley": {
        "id": "kl-glenmarie-valley",
        "name": "Glenmarie 高爾夫鄉村俱樂部 · Valley",
        "name_en": "Glenmarie G&CC - Valley Course",
        "description": (
            "園景丘陵球場，球道沿人工湖蜿蜒。"
            "Par 72、白梯 5983 碼，起伏明顯，與 Garden 場互補，距 Subang 約 15 分鐘。"
        ),
        "location": "雪蘭莪 Shah Alam",
        "city": "Kuala Lumpur",
        "address": "Jalan Kontraktor U1/14, Glenmarie, 40150 Shah Alam, Selangor",
        "country": "馬來西亞",
        "architect": "Ted Parslow",
        "visitor_policy": "訪客擊球開放；可搭配酒店住宿",
        "features": ["雙球場俱樂部", "湖泊景觀", "丘陵球道", "練習場"],
        "hero_image": f"{_IMG}/kl-glenmarie-valley.jpg",
        "photos": [_PHOTO_GOLF_3, _PHOTO_LAKE, _PHOTO_GOLF_4, _PHOTO_GOLF_1],
        "tees": {
            "white": _tee(
                "white", "白梯", "White Tee",
                _GLEN_PARS, _GLEN_WHITE, _GLEN_HCP,
                course_rating=69.1, slope_rating=126,
            ),
            "blue": _tee(
                "blue", "藍梯", "Blue Tee",
                _GLEN_PARS, _GLEN_BLUE, _GLEN_HCP,
                course_rating=71.3, slope_rating=130,
            ),
        },
    },
    "kl-tropicana-east": {
        "id": "kl-tropicana-east",
        "name": "Tropicana 高爾夫鄉村度假村 · East",
        "name_en": "Tropicana Golf & Country Resort - East",
        "description": (
            "Graham Marsh 設計 27 洞中的 18 洞 East 組合（East 1 + East 2）。"
            "Par 72、白梯 6201 碼，瀑布與水障景觀，支援夜間擊球與快速排水。"
        ),
        "location": "八打靈再也 Petaling Jaya",
        "city": "Kuala Lumpur",
        "address": "Jalan Kelab Tropicana, 47410 Petaling Jaya, Selangor",
        "country": "馬來西亞",
        "architect": "Graham Marsh",
        "visitor_policy": "訪客歡迎；夜間球場需預約時段",
        "features": ["夜間擊球", "水景瀑布", "27 洞系統", "快速排水"],
        "hero_image": f"{_IMG}/kl-tropicana-east.jpg",
        "photos": [_PHOTO_LAKE, _PHOTO_GOLF_2, _PHOTO_GOLF_3, _PHOTO_GOLF_4, _PHOTO_GOLF_1],
        "tees": {
            "white": _tee(
                "white", "白梯", "White Tee",
                _TROP_PARS, _TROP_WHITE, _TROP_HCP,
                course_rating=70.7, slope_rating=127,
            ),
            "blue": _tee(
                "blue", "藍梯", "Blue Tee",
                _TROP_PARS, _TROP_BLUE, _TROP_HCP,
                course_rating=73.4, slope_rating=132,
            ),
        },
    },
}
