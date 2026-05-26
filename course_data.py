# 香港賽馬會滘西洲公眾高爾夫球場 · 南場
# 數據來源：公開記分卡（白梯 White Tee，總長 5906 碼，Par 69）

COURSE_NAME = "滘西洲高爾夫球場 · 南場"
COURSE_NAME_EN = "Kau Sai Chau Public Golf Course - South"

# 每一洞的標準桿
PARS = [4, 3, 4, 4, 3, 4, 4, 4, 4, 4, 3, 4, 4, 4, 5, 3, 4, 4]

# 白梯碼數（碼）
YARDAGES_WHITE = [
    341, 149, 429, 285, 134, 301, 307, 315, 362,
    317, 159, 417, 377, 464, 577, 198, 375, 399,
]

# 差點（難度排名，1 最難）
HANDICAP = [5, 11, 1, 17, 7, 15, 9, 13, 3, 16, 14, 4, 10, 2, 8, 6, 18, 12]

PAR_TOTAL = sum(PARS)       # 69
PAR_FRONT = sum(PARS[:9])   # 34
PAR_BACK = sum(PARS[9:])    # 35
YARDAGE_TOTAL = sum(YARDAGES_WHITE)
