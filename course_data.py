# 向後相容：CLI（golf_score.py）預設使用滘西洲南場白梯
# 多球場資料請見 courses.py

from courses import DEFAULT_COURSE_ID, DEFAULT_TEE_ID, get_tee

_default = get_tee(DEFAULT_COURSE_ID, DEFAULT_TEE_ID)

COURSE_NAME = _default["course_name"]
COURSE_NAME_EN = "Kau Sai Chau Public Golf Course - South"
PARS = _default["pars"]
YARDAGES_WHITE = _default["yardages"]
HANDICAP = _default["handicap"]
PAR_TOTAL = _default["par_total"]
PAR_FRONT = _default["par_front"]
PAR_BACK = _default["par_back"]
YARDAGE_TOTAL = _default["yardage_total"]
