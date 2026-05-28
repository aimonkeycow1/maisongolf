"""球場 Hero 圖片：啟動時確保 static/img 內有各場專屬真實照片"""

import os
import shutil
import subprocess

from courses import COURSES, _HERO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_IMG = os.path.join(BASE_DIR, "static", "img")
HERO_JPG = os.path.join(STATIC_IMG, "hero.jpg")

# 來源檔 → 目標檔（若目標不存在時從本機備援複製）
_LOCAL_FALLBACKS = {
    "ksc-south.jpg": os.path.join(BASE_DIR, "south_course_hole12.jpg"),
    "ksc-aerial.jpg": os.path.join(BASE_DIR, "course_aerial.jpg"),
}

# 遠端真實球場照片（球會官網 / GolfDD 球場相簿 / Wikimedia Commons）
_REMOTE_HERO_URLS = {
    "ksc-east.jpg": "https://commons.wikimedia.org/wiki/Special:FilePath/Kau_Sai_Chau_01.jpg?width=1600",
    "ksc-north.jpg": (
        "https://commons.wikimedia.org/wiki/Special:FilePath/"
        "Kau_Sai_Chau_The_Jockey_Club_Public_Golf_Course_outside_28-03-2016(4).jpg?width=1600"
    ),
    "my-genting.jpg": (
        "https://commons.wikimedia.org/wiki/Special:FilePath/"
        "Genting-Highlands_Malaysia_Resorts-World-Genting-01.jpg?width=1600"
    ),
    "my-templer.jpg": (
        "https://commons.wikimedia.org/wiki/Special:FilePath/"
        "Shangri-La%27s_Rasa_Sayang_Resort_%26_Spa_-_Golf_Course.jpg?width=1600"
    ),
    "th-alpine.jpg": "https://www.alpinegolfclub.com/wp-content/uploads/2020/04/Cover-01.jpg",
    "th-tcc.jpg": "https://www.golfdd.com/u/course-photo/52_2335.jpg",
    "th-thana.jpg": "https://www.golfdd.com/u/course-photo/3_2420.jpg",
    "th-summit.jpg": "https://www.golfdd.com/u/course-photo/10_1786.jpg",
    "th-panya.jpg": "https://www.panyagolf.com/wp-content/uploads/2021/03/DJI_0743.jpg",
    # 吉隆坡球場（Unsplash placeholder，可之後換成球會授權圖）
    "kl-gcc-west.jpg": "https://images.unsplash.com/photo-1535131749006-b7f58c990b8e?auto=format&fit=crop&w=1600&q=80",
    "kl-gcc-east.jpg": "https://images.unsplash.com/photo-1587174482993-4eccc5aa6169?auto=format&fit=crop&w=1600&q=80",
    "kl-mines.jpg": "https://images.unsplash.com/photo-1596727147705-61a532a659b9?auto=format&fit=crop&w=1600&q=80",
    "kl-saujana-palm.jpg": "https://images.unsplash.com/photo-1592919505780-763a58753d32?auto=format&fit=crop&w=1600&q=80",
    "kl-glenmarie-valley.jpg": "https://images.unsplash.com/photo-1593111778420-763a58753d32?auto=format&fit=crop&w=1600&q=80",
    "kl-tropicana-east.jpg": "https://images.unsplash.com/photo-1596727147705-61a532a659b9?auto=format&fit=crop&w=1600&q=80",
}

_MAX_WIDTH = 1920


def _is_placeholder(dst: str) -> bool:
    """與 hero.jpg 同大小的檔案視為尚未換上的佔位圖。"""
    if not os.path.isfile(dst):
        return True
    if not os.path.isfile(HERO_JPG):
        return False
    return os.path.getsize(dst) == os.path.getsize(HERO_JPG)


def _curl_download(url: str, dst: str) -> bool:
    try:
        subprocess.run(
            ["curl", "-fsSL", "-A", "MaisonGolf/1.0", "-o", dst, url],
            check=True,
            capture_output=True,
            timeout=120,
        )
        if not os.path.isfile(dst) or os.path.getsize(dst) < 8000:
            return False
        kind = subprocess.check_output(["file", "-b", dst], text=True).lower()
        return "jpeg" in kind or "png" in kind or "webp" in kind
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False


def _resize_if_needed(path: str) -> None:
    try:
        out = subprocess.check_output(
            ["sips", "-g", "pixelWidth", path],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        for line in out.splitlines():
            if "pixelWidth" in line:
                width = int(line.split()[-1])
                if width > _MAX_WIDTH:
                    subprocess.run(
                        ["sips", "-Z", str(_MAX_WIDTH), path, "--out", path],
                        check=True,
                        capture_output=True,
                    )
                break
    except (subprocess.CalledProcessError, ValueError, OSError):
        pass


def _fetch_remote_heroes():
    os.makedirs(STATIC_IMG, exist_ok=True)
    for name, url in _REMOTE_HERO_URLS.items():
        dst = os.path.join(STATIC_IMG, name)
        if os.path.isfile(dst) and not _is_placeholder(dst):
            continue
        tmp = dst + ".part"
        if _curl_download(url, tmp):
            os.replace(tmp, dst)
            _resize_if_needed(dst)
        elif os.path.isfile(tmp):
            os.remove(tmp)


def ensure_course_images():
    """確保每個球場的 hero 圖存在；必要時下載遠端真實照片或從本機備援複製。"""
    os.makedirs(STATIC_IMG, exist_ok=True)
    _fetch_remote_heroes()

    for course in COURSES.values():
        rel = course.get("hero_image", _HERO)
        if not rel.startswith("/static/img/"):
            continue
        name = os.path.basename(rel)
        dst = os.path.join(STATIC_IMG, name)
        if os.path.isfile(dst) and not _is_placeholder(dst):
            continue
        src = _LOCAL_FALLBACKS.get(name)
        if src and os.path.isfile(src):
            shutil.copy2(src, dst)
            continue
        if os.path.isfile(HERO_JPG) and _is_placeholder(dst):
            shutil.copy2(HERO_JPG, dst)

    # 首頁預設 hero（南場第 12 洞）
    south_src = os.path.join(STATIC_IMG, "ksc-south.jpg")
    fallback = _LOCAL_FALLBACKS.get("ksc-south.jpg")
    if not os.path.isfile(HERO_JPG):
        if os.path.isfile(south_src):
            shutil.copy2(south_src, HERO_JPG)
        elif fallback and os.path.isfile(fallback):
            shutil.copy2(fallback, HERO_JPG)
