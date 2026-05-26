"""球場 Hero 圖片：啟動時確保 static/img 內有各場專屬照片"""

import os
import shutil

from courses import COURSES, _HERO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_IMG = os.path.join(BASE_DIR, "static", "img")

# 來源檔 → 目標檔（若目標不存在時從本機複製）
_LOCAL_FALLBACKS = {
    "ksc-south.jpg": os.path.join(BASE_DIR, "south_course_hole12.jpg"),
    "ksc-aerial.jpg": os.path.join(BASE_DIR, "course_aerial.jpg"),
}


def ensure_course_images():
    """確保每個球場的 hero 圖存在；必要時從本機備援複製。"""
    os.makedirs(STATIC_IMG, exist_ok=True)

    for course in COURSES.values():
        rel = course.get("hero_image", _HERO)
        if not rel.startswith("/static/img/"):
            continue
        name = os.path.basename(rel)
        dst = os.path.join(STATIC_IMG, name)
        if os.path.isfile(dst):
            continue
        src = _LOCAL_FALLBACKS.get(name)
        if src and os.path.isfile(src):
            shutil.copy2(src, dst)

    # 首頁預設 hero（南場第 12 洞）
    hero_dst = os.path.join(STATIC_IMG, "hero.jpg")
    south_src = os.path.join(STATIC_IMG, "ksc-south.jpg")
    fallback = _LOCAL_FALLBACKS.get("ksc-south.jpg")
    if not os.path.isfile(hero_dst):
        if os.path.isfile(south_src):
            shutil.copy2(south_src, hero_dst)
        elif fallback and os.path.isfile(fallback):
            shutil.copy2(fallback, hero_dst)
