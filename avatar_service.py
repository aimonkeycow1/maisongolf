"""會員頭像上傳、處理與儲存"""

from __future__ import annotations

import os
import uuid

from PIL import Image

from round_storage import BASE_DIR

AVATAR_DIR = os.path.join(BASE_DIR, "static", "uploads", "avatars")
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 2 * 1024 * 1024
AVATAR_SIZE = (256, 256)


def _ensure_avatar_dir() -> None:
    os.makedirs(AVATAR_DIR, exist_ok=True)


def avatar_relative_path(user_id: int) -> str:
    return f"uploads/avatars/user_{int(user_id)}.jpg"


def avatar_disk_path(user_id: int) -> str:
    return os.path.join(BASE_DIR, "static", avatar_relative_path(user_id))


def save_user_avatar(user_id: int, file_storage) -> tuple[str | None, str | None]:
    """儲存並壓縮頭像，回傳 (static 相對路徑, 錯誤訊息)。"""
    if not file_storage or not file_storage.filename:
        return None, "請選擇頭像圖片"

    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return None, "僅支援 JPG、PNG、WEBP"

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_BYTES:
        return None, "頭像檔案不可超過 2MB"

    _ensure_avatar_dir()
    dest = avatar_disk_path(user_id)
    tmp = dest + f".{uuid.uuid4().hex}.tmp"

    try:
        img = Image.open(file_storage.stream)
        img = img.convert("RGB")
        img.thumbnail(AVATAR_SIZE, Image.Resampling.LANCZOS)
        w, h = img.size
        if w != h:
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize(AVATAR_SIZE, Image.Resampling.LANCZOS)
        img.save(tmp, format="JPEG", quality=88, optimize=True)
        os.replace(tmp, dest)
    except Exception:
        if os.path.isfile(tmp):
            os.remove(tmp)
        return None, "無法讀取圖片，請換一張試試"
    finally:
        file_storage.stream.seek(0)

    return avatar_relative_path(user_id), None


def remove_user_avatar(user_id: int, current_path: str | None = None) -> None:
    path = avatar_disk_path(user_id)
    if os.path.isfile(path):
        os.remove(path)
    if current_path and current_path != avatar_relative_path(user_id):
        legacy = os.path.join(BASE_DIR, "static", current_path)
        if os.path.isfile(legacy):
            os.remove(legacy)
