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

# —— 東場 Par 72 · 數據來源：GolfPass（官方記分卡）——
# Tee    Dist   CR    SR
# Blue   6640  71.7  133
# White  6025  69.0  124
# Yellow 5634  67.1  116
# Red    4593  65.8  108
_KSC_EAST_PARS = [5, 4, 3, 4, 3, 5, 4, 3, 4,  5, 4, 4, 3, 4, 3, 5, 4, 5]  # Par 72
_KSC_EAST_HCP  = [11, 5, 17, 9, 15, 1, 13, 7, 3,  8, 12, 16, 14, 4, 18, 10, 2, 6]
_KSC_EAST_BLUE = [
    528, 386, 174, 366, 211, 527, 346, 232, 425,
    501, 416, 294, 209, 366, 147, 522, 441, 549,
]
_KSC_EAST_WHITE = [
    500, 352, 157, 304, 125, 507, 329, 199, 403,
    466, 370, 259, 137, 347, 130, 496, 411, 533,
]
_KSC_EAST_YELLOW = [
    476, 317, 138, 286, 119, 442, 313, 189, 382,
    439, 351, 249, 124, 343, 129, 452, 389, 496,
]

# —— 南場 Par 69 · 數據來源：GolfPass（官方記分卡）——
# Tee    Dist   CR    SR
# White  5906  68.7  125
# Yellow 5411  66.4  121
# Red    4734  67.2  117  (Ladies)
_KSC_SOUTH_PARS = [4, 3, 4, 4, 3, 4, 4, 4, 4,  4, 3, 4, 4, 4, 5, 3, 4, 4]  # Par 69
_KSC_SOUTH_HCP  = [5, 11, 1, 17, 7, 15, 9, 13, 3,  16, 14, 4, 10, 2, 8, 6, 18, 12]
_KSC_SOUTH_WHITE = [
    341, 149, 429, 285, 134, 301, 307, 315, 362,
    317, 159, 417, 377, 464, 577, 198, 375, 399,
]
_KSC_SOUTH_YELLOW = [
    317, 130, 401, 260, 131, 288, 276, 292, 341,
    287, 139, 394, 289, 425, 517, 180, 356, 388,
]

# —— 北場 Par 72 · 數據來源：GolfPass（官方記分卡）——
# Tee    Dist   CR    SR
# Blue   6719  73.4  134
# White  6357  71.2  133
# Yellow 6004  69.5  122
# Red    5414  71.7  121  (Ladies)
_KSC_NORTH_PARS = [5, 4, 3, 4, 4, 4, 3, 5, 4,  4, 3, 5, 4, 3, 4, 4, 5, 4]  # Par 72
_KSC_NORTH_HCP  = [5, 11, 9, 3, 13, 15, 17, 7, 1,  4, 12, 2, 18, 6, 14, 16, 8, 10]
_KSC_NORTH_BLUE = [
    560, 364, 174, 401, 348, 338, 148, 568, 464,
    462, 210, 521, 308, 205, 344, 308, 570, 426,
]
_KSC_NORTH_WHITE = [
    523, 335, 166, 379, 330, 317, 143, 541, 452,
    450, 166, 508, 303, 168, 344, 308, 551, 373,
]
_KSC_NORTH_YELLOW = [
    500, 306, 152, 362, 325, 294, 124, 511, 391,
    436, 141, 486, 293, 163, 330, 285, 549, 356,
]

# —— 清水灣高爾夫球場 · Par 70 · 官方 GolfPass / Golfify 記分卡 ——
# 數據來源：golfify.io + golfpass.com（2024 年版）
# Tee  Color    Dist    CR    SR
# Black         6608   73.4  140
# Blue          6193   71.4  128
# White         5793   69.2  123
# Red (Ladies)  5274   71.6  123
_CWBGC_PARS = [3, 5, 4, 3, 5, 3, 4, 4, 4,  4, 3, 4, 4, 3, 5, 3, 4, 5]  # Par 70
_CWBGC_HCP  = [11, 3, 1, 17, 5, 7, 15, 9, 13,  4, 16, 8, 2, 18, 12, 14, 6, 10]
_CWBGC_BLACK = [
    224, 573, 402, 186, 545, 211, 348, 342, 340,
    468, 216, 460, 446, 173, 529, 193, 409, 543,
]
_CWBGC_BLUE = [
    218, 561, 389, 157, 528, 199, 302, 331, 318,
    443, 173, 432, 420, 165, 499, 177, 366, 515,
]
_CWBGC_WHITE = [
    191, 538, 370, 141, 512, 180, 283, 320, 295,
    423, 155, 399, 383, 146, 479, 156, 332, 490,
]
_CWBGC_RED = [
    178, 510, 338, 124, 485, 165, 252, 301, 245,
    403, 126, 369, 339, 133, 447, 145, 322, 457,
]

