"""會員頭像上傳、處理與儲存"""

from __future__ import annotations

import os
import uuid
from io import BytesIO

from PIL import Image
from werkzeug.utils import secure_filename

from round_storage import BASE_DIR

# Render 可設定 INSTANCE_DATA_DIR 掛載持久化磁碟；否則存於 static/uploads/avatars
_DATA_ROOT = (os.environ.get("INSTANCE_DATA_DIR") or "").strip()
if _DATA_ROOT:
    AVATAR_DIR = os.path.join(_DATA_ROOT, "avatars")
else:
    AVATAR_DIR = os.path.join(BASE_DIR, "static", "uploads", "avatars")

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
MAX_BYTES = 2 * 1024 * 1024
AVATAR_SIZE = (256, 256)


def ensure_avatar_upload_dir() -> None:
    """啟動時建立上傳目錄（Render 首次部署時 static/uploads 可能不存在）。"""
    os.makedirs(AVATAR_DIR, exist_ok=True)
    if not _DATA_ROOT:
        legacy = os.path.join(BASE_DIR, "static", "uploads", "avatars")
        if legacy != AVATAR_DIR:
            os.makedirs(legacy, exist_ok=True)


def avatar_relative_path(user_id: int) -> str:
    """資料庫標記用（邏輯路徑，實際檔案由 avatar_disk_path 決定）。"""
    return f"uploads/avatars/user_{int(user_id)}.jpg"


def avatar_disk_path(user_id: int) -> str:
    return os.path.join(AVATAR_DIR, f"user_{int(user_id)}.jpg")


def avatar_exists_on_disk(user_id: int) -> bool:
    return os.path.isfile(avatar_disk_path(user_id))


def _guess_ext(filename: str, content_type: str | None, raw: bytes) -> str | None:
    name = secure_filename(filename or "") or ""
    ext = os.path.splitext(name)[1].lower()
    if ext in ALLOWED_EXT:
        return ext
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in MIME_EXT:
        return MIME_EXT[ct]
    if raw[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    # HEIC/HEIF（常見於 iPhone）
    if len(raw) >= 12 and raw[4:8] in (b"ftyp",):
        brand = raw[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"mif1"):
            return ".heic"
    return None


def _open_image(raw: bytes, ext: str) -> Image.Image:
    buf = BytesIO(raw)
    try:
        img = Image.open(buf)
        img.load()
        return img
    except Exception as exc:
        if ext in (".heic", ".heif"):
            raise ValueError(
                "iPhone HEIC 格式目前無法處理，請在相簿中「分享→儲存圖片」"
                " 或將相機格式改為「最相容」後再試"
            ) from exc
        raise ValueError("無法讀取圖片，請換一張 JPG 或 PNG 試試") from exc


def save_user_avatar(user_id: int, file_storage) -> tuple[str | None, str | None]:
    """儲存並壓縮頭像，回傳 (邏輯路徑, 錯誤訊息)。"""
    if not file_storage:
        return None, "請選擇頭像圖片"

    raw = file_storage.read()
    if not raw:
        return None, "請選擇頭像圖片"

    if len(raw) > MAX_BYTES:
        return None, "頭像檔案不可超過 2MB"

    ext = _guess_ext(getattr(file_storage, "filename", "") or "", file_storage.content_type, raw)
    if not ext:
        return None, "僅支援 JPG、PNG、WEBP（iPhone 請先儲存為 JPG 再上傳）"

    ensure_avatar_upload_dir()
    dest = avatar_disk_path(user_id)
    tmp = dest + f".{uuid.uuid4().hex}.tmp"

    try:
        img = _open_image(raw, ext)
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
    except ValueError as e:
        if os.path.isfile(tmp):
            os.remove(tmp)
        return None, str(e)
    except OSError:
        if os.path.isfile(tmp):
            os.remove(tmp)
        return None, "伺服器無法寫入頭像檔，請稍後再試或聯絡管理員"
    except Exception:
        if os.path.isfile(tmp):
            os.remove(tmp)
        return None, "無法處理這張圖片，請換一張試試"

    return avatar_relative_path(user_id), None


def remove_user_avatar(user_id: int, current_path: str | None = None) -> None:
    path = avatar_disk_path(user_id)
    if os.path.isfile(path):
        os.remove(path)
    if current_path and current_path != avatar_relative_path(user_id):
        legacy = os.path.join(BASE_DIR, "static", current_path)
        if os.path.isfile(legacy):
            os.remove(legacy)