# —— 香港哥爾夫球會 · 粉嶺 Eden 場 · Par 70 · 官方記分卡（HKGC 2024 年 11 月版）——
# 數據來源：hkgolfclub.org PDF + golfpass.com
# Tee           Dist    CR    SR
# Championship  6106   70.7  130
# Club          5688   68.8  126
# Forward       5373   67.4  123
_HKGC_EDEN_PARS = [5, 3, 4, 4, 3, 5, 5, 4, 3,  4, 4, 3, 4, 4, 3, 5, 3, 4]  # Par 70
_HKGC_EDEN_HCP  = [7, 17, 9, 1, 15, 3, 5, 13, 11,  4, 8, 16, 2, 12, 14, 10, 18, 6]
_HKGC_EDEN_CHAMP = [
    468, 149, 370, 428, 148, 493, 551, 288, 192,
    436, 381, 188, 410, 363, 200, 493, 138, 410,
]
_HKGC_EDEN_CLUB = [
    440, 132, 358, 406, 126, 463, 491, 272, 172,
    384, 370, 173, 394, 340, 181, 474, 125, 387,
]
_HKGC_EDEN_FWD = [
    424, 121, 341, 387, 111, 439, 460, 261, 164,
    370, 359, 165, 382, 317, 145, 444, 109, 374,
]

# —— 馬來西亞 · Templer Park · 官網記分卡 ——
# 數據來源：tpcc.com.my + golfify.io（2024 年）
# Tee    Dist   CR    SR
# Black  7143  73.2  131
# Blue   6725  71.6  127
# White  6343  69.8  124
# Red    5480  69.0   —
_TPCC_PARS = [5, 3, 4, 4, 4, 4, 5, 3, 4,  4, 3, 5, 4, 4, 5, 3, 4, 4]  # Par 72
_TPCC_HCP  = [11, 15, 1, 7, 5, 17, 13, 9, 3,  16, 12, 6, 10, 14, 2, 18, 4, 8]
_TPCC_BLACK = [
    544, 190, 430, 395, 430, 396, 567, 196, 420,
    405, 200, 560, 420, 400, 575, 160, 440, 415,
]
_TPCC_BLUE = [
    535, 160, 400, 365, 410, 382, 554, 169, 395,
    370, 180, 530, 385, 385, 540, 145, 425, 395,
]
_TPCC_WHITE = [
    505, 145, 370, 340, 385, 363, 542, 143, 370,
    355, 155, 520, 360, 370, 535, 125, 380, 380,
]
_TPCC_RED = [
    440, 120, 350, 315, 335, 290, 440, 125, 320,
    290, 120, 445, 340, 315, 445, 100, 340, 350,
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

# —— 泰國 · Alpine Golf · 官方記分卡（golfify.io / alpinegolfclub.com）——
# 數據來源：Golfify 2024 年
# Tee    Dist   CR    SR
# Black  7100  75.3  148
# Blue   6579  72.5  142
# White  6048  70.0  134
# Red    5226  71.1  128
_ALPINE_PARS = [4, 4, 3, 4, 5, 3, 5, 4, 4,  4, 4, 3, 4, 5, 3, 4, 5, 4]  # Par 72
_ALPINE_HCP  = [17, 3, 13, 15, 5, 7, 9, 1, 11,  2, 6, 14, 16, 8, 12, 18, 4, 10]
_ALPINE_BLACK = [
    406, 434, 207, 376, 569, 238, 555, 441, 380,
    433, 412, 200, 367, 546, 202, 355, 577, 402,
]
_ALPINE_BLUE = [
    382, 399, 185, 357, 528, 210, 507, 425, 361,
    417, 387, 173, 345, 493, 179, 311, 555, 365,
]
_ALPINE_WHITE = [
    334, 374, 165, 334, 506, 190, 471, 370, 344,
    378, 349, 157, 325, 469, 160, 272, 521, 329,
]
_ALPINE_RED = [
    296, 327, 137, 302, 412, 140, 431, 313, 312,
    335, 304, 125, 273, 404, 135, 245, 459, 276,
]

# —— 泰國 · Thai Country Club · 官方記分卡（Golfify 2024 年）——
# 數據來源：golfify.io
# Tee    Dist   CR    SR
# Black  7097  74.2  133
# Blue   6520  71.6  127
# White  6034  69.4  122
# Red    5248  71.1  119
_TCC_TH_PARS = [4, 4, 3, 5, 4, 3, 5, 4, 4,  4, 3, 4, 4, 5, 4, 3, 5, 4]  # Par 72
_TCC_TH_HCP  = [18, 12, 16, 4, 6, 8, 2, 14, 10,  9, 11, 3, 7, 1, 13, 17, 5, 15]
_TCC_TH_BLACK = [
    362, 399, 202, 497, 424, 227, 513, 414, 449,
    356, 161, 443, 418, 608, 431, 185, 573, 435,
]
_TCC_TH_BLUE = [
    353, 366, 176, 466, 393, 197, 476, 386, 413,
    337, 142, 410, 365, 579, 391, 166, 539, 365,
]
_TCC_TH_WHITE = [
    314, 337, 157, 443, 356, 167, 449, 365, 371,
    324, 124, 381, 347, 547, 352, 145, 522, 333,
]
_TCC_TH_RED = [
    246, 304, 131, 419, 317, 136, 421, 306, 325,
    270, 106, 330, 297, 488, 271, 104, 486, 291,
]

# —— 泰國 · Thana City · 官方記分卡（Thai Golf Booking）——
# Greg Norman 設計。數據來源：thaigolfbooking.com / GolfPass
# Tee    Dist   CR    SR
# White  6342  71.8  128
_THANA_PARS = [5, 4, 3, 4, 4, 4, 5, 3, 4,  4, 4, 5, 3, 5, 4, 3, 4, 4]  # Par 72
_THANA_HCP  = [6, 18, 16, 10, 12, 8, 2, 14, 4,  11, 17, 5, 13, 1, 9, 15, 7, 3]
_THANA_WHITE = [
    562, 377, 154, 374, 307, 391, 540, 166, 396,
    349, 272, 450, 124, 482, 360, 206, 412, 420,
]

# —— 泰國 · Summit Windmill · 官方記分卡（GolfPass / Thai Golf Booking）——
# Nick Faldo 設計。數據來源：golfpass.com + thaigolfbooking.com
# Tee    Dist   CR    SR
# Blue   6964  73.1  123
# White  6211  70.7  121
# Orange 5874  69.2  117
_SUMMIT_PARS = [5, 3, 4, 3, 4, 4, 5, 4, 4,  4, 4, 3, 4, 5, 4, 4, 3, 5]  # Par 72
_SUMMIT_HCP  = [3, 17, 9, 15, 7, 1, 11, 13, 5,  10, 6, 18, 2, 14, 8, 12, 16, 4]
_SUMMIT_BLUE = [
    618, 163, 378, 212, 413, 453, 504, 378, 438,
    385, 398, 154, 438, 493, 398, 371, 193, 577,
]
_SUMMIT_WHITE = [
    550, 134, 325, 181, 372, 419, 452, 305, 400,
    352, 358, 129, 403, 453, 363, 312, 160, 543,
]
_SUMMIT_ORANGE = [
    535, 124, 318, 169, 360, 379, 435, 285, 377,
    349, 332, 139, 385, 429, 335, 299, 149, 475,
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
    # ── 香港 ──────────────────────────────────────────────────────────────────
    "ksc-east": {
        "id": "ksc-east",
        "name": "滘西洲高爾夫球場 · 東場",
        "name_en": "Kau Sai Chau - East",
        "architect": "Robin Nelson & Neil Haworth",
        "description": (
            "Nelson & Haworth 設計，海蝕崖與藍海全景，三場中景觀最壯麗。"
            "Par 72、白梯 6025 碼（藍梯 6640 碼），需乘球車，風向多變。"
        ),
        "location": "西貢滘西洲",
        "country": "香港",
        "hero_image": f"{_IMG}/ksc-east.jpg",
        "slope": 124, "rating": 69.0,
        "tees": {
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _KSC_EAST_PARS, "yardages": _KSC_EAST_BLUE,
                "handicap": _KSC_EAST_HCP, "slope": 133, "rating": 71.7,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _KSC_EAST_PARS, "yardages": _KSC_EAST_WHITE,
                "handicap": _KSC_EAST_HCP, "slope": 124, "rating": 69.0,
            },
            "yellow": {
                "id": "yellow", "name": "黃梯", "name_en": "Yellow Tee",
                "pars": _KSC_EAST_PARS, "yardages": _KSC_EAST_YELLOW,
                "handicap": _KSC_EAST_HCP, "slope": 116, "rating": 67.1,
            },
        },
    },
    "ksc-south": {
        "id": "ksc-south",
        "name": "滘西洲高爾夫球場 · 南場",
        "name_en": "Kau Sai Chau - South",
        "architect": "Gary Player",
        "description": (
            "Gary Player 設計，三場中最平易近人。Par 69、白梯 5906 碼，"
            "可步行或乘球車，前九丘陵起伏、後九連續長 Par 4 考驗耐力。"
        ),
        "location": "西貢滘西洲",
        "country": "香港",
        "hero_image": f"{_IMG}/ksc-south.jpg",
        "slope": 125, "rating": 68.7,
        "tees": {
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _KSC_SOUTH_PARS, "yardages": _KSC_SOUTH_WHITE,
                "handicap": _KSC_SOUTH_HCP, "slope": 125, "rating": 68.7,
            },
            "yellow": {
                "id": "yellow", "name": "黃梯", "name_en": "Yellow Tee",
                "pars": _KSC_SOUTH_PARS, "yardages": _KSC_SOUTH_YELLOW,
                "handicap": _KSC_SOUTH_HCP, "slope": 121, "rating": 66.4,
            },
        },
    },
    "ksc-north": {
        "id": "ksc-north",
        "name": "滘西洲高爾夫球場 · 北場",
        "name_en": "Kau Sai Chau - North",
        "architect": "Gary Player",
        "description": (
            "Gary Player 設計，香港最佳球場之一（Golf Digest 2022 年第 2 名）。"
            "Par 72、白梯 6357 碼，純步行球場，兩個 Par 3 跨越海灣，震撼人心。"
        ),
        "location": "西貢滘西洲",
        "country": "香港",
        "hero_image": f"{_IMG}/ksc-north.jpg",
        "slope": 133, "rating": 71.2,
        "tees": {
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _KSC_NORTH_PARS, "yardages": _KSC_NORTH_BLUE,
                "handicap": _KSC_NORTH_HCP, "slope": 134, "rating": 73.4,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _KSC_NORTH_PARS, "yardages": _KSC_NORTH_WHITE,
                "handicap": _KSC_NORTH_HCP, "slope": 133, "rating": 71.2,
            },
            "yellow": {
                "id": "yellow", "name": "黃梯", "name_en": "Yellow Tee",
                "pars": _KSC_NORTH_PARS, "yardages": _KSC_NORTH_YELLOW,
                "handicap": _KSC_NORTH_HCP, "slope": 122, "rating": 69.5,
            },
        },
    },
    "hk-cwbgc": {
        "id": "hk-cwbgc",
        "name": "清水灣高爾夫球場",
        "name_en": "Clear Water Bay Golf & Country Club",
        "architect": "T. Sawai & A. Furukawa（2006 年 Thomson & Perret 重設計）",
        "description": (
            "1982 年開幕，私人會員制。Par 70，黑梯 6608 碼（CR 73.4 / SR 140）、"
            "白梯 5793 碼。六個 Par 3 均超過 150 碼且有海景壓迫，堪稱港島最難短洞組合。"
        ),
        "location": "清水灣，西貢（Po Toi O）",
        "country": "香港",
        "hero_image": f"{_IMG}/hk-cwbgc.jpg",
        "slope": 123, "rating": 69.2,
        "tees": {
            "black": {
                "id": "black", "name": "黑梯", "name_en": "Black Tee",
                "pars": _CWBGC_PARS, "yardages": _CWBGC_BLACK,
                "handicap": _CWBGC_HCP, "slope": 140, "rating": 73.4,
            },
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _CWBGC_PARS, "yardages": _CWBGC_BLUE,
                "handicap": _CWBGC_HCP, "slope": 128, "rating": 71.4,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _CWBGC_PARS, "yardages": _CWBGC_WHITE,
                "handicap": _CWBGC_HCP, "slope": 123, "rating": 69.2,
            },
            "red": {
                "id": "red", "name": "紅梯（女士）", "name_en": "Red Tee (Ladies)",
                "pars": _CWBGC_PARS, "yardages": _CWBGC_RED,
                "handicap": _CWBGC_HCP, "slope": 123, "rating": 71.6,
            },
        },
    },
    "hk-fanling-eden": {
        "id": "hk-fanling-eden",
        "name": "香港哥爾夫球會 · 粉嶺 Eden 場",
        "name_en": "Hong Kong Golf Club - Eden Course",
        "architect": "1970 年建造，多次由 HKGC 更新",
        "description": (
            "1970 年建造，三場中最緊湊精準。錦標梯 Par 70、6106 碼（CR 70.7 / SR 130）。"
            "10 個洞組成香港高球公開賽「合成場」，18 洞 The Ultimate 以水障收尾。"
        ),
        "location": "粉嶺",
        "country": "香港",
        "hero_image": f"{_IMG}/hk-fanling-eden.jpg",
        "slope": 130, "rating": 70.7,
        "tees": {
            "championship": {
                "id": "championship", "name": "錦標梯", "name_en": "Championship Tee",
                "pars": _HKGC_EDEN_PARS, "yardages": _HKGC_EDEN_CHAMP,
                "handicap": _HKGC_EDEN_HCP, "slope": 130, "rating": 70.7,
            },
            "club": {
                "id": "club", "name": "會員梯", "name_en": "Club Tee",
                "pars": _HKGC_EDEN_PARS, "yardages": _HKGC_EDEN_CLUB,
                "handicap": _HKGC_EDEN_HCP, "slope": 126, "rating": 68.8,
            },
            "forward": {
                "id": "forward", "name": "前梯", "name_en": "Forward Tee",
                "pars": _HKGC_EDEN_PARS, "yardages": _HKGC_EDEN_FWD,
                "handicap": _HKGC_EDEN_HCP, "slope": 123, "rating": 67.4,
            },
        },
    },
    # ── 馬來西亞 ──────────────────────────────────────────────────────────────
    "my-templer": {
        "id": "my-templer",
        "name": "Templer Park Country Club",
        "name_en": "Templer Park Country Club",
        "architect": "Masashi (Jumbo) Ozaki & Kentaro Sato",
        "description": (
            "Jumbo Ozaki 與 Kentaro Sato 設計，吉隆坡近郊石灰岩絕壁下的錦標名場。"
            "Par 72，黑梯 7143 碼（CR 73.2 / SR 131），白梯 6343 碼（CR 69.8 / SR 124）。"
            "曾舉辦 1995、1996 及 2000 年馬來西亞公開賽。"
        ),
        "location": "雪蘭莪 Rawang",
        "country": "馬來西亞",
        "hero_image": f"{_IMG}/my-templer.jpg",
        "slope": 124, "rating": 69.8,
        "tees": {
            "black": {
                "id": "black", "name": "黑梯", "name_en": "Black Tee",
                "pars": _TPCC_PARS, "yardages": _TPCC_BLACK,
                "handicap": _TPCC_HCP, "slope": 131, "rating": 73.2,
            },
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _TPCC_PARS, "yardages": _TPCC_BLUE,
                "handicap": _TPCC_HCP, "slope": 127, "rating": 71.6,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _TPCC_PARS, "yardages": _TPCC_WHITE,
                "handicap": _TPCC_HCP, "slope": 124, "rating": 69.8,
            },
            "red": {
                "id": "red", "name": "紅梯", "name_en": "Red Tee",
                "pars": _TPCC_PARS, "yardages": _TPCC_RED,
                "handicap": _TPCC_HCP, "slope": 113, "rating": 69.0,
            },
        },
    },
    "my-genting": {
        "id": "my-genting",
        "name": "雲頂高原 · Awana 球場",
        "name_en": "Awana Genting Highlands Golf & Country Resort",
        "architect": "Ronald Fream",
        "description": (
            "Ronald Fream 設計，海拔約 900 公尺（3000 呎），全年涼爽。"
            "Par 71、白梯 5884 碼，雨林球道縱橫，是東南亞最獨特的高原球場體驗。"
        ),
        "location": "彭亨雲頂",
        "country": "馬來西亞",
        "hero_image": f"{_IMG}/my-genting.jpg",
        "slope": 120, "rating": 68.5,
        "tees": {
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _GENTING_PARS, "yardages": _GENTING_WHITE,
                "handicap": _GENTING_HCP, "slope": 120, "rating": 68.5,
            },
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _GENTING_PARS, "yardages": _GENTING_BLUE,
                "handicap": _GENTING_HCP, "slope": 124, "rating": 70.2,
            },
        },
    },
    # ── 泰國 ──────────────────────────────────────────────────────────────────
    "th-alpine": {
        "id": "th-alpine",
        "name": "Alpine Golf & Sports Club",
        "name_en": "Alpine Golf & Sports Club",
        "architect": "Ron M. Garl",
        "description": (
            "Ron Garl 設計，曼谷近郊 Pathum Thani 最負盛名的錦標球場。"
            "Par 72，黑梯 7100 碼（CR 75.3 / SR 148），白梯 6048 碼（CR 70.0 / SR 134）。"
            "2000 年 Johnnie Walker Classic Tiger Woods 奪冠地；7、11 洞為島嶼果嶺。"
        ),
        "location": "曼谷 Pathum Thani",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-alpine.jpg",
        "slope": 134, "rating": 70.0,
        "tees": {
            "black": {
                "id": "black", "name": "黑梯", "name_en": "Black Tee",
                "pars": _ALPINE_PARS, "yardages": _ALPINE_BLACK,
                "handicap": _ALPINE_HCP, "slope": 148, "rating": 75.3,
            },
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _ALPINE_PARS, "yardages": _ALPINE_BLUE,
                "handicap": _ALPINE_HCP, "slope": 142, "rating": 72.5,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _ALPINE_PARS, "yardages": _ALPINE_WHITE,
                "handicap": _ALPINE_HCP, "slope": 134, "rating": 70.0,
            },
            "red": {
                "id": "red", "name": "紅梯", "name_en": "Red Tee",
                "pars": _ALPINE_PARS, "yardages": _ALPINE_RED,
                "handicap": _ALPINE_HCP, "slope": 128, "rating": 71.1,
            },
        },
    },
    "th-tcc": {
        "id": "th-tcc",
        "name": "Thai Country Club",
        "name_en": "Thai Country Club",
        "architect": "Denis Griffiths",
        "description": (
            "Denis Griffiths 設計，亞洲頂尖私人球場之一。Par 72，黑梯 7097 碼（CR 74.2 / SR 133），"
            "白梯 6034 碼（CR 69.4 / SR 122）。曾舉辦 Volvo Masters、亞洲本田經典賽，"
            "以精準球道管理與高速果嶺著稱，距素萬那普機場僅 25 分鐘。"
        ),
        "location": "曼谷 Chachoengsao（Km 35.5）",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-tcc.jpg",
        "slope": 122, "rating": 69.4,
        "tees": {
            "black": {
                "id": "black", "name": "黑梯", "name_en": "Black Tee",
                "pars": _TCC_TH_PARS, "yardages": _TCC_TH_BLACK,
                "handicap": _TCC_TH_HCP, "slope": 133, "rating": 74.2,
            },
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _TCC_TH_PARS, "yardages": _TCC_TH_BLUE,
                "handicap": _TCC_TH_HCP, "slope": 127, "rating": 71.6,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _TCC_TH_PARS, "yardages": _TCC_TH_WHITE,
                "handicap": _TCC_TH_HCP, "slope": 122, "rating": 69.4,
            },
            "red": {
                "id": "red", "name": "紅梯", "name_en": "Red Tee",
                "pars": _TCC_TH_PARS, "yardages": _TCC_TH_RED,
                "handicap": _TCC_TH_HCP, "slope": 119, "rating": 71.1,
            },
        },
    },
    "th-thana": {
        "id": "th-thana",
        "name": "Thana City Country Club",
        "name_en": "Thana City Country Club",
        "architect": "Greg Norman",
        "description": (
            "Greg Norman 設計，泰國唯一由其親自操刀的 18 洞錦標場。"
            "Par 72、白梯 6342 碼（CR 71.8 / SR 128）。以多座島嶼果嶺聞名，"
            "14 洞 Par 5 全長 482 碼是全場決勝關鍵，距素萬那普機場僅 15 分鐘。"
        ),
        "location": "曼谷 Samut Prakan",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-thana.jpg",
        "slope": 128, "rating": 71.8,
        "tees": {
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _THANA_PARS, "yardages": _THANA_WHITE,
                "handicap": _THANA_HCP, "slope": 128, "rating": 71.8,
            },
        },
    },
    "th-summit": {
        "id": "th-summit",
        "name": "Summit Windmill Golf Club",
        "name_en": "Summit Windmill Golf Club",
        "architect": "Nick Faldo",
        "description": (
            "Nick Faldo 1993 年設計，度假式球場兼具日／夜間球局。Par 72，"
            "藍梯 6964 碼（CR 73.1 / SR 123），白梯 6211 碼（CR 70.7 / SR 121）。"
            "湖泊水障策略性強，距曼谷市中心僅 26 公里，交通便利。"
        ),
        "location": "曼谷 Samut Prakan（Km 10.5）",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-summit.jpg",
        "slope": 121, "rating": 70.7,
        "tees": {
            "blue": {
                "id": "blue", "name": "藍梯", "name_en": "Blue Tee",
                "pars": _SUMMIT_PARS, "yardages": _SUMMIT_BLUE,
                "handicap": _SUMMIT_HCP, "slope": 123, "rating": 73.1,
            },
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _SUMMIT_PARS, "yardages": _SUMMIT_WHITE,
                "handicap": _SUMMIT_HCP, "slope": 121, "rating": 70.7,
            },
            "orange": {
                "id": "orange", "name": "橙梯", "name_en": "Orange Tee",
                "pars": _SUMMIT_PARS, "yardages": _SUMMIT_ORANGE,
                "handicap": _SUMMIT_HCP, "slope": 117, "rating": 69.2,
            },
        },
    },
    "th-panya": {
        "id": "th-panya",
        "name": "Panya Indra · Lagoon + Palm",
        "name_en": "Panya Indra Golf Club (Lagoon + Palm)",
        "architect": "Ronald Fream",
        "description": (
            "Ronald Fream 設計 27 洞名場，Lagoon 與 Palm 兩九組合。"
            "Par 72、白梯 6744 碼，水障與棕櫚球道，曾多次舉辦 LPGA 賽事。"
            "全場 10 個洞涉及水障，第 5、14 洞為超長 Par 5 考驗距離。"
        ),
        "location": "曼谷 Khan Na Yao",
        "country": "泰國",
        "hero_image": f"{_IMG}/th-panya.jpg",
        "slope": 132, "rating": 72.0,
        "tees": {
            "white": {
                "id": "white", "name": "白梯", "name_en": "White Tee",
                "pars": _PANYA_PARS, "yardages": _PANYA_WHITE,
                "handicap": _PANYA_HCP, "slope": 132, "rating": 72.0,
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
                "course_rating": t.get("course_rating") or t.get("rating"),
                "slope_rating": t.get("slope_rating") or t.get("slope"),
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
